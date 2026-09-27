"""The Statistics window: today's counts, a weekly chart, streaks and a few small,
optional achievement badges. Everything here is read from HistoryStore; nothing here
writes to it except "Clear history"."""
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox,
                               QPushButton, QScrollArea, QVBoxLayout, QWidget)

from app.database import HistoryStore
from app.reminder import REMINDER_TYPES
from app.ui.charts import WeekBarChart
from app.ui.icons import make_app_icon
from app.ui.theme import ACCENTS, DEFAULT_ACCENT, current_palette, popup_stylesheet

EXTRA_STYLE = """
QLabel#hero {{ font-size: 22px; font-weight: 700; color: {title}; }}
QLabel#subtitle {{ font-size: 12px; color: {message}; }}
QLabel#section {{ font-size: 11px; font-weight: 700; color: {message}; letter-spacing: 0.5px; }}
QLabel#rowname {{ font-size: 14px; font-weight: 600; color: {title}; }}
QLabel#count {{ font-size: 14px; font-weight: 700; color: {title}; }}
QLabel#stat_value {{ font-size: 26px; font-weight: 800; color: {title}; }}
QLabel#stat_label {{ font-size: 11.5px; color: {message}; }}
QLabel#badge {{ font-size: 11px; font-weight: 600; border-radius: 13px; padding: 6px 10px; }}
QFrame#card {{ background: {card_alt}; border-radius: 16px; }}
QPushButton#danger {{ background: transparent; color: {danger}; font-size: 12px; font-weight: 700;
                      border: none; padding: 4px 6px; }}
QPushButton#danger:hover {{ text-decoration: underline; }}
"""

ACHIEVEMENTS = (
    ("🌱", "First step", lambda db: db.total_done() >= 1),
    ("✨", "10 completed", lambda db: db.total_done() >= 10),
    ("💯", "100 completed", lambda db: db.total_done() >= 100),
    ("🔥", "3-day streak", lambda db: db.longest_streak() >= 3),
    ("🏆", "7-day streak", lambda db: db.longest_streak() >= 7),
)


class StatisticsWindow(QWidget):
    def __init__(self, history: HistoryStore):
        super().__init__()
        self.history = history
        pal = current_palette()
        self.setWindowTitle("Nudge Statistics")
        self.setWindowIcon(make_app_icon(False))
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.resize(480, 700)

        card_alt = "#F7F5FC" if not pal.dark else "#2A2735"
        danger = "#E0607A" if not pal.dark else "#F08FA3"
        self.setStyleSheet(
            popup_stylesheet(DEFAULT_ACCENT, pal)
            + EXTRA_STYLE.format(title=pal.title.name(), message=pal.message.name(),
                                 edge=pal.edge.name(), card_alt=card_alt, danger=danger)
            + f"\nStatisticsWindow {{ background: {pal.card.name()}; }}")
        self._pal, self._card_alt = pal, card_alt

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(frameShape=QFrame.NoFrame, widgetResizable=True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.viewport().setStyleSheet("background: transparent;")
        outer.addWidget(scroll)
        body = QWidget()
        body.setAttribute(Qt.WA_StyledBackground, True)
        body.setStyleSheet("background: transparent;")
        scroll.setWidget(body)

        root = QVBoxLayout(body)
        root.setContentsMargins(26, 24, 26, 24)
        root.setSpacing(18)

        head = QVBoxLayout()
        head.setSpacing(2)
        head.addWidget(QLabel("Your Stats", objectName="hero"))
        head.addWidget(QLabel("A quiet look at how you're doing.", objectName="subtitle"))
        root.addLayout(head)

        root.addWidget(QLabel("TODAY", objectName="section"))
        self._today_card, self._today_rows = self._build_today_card()
        root.addWidget(self._today_card)

        root.addWidget(QLabel("THIS WEEK", objectName="section"))
        week_card = QFrame(objectName="card")
        wl = QVBoxLayout(week_card)
        wl.setContentsMargins(18, 16, 18, 14)
        wl.setSpacing(8)
        self._chart = WeekBarChart([], DEFAULT_ACCENT, pal)
        wl.addWidget(self._chart)
        self._week_caption = QLabel("", objectName="stat_label")
        self._week_caption.setAlignment(Qt.AlignCenter)
        wl.addWidget(self._week_caption)
        root.addWidget(week_card)

        root.addWidget(QLabel("STREAKS", objectName="section"))
        streak_card = QFrame(objectName="card")
        sl = QHBoxLayout(streak_card)
        sl.setContentsMargins(18, 16, 18, 16)
        self._current_streak_value = QLabel("0", objectName="stat_value")
        self._longest_streak_value = QLabel("0", objectName="stat_value")
        sl.addLayout(self._stat_tile("🔥 Current streak", self._current_streak_value))
        sl.addWidget(self._vhair())
        sl.addLayout(self._stat_tile("🏅 Best streak", self._longest_streak_value))
        root.addWidget(streak_card)

        root.addWidget(QLabel("ACHIEVEMENTS", objectName="section"))
        self._badges_row = QHBoxLayout()
        self._badges_row.setSpacing(8)
        badge_wrap = QWidget()
        badge_wrap.setLayout(self._badges_row)
        root.addWidget(badge_wrap)

        root.addStretch(1)
        footer = QHBoxLayout()
        footer.addStretch(1)
        self.clear_btn = QPushButton("Clear history", objectName="danger")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        footer.addWidget(self.clear_btn)
        root.addLayout(footer)

        self.refresh()

    # ---- small builders -------------------------------------------------
    def _vhair(self) -> QFrame:
        # Styled inline rather than via QSS — see the long comment on SettingsWindow._hair()
        # for why an ID-selector rule from the window's stylesheet can't reach a widget
        # nested inside the (separately styled) scroll-area body.
        line = QFrame(objectName="vhair")
        line.setAttribute(Qt.WA_StyledBackground, True)
        line.setFixedWidth(1)
        line.setMinimumHeight(56)
        c = self._pal.edge
        line.setStyleSheet(f"background-color: rgba({c.red()}, {c.green()}, {c.blue()}, {c.alphaF():.3f});")
        return line

    def _stat_tile(self, caption: str, value_label: QLabel) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(2)
        col.setAlignment(Qt.AlignCenter)
        value_label.setAlignment(Qt.AlignCenter)
        cap = QLabel(caption, objectName="stat_label")
        cap.setAlignment(Qt.AlignCenter)
        col.addWidget(value_label)
        col.addWidget(cap)
        return col

    def _build_today_card(self):
        card = QFrame(objectName="card")
        layout = QGridLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)
        rows: dict[str, QLabel] = {}
        for i, (key, rt) in enumerate(REMINDER_TYPES.items()):
            layout.addWidget(QLabel(f"{rt.emoji}  {rt.label}", objectName="rowname"), i, 0)
            count = QLabel("0", objectName="count")
            count.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            layout.addWidget(count, i, 1)
            rows[key] = count
        layout.setColumnStretch(0, 1)
        return card, rows

    def _badge_chip(self, emoji: str, label: str, unlocked: bool) -> QLabel:
        chip = QLabel(f"{emoji}  {label}", objectName="badge")
        if unlocked:
            # solid, saturated pill: unmistakably "earned", in both themes
            chip.setStyleSheet(f"background: {DEFAULT_ACCENT.main}; color: white;")
        else:
            # deliberately colourless (no accent tint) so it can't be mistaken for "earned"
            bg = "#EBEBEF" if not self._pal.dark else "#26232E"
            fg = "#A8A3B8" if not self._pal.dark else "#5C5770"
            chip.setStyleSheet(f"background: {bg}; color: {fg};")
            chip.setEnabled(False)
        return chip

    # ---- data ------------------------------------------------------------
    def refresh(self) -> None:
        today = date.today()
        counts = self.history.counts_for_day(today)
        for key, label in self._today_rows.items():
            label.setText(str(counts.get(key, 0)))

        totals = self.history.daily_totals(days=7, end=today)
        self._chart.set_data(totals)
        week_total = sum(c for _, c in totals)
        self._week_caption.setText(
            "No completions yet this week." if week_total == 0
            else f"{week_total} completed this week")

        self._current_streak_value.setText(str(self.history.current_streak(today)))
        self._longest_streak_value.setText(str(self.history.longest_streak()))

        while self._badges_row.count():
            item = self._badges_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for emoji, label, check in ACHIEVEMENTS:
            self._badges_row.addWidget(self._badge_chip(emoji, label, check(self.history)))
        self._badges_row.addStretch(1)

    # ---- clearing ----------------------------------------------------------
    def _on_clear_clicked(self) -> None:
        answer = QMessageBox.question(
            self, "Clear history?",
            "This removes all recorded reminder activity, including streaks and "
            "achievements. This can't be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer == QMessageBox.Yes:
            self._clear_now()

    def _clear_now(self) -> None:
        """Split from _on_clear_clicked so tests can clear without a modal dialog."""
        self.history.clear()
        self.refresh()

    def present(self) -> None:
        self.refresh()
        self.showNormal()
        self.raise_()
        self.activateWindow()
