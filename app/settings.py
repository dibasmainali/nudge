"""Settings model: what the app remembers, and where it lives on disk.

Changes made in the Settings window are saved here immediately (see
`Settings.save`), so there is no separate "Apply" step and nothing is lost
if the app is closed from the tray.
"""
import json
import os
import sys
from dataclasses import asdict, dataclass, field


@dataclass
class ReminderConfig:
    enabled: bool = True
    interval_minutes: float = 45


def _default_reminders() -> dict[str, ReminderConfig]:
    return {
        "water": ReminderConfig(True, 45),
        "eye": ReminderConfig(True, 30),
        "movement": ReminderConfig(True, 60),
        "focus": ReminderConfig(True, 50),
        "sleep": ReminderConfig(True, 30),
    }


REMINDER_KEYS = tuple(_default_reminders())


def config_dir() -> str:
    """Per-user, per-app folder to store settings.json (and, later, the database)."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "Nudge")


def default_settings_path() -> str:
    return os.path.join(config_dir(), "settings.json")


@dataclass
class Settings:
    reminders: dict[str, ReminderConfig] = field(default_factory=_default_reminders)
    snooze_minutes: float = 10
    break_minutes: float = 10   # length of the break after a focus session
    animations: bool = True
    sounds: bool = True
    start_with_windows: bool = False
    popup_timeout_seconds: int = 90
    wind_down_start_hour: int = 22   # sleep reminder only fires 22:00 ...
    wind_down_end_hour: int = 5      # ... until 05:00

    # ---- (de)serialisation --------------------------------------------
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        """Builds a Settings from parsed JSON. Unknown/missing/malformed fields are
        ignored rather than raising, so an old or hand-edited file never crashes the app."""
        s = cls()
        for key, cfg in (data.get("reminders") or {}).items():
            if key in s.reminders and isinstance(cfg, dict):
                try:
                    s.reminders[key] = ReminderConfig(
                        enabled=bool(cfg.get("enabled", True)),
                        interval_minutes=max(1.0, float(cfg.get("interval_minutes",
                                             s.reminders[key].interval_minutes))))
                except (TypeError, ValueError):
                    pass
        for f in ("snooze_minutes", "break_minutes", "popup_timeout_seconds",
                  "wind_down_start_hour", "wind_down_end_hour"):
            if f in data:
                try:
                    setattr(s, f, type(getattr(s, f))(data[f]))
                except (TypeError, ValueError):
                    pass
        for f in ("animations", "sounds", "start_with_windows"):
            if f in data:
                setattr(s, f, bool(data[f]))
        return s

    # ---- disk I/O -------------------------------------------------------
    def save(self, path: str | None = None) -> None:
        path = path or default_settings_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        os.replace(tmp, path)          # atomic, so a crash mid-write can't corrupt the file

    @classmethod
    def load(cls, path: str | None = None) -> "Settings":
        path = path or default_settings_path()
        try:
            with open(path, "r", encoding="utf-8") as f:
                return cls.from_dict(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError, OSError, UnicodeDecodeError):
            return cls()
