# Changelog

All notable changes to Nudge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-26

### Added
- **Phase 1**: Core reminder engine with 5 reminder types (Water, Eye break, Movement, Focus, Sleep)
- **Phase 2**: Polished popup UI with rounded corners, smooth animations, per-reminder colors
- **Phase 3**: Vector mascot with 5 moods (happy, relaxed, energetic, focused, sleepy), idle animation, blinking, pop-in entrance, celebration animation
- **Phase 4**: System tray integration with custom mascot-based icon, context menu, single-instance guard
- **Phase 5**: Settings window with per-reminder intervals, enable/disable toggles, snooze, sounds, animations, "Start with Windows", pause-all
- **Phase 6**: SQLite history database, Statistics window with today's counts, 7-day chart, streaks, achievement badges
- **Phase 7**: Hardened "Start with Windows" using pythonw.exe to prevent console flash at login
- **Phase 8**: PyInstaller build for standalone Windows executable (~54 MB)
- **Phase 9**: Inno Setup installer (NudgeSetup.exe) with Start Menu/Desktop shortcuts, Start with Windows option, clean uninstaller

### Features
- 5 reminder types with customizable intervals
- Cute animated mascot that reacts to reminder type
- System tray with pause/resume, settings, statistics, quit
- Local SQLite storage (no cloud, privacy-first)
- Light/dark/auto theme following Windows
- Sound notifications (chime on reminder, done sound on completion)
- Keyboard accessible, screen-reader friendly
- Portable: runs from anywhere, no admin required for user-mode install

### Technical
- Python 3.10+ with PySide6 (Qt 6)
- Modular architecture for future macOS/Linux support
- Single-instance enforcement via local socket
- Atomic settings writes (no corruption on crash)
- Frozen detection for PyInstaller (autostart uses .exe directly)

## [Unreleased]

### Planned
- Code signing certificate (when available)
- macOS/Linux builds
- More mascot animations
- Custom reminder messages
- Export/import settings