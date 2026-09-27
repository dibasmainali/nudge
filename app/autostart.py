""""Start with Windows", via the per-user Run registry key.

On any OS other than Windows this is a harmless no-op: `is_supported()` is
False and `is_enabled()` / `set_enabled()` never touch anything, so the rest
of the app can call this module unconditionally.
"""
import ntpath
import os
import sys

APP_NAME = "Nudge"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def is_supported() -> bool:
    return sys.platform == "win32"


def _quiet_python(python_exe: str, exists=os.path.exists) -> str:
    """Prefer pythonw.exe over python.exe for the login command: python.exe opens a
    visible console window (even briefly, at every login), while pythonw.exe is the
    same interpreter built without one. Falls back to python_exe unchanged if no
    pythonw.exe sits next to it (e.g. some non-standard installs).

    Deliberately uses ntpath rather than os.path: these are always Windows paths
    (this whole module is Windows-only), regardless of which OS runs the code that
    builds the string — including this test suite, which may run on Linux."""
    folder = ntpath.dirname(python_exe)
    name = ntpath.basename(python_exe)
    if name.lower() == "pythonw.exe":
        return python_exe
    candidate = ntpath.join(folder, "pythonw.exe")
    return candidate if exists(candidate) else python_exe


def launch_command(python_exe: str, script: str, frozen: bool, frozen_exe: str,
                    exists=os.path.exists) -> str:
    """The command line Windows should run at login. A pure function so it's testable
    on any OS: a frozen (PyInstaller) build runs its own .exe (already windowed, so no
    console concern); running from source re-invokes the interpreter, preferring the
    windowless pythonw.exe, with --background."""
    if frozen:
        return f'"{frozen_exe}" --background'
    quiet = _quiet_python(python_exe, exists)
    return f'"{quiet}" "{script}" --background'


def _current_command() -> str:
    return launch_command(sys.executable, os.path.abspath(sys.argv[0]),
                          getattr(sys, "frozen", False), sys.executable)


def is_enabled() -> bool:
    if not is_supported():
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, APP_NAME)
        return True
    except OSError:
        return False


def set_enabled(enabled: bool) -> None:
    if not is_supported():
        return
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _current_command())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
