"""The Settings window. Every control saves to disk and takes effect immediately —
there is no Save or Apply button."""
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (QDoubleSpinBox, QFrame, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QSpinBox, QVBoxLayout,
                               QWidget)

from app import autostart
from app.reminder import REMINDER_TYPES, ReminderEngine
from app.settings import Settings
from app.ui.icons import make_app_icon
from app.ui.theme import ACCENTS, DEFAULT_ACCENT, current_palette, popup_stylesheet
from app.ui.widgets import ToggleSwitch

EXTRA_STYLE = """
QLabel#hero {{ font-size: 22px; font-weight: 700; color: {title}; }}
QLabel#subtitle {{ font-size: 12px; color: {message}; }}
QLabel#rowname {{ font-size: 14px; font-weight: 600; color: {title}; }}
QLabel#rowcaption {{ font-size: 11.5px; color: {message}; }}
QLabel#section {{ font-size: 11px; font-weight: 700; color: {message}; letter-spacing: 0.5px; }}
QFrame#card {{ background: {card_alt}; border-radius: 16px; }}
QSpinBox, QDoubleSpinBox {{
    background: {spin_bg}; color: {title}; border: 1px solid {edge}; border-radius: 10px;
    padding: 4px 6px; min-height: 26px; min-width: 62px; font-size: 13px; font-weight: 600;
}}
QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    width: 16px; border: none;
}}
QPushButton#try {{ background: transparent; color: {accent}; font-size: 12px; font-weight: 700;
                   border: none; padding: 2px 6px; text-align: left; }}
QPushButton#try:hover {{ text-decoration: underline; }}
QPushButton#try:disabled {{ color: {message}; }}
"""


class SettingsWindow(QWidget):
    """`settings_path` lets tests (and, if ever needed, --portable mode) redirect where
    changes are written; production code leaves it as None (the OS-standard location)."""

    def __init__(self, engine: ReminderEngine, settings: Settings,
                 settings_path: str | None = None):
        super().__init__()
        self.engine, self.settings, self._path = engine, settings, settings_path
        pal = current_palette()
        self._pal = pal
        self.setWindowTitle("Nudge Settings")
        self.setWindowIcon(make_app_icon(False))
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.resize(520, 640)

        spin_bg = pal.card.name() if not pal.dark else "#2E2A3B"
        card_alt = "#F7F5FC" if not pal.dark else "#2A2735"
        self.setStyleSheet(
            popup_stylesheet(DEFAULT_ACCENT, pal)
            + EXTRA_STYLE.format(title=pal.title.name(), message=pal.message.name(),
                                 edge=pal.edge.name(), spin_bg=spin_bg, card_alt=card_alt,
                                 accent=DEFAULT_ACCENT.main))
        self.setStyleSheet(self.styleSheet() + f"\nSettingsWindow {{ background: {pal.card.name()}; }}")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(frameShape=QFrame.NoFrame, widgetResizable=True)
        # Otherwise the scroll area's own (always-white) background sits on top of ours.
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.viewport().setStyleSheet("background: transparent;")
        outer.addWidget(scroll)
        body = QWidget()
        body.setAttribute(Qt.WA_StyledBackground, True)
        body.setStyleSheet("background: transparent;")
        scroll.setWidget(body)
        root = QVBoxLayout(body)
        root.setContentsMargins(26, 24, 26, 24)
        root.setSpacing(18)

        head = QVBoxLayout()
        head.setSpacing(2)
        head.addWidget(QLabel("Nudge Settings", objectName="hero"))
        head.addWidget(QLabel("Everything here saves automatically.", objectName="subtitle"))
        root.addLayout(head)

        root.addWidget(self._section("REMINDERS"))
        self._interval_spins: dict[str, QDoubleSpinBox] = {}
        self._toggles: dict[str, ToggleSwitch] = {}
        self._try_buttons: dict[str, QPushButton] = {}
        for key, rt in REMINDER_TYPES.items():
            root.addWidget(self._reminder_card(key, rt, pal))

        root.addWidget(self._section("GENERAL"))
        general = QFrame(objectName="card")
        gl = QVBoxLayout(general)
        gl.setContentsMargins(18, 14, 18, 14)
        gl.setSpacing(14)

        self.snooze_spin = self._spin(QSpinBox, self.settings.snooze_minutes, 1, 120, " min")
        gl.addLayout(self._field_row("Snooze duration", "Wait time after \u201cLater\u201d", self.snooze_spin))
        self.snooze_spin.valueChanged.connect(self._on_snooze_changed)

        self.focus_break_spin = self._spin(QSpinBox, self.settings.break_minutes, 1, 60, " min")
        gl.addLayout(self._field_row("Focus break length",
                                     "How long the focus timer waits before counting again",
                                     self.focus_break_spin))
        self.focus_break_spin.valueChanged.connect(self._on_focus_break_changed)

        gl.addWidget(self._hair())
        self.sounds_toggle = self._toggle_row(gl, "Sounds", "Play a soft chime with each reminder",
                                              self.settings.sounds, self._on_sounds_toggled)
        self.animations_toggle = self._toggle_row(gl, "Animations", "Motion in popups and the mascot",
                                                   self.settings.animations, self._on_animations_toggled)

        gl.addWidget(self._hair())
        supported = autostart.is_supported()
        caption = "Launch quietly in the tray when you log in" if supported else "Windows only"
        self.autostart_toggle = self._toggle_row(
            gl, "Start with Windows", caption,
            self.settings.start_with_windows if supported else False, self._on_autostart_toggled)
        self.autostart_toggle.setEnabled(supported)

        gl.addWidget(self._hair())
        self.pause_toggle = self._toggle_row(gl, "Pause all reminders",
                                             "Turn every reminder off without changing your settings",
                                             self.engine.paused, self._on_pause_all_toggled)
        root.addWidget(general)
        root.addStretch(1)
        self.engine.state_changed.connect(self._sync_pause_toggle)

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(250)
        self._save_timer.timeout.connect(self._flush_save)

    # ---- small builders -------------------------------------------------
    def _section(self, text: str) -> QLabel:
        return QLabel(text, objectName="section")

    def _hair(self) -> QFrame:
        # Styled inline, not via the "#hair" QSS rule: the scroll area's body widget sets its
        # own stylesheet (so the window's dark/light fill shows through it), and once any
        # ancestor in the chain has its own stylesheet, Qt stops cascading ID-selector rules
        # from further up to *that ancestor's descendants* — so a rule defined on the window
        # never reaches a widget inside the scroll area. Setting the colour directly sidesteps it.
        line = QFrame(objectName="hair")
        line.setAttribute(Qt.WA_StyledBackground, True)
        line.setFixedHeight(1)
        c = self._pal.edge
        line.setStyleSheet(f"background-color: rgba({c.red()}, {c.green()}, {c.blue()}, {c.alphaF():.3f});")
        return line

    def _spin(self, cls, value, minimum, maximum, suffix):
        s = cls()
        s.setRange(minimum, maximum)
        s.setSuffix(suffix)
        s.setValue(value)
        s.setAlignment(Qt.AlignRight)
        return s

    def _field_row(self, title: str, caption: str, control: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)
        texts = QVBoxLayout()
        texts.setSpacing(1)
        texts.addWidget(QLabel(title, objectName="rowname"))
        texts.addWidget(QLabel(caption, objectName="rowcaption"))
        row.addLayout(texts, 1)
        row.addWidget(control, 0, Qt.AlignRight)
        return row

    def _toggle_row(self, layout: QVBoxLayout, title: str, caption: str,
                    checked: bool, handler) -> ToggleSwitch:
        toggle = ToggleSwitch(checked, DEFAULT_ACCENT.main, current_palette())
        layout.addLayout(self._field_row(title, caption, toggle))
        toggle.toggled.connect(handler)
        return toggle

    def _reminder_card(self, key: str, rt, pal) -> QFrame:
        accent = ACCENTS[key]
        cfg = self.settings.reminders[key]
        card = QFrame(objectName="card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(10)
        top.addWidget(QLabel(f"{rt.emoji}  {rt.label}", objectName="rowname"), 1)
        toggle = ToggleSwitch(cfg.enabled, accent.main, pal)
        toggle.toggled.connect(lambda checked, k=key: self._on_enabled_changed(k, checked))
        top.addWidget(toggle, 0, Qt.AlignRight)
        layout.addLayout(top)
        self._toggles[key] = toggle

        bottom = QHBoxLayout()
        bottom.setSpacing(10)
        if key == "focus":
            work = self._spin(QSpinBox, int(cfg.interval_minutes), 10, 180, " min work")
            work.valueChanged.connect(lambda v, k=key: self._on_interval_changed(k, float(v)))
            bottom.addWidget(work)
            self._interval_spins[key] = work
        else:
            interval = self._spin(QDoubleSpinBox, cfg.interval_minutes, 5, 240, " min")
            interval.setDecimals(0)
            interval.valueChanged.connect(lambda v, k=key: self._on_interval_changed(k, float(v)))
            bottom.addWidget(QLabel("Every"))
            bottom.addWidget(interval)
            self._interval_spins[key] = interval
        bottom.addStretch(1)
        try_btn = QPushButton("Try it \u2192", objectName="try")
        try_btn.setCursor(Qt.PointingHandCursor)
        try_btn.clicked.connect(lambda _=False, k=key: self.engine.trigger_now(k))
        bottom.addWidget(try_btn)
        layout.addLayout(bottom)
        self._try_buttons[key] = try_btn

        if key == "sleep":
            note = QLabel(f"Only checked between {self._fmt_hour(self.settings.wind_down_start_hour)} "
                          f"and {self._fmt_hour(self.settings.wind_down_end_hour)}.", objectName="rowcaption")
            layout.addWidget(note)

        self._set_row_enabled(key, cfg.enabled)
        return card

    @staticmethod
    def _fmt_hour(hour: int) -> str:
        suffix = "AM" if hour < 12 else "PM"
        h12 = hour % 12 or 12
        return f"{h12} {suffix}"

    def _set_row_enabled(self, key: str, enabled: bool) -> None:
        self._interval_spins[key].setEnabled(enabled)
        self._try_buttons[key].setEnabled(enabled)

    # ---- handlers ---------------------------------------------------------
    def _on_interval_changed(self, key: str, value: float) -> None:
        self.settings.reminders[key].interval_minutes = value
        self.engine.refresh_schedule()                 # this key gets a fresh countdown now
        self._mark_dirty()

    def _on_enabled_changed(self, key: str, checked: bool) -> None:
        self.settings.reminders[key].enabled = checked
        self._set_row_enabled(key, checked)
        self.engine.refresh_schedule()                 # re-enabling starts fresh, not overdue
        self._mark_dirty()

    def _on_snooze_changed(self, value: int) -> None:
        self.settings.snooze_minutes = value
        self._mark_dirty()

    def _on_focus_break_changed(self, value: int) -> None:
        self.settings.break_minutes = value
        self._mark_dirty()

    def _on_sounds_toggled(self, checked: bool) -> None:
        self.settings.sounds = checked
        self._mark_dirty()

    def _on_animations_toggled(self, checked: bool) -> None:
        self.settings.animations = checked
        self._mark_dirty()

    def _on_autostart_toggled(self, checked: bool) -> None:
        self.settings.start_with_windows = checked
        autostart.set_enabled(checked)
        self._mark_dirty()

    def _on_pause_all_toggled(self, checked: bool) -> None:
        (self.engine.pause if checked else self.engine.resume)()

    def _sync_pause_toggle(self) -> None:
        self.pause_toggle.setChecked(self.engine.paused)      # doesn't emit -> no feedback loop

    # ---- persistence --------------------------------------------------------
    def _mark_dirty(self) -> None:
        self._save_timer.start()

    def _flush_save(self) -> None:
        try:
            self.settings.save(self._path)
        except OSError as exc:
            print(f"[nudge] could not save settings: {exc}")

    def present(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event) -> None:
        if self._save_timer.isActive():                       # don't lose a change made just before closing
            self._save_timer.stop()
            self._flush_save()
        super().closeEvent(event)
