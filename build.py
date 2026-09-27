"""Build script for Nudge - creates a standalone Windows executable using PyInstaller."""
import os
import sys
import shutil
import subprocess
from pathlib import Path

from app.version import __version__


def run_build():
    project_root = Path(__file__).parent
    dist_dir = project_root / "dist"
    build_dir = project_root / "build_pyinstaller"

    # Clean previous builds
    for d in (dist_dir, build_dir):
        if d.exists():
            shutil.rmtree(d)

    version_tuple = tuple(int(x) for x in __version__.split("."))
    version_file = project_root / "file_version_info.txt"
    # Update version in file_version_info.txt
    content = version_file.read_text(encoding="utf-8")
    content = content.replace("(1, 0, 0, 0)", f"({version_tuple[0]}, {version_tuple[1]}, {version_tuple[2]}, 0)")
    content = content.replace("u'1.0.0'", f"u'{__version__}'")
    version_file.write_text(content, encoding="utf-8")

    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Nudge",
        "--windowed",
        "--onefile",
        "--clean",
        "--noconfirm",
        f"--add-data={project_root / 'assets'};assets",
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
        print("\n✅ Build successful!")
        print(f"Executable: {dist_dir / 'Nudge.exe'}")
    else:
        print("\n❌ Build failed!")
        sys.exit(result.returncode)


if __name__ == "__main__":
    run_build()