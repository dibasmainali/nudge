"""Popup glue: engine says 'something is due' -> show popup -> tell engine the outcome."""
from app.database import HistoryStore
from app.reminder import REMINDER_TYPES, ReminderEngine
from app.settings import Settings
from app.sound import SoundPlayer
from app.ui.popup import ReminderPopup


class NudgeController:
    def __init__(self, settings: Settings, engine: ReminderEngine, sounds: SoundPlayer | None = None,
                 history: HistoryStore | None = None):
        self.settings = settings
        self.engine = engine
        self.sounds = sounds
        self.history = history
        self._popup: ReminderPopup | None = None
        engine.reminder_due.connect(self.show_reminder)

    def show_reminder(self, key: str) -> None:
        rt = REMINDER_TYPES[key]
        minutes = self.settings.reminders[key].interval_minutes
        title, message = rt.pick_text(minutes, self.settings.break_minutes)
        snooze = int(self.settings.snooze_minutes)
        popup = ReminderPopup(
            rt.key, rt.mood, title, message,
            rt.done_label.format(snooze=snooze), rt.later_label.format(snooze=snooze),
            animations=self.settings.animations,
            timeout_seconds=self.settings.popup_timeout_seconds)
        popup.closed_with.connect(lambda action, k=key: self._on_closed(k, action))
        self._popup = popup
        popup.show_animated()
        if self.sounds:
            self.sounds.play("chime")
        print(f"[nudge] showing '{key}' reminder")

    def _on_closed(self, key: str, action: str) -> None:
        print(f"[nudge] '{key}' -> {action}")
        self._popup = None
        self.engine.resolve(key, action)
        if self.history:
            self.history.record(key, action)          # every outcome, not just "done" —
        if action == "done" and self.sounds:           # later analysis may want the snooze pattern too
            self.sounds.play("done")
