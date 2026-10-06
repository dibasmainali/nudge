"""The 'Open Nudge' home window: status, pause control and what's coming up."""
import math

from PySide6.QtCore import QTime, QTimer, Qt, Signal
from PySide6.QtWidgets import (QGridLayout, QHBoxLayout, QLabel, QPushButton,
                               QVBoxLayout, QWidget)

from app.reminder import REMINDER_TYPES, ReminderEngine
from app.settings import Settings
from app.tray import describe_state, make_pause_menu
from app.ui.icons import make_app_icon
from app.ui.mascot import MascotWidget
from app.ui.theme import DEFAULT_ACCENT, current_palette, popup_stylesheet


def format_eta(minutes: float) -> str:
    if minutes < 1:
        return "in under a minute"
    m = math.ceil(minutes)
    if m < 60:
        return f"in {m} min"
    h, rest = divmod(m, 60)
    return f"in {h} h" if rest == 0 else f"in {h} h {rest:02d} min"


class MainWindow(QWidget):
    hidden_to_tray = Signal()
    settings_requested = Signal()
    stats_requested = Signal()

    settings_requested = Signal()

    def __init__(self, engine: ReminderEngine, settings: Settings, to_tray: bool = True):
        super().__init__()
        self.engine, self.settings, self._to_tray = engine, settings, to_tray
        pal = current_palette()
        self.setObjectName("root")
        self.setWindowTitle("Nudge")
        self.setWindowIcon(make_app_icon(False))
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.resize(400, 440)
        self.setMinimumWidth(360)
        self.setMaximumWidth(440)
        self.setStyleSheet(popup_stylesheet(DEFAULT_ACCENT, pal) + f"""
            #root {{ background: {pal.card.name()}; border: 1px solid {pal.edge.name()}; border-radius: 24px; }}
            QLabel#hero {{ color: {pal.title.name()}; font-size: 25px; font-weight: 700; }}
            QLabel#message {{ color: {pal.message.name()}; font-size: 12.5px; font-weight: 500; }}
            QLabel#summary {{ color: {pal.title.name()}; font-size: 12px; font-weight: 700; letter-spacing: 0.2px; }}
            QLabel#timebadge {{ background: {DEFAULT_ACCENT.main}; color: white; border-radius: 999px; padding: 6px 10px; font-size: 11px; font-weight: 700; }}
            QLabel#rowname {{ color: {pal.title.name()}; font-size: 14px; }}
            QLabel#eta {{ color: {pal.message.name()}; font-size: 13px; }}
            QLabel#section {{ color: {pal.message.name()}; font-size: 11px; font-weight: 700; letter-spacing: 0.6px; }}
            QWidget#overview {{ background: {pal.surface.name()}; border: 1px solid {pal.edge.name()}; border-radius: 18px; }}
            QGridLayout {{ background: transparent; }}
            QPushButton {{ min-height: 38px; }}
            QPushButton#primary::menu-indicator {{ image: none; width: 0px; }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 18)
        root.setSpacing(16)

        head = QHBoxLayout()
        head.setSpacing(14)
        self.mascot = MascotWidget("happy", DEFAULT_ACCENT, pal, size=92, droplet=False)
        head.addWidget(self.mascot)
        texts = QVBoxLayout()
        texts.setSpacing(4)
        texts.addWidget(QLabel("Nudge", objectName="hero"))
        self.status = QLabel("", objectName="message")
        self.summary = QLabel("", objectName="summary")
        texts.addWidget(self.status)
        texts.addWidget(self.summary)
        head.addLayout(texts, 1)
        self.time_badge = QLabel("", objectName="timebadge")
        self.time_badge.setAlignment(Qt.AlignCenter)
        self.time_badge.setFixedHeight(28)
        head.addWidget(self.time_badge, 0, Qt.AlignVCenter)
        root.addLayout(head)

        overview = QWidget(objectName="overview")
        overview_layout = QHBoxLayout(overview)
        overview_layout.setContentsMargins(14, 10, 14, 10)
        overview_layout.setSpacing(8)
        overview_label = QLabel("Today’s rhythm")
        overview_label.setStyleSheet(f"color: {pal.message.name()}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        overview_layout.addWidget(overview_label)
        overview_layout.addStretch(1)
        self.overview_state = QLabel("", objectName="summary")
        overview_layout.addWidget(self.overview_state)
        root.addWidget(overview)

        root.addWidget(QLabel("COMING UP", objectName="section"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        self._rows: dict[str, QLabel] = {}
        for i, (key, rt) in enumerate(REMINDER_TYPES.items()):
            grid.addWidget(QLabel(f"{rt.emoji}  {rt.label}", objectName="rowname"), i, 0)
            eta = QLabel("", objectName="eta")
            eta.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(eta, i, 1)
            self._rows[key] = eta
        grid.setColumnStretch(0, 1)
        root.addLayout(grid)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.pause_btn = QPushButton("", objectName="primary")
        self.pause_btn.setCursor(Qt.PointingHandCursor)
        self.pause_btn.setMinimumWidth(110)
        self.pause_btn.setMaximumWidth(130)
        self._pause_menu = make_pause_menu(engine, self)
        self.pause_btn.clicked.connect(engine.resume)          # only fires while paused (no menu)
        self.stats_btn = QPushButton("Statistics", objectName="secondary")
        self.stats_btn.setCursor(Qt.PointingHandCursor)
        self.stats_btn.clicked.connect(self.stats_requested)
        self.settings_btn = QPushButton("Settings", objectName="secondary")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.clicked.connect(self.settings_requested)
        self.hide_btn = QPushButton("Hide" if to_tray else "Close", objectName="secondary")
        self.hide_btn.setCursor(Qt.PointingHandCursor)
        self.hide_btn.clicked.connect(self.close)
        buttons.addWidget(self.pause_btn, 5)
        buttons.addWidget(self.stats_btn, 3)
        buttons.addWidget(self.settings_btn, 3)
        buttons.addWidget(self.hide_btn, 2)
        root.addLayout(buttons)

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.refresh)
        self._last_status = None
        engine.state_changed.connect(self.refresh)
        self.refresh()

    # ---- state ---------------------------------------------------------
    def refresh(self) -> None:
        paused = self.engine.paused
        status = describe_state(self.engine)
        active_count = sum(1 for key in REMINDER_TYPES if self.engine.minutes_until(key) is not None and not paused)
        if status != self._last_status:
            self.status.setText(status)
            self._last_status = status

        self.time_badge.setText(QTime.currentTime().toString("h:mm AP"))
        self.summary.setText("All systems calm" if paused else "Focus is on track")
        self.overview_state.setText(
            "Paused" if paused else f"{active_count} active reminder{'s' if active_count != 1 else ''}"
        )

        self.mascot.set_mood("sleepy" if paused else "happy")   # takes a nap while paused
        if paused:
            self.pause_btn.setMenu(None)
            self.pause_btn.setText("Resume")
            self.pause_btn.setToolTip("Resume reminders")
        else:
            self.pause_btn.setMenu(self._pause_menu)
            self.pause_btn.setText("Pause")
            self.pause_btn.setToolTip("Pause reminders")
        for key, label in self._rows.items():
            minutes = self.engine.minutes_until(key)
            label.setText("off" if minutes is None else "paused" if paused else format_eta(minutes))

    def present(self) -> None:
        self.refresh()
        self.showNormal()
        self.raise_()
        self.activateWindow()

    # ---- window events ---------------------------------------------------
    def showEvent(self, event) -> None:
        self._timer.start()
        self.mascot.start()
        super().showEvent(event)

    def hideEvent(self, event) -> None:
        self._timer.stop()
        self.mascot.stop()
        super().hideEvent(event)

    def closeEvent(self, event) -> None:
        if self._to_tray:                       # closing the window is not quitting
            event.ignore()
            self.hide()
            self.hidden_to_tray.emit()
        else:
            event.accept()
