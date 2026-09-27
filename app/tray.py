"""System tray icon + context menu. Talks to the engine, knows nothing about popups."""
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from app.reminder import ReminderEngine
from app.ui.icons import make_app_icon

PAUSE_CHOICES = (("For 30 minutes", 30), ("For 1 hour", 60),
                 ("For 2 hours", 120), ("Until I resume", None))


def make_pause_menu(engine: ReminderEngine, parent=None) -> QMenu:
    """The 'Pause reminders' submenu (shared by the tray and the home window)."""
    menu = QMenu("Pause reminders", parent)
    for text, minutes in PAUSE_CHOICES:
        action = menu.addAction(text)
        action.triggered.connect(lambda _checked=False, m=minutes: engine.pause(m))
    return menu


def describe_state(engine: ReminderEngine) -> str:
    if not engine.paused:
        return "Reminders are on"
    until = engine.paused_until()
    if until is None:
        return "Reminders are paused"
    return "Paused until " + until.strftime("%I:%M %p").lstrip("0")


class NudgeTray(QObject):
    open_requested = Signal()
    settings_requested = Signal()
    stats_requested = Signal()
    quit_requested = Signal()

    def __init__(self, engine: ReminderEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.available = QSystemTrayIcon.isSystemTrayAvailable()
        self._hint_shown = False

        self.icon = QSystemTrayIcon(make_app_icon(False), self)
        self.menu = QMenu()                       # top-level menu: we own it (no parent widget)

        self.status_action = self.menu.addAction("")
        self.status_action.setEnabled(False)
        self.menu.addSeparator()

        self.open_action = self.menu.addAction("Open Nudge")
        font = self.open_action.font(); font.setBold(True); self.open_action.setFont(font)
        self.pause_menu = make_pause_menu(engine, self.menu)
        self.pause_action = self.menu.addMenu(self.pause_menu)          # QAction of the submenu
        self.resume_action = self.menu.addAction("Resume reminders")
        self.menu.addSeparator()
        self.settings_action = self.menu.addAction("Settings…")
        self.stats_action = self.menu.addAction("View statistics")
        self.menu.addSeparator()
        self.quit_action = self.menu.addAction("Quit Nudge")

        self.open_action.triggered.connect(self.open_requested)
        self.resume_action.triggered.connect(engine.resume)
        self.settings_action.triggered.connect(self.settings_requested)
        self.stats_action.triggered.connect(self.stats_requested)
        self.quit_action.triggered.connect(self.quit_requested)

        self.icon.setContextMenu(self.menu)
        self.icon.activated.connect(self._on_activated)
        self.menu.aboutToShow.connect(self.refresh)
        engine.state_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        paused = self.engine.paused
        text = describe_state(self.engine)
        self.status_action.setText(text)
        self.pause_action.setVisible(not paused)
        self.resume_action.setVisible(paused)
        self.icon.setIcon(make_app_icon(paused))
        self.icon.setToolTip(f"Nudge — {text.lower()}")

    def _on_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.open_requested.emit()

    def show(self) -> None:
        if self.available:
            self.icon.show()

    def hide(self) -> None:
        self.icon.hide()          # otherwise Windows can leave a ghost icon behind after quit

    def hint_once(self) -> None:
        """Tell the user, once per session, that closing the window did not quit the app."""
        if self._hint_shown or not self.available:
            return
        self._hint_shown = True
        self.icon.showMessage("Nudge is still running",
                              "I'll keep quietly nudging from the tray. Right-click the icon to quit.",
                              make_app_icon(False), 5000)
