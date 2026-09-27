"""Tiny sound player with a pluggable backend, so it's fully testable without a real
audio device. `settings.sounds` is re-read on every `play()` call, so toggling it in
the Settings window takes effect immediately."""
from pathlib import Path

from app.paths import resource_path
from app.settings import Settings


class QtBackend:
    """Wraps QSoundEffect. Constructed lazily, so just importing this module never
    requires a real audio device or even QtMultimedia to be installed."""

    def __init__(self):
        self.available = False
        try:
            from PySide6.QtCore import QUrl
            from PySide6.QtMultimedia import QSoundEffect
            self._QUrl, self._QSoundEffect = QUrl, QSoundEffect
            self._effects: dict[str, "QSoundEffect"] = {}
            self.available = True
        except ImportError:
            pass

    def play(self, path: Path) -> None:
        if not self.available:
            raise RuntimeError("QtMultimedia is not available")
        key = str(path)
        effect = self._effects.get(key)
        if effect is None:
            effect = self._QSoundEffect()
            effect.setSource(self._QUrl.fromLocalFile(key))
            effect.setVolume(0.5)
            self._effects[key] = effect
        effect.play()


class SoundPlayer:
    def __init__(self, settings: Settings, backend=None, sounds_dir: Path | None = None):
        self.settings = settings
        self.backend = backend if backend is not None else QtBackend()
        self.sounds_dir = sounds_dir or resource_path("assets", "sounds")

    def play(self, name: str) -> bool:
        """Returns whether a sound actually played — mainly useful for tests.
        Never raises: a missing file, a missing audio device, or sounds being
        switched off are all just reasons to stay quiet."""
        if not self.settings.sounds:
            return False
        path = Path(self.sounds_dir) / f"{name}.wav"
        if not path.exists():
            return False
        try:
            self.backend.play(path)
        except Exception:
            return False
        return True
