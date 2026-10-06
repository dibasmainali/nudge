"""Local SQLite history: one row per reminder outcome (done / later / ignored).

Everything here is local-only, matching Nudge's privacy-first design — no
account, no network, nothing leaves this computer. `HistoryStore.clear()`
lets the person wipe it from the Statistics window whenever they like.
"""
import os
import sqlite3
from datetime import date, datetime, timedelta

from app.settings import config_dir

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL,
    action TEXT NOT NULL,
    at TEXT NOT NULL           -- local ISO 8601 timestamp, e.g. 2026-09-25T14:03:00
);
CREATE INDEX IF NOT EXISTS idx_events_action_at ON events(action, at);
"""


def default_history_path() -> str:
    return os.path.join(config_dir(), "history.db")


class HistoryStore:
    def __init__(self, path: str | None = None):
        self.path = path or default_history_path()
        if self.path != ":memory:":
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # ---- writing ----------------------------------------------------------
    def record(self, key: str, action: str, when: datetime | None = None) -> None:
        when = when or datetime.now()
        self._conn.execute("INSERT INTO events (key, action, at) VALUES (?, ?, ?)",
                           (key, action, when.isoformat(timespec="seconds")))
        self._conn.commit()

    def clear(self) -> None:
        self._conn.execute("DELETE FROM events")
        self._conn.commit()

    # ---- reading ------------------------------------------------------------
    def counts_for_day(self, day: date, action: str = "done") -> dict[str, int]:
        """{reminder key: count} for one calendar day. Keys with 0 are simply absent."""
        cur = self._conn.execute(
            "SELECT key, COUNT(*) FROM events WHERE action = ? AND date(at) = ? GROUP BY key",
            (action, day.isoformat()))
        return dict(cur.fetchall())

    def daily_totals(self, days: int = 7, end: date | None = None,
                     action: str = "done") -> list[tuple[date, int]]:
        """`days` calendar days ending at `end` (default today), oldest first."""
        end = end or date.today()
        start = end - timedelta(days=days - 1)
        cur = self._conn.execute(
            "SELECT date(at) as d, COUNT(*) FROM events WHERE action = ? AND d BETWEEN ? AND ? "
            "GROUP BY d", (action, start.isoformat(), end.isoformat()))
        by_day = dict(cur.fetchall())
        return [(start + timedelta(days=i), by_day.get((start + timedelta(days=i)).isoformat(), 0))
                for i in range(days)]

    def total_done(self, key: str | None = None) -> int:
        if key is None:
            cur = self._conn.execute("SELECT COUNT(*) FROM events WHERE action = 'done'")
        else:
            cur = self._conn.execute(
                "SELECT COUNT(*) FROM events WHERE action = 'done' AND key = ?", (key,))
        return cur.fetchone()[0]

    def active_days(self, action: str = "done") -> set[date]:
        """Every distinct calendar day with at least one matching event."""
        cur = self._conn.execute("SELECT DISTINCT date(at) FROM events WHERE action = ?", (action,))
        return {date.fromisoformat(row[0]) for row in cur.fetchall()}

    def current_streak(self, today: date | None = None) -> int:
        """Consecutive days up to today with >=1 completion. If today has none *yet*,
        counting starts from yesterday instead — so the streak doesn't look broken
        first thing in the morning, before there's been a chance to act today."""
        today = today or date.today()
        days = self.active_days()
        cursor = today if today in days else today - timedelta(days=1)
        streak = 0
        d = cursor
        while d in days:
            streak += 1
            d -= timedelta(days=1)
        return streak

    def longest_streak(self) -> int:
        """The best streak ever reached. Doesn't shrink when a current streak breaks,
        so an earned achievement badge stays earned."""
        days = sorted(self.active_days())
        if not days:
            return 0
        best = run = 1
        for prev, cur in zip(days, days[1:]):
            run = run + 1 if cur == prev + timedelta(days=1) else 1
            best = max(best, run)
        return best
