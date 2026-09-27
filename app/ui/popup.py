"""The floating reminder popup (Phase 2: custom-painted, themed, animated)."""
from PySide6.QtCore import (QEasingCurve, QPoint, QParallelAnimationGroup, QPointF,
                            QPropertyAnimation, QRectF, Qt, QTimer, QVariantAnimation, Signal)
from PySide6.QtGui import (QBrush, QColor, QCursor, QGuiApplication, QLinearGradient,
                           QPainter, QPainterPath, QPen)
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.theme import (ACCENTS, DEFAULT_ACCENT, current_palette, popup_stylesheet)
from app.ui.mascot import MascotWidget


class ReminderPopup(QWidget):
    """Emits `closed_with(action)` AFTER it has faded out. action: done|later|ignored."""

    responded = Signal(str)       # the instant the user acts (used for the 'done' sound)
    closed_with = Signal(str)

    WIDTH = 392
    RADIUS = 22
    MARGIN = 20        # gap between the card and the screen edge
    SHADOW_PAD = 26    # transparent space around the card for the shadow

    def __init__(self, key: str, mood: str, title: str, message: str,
                 done_label: str, later_label: str,
                 animations: bool = True, timeout_seconds: int = 90):
        super().__init__()
        self._animations = animations
        self._responded = False
        self._progress = 1.0
        self._group: QParallelAnimationGroup | None = None
        self._accent = ACCENTS.get(key, DEFAULT_ACCENT)
        self._pal = current_palette()

        # Frameless, always on top, hidden from the taskbar, never steals keyboard focus.
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
                            | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedWidth(self.WIDTH)
        self.setStyleSheet(popup_stylesheet(self._accent, self._pal))

        # ---- layout (the card is painted by us; children sit inside its padding) ----
        pad = self.SHADOW_PAD
        root = QVBoxLayout(self)
        root.setContentsMargins(pad + 22, pad + 20, pad + 22, pad + 26)
        root.setSpacing(16)

        row = QHBoxLayout()
        row.setSpacing(14)
        self._badge = MascotWidget(mood, self._accent, self._pal)
        row.addWidget(self._badge, 0, Qt.AlignTop)
        texts = QVBoxLayout()
        texts.setSpacing(4)
        title_label = QLabel(title, objectName="title", wordWrap=True)
        title_label.setContentsMargins(0, 8, 22, 0)      # keep clear of the close button
        texts.addWidget(title_label)
        texts.addWidget(QLabel(message, objectName="message", wordWrap=True))
        texts.addStretch(1)
        row.addLayout(texts, 1)
        root.addLayout(row)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self._done_btn = QPushButton(done_label, objectName="primary")
        self._later_btn = QPushButton(later_label, objectName="secondary")
        for b in (self._done_btn, self._later_btn):
            b.setCursor(Qt.PointingHandCursor)
            b.setFocusPolicy(Qt.NoFocus)
            buttons.addWidget(b, 1)
        root.addLayout(buttons)

        self._close_btn = QPushButton("×", self, objectName="close")
        self._close_btn.setToolTip("Dismiss")
        self._close_btn.setCursor(Qt.PointingHandCursor)
        self._close_btn.setFocusPolicy(Qt.NoFocus)
        self._close_btn.setFixedSize(22, 22)

        self._done_btn.clicked.connect(lambda: self._respond("done"))
        self._later_btn.clicked.connect(lambda: self._respond("later"))
        self._close_btn.clicked.connect(lambda: self._respond("ignored"))

        # Slow countdown until the popup gives up and goes away by itself.
        self._countdown = QVariantAnimation(self)
        self._countdown.setStartValue(1.0)
        self._countdown.setEndValue(0.0)
        self._countdown.setDuration(max(1, timeout_seconds) * 1000)
        self._countdown.valueChanged.connect(self._on_countdown)
        self._countdown.finished.connect(lambda: self._respond("ignored"))

    # ---- geometry helpers ---------------------------------------------
    def _card_rect(self) -> QRectF:
        p = self.SHADOW_PAD
        return QRectF(self.rect()).adjusted(p, p, -p, -p)

    def _bar_rect(self) -> QRectF:
        c = self._card_rect()
        return QRectF(c.left() + 22, c.bottom() - 13, c.width() - 44, 3)

    def resizeEvent(self, event) -> None:
        c = self._card_rect()
        self._close_btn.move(int(c.right()) - 22 - 12, int(c.top()) + 12)
        self._close_btn.raise_()
        super().resizeEvent(event)

    def _target_pos(self) -> QPoint:
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        area = screen.availableGeometry()          # excludes the taskbar
        inset = self.SHADOW_PAD - self.MARGIN
        return QPoint(area.right() + 1 - self.width() + inset,
                      area.bottom() + 1 - self.height() + inset)

    # ---- painting -----------------------------------------------------
    def paintEvent(self, _event) -> None:
        pal, card = self._pal, self._card_rect()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # soft shadow: stacked translucent rounded rects, fading outwards
        p.setPen(Qt.NoPen)
        pad = self.SHADOW_PAD
        sh = pal.shadow
        for i in range(pad, 0, -1):
            alpha = int(pal.shadow_strength * (1 - i / pad) ** 2)
            p.setBrush(QColor(sh.red(), sh.green(), sh.blue(), alpha))
            p.drawRoundedRect(card.translated(0, 5).adjusted(-i, -i, i, i),
                              self.RADIUS + i, self.RADIUS + i)

        # card body + a soft accent glow from the top-left corner
        path = QPainterPath()
        path.addRoundedRect(card, self.RADIUS, self.RADIUS)
        p.fillPath(path, pal.card)
        glow = QColor(self._accent.main if pal.dark else self._accent.tint)
        glow.setAlpha(60 if pal.dark else 190)
        clear = QColor(glow); clear.setAlpha(0)
        g = QLinearGradient(card.topLeft(),
                            QPointF(card.left() + card.width() * 0.75,
                                    card.top() + card.height() * 0.95))
        g.setColorAt(0.0, glow)
        g.setColorAt(0.65, clear)
        p.fillPath(path, QBrush(g))
        p.setPen(QPen(pal.edge, 1))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)

        # thin countdown bar (only when animations are on)
        if self._animations:
            bar = self._bar_rect()
            p.setPen(Qt.NoPen)
            p.setBrush(pal.track)
            p.drawRoundedRect(bar, 1.5, 1.5)
            fill = QColor(self._accent.main)
            fill.setAlpha(170)
            p.setBrush(fill)
            p.drawRoundedRect(QRectF(bar.left(), bar.top(), bar.width() * self._progress,
                                     bar.height()), 1.5, 1.5)

    def _on_countdown(self, value) -> None:
        self._progress = float(value)
        self.update(self._bar_rect().toAlignedRect().adjusted(-2, -2, 2, 2))

    # ---- hover pauses the countdown ----------------------------------
    def enterEvent(self, event) -> None:
        if self._countdown.state() == QVariantAnimation.Running:
            self._countdown.pause()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        if self._countdown.state() == QVariantAnimation.Paused:
            self._countdown.resume()
        super().leaveEvent(event)

    # ---- show / hide --------------------------------------------------
    def _animate(self, start: QPoint, end: QPoint, o_from: float, o_to: float,
                 move_ms: int, fade_ms: int, move_curve: QEasingCurve,
                 fade_curve: QEasingCurve, on_done=None) -> None:
        move = QPropertyAnimation(self, b"pos")
        move.setStartValue(start); move.setEndValue(end)
        move.setDuration(move_ms); move.setEasingCurve(move_curve)
        fade = QPropertyAnimation(self, b"windowOpacity")
        fade.setStartValue(o_from); fade.setEndValue(o_to)
        fade.setDuration(fade_ms); fade.setEasingCurve(fade_curve)
        group = QParallelAnimationGroup(self)
        group.addAnimation(move)
        group.addAnimation(fade)
        if on_done:
            group.finished.connect(on_done)
        self._group = group          # keep a reference so it isn't garbage collected
        group.start()

    def fit_to_content(self) -> None:
        """Size the popup so wrapped text is never clipped (width is fixed, height follows)."""
        lay = self.layout()
        lay.activate()
        self.setFixedHeight(max(lay.totalHeightForWidth(self.WIDTH), lay.minimumSize().height()))

    def show_animated(self) -> None:
        self.fit_to_content()
        end = self._target_pos()
        if self._animations:
            start = end + QPoint(0, 36)
            spring = QEasingCurve(QEasingCurve.OutBack)
            spring.setOvershoot(1.05)
            self._badge.prepare()
            self.setWindowOpacity(0.0)
            self.move(start)
            self.show()
            self._animate(start, end, 0.0, 1.0, 460, 260, spring,
                          QEasingCurve(QEasingCurve.OutCubic), self._badge.start)
        else:
            self.move(end)
            self.show()
        self._countdown.start()

    def _respond(self, action: str) -> None:
        if self._responded:                      # ignore double clicks / races
            return
        self._responded = True
        self.responded.emit(action)
        self._countdown.stop()
        for b in (self._done_btn, self._later_btn, self._close_btn):
            b.setEnabled(False)

        def finish():
            self._badge.stop()
            self.hide()
            self.closed_with.emit(action)
            self.deleteLater()

        def slide_out():
            start = self.pos()
            self._animate(start, start + QPoint(0, 18), 1.0, 0.0, 220, 220,
                          QEasingCurve(QEasingCurve.InCubic),
                          QEasingCurve(QEasingCurve.InCubic), finish)

        if not self._animations:
            finish()
        elif action == "done":                   # a little happy hop before leaving
            self._badge.celebrate()
            QTimer.singleShot(480, slide_out)
        else:
            slide_out()
