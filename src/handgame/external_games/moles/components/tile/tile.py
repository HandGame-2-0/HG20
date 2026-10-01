from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QLabel

from .basket import BasketWidget
from config import (
    ASSETS_DIR,
    DEFAULT_MARGIN_MS,
    DEFAULT_WAIT_DURATION_MS,
    TILE_DIR,
)


# pobranie grafiki z folderu
def load_tile_pixmap(filename: str) -> QPixmap:
    candidate_paths = [
        ASSETS_DIR / filename,
        ASSETS_DIR / "tile" / filename,
        TILE_DIR / filename,
    ]

    for path in candidate_paths:
        pix = QPixmap(str(path))
        if not pix.isNull():
            return pix

    return QPixmap()


class Tile(QLabel):
    WAIT_DURATION_MS = DEFAULT_WAIT_DURATION_MS
    MARGIN_MS = DEFAULT_MARGIN_MS

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background: transparent; border: none;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Domyślna grafika norki
        self.norka = load_tile_pixmap("norka.png")

        # Animacje krecika z wyciągniętych grafik
        self.anims = {
            "wyskok": (
                load_tile_pixmap("krecikWyskakuje.png"),
                [100, 100, 50, 50, 50, 50, 50],
            ),
            "smiech": (
                load_tile_pixmap("krecikSmiech.png"),
                [100, 200, 75, 75, 75, 75, 75, 50, 50, 50, 50, 100],
            ),
            "oberwal": (
                load_tile_pixmap("krecikOberwal.png"),
                [50, 150, 100, 50, 50, 50, 50],
            ),
        }

        # Widget koszyczka
        self.basket = BasketWidget(parent=self)

        # Stan kafelka
        self.current_sheet = None
        self.current_delays = []
        self.current_frame = 0
        self.current_anim_name = None
        self.current_wait_ms = self.WAIT_DURATION_MS
        self.current_letter = None
        self.show_letter = False
        self.use_basket = False

        # Timery animacji i stanu standby
        self.timer = QTimer(self, timeout=self._next_frame)

        self.wait_timer = QTimer(self)
        self.wait_timer.setSingleShot(True)
        self.wait_timer.timeout.connect(self._on_wait_finished)

        self.letter_show_timer = QTimer(self)
        self.letter_show_timer.setSingleShot(True)
        self.letter_show_timer.timeout.connect(self._on_show_letter)

        self.letter_hide_timer = QTimer(self)
        self.letter_hide_timer.setSingleShot(True)
        self.letter_hide_timer.timeout.connect(self._on_hide_letter)

        self.basket_show_timer = QTimer(self)
        self.basket_show_timer.setSingleShot(True)
        self.basket_show_timer.timeout.connect(self._on_show_basket)

        self._refresh_display()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_basket_geometry()
        self._refresh_display()

    # Powiększa wysokość widgetu koszyczka w górę

    def _update_basket_geometry(self):
        basket_w = int(self.width() * 0.60)
        basket_h = int(self.height() * 0.62)
        basket_x = int(self.width() * 0.20)
        basket_y = int(self.height() * 0.35)

        self.basket.setGeometry(basket_x, basket_y, basket_w, basket_h)

    def is_busy(self) -> bool:
        return (
            self.current_sheet is not None and self.timer.isActive()
        ) or self.wait_timer.isActive()

    def start_cycle(
        self,
        letter: str,
        wait_ms: int = None,
        use_basket: bool = False,
        basket_delay_ms: int = 400,
    ):
        if self.is_busy():
            return

        self.current_letter = letter
        self.use_basket = use_basket
        self.current_wait_ms = wait_ms if wait_ms is not None else self.WAIT_DURATION_MS
        self.show_letter = False
        self.basket.hide()

        total_wyskok_time = sum(self.anims["wyskok"][1])
        show_delay = max(0, total_wyskok_time - self.MARGIN_MS)

        self.letter_show_timer.start(show_delay)

        if self.use_basket:
            self.basket_show_timer.start(basket_delay_ms)

        self._start_animation("wyskok")

    def play_oberwal(self):
        self.wait_timer.stop()
        self.letter_show_timer.stop()
        self.letter_hide_timer.stop()
        self.basket_show_timer.stop()
        self.show_letter = False
        self.basket.hide()

        self.current_letter = None
        self._start_animation("oberwal")

    def reset_tile(self):
        self.timer.stop()
        self.wait_timer.stop()
        self.letter_show_timer.stop()
        self.letter_hide_timer.stop()
        self.basket_show_timer.stop()
        self.show_letter = False
        self.basket.hide()

        self.current_sheet = None
        self.current_anim_name = None
        self.current_frame = 0
        self.current_letter = None
        self._refresh_display()

    def _refresh_display(self):
        if self.width() <= 0 or self.height() <= 0:
            return

        if (
            self.current_sheet
            and not self.current_sheet.isNull()
            and (self.timer.isActive() or self.wait_timer.isActive())
        ):
            self._render_frame()
        elif not self.norka.isNull():
            self._set_scaled_pixmap(self.norka)

    def _start_animation(self, name):
        sheet, delays = self.anims.get(name, (None, []))
        if not sheet or sheet.isNull():
            return

        self.timer.stop()
        self.wait_timer.stop()

        self.current_anim_name = name
        self.current_sheet, self.current_delays, self.current_frame = sheet, delays, 0
        self._render_frame()

    def _render_frame(self):
        if not self.current_sheet or self.current_sheet.isNull() or self.width() <= 0:
            return

        total_frames = len(self.current_delays)
        frame_idx = min(self.current_frame, total_frames - 1)
        frame_w = self.current_sheet.width() // total_frames

        crop_rect = QRect(frame_idx * frame_w, 0, frame_w, self.current_sheet.height())
        frame_pixmap = self.current_sheet.copy(crop_rect)

        if self.current_letter and self.show_letter:
            frame_pixmap = self._draw_letter_on_pixmap(
                frame_pixmap, self.current_letter, use_basket=self.use_basket
            )

        self._set_scaled_pixmap(frame_pixmap)

        if self.current_frame < total_frames and not self.wait_timer.isActive():
            self.timer.start(self.current_delays[self.current_frame])

    def _draw_letter_on_pixmap(
        self, pixmap: QPixmap, letter: str, use_basket: bool = False
    ) -> QPixmap:
        result = pixmap.copy()
        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        font = painter.font()
        font.setBold(True)

        if use_basket:
            font.setPixelSize(int(result.height() * 0.18))
            text_rect = QRect(
                0,
                int(result.height() * 0.62),
                result.width(),
                int(result.height() * 0.22),
            )
        else:
            font.setPixelSize(int(result.height() * 0.22))
            text_rect = QRect(
                0,
                int(result.height() * 0.54),
                result.width(),
                int(result.height() * 0.25),
            )

        painter.setFont(font)
        painter.setPen(Qt.GlobalColor.white)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, letter)
        painter.end()

        return result

    def _next_frame(self):
        self.current_frame += 1
        total_frames = len(self.current_delays)

        if self.current_frame < total_frames:
            self._render_frame()
        else:
            self.timer.stop()

            if self.current_anim_name == "wyskok":
                self.current_frame = total_frames - 1
                self.wait_timer.start(self.current_wait_ms)
                self._render_frame()
            else:
                self.reset_tile()

    def _on_show_letter(self):
        self.show_letter = True
        self._render_frame()

    def _on_show_basket(self):
        if self.use_basket and (self.timer.isActive() or self.wait_timer.isActive()):
            self._update_basket_geometry()
            self.basket.set_letter(self.current_letter)
            self.basket.show()
            self.basket.raise_()

    def _on_hide_letter(self):
        self.show_letter = False
        self.basket.hide()
        self._render_frame()

    def _on_wait_finished(self):
        self.letter_hide_timer.start(self.MARGIN_MS)
        self._start_animation("smiech")

    def _set_scaled_pixmap(self, pixmap):
        self.setPixmap(
            pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
