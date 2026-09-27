# Nudge

A tiny friendly desktop companion that gently reminds you to drink water, rest your eyes, stretch, take focus breaks, and wind down at night.

[![Release](https://img.shields.io/github/v/release/dibasmainali/nudge?include_prereleases&label=latest)](https://github.com/dibasmainali/nudge/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.txt)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)]()

> **Nudge** is not a boring notification app. It feels like a small desktop companion that occasionally appears in the corner of your screen with a beautiful, friendly UI and a cute animated character.

## ✨ Features

| Feature | Description |
|---------|-------------|
| **💧 Hydration** | Customizable water break reminders |
| **👀 Eye breaks** | 20-20-20 rule reminders |
| **🧘 Movement** | Stretch & stand reminders |
| **📚 Focus sessions** | Work/break timer (Pomodoro-style) |
| **🌙 Wind-down** | Bedtime reminders (configurable hours) |
| **🎭 Animated mascot** | 5 moods: happy, relaxed, energetic, focused, sleepy |
| **📊 Statistics** | Daily counts, 7-day charts, streaks, achievements |
| **⚙️ Settings** | Per-reminder intervals, snooze, sounds, animations, auto-start |
| **🔕 System tray** | Pause/resume, quick access, single-instance |
| **🔒 Privacy-first** | All data stored locally (SQLite), no cloud, no accounts |

## 📥 Download

**Latest release:** [NudgeSetup.exe](https://github.com/dibasmainali/nudge/releases/latest)

| File | Size | Description |
|------|------|-------------|
| `NudgeSetup.exe` | ~57 MB | Windows installer (recommended) |
| `Nudge.exe` | ~55 MB | Portable standalone executable |

> **No Python installation required.** Just download, install, and run.

## 🚀 Quick Start

1. Download `NudgeSetup.exe` from [Releases](https://github.com/dibasmainali/nudge/releases)
2. Run the installer (no admin rights needed)
3. Nudge starts automatically and lives in your system tray
4. Right-click the tray icon → **Settings** to customize

## 🛠️ For Developers

### Requirements
- Python 3.10+
- Windows 10/11 (primary target)

### Setup
```powershell
git clone https://github.com/dibasmainali/nudge.git
cd nudge
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run from source
```powershell
python -m app.main
```

### Test commands
```powershell
# Show a water reminder immediately
python -m app.main --show water

# Speed up time (45 min → 9 sec) for testing
python -m app.main --speed 300 --show water

# Force dark theme
python -m app.main --show water --theme dark

# Start hidden in tray (like Windows startup)
python -m app.main --background
```

### Run tests
```powershell
python -m unittest discover -s tests -t .
```

### Build executable
```powershell
python build.py
# Output: dist/Nudge.exe
```

### Build installer
```powershell
# Requires Inno Setup 7
iscc setup.iss
# Output: dist/NudgeSetup.exe
```

## 🏗️ Architecture

```
nudge/
├── app/
│   ├── main.py              # Entry point
│   ├── controller.py        # Glue: engine ↔ UI ↔ tray ↔ history
│   ├── reminder.py          # ReminderEngine (timing logic)
│   ├── settings.py          # Settings model + JSON persistence
│   ├── database.py          # HistoryStore (SQLite)
│   ├── tray.py              # System tray + menu
│   ├── autostart.py         # Windows "Run" registry key
│   ├── sound.py             # SoundPlayer (chime/done)
│   ├── single_instance.py   # Local socket singleton
│   ├── updater.py           # GitHub Releases auto-update check
│   ├── version.py           # Version constant
│   └── ui/
│       ├── popup.py         # Animated reminder popup
│       ├── main_window.py   # Home window
│       ├── settings_window.py
│       ├── stats_window.py  # Statistics + charts
│       ├── mascot.py        # Vector mascot (5 moods, animations)
│       ├── charts.py        # 7-day bar chart
│       ├── theme.py         # Light/dark stylesheets
│       ├── icons.py         # Procedural app/tray icons
│       └── widgets.py       # Custom Qt widgets
├── assets/
│   ├── icon.ico             # Generated from mascot
│   ├── sounds/              # chime.wav, done.wav
│   └── mascot/              # (reserved for future SVG assets)
├── tools/                   # Preview/debug scripts
├── tests/                   # 72 unit tests
├── build.py                 # PyInstaller build script
├── setup.iss                # Inno Setup installer script
├── file_version_info.txt    # Windows version metadata
├── CHANGELOG.md
└── LICENSE.txt
```

## 🔧 Configuration

Settings are stored in `%APPDATA%\Nudge\settings.json`:
- Reminder intervals & enable/disable
- Snooze duration
- Break length
- Sound/animation toggles
- Start with Windows
- Theme (auto/light/dark)

History (SQLite) in `%APPDATA%\Nudge\history.db`:
- Records every reminder outcome (done/later/ignored)
- Powers statistics: daily totals, 7-day chart, streaks
- "Clear history" button in Statistics window

  
## 📸 Screenshots
<table>
  <tr>
    <td>
<p align="center">
  <img width="450" alt="Nudge main view" src="https://github.com/user-attachments/assets/805c6de0-68b8-4704-b8f9-43652e716e23" /><br/>
  <em>Main reminder popup</em>
</p></td>
<td>
<p align="center">
  <img width="450" alt="Nudge settings" src="https://github.com/user-attachments/assets/4deb0dd3-3990-473e-a893-b6b8920ec7b2" /><br/>
  <em>Settings panel</em>
</p>
  <td>
</tr>
</table>
## 🗺️ Roadmap

- [x] Update check via GitHub Releases (opens the download page)
- [ ] Code signing certificate (Windows SmartScreen)
- [ ] macOS/Linux builds
- [ ] Custom reminder messages
- [ ] Export/import settings
- [ ] More mascot animations

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

## 📄 License

MIT License — see [LICENSE.txt](LICENSE.txt)

## 🙏 Acknowledgments

- Built with [PySide6](https://wiki.qt.io/Qt_for_Python) (Qt 6)
- Inspired by the need for a gentler, friendlier desktop wellness companion
- Mascot drawn procedurally with Qt's QPainter (no image assets required)

---

**Made with 💜 by [Dibas Mainali](https://github.com/dibasmainali)**
