"""Camera preview box shared by the calibration and gameplay screens.

A dumb display widget: the GUI pushes frames in through ``update_frame``. It
never talks to BaseGame - the camera preview is rendered by the GUI directly.
With no frame yet it paints a placeholder instead of a black box, and it can
draw the dashed detection zone the player should put their hand in.
"""

from __future__ import annotations

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen, QPixmap
from PySide6.QtWidgets import QFrame, QSizePolicy, QWidget

from handgame.gui.screens.common import set_dynamic_property

PLACEHOLDER_TEXT = "Oczekiwanie na obraz z kamery\N{HORIZONTAL ELLIPSIS}"

# Detection-zone outline per ``state`` property.
_ZONE_COLORS: dict[str, str] = {
    "": "#0B2545",
    "error": "#DC3220",
    "locked": "#009E73",
}
# Zone covers the middle of the frame (fractions of the preview size).
_ZONE_WIDTH = 0.5
_ZONE_HEIGHT = 0.7


class CameraPreviewWidget(QFrame):
    def __init__(self, *, show_zone: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(240, 180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._show_zone = show_zone
        self._zone_state = ""
        self._pixmap: QPixmap | None = None
        set_dynamic_property(self, "state", "")

    # --- state ---

    def zone_state(self) -> str:
        return self._zone_state

    def set_zone_state(self, state: str) -> None:
        """``""`` (neutral), ``"error"`` or ``"locked"`` - drives border + zone colour."""
        self._zone_state = state
        set_dynamic_property(self, "state", state)

    def has_frame(self) -> bool:
        return self._pixmap is not None

    def update_frame(self, pixmap: QPixmap) -> None:
        self._pixmap = None if pixmap.isNull() else pixmap
        self.update()

    def clear_frame(self) -> None:
        self._pixmap = None
        self.update()

    # --- painting ---

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 - Qt override
        super().paintEvent(event)  # QSS border / background
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        area = self.contentsRect().adjusted(4, 4, -4, -4)

        if self._pixmap is not None:
            scaled = self._pixmap.scaled(
                area.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            target = QRect(0, 0, scaled.width(), scaled.height())
            target.moveCenter(area.center())
            painter.drawPixmap(target, scaled)
        else:
            painter.setPen(QColor("#3E4C63"))
            flags = Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap
            painter.drawText(area, flags, PLACEHOLDER_TEXT)

        if self._show_zone:
            pen = QPen(QColor(_ZONE_COLORS.get(self._zone_state, _ZONE_COLORS[""])), 2)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            zone = QRectF(0, 0, area.width() * _ZONE_WIDTH, area.height() * _ZONE_HEIGHT)
            zone.moveCenter(QRectF(area).center())
            painter.drawRoundedRect(zone, 8, 8)
        painter.end()
