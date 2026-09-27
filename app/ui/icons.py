"""App / tray icon, drawn from the mascot so we need no image files."""
from functools import lru_cache

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap

from app.ui.mascot import BODY_BOTTOM, BODY_TOP, INK, body_path

SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)
BRAND_TOP, BRAND_BOTTOM = QColor("#9486F8"), QColor("#6A5BE2")


def draw_icon(p: QPainter, size: int, paused: bool = False) -> None:
    """Paint the icon into a size x size area."""
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(size / 100.0, size / 100.0)

    tile = QPainterPath()
    tile.addRoundedRect(QRectF(3, 3, 94, 94), 26, 26)
    g = QLinearGradient(0, 0, 100, 100)
    g.setColorAt(0, BRAND_TOP); g.setColorAt(1, BRAND_BOTTOM)
    p.setPen(Qt.NoPen); p.setBrush(g); p.drawPath(tile)

    # the blob, enlarged so it fills the tile
    p.save()
    p.translate(50, 53); p.scale(1.12, 1.12); p.translate(-50, -57)
    bg = QLinearGradient(50, 26, 50, 86)
    bg.setColorAt(0, BODY_TOP); bg.setColorAt(1, BODY_BOTTOM)
    p.setBrush(bg); p.drawPath(body_path())
    if size >= 24:                                   # cheeks are mush at 16px
        p.setBrush(QColor(255, 140, 155, 170))
        for cx in (28.5, 71.5):
            p.drawEllipse(QPointF(cx, 64), 5.4, 3.3)
    if paused:                                       # sleeping while paused
        p.setBrush(Qt.NoBrush)
        pen = QPen(INK, 4.2, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        for cx in (38, 62):
            arc = QPainterPath(QPointF(cx - 5.5, 55)); arc.quadTo(cx, 61.5, cx + 5.5, 55)
            p.drawPath(arc)
    else:
        p.setBrush(INK)
        for cx in (38, 62):
            p.drawEllipse(QPointF(cx, 56), 5.2, 6.2)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(INK, 3.4, Qt.SolidLine, Qt.RoundCap))
        smile = QPainterPath(QPointF(43.5, 66)); smile.quadTo(50, 73, 56.5, 66)
        p.drawPath(smile)
    p.restore()

    if paused:                                       # small "pause" badge, bottom-right
        p.setPen(QPen(QColor("white"), 3))
        p.setBrush(QColor("#FF9E6B"))
        p.drawEllipse(QPointF(76, 76), 20, 20)
        p.setPen(Qt.NoPen); p.setBrush(QColor("white"))
        p.drawRoundedRect(QRectF(68.5, 66, 5.5, 20), 2, 2)
        p.drawRoundedRect(QRectF(78.5, 66, 5.5, 20), 2, 2)


@lru_cache(maxsize=4)
def make_app_icon(paused: bool = False) -> QIcon:
    icon = QIcon()
    for s in SIZES:
        pm = QPixmap(s, s)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        draw_icon(p, s, paused)
        p.end()
        icon.addPixmap(pm)
    return icon
