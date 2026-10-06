"""Where things live on disk, both running from source and as a frozen .exe."""
import sys
from pathlib import Path


def app_root() -> Path:
    """Folder that contains assets/ — the PyInstaller temp dir when frozen, else the repo root."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def resource_path(*parts: str) -> Path:
    """Join path parts (each may itself contain '/') onto the app root."""
    return app_root().joinpath(*parts)
