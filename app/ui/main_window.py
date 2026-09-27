"""The 'Open Nudge' home window: status, pause control and what's coming up."""
import math

from PySide6.QtCore import QTimer, Qt, Signal
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
        self.setFixedWidth(400)
        self.setStyleSheet(popup_stylesheet(DEFAULT_ACCENT, pal) + f"""
            #root {{ background: {pal.card.name()}; }}
            QLabel#hero {{ color: {pal.title.name()}; font-size: 24px; font-weight: 700; }}
            QLabel#rowname {{ color: {pal.title.name()}; font-size: 14px; }}
            QLabel#eta {{ color: {pal.message.name()}; font-size: 13px; }}
            QLabel#section {{ color: {pal.message.name()}; font-size: 11px; font-weight: 600; }}
            QPushButton#primary::menu-indicator {{ image: none; width: 0px; }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 26, 28, 22)
        root.setSpacing(18)

        head = QHBoxLayout()
        head.setSpacing(16)
        self.mascot = MascotWidget("happy", DEFAULT_ACCENT, pal, size=104, droplet=False)
        head.addWidget(self.mascot)
        texts = QVBoxLayout()
        texts.addStretch(1)
        texts.addWidget(QLabel("Nudge", objectName="hero"))
        self.status = QLabel("", objectName="message")
        texts.addWidget(self.status)
        texts.addStretch(1)
        head.addLayout(texts, 1)
        root.addLayout(head)

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
        engine.state_changed.connect(self.refresh)
        self.refresh()

    # ---- state ---------------------------------------------------------
    def refresh(self) -> None:
        paused = self.engine.paused
        self.status.setText(describe_state(self.engine))
        self.mascot.set_mood("sleepy" if paused else "happy")   # takes a nap while paused
        if paused:
            self.pause_btn.setMenu(None)
            self.pause_btn.setText("Resume reminders")
        else:
            self.pause_btn.setMenu(self._pause_menu)
            self.pause_btn.setText("Pause reminders  ▾")
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
