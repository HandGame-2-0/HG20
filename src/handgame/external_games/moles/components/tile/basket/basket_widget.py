from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from config import (
    ASSETS_DIR,
    BASKET_DIR,
    COLOR_LETTER_GREEN,
    COLOR_OUTLINE,
    HANDLES_DIR,
)


class BasketWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent; border: none;")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.hide()

        self.letter = ""

        # Wczytanie warstw tła i przodu koszyczka ze ścieżek w config.py
        self.pixmap_back = self._load_layer("koszyczek_tyl.png")
        self.pixmap_front = self._load_layer("koszyczek_przod.png")
        self.pixmap_handle = QPixmap()

    def _load_layer(self, filename: str) -> QPixmap:
        candidate_paths = [
            BASKET_DIR / filename,
            ASSETS_DIR / filename,
        ]

        for path in candidate_paths:
            pix = QPixmap(str(path))
            if not pix.isNull():
                return pix

        return QPixmap()

    # Pobranie grafiki gestu
    def set_letter(self, letter: str):
        self.letter = letter if letter else ""
        if not letter:
            self.pixmap_handle = QPixmap()
            self.update()
            return

        possible_filenames = [
            f"{letter}.png",
            f"Litera {letter}.png",
            f"Litera_{letter}.png",
            f"{letter.lower()}.png",
        ]

        candidate_dirs = [
            HANDLES_DIR,
            BASKET_DIR / "raczki",
            ASSETS_DIR / "raczki",
        ]

        loaded_pixmap = QPixmap()
        for r_dir in candidate_dirs:
            for fname in possible_filenames:
                path = r_dir / fname
                pix = QPixmap(str(path))
                if not pix.isNull():
                    loaded_pixmap = pix
                    break
            if not loaded_pixmap.isNull():
                break

        self.pixmap_handle = loaded_pixmap
        self.update()

    # Rysowanie w kolejności "tylny koszyczek" > "gest" > "przedni koszyczek" > "literka z ramką"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        target_rect = self.rect()

        body_h = int(target_rect.height() * (0.45 / 0.62))
        body_y = target_rect.height() - body_h
        body_rect = QRect(0, body_y, target_rect.width(), body_h)

        if not self.pixmap_back.isNull():
            painter.drawPixmap(body_rect, self.pixmap_back)

        if not self.pixmap_handle.isNull():
            handle_size = int(target_rect.height() * 0.65)
            handle_w = handle_size
            handle_h = handle_size

            handle_x = int((target_rect.width() - handle_w) / 2.0)
            handle_y = int(handle_h * 0.05)

            handle_rect = QRect(handle_x, handle_y, handle_w, handle_h)
            painter.drawPixmap(handle_rect, self.pixmap_handle)

        if not self.pixmap_front.isNull():
            painter.drawPixmap(body_rect, self.pixmap_front)

        if self.letter:
            font = painter.font()
            font.setBold(True)
            font.setPixelSize(int(body_rect.height() * 0.40))
            painter.setFont(font)

            outline_color = QColor(COLOR_OUTLINE)
            main_color = QColor(COLOR_LETTER_GREEN)

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
                    body_rect.translated(dx, dy),
                    Qt.AlignmentFlag.AlignCenter,
                    self.letter,
                )

            # Główna zielona litera
            painter.setPen(main_color)
            painter.drawText(body_rect, Qt.AlignmentFlag.AlignCenter, self.letter)

        painter.end()
