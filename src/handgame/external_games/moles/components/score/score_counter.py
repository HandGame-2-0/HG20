from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from config import (
    COLOR_OUTLINE,
    COLOR_TEXT_WHITE,
    DESKA_IMAGE_PATH,
)


class ScoreCounter(QWidget):
    def __init__(self, parent=None, pixmap_path=DESKA_IMAGE_PATH):
        super().__init__(parent)
        self.score = 0
        self.hide()

        # Wczytanie tekstury deski
        self.bg_pixmap = QPixmap(str(pixmap_path))

    def add_points(self, points: int):
        self.score += points
        self.update()

    def reset_score(self):
        self.score = 0
        self.update()

    def update_scale(self, scale, offset_x, offset_y, ref_w, ref_h):
        width = int(340 * scale)
        height = int(100 * scale)
        spacing = int(20 * scale)

        total_pair_w = (width * 2) + spacing
        center_x = offset_x + (ref_w * scale) / 2.0

        x = int(center_x - (total_pair_w / 2.0) + width + spacing)
        y = int(offset_y + (ref_h * scale) - height - (20 * scale))

        self.setGeometry(x, y, width, height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        target_rect = self.rect()

        if not self.bg_pixmap.isNull():
            painter.drawPixmap(target_rect, self.bg_pixmap)

        text = f"PKT: {self.score}"
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(max(14, int(target_rect.height() * 0.42)))
        painter.setFont(font)

        outline_color = QColor(COLOR_OUTLINE)
        main_color = QColor(COLOR_TEXT_WHITE)

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

        # Główny biały tekst
        painter.setPen(main_color)
        painter.drawText(target_rect, Qt.AlignmentFlag.AlignCenter, text)

        painter.end()
