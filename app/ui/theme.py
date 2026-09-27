"""Colours and stylesheet for the popup. All visual constants live here."""
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication

FONT_STACK = '"Segoe UI Variable Text", "Segoe UI", "Inter", "Helvetica Neue", sans-serif'
EMOJI_FONTS = ["Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji"]


@dataclass(frozen=True)
class Accent:
    main: str    # buttons, progress bar
    tint: str    # soft background glow / badge


ACCENTS: dict[str, Accent] = {
    "water":    Accent("#4C9AF5", "#DCEBFF"),   # sky blue
    "eye":      Accent("#3FB5A4", "#D9F3EE"),   # calm teal
    "movement": Accent("#F58A5B", "#FFE5D8"),   # warm coral
    "focus":    Accent("#7C6CF0", "#E8E4FE"),   # violet
    "sleep":    Accent("#5C6BD0", "#E0E4F8"),   # dusk indigo
}
DEFAULT_ACCENT = ACCENTS["focus"]


@dataclass(frozen=True)
class Palette:
    dark: bool
    card: QColor
    edge: QColor
    title: QColor
    message: QColor
    track: QColor           # empty part of the progress bar
    shadow: QColor
    shadow_strength: float  # peak alpha of one shadow layer
    surface: QColor         # cards inside windows (settings)


LIGHT = Palette(False, QColor("#FFFFFF"), QColor(30, 20, 80, 22), QColor("#2A2340"),
                QColor("#6E6787"), QColor(30, 20, 80, 16), QColor(35, 25, 90), 7.0, QColor("#F6F4FC"))
DARK = Palette(True, QColor("#25222F"), QColor(255, 255, 255, 24), QColor("#F4F1FF"),
               QColor("#B4AECB"), QColor(255, 255, 255, 22), QColor(0, 0, 0), 12.0, QColor("#302C3D"))

_override: str | None = None    # "light" | "dark" | None (follow the OS)


def set_theme_override(mode: str | None) -> None:
    global _override
    _override = mode if mode in ("light", "dark") else None


def is_dark() -> bool:
    if _override:
        return _override == "dark"
    try:
        return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except Exception:
        return False


def current_palette() -> Palette:
    return DARK if is_dark() else LIGHT


def mix(a: QColor, b: QColor, t: float) -> QColor:
    """Blend a towards b by t (0..1)."""
    return QColor(round(a.red() + (b.red() - a.red()) * t),
                  round(a.green() + (b.green() - a.green()) * t),
                  round(a.blue() + (b.blue() - a.blue()) * t))


def popup_stylesheet(accent: Accent, pal: Palette) -> str:
    main, tint = QColor(accent.main), QColor(accent.tint)
    if pal.dark:
        sec_bg, sec_hover, sec_text = mix(pal.card, main, 0.24), mix(pal.card, main, 0.36), tint
    else:
        sec_bg, sec_hover, sec_text = tint, mix(tint, main, 0.2), main.darker(130)
    close_hover = "rgba(255,255,255,30)" if pal.dark else "rgba(30,20,80,18)"
    return f"""
    * {{ font-family: {FONT_STACK}; }}
    QLabel {{ background: transparent; }}
    QLabel#title {{ color: {pal.title.name()}; font-size: 17px; font-weight: 600; }}
    QLabel#message {{ color: {pal.message.name()}; font-size: 13px; }}
    QPushButton {{ border: none; border-radius: 12px; padding: 0 14px;
                   min-height: 38px; font-size: 13px; font-weight: 600; }}
    QPushButton#primary {{ background: {main.name()}; color: white; }}
    QPushButton#primary:hover {{ background: {main.darker(108).name()}; }}
    QPushButton#primary:pressed {{ background: {main.darker(122).name()}; }}
    QPushButton#secondary {{ background: {sec_bg.name()}; color: {sec_text.name()}; }}
    QPushButton#secondary:hover {{ background: {sec_hover.name()}; }}
    QPushButton#secondary:pressed {{ background: {sec_hover.darker(106).name()}; }}
    QPushButton#close {{ background: transparent; color: {pal.message.name()};
                         border-radius: 11px; padding: 0; min-height: 22px; min-width: 22px;
                         font-size: 16px; font-weight: 400; }}
    QPushButton#close:hover {{ background: {close_hover}; }}
    """
