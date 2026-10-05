from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QPushButton, QWidget

from config import (
    COLOR_OUTLINE,
    COLOR_TEXT_WHITE,
    DESKA_IMAGE_PATH,
)


# Przycisk z teksturą deski
class SubMenuButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("background: transparent; border: none;")

        # Wczytanie tekstury deski
        self.bg_pixmap = QPixmap(str(DESKA_IMAGE_PATH))

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
            font.setPixelSize(max(12, int(target_rect.height() * 0.3)))
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

            # Czarny kontur
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


class DiffMenu(QWidget):
    button_clicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.hide()

        self.buttons = []
        for i in range(1, 6):
            btn = SubMenuButton(f"Poziom {i}", parent=self)
            btn.clicked.connect(
                lambda checked=False, b_id=i: self.button_clicked.emit(b_id)
            )
            self.buttons.append(btn)

    def set_button_names(self, difficulties_config: dict):
        for i, btn in enumerate(self.buttons, start=1):
            mode_data = difficulties_config.get(str(i), {})
            name = mode_data.get("name", f"Poziom {i}")
            hotkey = mode_data.get("hotkey", "")

            if hotkey:
                btn.setText(f"{name} [{hotkey.upper()}]")
            else:
                btn.setText(name)

    def update_scale(self, board_w, center_x, center_y, scale):
        btn_w = int(board_w * 0.38)
        btn_h = int(btn_w * 0.23)
        spacing = int(10 * scale)

        total_h = 5 * btn_h + 4 * spacing
        start_y = int(center_y - total_h / 2.0)
        btn_x = int(center_x - btn_w / 2.0)

        self.setGeometry(btn_x, start_y, btn_w, total_h)

        for i, btn in enumerate(self.buttons):
            y_pos = i * (btn_h + spacing)
            btn.setGeometry(0, y_pos, btn_w, btn_h)
