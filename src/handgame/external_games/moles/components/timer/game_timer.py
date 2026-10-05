from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from config import (
    COLOR_OUTLINE,
    COLOR_TEXT_WHITE,
    DEFAULT_GAME_DURATION_SEC,
    DESKA_IMAGE_PATH,
)


class GameTimer(QWidget):
    timeout_signal = Signal()

    def __init__(self, parent=None, duration_sec=DEFAULT_GAME_DURATION_SEC):
        super().__init__(parent)
        self.duration_sec = duration_sec
        self.remaining_sec = duration_sec
        self.hide()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

        # Wczytanie tekstury deski
        self.bg_pixmap = QPixmap(str(DESKA_IMAGE_PATH))

    def set_duration(self, sec: int):
        self.duration_sec = sec
        self.remaining_sec = sec
        self.update()

    def start_timer(self):
        self.remaining_sec = self.duration_sec
        self.update()
        self.timer.start(1000)

    def stop_timer(self):
        self.timer.stop()

    def _tick(self):
        self.remaining_sec -= 1
        self.update()
        if self.remaining_sec <= 0:
            self.timer.stop()
            self.timeout_signal.emit()

    def update_scale(self, scale, offset_x, offset_y, ref_w, ref_h):
        width = int(340 * scale)
        height = int(100 * scale)
        spacing = int(20 * scale)

        total_pair_w = (width * 2) + spacing
        center_x = offset_x + (ref_w * scale) / 2.0

        x = int(center_x - (total_pair_w / 2.0))
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

        text = f"CZAS: {self.remaining_sec}s"
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
