from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QPushButton

from config import START_BTN_IMAGE_PATH


class StartButton(QPushButton):
    # Wymiary grafiki start.png (875x510)
    ORIGINAL_WIDTH = 875.0
    ORIGINAL_HEIGHT = 510.0
    ASPECT_RATIO = ORIGINAL_WIDTH / ORIGINAL_HEIGHT

    def __init__(self, parent=None, pixmap_path=START_BTN_IMAGE_PATH):
        super().__init__("", parent)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Wczytanie grafiki
        self.pixmap_raw = QPixmap(str(pixmap_path))

        if not self.pixmap_raw.isNull():
            self.setStyleSheet("QPushButton { background: transparent; border: none; }")
        else:
            self.setText("Start")
            self.setStyleSheet("""
                QPushButton {
                    background-color: yellow;
                    color: red;
                    font-size: 36px;
                    font-weight: bold;
                    border: 3px solid red;
                    border-radius: 15px;
                }
            """)

    def update_position(self, board_width: float, center_x: float, target_y: float):
        btn_w = int(board_width * 0.20)
        btn_h = int(btn_w / self.ASPECT_RATIO)

        btn_x = int(center_x - btn_w / 2.0)
        btn_y = int(target_y)

        self.setGeometry(btn_x, btn_y, btn_w, btn_h)

        if not self.pixmap_raw.isNull() and btn_w > 0 and btn_h > 0:
            icon_pixmap = self.pixmap_raw.scaled(
                QSize(btn_w, btn_h),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.setIcon(QIcon(icon_pixmap))
            self.setIconSize(QSize(btn_w, btn_h))

    def update_scale(self, scale_or_board_w: float, center_x: float, target_y: float):
        if scale_or_board_w < 10.0:
            board_w = 1920.0 * scale_or_board_w
        else:
            board_w = scale_or_board_w

        self.update_position(board_w, center_x, target_y)
