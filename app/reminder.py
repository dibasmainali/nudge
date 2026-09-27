"""Reminder engine: decides *when* a reminder is due. Knows nothing about UI."""
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

from PySide6.QtCore import QObject, QTimer, Signal

from app.settings import Settings


@dataclass(frozen=True)
class ReminderType:
    key: str
    emoji: str
    mood: str                                  # used by the mascot in Phase 3
    variants: tuple[tuple[str, str], ...]      # (title, message) pairs
    done_label: str
    later_label: str
    night_only: bool = False
    label: str = ""                            # short name for menus / the home window
    later_skips: bool = False                  # "later" means skip this one (wait a full interval)

    def pick_text(self, minutes: float, break_minutes: float = 10) -> tuple[str, str]:
        title, message = random.choice(self.variants)
        return title, message.format(minutes=int(minutes), break_minutes=int(break_minutes))


REMINDER_TYPES: dict[str, ReminderType] = {
    "water": ReminderType(
        "water", "💧", "happy",
        (("A little water break!", "Your body will thank you for it."),
         ("Want to keep yourself hydrated?", "A few sips go a long way.")),
        "I drank 💧", "Later · {snooze} min", label="Water"),
    "eye": ReminderType(
        "eye", "👀", "relaxed",
        (("Rest your eyes", "You've been looking at the screen for a while."),
         ("Give your eyes a short break", "Look at something far away for 20 seconds.")),
        "Done ✓", "Later · {snooze} min", label="Eye break"),
    "movement": ReminderType(
        "movement", "🧘", "energetic",
        (("Your body deserves a tiny break", "Stand up and stretch for a minute."),),
        "Done ✓", "Later · {snooze} min", label="Movement"),
    "focus": ReminderType(
        "focus", "📚", "focused",
        (("Great focus session!", "You've been going for {minutes} minutes. Take a {break_minutes}-minute break."),),
        "Start break", "Skip", label="Focus", later_skips=True),
    "sleep": ReminderType(
        "sleep", "🌙", "sleepy",
        (("It's getting late", "Maybe it's time to start winding down."),),
        "Okay", "Later · {snooze} min", night_only=True, label="Wind-down"),
}


def is_wind_down_time(hour: int, start: int, end: int) -> bool:
    """True if `hour` is inside the (possibly midnight-crossing) window."""
    if start > end:
        return hour >= start or hour < end
    return start <= hour < end


class ReminderEngine(QObject):
    """Checks once a second whether any reminder is due.

    Emits `reminder_due(key)` for at most one reminder at a time. After the UI
    is finished with it, the UI must call `resolve(key, action)`.
    `state_changed` fires whenever reminders are paused or resumed.
    """

    reminder_due = Signal(str)
    state_changed = Signal()

    def __init__(self, settings: Settings, speed: float = 1.0,
                 respect_night_window: bool = True,
                 clock: Callable[[], float] = time.monotonic,
                 hour_provider: Callable[[], int] = lambda: datetime.now().hour,
                 parent=None):
        super().__init__(parent)
        self.settings = settings
        self.speed = speed                    # >1 shrinks "minutes" for testing
        self._respect_night = respect_night_window
        self._clock = clock
        self._hour = hour_provider
        self._paused = False
        self._resume_at: float | None = None  # clock time of an automatic resume
        self._busy = False                    # a popup is currently on screen
        self._next_due: dict[str, float] = {}
        self._snapshot: dict[str, tuple] = {}   # (enabled, interval) each timer was scheduled with
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.tick)
        self._schedule_all()

    # ---- scheduling helpers -------------------------------------------
    def _seconds(self, minutes: float) -> float:
        return minutes * 60.0 / self.speed

    def _schedule_all(self) -> None:
        now = self._clock()
        for key, cfg in self.settings.reminders.items():
            self._next_due[key] = now + self._seconds(cfg.interval_minutes)
            self._snapshot[key] = (cfg.enabled, cfg.interval_minutes)

    def refresh_schedule(self) -> None:
        """Call after settings changed: a reminder whose interval or on/off state changed
        starts a fresh countdown from now; the others keep theirs."""
        now = self._clock()
        for key, cfg in self.settings.reminders.items():
            snap = (cfg.enabled, cfg.interval_minutes)
            if self._snapshot.get(key) != snap:
                self._snapshot[key] = snap
                self._next_due[key] = now + self._seconds(cfg.interval_minutes)

    # ---- public API ---------------------------------------------------
    def start(self) -> None:
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def pause(self, minutes: float | None = None) -> None:
        """Pause all reminders; resume automatically after `minutes` (None = until resume())."""
        self._paused = True
        self._resume_at = None if minutes is None else self._clock() + self._seconds(minutes)
        self.state_changed.emit()

    def resume(self) -> None:
        self._paused = False
        self._resume_at = None
        self._schedule_all()                  # start fresh intervals
        self.state_changed.emit()

    @property
    def paused(self) -> bool:
        return self._paused

    def paused_until(self) -> datetime | None:
        """Wall-clock time of the automatic resume, or None."""
        if not self._paused or self._resume_at is None:
            return None
        remaining = max(0.0, self._resume_at - self._clock()) * self.speed
        return datetime.now() + timedelta(seconds=remaining)

    def minutes_until(self, key: str) -> float | None:
        """Minutes (in the user's time scale) until `key` is due; None if it is switched off."""
        if not self.settings.reminders[key].enabled:
            return None
        return max(0.0, self._next_due[key] - self._clock()) * self.speed / 60.0

    def try_claim(self) -> bool:
        """Reserve the screen for a popup that isn't a scheduled reminder (e.g. a preview)."""
        if self._busy:
            return False
        self._busy = True
        return True

    def release(self) -> None:
        self._busy = False

    def trigger_now(self, key: str) -> None:
        """Show a reminder immediately (for testing)."""
        if self.try_claim():
            self.reminder_due.emit(key)

    def resolve(self, key: str, action: str) -> None:
        """Called by the UI when the popup is gone. action: done | later | ignored."""
        now = self._clock()
        interval = self.settings.reminders[key].interval_minutes
        if key == "focus" and action == "done":            # the work timer restarts after the break
            wait = self._seconds(self.settings.break_minutes + interval)
        elif action == "done" or (action == "later" and REMINDER_TYPES[key].later_skips):
            wait = self._seconds(interval)
        else:                                 # "later" or "ignored" -> snooze
            wait = self._seconds(self.settings.snooze_minutes)
        self._next_due[key] = now + wait
        self._busy = False

    # ---- the heartbeat ------------------------------------------------
    def tick(self) -> None:
        now = self._clock()
        if self._paused:
            if self._resume_at is not None and now >= self._resume_at:
                self.resume()
            return
        if self._busy:
            return
        for key in sorted(self._next_due, key=self._next_due.get):   # most overdue first
            cfg = self.settings.reminders[key]
            if not cfg.enabled or now < self._next_due[key]:
                continue
            if self._respect_night and REMINDER_TYPES[key].night_only:
                s = self.settings
                if not is_wind_down_time(self._hour(), s.wind_down_start_hour,
                                         s.wind_down_end_hour):
                    self._next_due[key] = now + self._seconds(cfg.interval_minutes)
                    continue
            self._busy = True
            self.reminder_due.emit(key)
            return
