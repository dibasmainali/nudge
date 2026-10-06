"""A small hand-painted bar chart for the Statistics window (no charting library needed
for one simple weekly view)."""
from datetime import date

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter
from PySide6.QtWidgets import QWidget

from app.ui.theme import Accent, Palette


class WeekBarChart(QWidget):
    """`data`: list of (date, count), oldest first — exactly what HistoryStore.daily_totals returns."""

    def __init__(self, data: list[tuple[date, int]], accent: Accent, pal: Palette, parent=None):
        super().__init__(parent)
        self._data = data
        self._accent = QColor(accent.main)
        self._pal = pal
        self.setMinimumHeight(120)

    def set_data(self, data: list[tuple[date, int]]) -> None:
        self._data = data
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        if not self._data:
            return
        w, h = self.width(), self.height()
        label_h = 18
        top_pad = 20
        plot_h = h - label_h - top_pad
        n = len(self._data)
        gap = 10
        bar_w = (w - gap * (n - 1)) / n
        peak = max((c for _, c in self._data), default=0) or 1

        font = QFont()
        font.setPixelSize(10)
        p.setFont(font)
        today = date.today()

        for i, (day, count) in enumerate(self._data):
            x = i * (bar_w + gap)
            frac = count / peak if peak else 0
            bar_h = max(4, plot_h * frac) if count > 0 else 3
            y = top_pad + (plot_h - bar_h)
            rect = QRectF(x, y, bar_w, bar_h)

            is_today = day == today
            color = QColor(self._accent) if is_today else QColor(self._accent)
            if not is_today:
                color.setAlphaF(0.45 if not self._pal.dark else 0.55)
            g = QLinearGradient(0, y, 0, y + bar_h)
            g.setColorAt(0, color.lighter(115) if is_today else color)
            g.setColorAt(1, color)
            p.setPen(Qt.NoPen)
            p.setBrush(g)
            radius = min(7, bar_w / 2)
            p.drawRoundedRect(rect, radius, radius)

            if count > 0:
                p.setPen(self._pal.title if is_today else self._pal.message)
                p.drawText(QRectF(x, y - 16, bar_w, 14), Qt.AlignCenter, str(count))

            p.setPen(self._pal.title if is_today else self._pal.message)
            weekday = day.strftime("%a")[0]
            p.drawText(QRectF(x, h - label_h, bar_w, label_h), Qt.AlignCenter, weekday)
