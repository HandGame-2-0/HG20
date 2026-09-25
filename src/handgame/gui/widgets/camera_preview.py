"""Camera preview box shared by the calibration and gameplay screens.

A dumb display widget: the GUI pushes frames in through ``update_frame``. It
never talks to BaseGame - the camera preview is rendered by the GUI directly.
With no frame yet it paints a placeholder instead of a black box, and it can
draw the dashed detection zone the player should put their hand in.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen, QPixmap
from PySide6.QtWidgets import QFrame, QSizePolicy, QWidget

from handgame.gui.screens.common import set_dynamic_property

PLACEHOLDER_TEXT = "Oczekiwanie na obraz z kamery\N{HORIZONTAL ELLIPSIS}"

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
        # Detection-zone outline per ``state``; the theme stylesheet sets these
        # via qproperty-zoneColor / zoneErrorColor / zoneLockedColor.
        self._zone_colors: dict[str, QColor] = {
            "": QColor("#0B2545"),
            "error": QColor("#DC3220"),
            "locked": QColor("#009E73"),
        }
        set_dynamic_property(self, "state", "")

    # --- theme hooks (Qt properties, set from QSS) ---

    def _get_zone_color(self) -> QColor:
        return self._zone_colors[""]

    def _set_zone_color(self, color: QColor) -> None:
        self._zone_colors[""] = QColor(color)
        self.update()

    def _get_zone_error_color(self) -> QColor:
        return self._zone_colors["error"]

    def _set_zone_error_color(self, color: QColor) -> None:
        self._zone_colors["error"] = QColor(color)
        self.update()

    def _get_zone_locked_color(self) -> QColor:
        return self._zone_colors["locked"]

    def _set_zone_locked_color(self, color: QColor) -> None:
        self._zone_colors["locked"] = QColor(color)
        self.update()

    zoneColor = Property(QColor, _get_zone_color, _set_zone_color)  # noqa: N815 - QSS name
    zoneErrorColor = Property(QColor, _get_zone_error_color, _set_zone_error_color)  # noqa: N815
    zoneLockedColor = Property(QColor, _get_zone_locked_color, _set_zone_locked_color)  # noqa: N815

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
            painter.setPen(self.palette().windowText().color())  # QSS ``color``
            flags = Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap
            painter.drawText(area, flags, PLACEHOLDER_TEXT)

        if self._show_zone:
            pen = QPen(self._zone_colors.get(self._zone_state, self._zone_colors[""]), 2)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            zone = QRectF(0, 0, area.width() * _ZONE_WIDTH, area.height() * _ZONE_HEIGHT)
            zone.moveCenter(QRectF(area).center())
            painter.drawRoundedRect(zone, 8, 8)
        painter.end()
