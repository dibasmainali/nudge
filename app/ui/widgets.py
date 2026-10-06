"""Small reusable custom widgets."""
from PySide6.QtCore import (Property, QEasingCurve, QPropertyAnimation, QRectF,
                            Qt, Signal)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from app.ui.theme import Palette, mix


class ToggleSwitch(QWidget):
    """An iOS-style on/off switch. Call setChecked() to sync state programmatically
    (no signal emitted); the user clicking it emits `toggled(bool)`."""

    toggled = Signal(bool)
    WIDTH, HEIGHT = 42, 24

    def __init__(self, checked: bool = False, accent: str = "#7C6CF0",
                 pal: Palette | None = None, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._accent = QColor(accent)
        self._pal = pal
        self._pos = 1.0 if checked else 0.0
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setCursor(Qt.PointingHandCursor)
        self._anim = QPropertyAnimation(self, b"knob_pos", self)
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool, animate: bool = True) -> None:
        checked = bool(checked)
        if checked == self._checked:
            return
        self._checked = checked
        self._anim.stop()
        if animate and self.isVisible():
            self._anim.setStartValue(self._pos)
            self._anim.setEndValue(1.0 if checked else 0.0)
            self._anim.start()
        else:
            self.set_knob_pos(1.0 if checked else 0.0)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and self.rect().contains(event.pos()) and self.isEnabled():
            self.setChecked(not self._checked)
            self.toggled.emit(self._checked)
        super().mouseReleaseEvent(event)

    def get_knob_pos(self) -> float:
        return self._pos

    def set_knob_pos(self, value: float) -> None:
        self._pos = value
        self.update()

    knob_pos = Property(float, get_knob_pos, set_knob_pos)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        off = QColor(120, 113, 140, 90) if (self._pal and self._pal.dark) else QColor(210, 206, 226)
        track = mix(off, self._accent, self._pos)
        if not self.isEnabled():
            track = QColor(track.red(), track.green(), track.blue(), 90)
        p.setPen(Qt.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(QRectF(0, 0, self.WIDTH, self.HEIGHT), self.HEIGHT / 2, self.HEIGHT / 2)
        r = self.HEIGHT / 2 - 3
        cx = r + 3 + self._pos * (self.WIDTH - self.HEIGHT)
        p.setBrush(QColor("white"))
        p.drawEllipse(QRectF(cx - r, self.HEIGHT / 2 - r, r * 2, r * 2))
