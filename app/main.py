"""Nudge entry point. Run from the project root with:  python -m app.main"""
import argparse
import signal
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from app import autostart
from app.controller import NudgeController
from app.database import HistoryStore
from app.reminder import REMINDER_TYPES, ReminderEngine
from app.settings import Settings
from app.single_instance import SingleInstance
from app.sound import SoundPlayer
from app.tray import NudgeTray
from app.ui.icons import make_app_icon
from app.ui.main_window import MainWindow
from app.ui.settings_window import SettingsWindow
from app.ui.stats_window import StatisticsWindow
from app.ui.theme import set_theme_override
from app.updater import maybe_notify_update


def parse_args(argv):
    p = argparse.ArgumentParser(prog="nudge")
    p.add_argument("--speed", type=float, default=1.0,
                   help="Time multiplier for testing. 300 turns 45 minutes into 9 seconds.")
    p.add_argument("--show", choices=list(REMINDER_TYPES),
                   help="Show one reminder immediately, then keep running.")
    p.add_argument("--theme", choices=["auto", "light", "dark"], default="auto",
                   help="Force the popup theme (default: follow Windows).")
    p.add_argument("--background", action="store_true",
                   help="Start hidden in the tray (this is how Windows startup will launch us).")
    return p.parse_known_args(argv)


def _set_windows_app_id() -> None:
    """Lets Windows show our icon (not python.exe's) on the taskbar and in notifications."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Nudge.Desktop.App")
        except Exception:
            pass


def main() -> int:
    args, qt_args = parse_args(sys.argv[1:])
    _set_windows_app_id()
    app = QApplication([sys.argv[0], *qt_args])
    app.setApplicationName("Nudge")
    app.setWindowIcon(make_app_icon(False))

    guard = SingleInstance()
    if not guard.become_primary():
        print("[nudge] already running - asked the running copy to show its window.")
        return 0

    set_theme_override(args.theme)
    settings = Settings.load()
    if autostart.is_supported():                 # the registry, not our file, is the source of truth
        settings.start_with_windows = autostart.is_enabled()

    history = HistoryStore()
    engine = ReminderEngine(settings, speed=args.speed,
                            respect_night_window=(args.speed == 1.0))
    controller = NudgeController(settings, engine, SoundPlayer(settings), history)  # noqa: F841
    tray = NudgeTray(engine)
    window = MainWindow(engine, settings, to_tray=tray.available)
    settings_window = SettingsWindow(engine, settings)
    stats_window = StatisticsWindow(history)
    window.settings_requested.connect(settings_window.present)
    window.stats_requested.connect(stats_window.present)
    # Without a tray (rare Linux desktops) closing the window has to quit, or Nudge would be invisible.
    app.setQuitOnLastWindowClosed(not tray.available)

    # tray + second launches -> window; quit -> really quit
    for signal_ in (tray.open_requested, guard.activated):
        signal_.connect(window.present)
    tray.settings_requested.connect(settings_window.present)
    tray.stats_requested.connect(stats_window.present)
    tray.quit_requested.connect(app.quit)
    app.aboutToQuit.connect(tray.hide)
    app.aboutToQuit.connect(history.close)
    window.hidden_to_tray.connect(tray.hint_once)

    tray.show()
    engine.start()
    if not args.background or not tray.available:
        window.present()

    # Check for updates (non-blocking, once per day)
    if not args.background:
        maybe_notify_update(window)

    # Let Ctrl+C in the terminal quit cleanly (Qt's loop otherwise swallows it).
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    keepalive = QTimer()
    keepalive.start(250)
    keepalive.timeout.connect(lambda: None)

    if args.show:
        QTimer.singleShot(500, lambda: engine.trigger_now(args.show))

    print("[nudge] running" + (" in the tray" if tray.available else " (no system tray found)")
          + ". Press Ctrl+C in this terminal to quit.")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
