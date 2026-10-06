"""Build script for Nudge - creates a standalone Windows executable using PyInstaller."""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from app.version import __version__


def _version_tuple(version: str):
    match = re.match(r"(\d+)\.(\d+)\.(\d+)", version)
    if match is None:
        raise ValueError(f"Unsupported version string: {version!r}")
    return tuple(int(part) for part in match.groups())


def _update_version_file(version_file: Path, version: str):
    if not version_file.exists():
        return

    major, minor, patch = _version_tuple(version)
    content = version_file.read_text(encoding="utf-8")
    content = re.sub(
        r"filevers=\(\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+\)",
        f"filevers=({major}, {minor}, {patch}, 0)",
        content,
    )
    content = re.sub(
        r"prodvers=\(\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+\)",
        f"prodvers=({major}, {minor}, {patch}, 0)",
        content,
    )
    for field in ("FileVersion", "ProductVersion"):
        pattern = rf"(StringStruct\(u'{field}',\s*u')[^']+(')"
        content, replacements = re.subn(pattern, rf"\g<1>{version}\g<2>", content)
        if replacements != 1:
            raise ValueError(
                f"Expected one {field} entry in {version_file}, found {replacements}"
            )
    version_file.write_text(content, encoding="utf-8")


def run_build():
    project_root = Path(__file__).parent
    dist_dir = project_root / "dist"
    build_dir = project_root / "build_pyinstaller"

    # Clean previous builds
    for d in (dist_dir, build_dir):
        if d.exists():
            shutil.rmtree(d)

    version_file = project_root / "file_version_info.txt"
    _update_version_file(version_file, __version__)

    assets_dir = project_root / "assets"
    asset_data = os.pathsep.join([str(assets_dir), "assets"])

    # PyInstaller command
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=Nudge",
        "--windowed",
        "--onefile",
        "--clean",
        "--noconfirm",
        f"--specpath={build_dir}",
        f"--workpath={build_dir}",
        f"--add-data={asset_data}",
        f"--icon={project_root / 'assets' / 'icon.ico'}" if (project_root / "assets" / "icon.ico").exists() else "",
        f"--version-file={version_file}",
        "--hidden-import=winreg",
        "--hidden-import=ctypes",
        "--hidden-import=sqlite3",
        "--hidden-import=json",
        "--hidden-import=app.ui.mascot",
        "--hidden-import=app.ui.charts",
        "--hidden-import=app.ui.widgets",
        "--hidden-import=app.ui.theme",
        "--hidden-import=app.ui.stats_window",
        "--hidden-import=app.ui.settings_window",
        "--hidden-import=app.ui.main_window",
        "--hidden-import=app.ui.popup",
        "--hidden-import=app.ui.icons",
        "--hidden-import=app.controller",
        "--hidden-import=app.reminder",
        "--hidden-import=app.settings",
        "--hidden-import=app.database",
        "--hidden-import=app.sound",
        "--hidden-import=PySide6.QtMultimedia",
        "--hidden-import=app.tray",
        "--hidden-import=app.autostart",
        "--hidden-import=app.paths",
        "--hidden-import=app.single_instance",
        "--hidden-import=app.updater",
        "--hidden-import=app.version",
        "app/main.py",
    ]

    # Remove empty icon arg if no icon exists
    cmd = [c for c in cmd if c]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)

    if result.returncode == 0:
        print("\n[OK] Build successful!")
        print(f"Executable: {dist_dir / 'Nudge.exe'}")
    else:
        print("\n[ERROR] Build failed!")
        sys.exit(result.returncode)


if __name__ == "__main__":
    run_build()