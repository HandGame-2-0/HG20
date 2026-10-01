from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QPushButton, QWidget

from config import (
    COLOR_OUTLINE,
    COLOR_TEXT_RED,
    COLOR_TEXT_WHITE,
    COLOR_TITLE_GOLD,
    DESKA_IMAGE_PATH,
)


class DeskaButton(QPushButton):
    def __init__(
        self,
        text="",
        text_color=COLOR_TEXT_WHITE,
        parent=None,
        pixmap_path=DESKA_IMAGE_PATH,
    ):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")
        self.text_color = QColor(text_color)

        # Wczytanie tekstury deski z config.py
        self.bg_pixmap = QPixmap(str(pixmap_path))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        target_rect = self.rect()

        if not self.bg_pixmap.isNull():
            painter.drawPixmap(target_rect, self.bg_pixmap)

        text = self.text()
        if text:
            font = painter.font()
            font.setBold(True)
            font.setPixelSize(max(12, int(target_rect.height() * 0.38)))
            painter.setFont(font)

            outline_color = QColor(COLOR_OUTLINE)
            stroke_width = 2
            offsets = [
                (-stroke_width, 0),
                (stroke_width, 0),
                (0, -stroke_width),
                (0, stroke_width),
                (-stroke_width, -stroke_width),
                (stroke_width, -stroke_width),
                (-stroke_width, stroke_width),
                (stroke_width, stroke_width),
            ]

            # Czarna obramówka
            painter.setPen(outline_color)
            for dx, dy in offsets:
                painter.drawText(
                    target_rect.translated(dx, dy),
                    Qt.AlignmentFlag.AlignCenter,
                    text,
                )

            # Właściwy tekst
            painter.setPen(self.text_color)
            painter.drawText(target_rect, Qt.AlignmentFlag.AlignCenter, text)

        painter.end()


class EndGameOverlay(QWidget):
    restart_signal = Signal()
    exit_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hide()
        self.score = 0

        self.restart_button = DeskaButton(
            "Jeszcze raz? [L]", text_color=COLOR_TEXT_WHITE, parent=self
        )
        self.restart_button.clicked.connect(self.restart_signal.emit)

        self.exit_button = DeskaButton(
            "Wyjdź z gry [ESC]", text_color=COLOR_TEXT_RED, parent=self
        )
        self.exit_button.clicked.connect(self.exit_signal.emit)

    def set_score(self, score: int):
        self.score = score
        self.update()

    def update_scale(self, scale, offset_x, offset_y, ref_w, ref_h):
        self.setGeometry(
            int(offset_x), int(offset_y), int(ref_w * scale), int(ref_h * scale)
        )

        btn_w = int(340 * scale)
        btn_h = int(100 * scale)
        spacing = int(20 * scale)

        center_x = (ref_w * scale) / 2.0
        center_y = (ref_h * scale) / 2.0

        total_h = (btn_h * 2) + spacing
        start_y = int(center_y - (total_h / 2.0) + (50 * scale))

        restart_x = int(center_x - (btn_w / 2.0))
        restart_y = start_y

        exit_x = int(center_x - (btn_w / 2.0))
        exit_y = start_y + btn_h + spacing

        self.restart_button.setGeometry(restart_x, restart_y, btn_w, btn_h)
        self.exit_button.setGeometry(exit_x, exit_y, btn_w, btn_h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Półprzezroczyste ciemne tło
        painter.fillRect(self.rect(), QColor(0, 0, 0, 180))

        # 1. Napis "KONIEC GRY"
        text_title = "KONIEC GRY"
        font_title = painter.font()
        font_title.setBold(True)
        font_title.setPixelSize(int(self.height() * 0.11))
        painter.setFont(font_title)

        title_rect = QRect(
            0, int(self.height() * 0.12), self.width(), int(self.height() * 0.15)
        )

        outline_color = QColor(COLOR_OUTLINE)
        main_color = QColor(COLOR_TITLE_GOLD)

        stroke_width = 3
        offsets = [
            (-stroke_width, 0),
            (stroke_width, 0),
            (0, -stroke_width),
            (0, stroke_width),
            (-stroke_width, -stroke_width),
            (stroke_width, -stroke_width),
            (-stroke_width, stroke_width),
            (stroke_width, stroke_width),
        ]

        painter.setPen(outline_color)
        for dx, dy in offsets:
            painter.drawText(
                title_rect.translated(dx, dy),
                Qt.AlignmentFlag.AlignCenter,
                text_title,
            )

        painter.setPen(main_color)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, text_title)

        # 2. Napis z wynikiem punktowym pod "KONIEC GRY"
        text_score = f"TWÓJ WYNIK: {self.score} PKT"
        font_score = painter.font()
        font_score.setBold(True)
        font_score.setPixelSize(int(self.height() * 0.06))
        painter.setFont(font_score)

        score_rect = QRect(
            0, int(self.height() * 0.28), self.width(), int(self.height() * 0.10)
        )

        painter.setPen(outline_color)
        for dx, dy in offsets:
            painter.drawText(
                score_rect.translated(dx, dy),
                Qt.AlignmentFlag.AlignCenter,
                text_score,
            )

        painter.setPen(QColor(COLOR_TEXT_WHITE))
        painter.drawText(score_rect, Qt.AlignmentFlag.AlignCenter, text_score)

        painter.end()
