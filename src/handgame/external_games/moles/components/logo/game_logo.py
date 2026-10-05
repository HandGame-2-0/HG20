from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel

from config import LOGO_IMAGE_PATH


class GameLogo(QLabel):
    # Wymiary referencyjne grafiki (1000x538)
    ORIGINAL_WIDTH = 1000.0
    ORIGINAL_HEIGHT = 538.0
    ASPECT_RATIO = ORIGINAL_WIDTH / ORIGINAL_HEIGHT

    def __init__(self, parent=None, pixmap_path=LOGO_IMAGE_PATH):
        super().__init__(parent)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent; border: none;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Wczytanie grafiki logo
        self.pixmap_raw = QPixmap(str(pixmap_path))

        if self.pixmap_raw.isNull():
            print(f"[BŁĄD GameLogo] Nie można załadować logo ze ścieżki: {pixmap_path}")

    def update_position(
        self, board_width: float, center_x: float, btn_y: float, scale: float
    ):
        logo_w = int(board_width * 0.5)
        logo_h = int(logo_w / self.ASPECT_RATIO)
        spacing = int(15 * scale)

        logo_x = int(center_x - logo_w / 2.0)
        logo_y = int(btn_y - logo_h - spacing)

        self.setGeometry(logo_x, logo_y, logo_w, logo_h)

        if not self.pixmap_raw.isNull() and logo_w > 0 and logo_h > 0:
            self.setPixmap(
                self.pixmap_raw.scaled(
                    QSize(logo_w, logo_h),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
