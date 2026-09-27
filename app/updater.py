"""Auto-update check via GitHub Releases API."""
import json
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from app.settings import config_dir
from app.version import __version__ as CURRENT_VERSION

GITHUB_REPO = "dibasmainali/nudge"
CHECK_INTERVAL_DAYS = 1


def _get_cache_path() -> Path:
    return Path(config_dir()) / "update_cache.json"


def _load_cache() -> dict:
    path = _get_cache_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save_cache(data: dict) -> None:
    path = _get_cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    import os
    os.replace(tmp, path)


def _parse_version(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.lstrip("v").split(".")[:3])


def check_for_update(force: bool = False) -> dict | None:
    """
    Check GitHub Releases for a newer version.
    Returns dict with keys: has_update, latest_version, url, notes
    Returns None if check failed or not time yet.
    """
    cache = _load_cache()
    last_check = cache.get("last_check")
    if not force and last_check:
        try:
            last = datetime.fromisoformat(last_check)
            if datetime.now() - last < timedelta(days=CHECK_INTERVAL_DAYS):
                return None
        except Exception:
            pass

    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    req = urllib.request.Request(url, headers={"User-Agent": "Nudge-Updater"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.load(resp)
    except Exception:
        return None

    latest_tag = data.get("tag_name", "")
    try:
        latest_version = _parse_version(latest_tag)
        current_version = _parse_version(CURRENT_VERSION)
    except ValueError:
        return None

    _save_cache({
        "last_check": datetime.now().isoformat(),
        "latest_version": latest_tag,
        "latest_url": data.get("html_url", ""),
    })

    if latest_version > current_version:
        return {
            "has_update": True,
            "latest_version": latest_tag,
            "url": data.get("html_url", ""),
            "notes": data.get("body", "")[:500],
        }
    return {"has_update": False}


def maybe_notify_update(parent_widget=None) -> None:
    """Check GitHub in the background so a slow network never freezes the UI."""
    from PySide6.QtCore import QObject, QThread, QTimer, Signal
    from PySide6.QtWidgets import QApplication, QMessageBox

    owner = parent_widget or QApplication.instance()
    if owner is None:
        return

    class _Worker(QObject):
        finished = Signal(object)

        def run(self):
            self.finished.emit(check_for_update())

    thread = QThread(owner)
    worker = _Worker()
    worker.moveToThread(thread)

    def show_dialog(result):
        thread.quit()
        if not result or not result.get("has_update"):
            return
        msg = QMessageBox(parent_widget)
        msg.setWindowTitle("Nudge Update Available")
        msg.setIcon(QMessageBox.Information)
        msg.setText(f"Version {result['latest_version']} is available!")
        msg.setInformativeText(
            f"{result['notes']}\n\nWould you like to open the download page?"
        )
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        if msg.exec() == QMessageBox.Yes:
            import webbrowser
            webbrowser.open(result["url"])

    worker.finished.connect(show_dialog)
    thread.started.connect(worker.run)
    thread.finished.connect(worker.deleteLater)
    owner._nudge_update_thread = thread  # keep alive
    owner._nudge_update_worker = worker
    QTimer.singleShot(2000, thread.start)