"""The Nudge mascot: a soft mochi-like blob drawn entirely with QPainter (vector, no assets).

One character, five moods. Each mood has its own face, accessory and idle motion:
    happy      water     - smiling, gentle sway, floating droplet
    relaxed    eye break - closed content eyes, slow breathing
    energetic  movement  - hops, waves both arms, sparkles
    focused    study     - round glasses, eyes scanning side to side
    sleepy     wind-down - closed eyes, nightcap, floating z's
"""
import math
import random

from PySide6.QtCore import QEasingCurve, QPointF, QRectF, Qt, QTimer, QVariantAnimation
from PySide6.QtGui import (QColor, QFont, QLinearGradient, QPainter, QPainterPath,
                           QPen, QRadialGradient)
from PySide6.QtWidgets import QWidget

from app.ui.theme import Accent, Palette, mix

TAU = 2 * math.pi
MOODS = ("happy", "relaxed", "energetic", "focused", "sleepy")

INK = QColor("#3B2F4F")
BODY_TOP, BODY_BOTTOM, ARM = QColor("#FFFDF9"), QColor("#FFDFCF"), QColor("#FFEADD")
SPARK_WARM, SPARK_GOLD = QColor("#FF9E6B"), QColor("#FFC857")


def body_path() -> QPainterPath:
    """The blob silhouette (100x100 space). Shared with the tray icon."""
    path = QPainterPath(QPointF(50, 26))
    path.cubicTo(72, 26, 84, 42, 84, 60)
    path.cubicTo(84, 77, 72, 86, 50, 86)
    path.cubicTo(28, 86, 16, 77, 16, 60)
    path.cubicTo(16, 42, 28, 26, 50, 26)
    return path


def _star(p: QPainter, cx: float, cy: float, r: float, color: QColor, alpha: float = 1.0) -> None:
    """Four-point sparkle."""
    if r <= 0.2 or alpha <= 0:
        return
    path = QPainterPath()
    for i in range(8):
        ang = i * math.pi / 4
        rad = r if i % 2 == 0 else r * 0.28
        pt = QPointF(cx + rad * math.cos(ang), cy + rad * math.sin(ang))
        path.moveTo(pt) if i == 0 else path.lineTo(pt)
    path.closeSubpath()
    c = QColor(color)
    c.setAlphaF(max(0.0, min(1.0, alpha)))
    p.setPen(Qt.NoPen)
    p.setBrush(c)
    p.drawPath(path)


class MascotWidget(QWidget):
    """Animated mascot. Everything is drawn in a 100x100 coordinate space and scaled."""

    def __init__(self, mood: str, accent: Accent, pal: Palette, size: int = 96,
                 droplet: bool = True, parent=None):
        super().__init__(parent)
        self.mood = mood if mood in MOODS else "happy"
        self._accent, self._pal = accent, pal
        self._droplet = droplet        # the water droplet only belongs to the water reminder
        self._t = 0.0                  # position in the 6-second idle loop (0..1)
        self._blink = 0.0              # 0 = eyes open, 1 = closed
        self._pop = 1.0                # entrance scale-in (0..1)
        self._cel: float | None = None  # celebration progress, None when idle
        self.setFixedSize(size, size)

        self._loop = QVariantAnimation(self)
        self._loop.setStartValue(0.0); self._loop.setEndValue(1.0)
        self._loop.setDuration(6000); self._loop.setLoopCount(-1)
        self._loop.setEasingCurve(QEasingCurve.Linear)
        self._loop.valueChanged.connect(lambda v: self._set("_t", v))

        self._blink_anim = QVariantAnimation(self)
        self._blink_anim.setDuration(150)
        self._blink_anim.setKeyValueAt(0.0, 0.0)
        self._blink_anim.setKeyValueAt(0.5, 1.0)
        self._blink_anim.setKeyValueAt(1.0, 0.0)
        self._blink_anim.valueChanged.connect(lambda v: self._set("_blink", v))
        self._blink_timer = QTimer(self, singleShot=True)
        self._blink_timer.timeout.connect(self._do_blink)

        self._pop_anim = QVariantAnimation(self)
        self._pop_anim.setStartValue(0.0); self._pop_anim.setEndValue(1.0)
        self._pop_anim.setDuration(520)
        curve = QEasingCurve(QEasingCurve.OutBack); curve.setOvershoot(2.2)
        self._pop_anim.setEasingCurve(curve)
        self._pop_anim.valueChanged.connect(lambda v: self._set("_pop", v))

        self._cel_anim = QVariantAnimation(self)
        self._cel_anim.setStartValue(0.0); self._cel_anim.setEndValue(1.0)
        self._cel_anim.setDuration(460)
        self._cel_anim.valueChanged.connect(lambda v: self._set("_cel", v))
        self._cel_anim.finished.connect(lambda: self._set("_cel", None))

    # ---- control API ------------------------------------------------------
    def _set(self, name: str, value) -> None:
        setattr(self, name, None if value is None else float(value))
        self.update()

    def prepare(self) -> None:
        """Hide the mascot (scale 0) so start() can pop it in."""
        self._pop = 0.0
        self.update()

    def start(self) -> None:
        self._pop_anim.start()
        self._loop.start()
        if self.mood in ("happy", "energetic", "focused"):
            self._blink_timer.start(random.randint(1800, 3500))

    def stop(self) -> None:
        for a in (self._loop, self._blink_anim, self._pop_anim):
            a.stop()
        self._blink_timer.stop()

    def set_mood(self, mood: str) -> None:
        """Switch mood on the fly (e.g. the home window goes sleepy while paused)."""
        mood = mood if mood in MOODS else "happy"
        if mood == self.mood:
            return
        self.mood = mood
        if self._loop.state() == QVariantAnimation.Running and mood in ("happy", "energetic", "focused"):
            self._blink_timer.start(random.randint(1800, 3500))
        else:
            self._blink_timer.stop()
        self.update()

    def celebrate(self) -> None:
        self._cel_anim.start()

    def set_pose(self, t: float = 0.0, blink: float = 0.0, cel: float | None = None) -> None:
        """Freeze the mascot in a given pose (used by the preview tools)."""
        self._t, self._blink, self._cel, self._pop = t, blink, cel, 1.0
        self.update()

    def _do_blink(self) -> None:
        self._blink_anim.start()
        self._blink_timer.start(random.randint(2600, 5200))

    # ---- motion -------------------------------------------------------------
    def _motion(self):
        """Returns (dy, rotation°, sx, sy, air) where air is 0..1 height off the ground."""
        t, m = self._t, self.mood
        dy = rot = 0.0
        sx = sy = 1.0
        air = 0.0
        if m == "happy":
            s = math.sin(TAU * 2 * t); rot = 3 * s; sy = 1 + 0.02 * s; sx = 1 - 0.012 * s
        elif m == "relaxed":
            s = math.sin(TAU * t); sy = 1 + 0.03 * s; sx = 1 - 0.02 * s
        elif m == "energetic":
            air = abs(math.sin(math.pi * 5 * t)); dy = -10 * air
            land = (1 - air) ** 6
            sy = 1 - 0.08 * land + 0.03 * air; sx = 1 + 0.06 * land - 0.02 * air
        elif m == "focused":
            s = math.sin(TAU * 2 * t); sy = 1 + 0.012 * s; sx = 1 - 0.008 * s
        else:  # sleepy
            s = math.sin(TAU * t); rot = 4 * s; sy = 1 + 0.02 * s
        if self._cel is not None:
            jump = math.sin(math.pi * self._cel)
            dy -= 9 * jump; air = max(air, jump)
        return dy, rot, sx, sy, air

    # ---- painting -----------------------------------------------------------
    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        k = self.width() / 100.0
        p.scale(k, k)
        pal, acc = self._pal, self._accent
        tint, main = QColor(acc.tint), QColor(acc.main)
        dy, rot, sx, sy, air = self._motion()

        # soft halo behind the character
        halo = QRadialGradient(50, 50, 44)
        if pal.dark:
            halo.setColorAt(0.0, QColor(main.red(), main.green(), main.blue(), 105))
            halo.setColorAt(1.0, QColor(main.red(), main.green(), main.blue(), 30))
        else:
            halo.setColorAt(0.0, mix(tint, QColor("white"), 0.5))
            halo.setColorAt(1.0, tint)
        p.setPen(Qt.NoPen)
        p.setBrush(halo)
        p.drawEllipse(QPointF(50, 52), 44, 44)

        # pop-in: scale + fade everything else from the bottom centre
        p.save()
        p.translate(50, 86)
        p.scale(0.55 + 0.45 * self._pop, 0.55 + 0.45 * self._pop)
        p.translate(-50, -86)
        p.setOpacity(max(0.0, min(1.0, self._pop * 1.6)))

        # ground shadow shrinks as the character leaves the ground
        shadow = QColor(0, 0, 0, 90) if pal.dark else QColor(70, 45, 110, 48)
        p.setBrush(shadow)
        p.drawEllipse(QPointF(50, 87.5), 23 * (1 - 0.3 * air), 3.6 * (1 - 0.3 * air))

        # ---- body (squash/stretch + tilt around the feet) ----
        p.save()
        p.translate(50, 86 + dy)
        p.rotate(rot)
        p.scale(sx, sy)
        p.translate(-50, -86)

        if self.mood == "energetic" or self._cel is not None:
            self._arms(p)
        self._body(p)
        self._face(p)
        if self.mood == "focused":
            self._glasses(p)
        elif self.mood == "sleepy":
            self._nightcap(p)
        p.restore()

        self._floaters(p)
        p.restore()

    def _arms(self, p: QPainter) -> None:
        wave = 6 * math.sin(TAU * 10 * self._t) if self._cel is None else 4
        for side, sign in (("L", -1), ("R", 1)):
            root = QPointF(50 + sign * 31, 62)
            tip = QPointF(50 + sign * (41 + (wave if side == "R" else -wave) * 0.3),
                          40 + (wave if side == "R" else -wave))
            edge = QPen(QColor(90, 60, 120, 45) if not self._pal.dark else QColor(0, 0, 0, 60),
                        9.6, Qt.SolidLine, Qt.RoundCap)
            p.setPen(edge); p.drawLine(root, tip)
            p.setPen(QPen(ARM, 8, Qt.SolidLine, Qt.RoundCap)); p.drawLine(root, tip)

    def _body(self, p: QPainter) -> None:
        path = body_path()
        g = QLinearGradient(50, 26, 50, 86)
        g.setColorAt(0, BODY_TOP); g.setColorAt(1, BODY_BOTTOM)
        p.setBrush(g)
        p.setPen(QPen(QColor(90, 60, 120, 45), 0.9) if not self._pal.dark else Qt.NoPen)
        p.drawPath(path)
        # glossy highlight
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 190))
        p.save(); p.translate(37, 35); p.rotate(-30)
        p.drawEllipse(QPointF(0, 0), 8.5, 3.4)
        p.restore()

    # ---- face ---------------------------------------------------------------
    def _eye_open(self, p, cx, cy, rx, ry, look=0.0):
        openness = 1.0 - self._blink * 0.95
        p.setPen(Qt.NoPen); p.setBrush(INK)
        p.drawEllipse(QPointF(cx + look, cy), rx, max(0.5, ry * openness))
        if openness > 0.4:
            p.setBrush(QColor("white"))
            p.drawEllipse(QPointF(cx + look - rx * 0.32, cy - ry * 0.35 * openness), rx * 0.34, rx * 0.34)

    def _eye_arc(self, p, cx, cy, up=True):
        path = QPainterPath(QPointF(cx - 5, cy + (1.5 if up else -0.5)))
        path.quadTo(cx, cy - 6 if up else cy + 6, cx + 5, cy + (1.5 if up else -0.5))
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(INK, 2.3, Qt.SolidLine, Qt.RoundCap))
        p.drawPath(path)

    def _smile(self, p, half_width=5.5, depth=6.0, y=65.5):
        path = QPainterPath(QPointF(50 - half_width, y))
        path.quadTo(50, y + depth, 50 + half_width, y)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(INK, 2.2, Qt.SolidLine, Qt.RoundCap))
        p.drawPath(path)

    def _open_mouth(self, p):
        path = QPainterPath(QPointF(43.5, 64))
        path.lineTo(56.5, 64)
        path.quadTo(56, 75.5, 50, 75.5)
        path.quadTo(44, 75.5, 43.5, 64)
        p.setPen(Qt.NoPen); p.setBrush(INK); p.drawPath(path)
        p.setBrush(QColor("#FF8FA3")); p.drawEllipse(QPointF(50, 72.6), 3.6, 2.2)

    def _face(self, p: QPainter) -> None:
        m, t = self.mood, self._t
        celebrating = self._cel is not None
        # cheeks
        cheek = QColor(255, 140, 155, 170 if not self._pal.dark else 140)
        if m in ("relaxed", "sleepy"):
            cheek.setAlpha(210)
        p.setPen(Qt.NoPen); p.setBrush(cheek)
        for cx in (28.5, 71.5):
            p.drawEllipse(QPointF(cx, 64), 5.4, 3.3)

        if celebrating:
            self._eye_arc(p, 38, 56, up=True); self._eye_arc(p, 62, 56, up=True)
            self._open_mouth(p)
        elif m == "happy":
            for cx in (38, 62): self._eye_open(p, cx, 56, 4.4, 5.6)
            self._smile(p)
        elif m == "relaxed":
            self._eye_arc(p, 38, 56, up=True); self._eye_arc(p, 62, 56, up=True)
            self._smile(p, 4.8, 4.5)
        elif m == "energetic":
            for cx in (38, 62): self._eye_open(p, cx, 55.5, 5.0, 6.4)
            self._open_mouth(p)
        elif m == "focused":
            look = 1.3 * math.sin(TAU * 3 * t)
            for cx in (38, 62): self._eye_open(p, cx, 56, 3.7, 4.5, look)
            path = QPainterPath(QPointF(46, 67)); path.quadTo(50, 68.4, 54, 67)
            p.setBrush(Qt.NoBrush); p.setPen(QPen(INK, 2.0, Qt.SolidLine, Qt.RoundCap)); p.drawPath(path)
        else:  # sleepy
            self._eye_arc(p, 38, 56, up=False); self._eye_arc(p, 62, 56, up=False)
            r = 2.3 + 0.5 * math.sin(TAU * t)
            p.setPen(Qt.NoPen); p.setBrush(QColor(INK.red(), INK.green(), INK.blue(), 225))
            p.drawEllipse(QPointF(50, 67), r, r * 1.2)

    def _glasses(self, p: QPainter) -> None:
        frame = QColor(self._accent.main).darker(115)
        p.setBrush(QColor(255, 255, 255, 40))
        p.setPen(QPen(frame, 1.8))
        for cx in (38, 62): p.drawEllipse(QPointF(cx, 56), 8.6, 8.6)
        p.drawLine(QPointF(46.6, 55), QPointF(53.4, 55))

    def _nightcap(self, p: QPainter) -> None:
        main = QColor(self._accent.main)
        cap = QPainterPath(QPointF(24, 39))
        cap.cubicTo(27, 21, 46, 10, 66, 14)
        cap.cubicTo(76, 16, 83, 24, 88, 38)
        cap.lineTo(76, 36)
        cap.cubicTo(62, 31, 40, 33, 24, 39)
        g = QLinearGradient(30, 12, 60, 40)
        g.setColorAt(0, main.lighter(115)); g.setColorAt(1, main.darker(105))
        p.setPen(Qt.NoPen); p.setBrush(g); p.drawPath(cap)
        p.setPen(QPen(QColor("#F6F3FF"), 4.2, Qt.SolidLine, Qt.RoundCap))     # fluffy rim
        p.drawLine(QPointF(25, 39), QPointF(77, 36))
        p.setPen(Qt.NoPen); p.setBrush(QColor("#FFFFFF")); p.drawEllipse(QPointF(88, 39), 4.6, 4.6)

    # ---- floating extras (not attached to the body) ---------------------------
    def _floaters(self, p: QPainter) -> None:
        m, t = self.mood, self._t
        main, tint = QColor(self._accent.main), QColor(self._accent.tint)
        if m == "happy":
            if self._droplet:
                self._droplet_shape(p, 80, 27 + 3 * math.sin(TAU * 2 * t + 1), 10 * math.sin(TAU * 2 * t))
            _star(p, 17, 34, 4 + 1.2 * math.sin(TAU * 3 * t), main, 0.9)
        elif m == "relaxed":
            _star(p, 19, 32, 4.5 + 1.3 * math.sin(TAU * 2 * t), main, 0.9)
            _star(p, 82, 40, 3.2 + 1.0 * math.sin(TAU * 2 * t + 2), main, 0.75)
        elif m == "energetic":
            for i, (x, y, col) in enumerate(((13, 30, SPARK_WARM), (88, 26, SPARK_GOLD), (78, 10, SPARK_WARM))):
                _star(p, x, y, 5 + 2.2 * math.sin(TAU * 3 * t + i * 2), col, 0.95)
        elif m == "sleepy":
            font = QFont(); font.setFamilies(["Segoe UI", "Inter", "Helvetica Neue", "Arial"])
            font.setPixelSize(10); font.setBold(True); font.setItalic(True)
            p.setFont(font)
            for i in range(3):
                u = (t * 2 + i / 3) % 1.0
                p.save()
                p.translate(72 + 12 * u, 36 - 22 * u)
                s = (7 + 6 * u) / 10.0
                p.scale(s, s)
                c = QColor(tint if self._pal.dark else main)
                c.setAlphaF(math.sin(math.pi * u) * 0.95)
                p.setPen(c)
                p.drawText(QPointF(0, 0), "z")
                p.restore()
        if self._cel is not None:                      # burst of sparkles on "done"
            c = self._cel
            for i in range(6):
                ang = TAU * i / 6 + 0.4
                rad = 22 + 24 * c
                _star(p, 50 + rad * math.cos(ang), 50 + rad * math.sin(ang) * 0.9,
                      5.5 * math.sin(math.pi * c) + 0.3, SPARK_GOLD if i % 2 else SPARK_WARM,
                      1.0 - c * 0.6)

    def _droplet_shape(self, p: QPainter, cx: float, cy: float, tilt: float) -> None:
        main = QColor(self._accent.main)
        drop = QPainterPath(QPointF(0, -9))
        drop.cubicTo(2, -5, 6, -1, 6, 3)
        drop.cubicTo(6, 7, 3, 10, 0, 10)
        drop.cubicTo(-3, 10, -6, 7, -6, 3)
        drop.cubicTo(-6, -1, -2, -5, 0, -9)
        p.save(); p.translate(cx, cy); p.rotate(tilt); p.scale(0.95, 0.95)
        g = QLinearGradient(0, -9, 0, 10)
        g.setColorAt(0, main.lighter(130)); g.setColorAt(1, main)
        p.setPen(Qt.NoPen); p.setBrush(g); p.drawPath(drop)
        p.setBrush(QColor(255, 255, 255, 200)); p.drawEllipse(QPointF(-2.0, 3.0), 1.4, 2.4)
        p.restore()
