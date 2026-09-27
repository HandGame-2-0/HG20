"""Camera preview box shared by the calibration and gameplay screens.

A dumb display widget: the GUI pushes frames in through ``update_frame``. It
never talks to BaseGame - the camera preview is rendered by the GUI directly.
With no frame yet it paints a placeholder instead of a black box, and it can
draw the dashed detection zone the player should put their hand in, the
tracked hand skeleton and the currently recognised letter.
"""

from __future__ import annotations

import time
from collections.abc import Sequence

from PySide6.QtCore import Property, QPointF, QRect, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPaintEvent, QPen, QPixmap
from PySide6.QtWidgets import QFrame, QSizePolicy, QWidget

from handgame.gui.screens.common import set_dynamic_property

PLACEHOLDER_TEXT = "Oczekiwanie na obraz z kamery\N{HORIZONTAL ELLIPSIS}"

# Zone covers the middle of the frame (fractions of the frame size).
_ZONE_WIDTH = 0.5
_ZONE_HEIGHT = 0.7

# MediaPipe Hands topology (21 points: wrist, then 4 per finger).
# Colours follow the usual MediaPipe drawing_utils finger palette.
_THUMB = ((0, 1), (1, 2), (2, 3), (3, 4))
_INDEX = ((5, 6), (6, 7), (7, 8))
_MIDDLE = ((9, 10), (10, 11), (11, 12))
_RING = ((13, 14), (14, 15), (15, 16))
_PINKY = ((17, 18), (18, 19), (19, 20))
_PALM = ((0, 5), (5, 9), (9, 13), (13, 17), (0, 17))
HAND_CONNECTIONS: tuple[tuple[int, int], ...] = _THUMB + _INDEX + _MIDDLE + _RING + _PINKY + _PALM
_FINGER_COLORS: tuple[tuple[tuple[tuple[int, int], ...], QColor], ...] = (
    (_THUMB, QColor("#E74C3C")),
    (_INDEX, QColor("#F1C40F")),
    (_MIDDLE, QColor("#2ECC71")),
    (_RING, QColor("#3498DB")),
    (_PINKY, QColor("#9B59B6")),
    (_PALM, QColor(255, 255, 255, 220)),
)

# An overlay older than this is not drawn (e.g. recognition stopped or lags).
OVERLAY_TTL_S = 0.5

_JOINT_COLOR = QColor("#00E5FF")
_LABEL_BACKGROUND = QColor(11, 37, 69, 210)
_LABEL_TEXT_COLOR = QColor("#FFFFFF")


def point_in_zone(x: float, y: float) -> bool:
    """Is a point, given as fractions of the frame size, inside the detection zone?"""
    return abs(x - 0.5) <= _ZONE_WIDTH / 2 and abs(y - 0.5) <= _ZONE_HEIGHT / 2


class CameraPreviewWidget(QFrame):
    def __init__(self, *, show_zone: bool = True, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(240, 180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._show_zone = show_zone
        self._zone_state = ""
        self._pixmap: QPixmap | None = None
        self._hand_points: tuple[tuple[float, float], ...] | None = None
        self._hand_label: str | None = None
        self._overlay_time = 0.0
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
        self.clear_hand_overlay()

    def set_hand_overlay(
        self, points: Sequence[tuple[float, float]] | None, label: str | None = None
    ) -> None:
        """Hand skeleton (points as fractions of the frame) and a caption like "A 87%"."""
        self._hand_points = tuple(points) if points else None
        self._hand_label = label
        self._overlay_time = time.monotonic()
        self.update()

    def clear_hand_overlay(self) -> None:
        self._hand_points = None
        self._hand_label = None
        self.update()

    def has_hand_overlay(self) -> bool:
        return self._hand_points is not None

    def hand_label(self) -> str | None:
        return self._hand_label

    # --- painting ---

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 - Qt override
        super().paintEvent(event)  # QSS border / background
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        area = self.contentsRect().adjusted(4, 4, -4, -4)
        frame_rect = QRectF(area)

        if self._pixmap is not None:
            scaled = self._pixmap.scaled(
                area.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            target = QRect(0, 0, scaled.width(), scaled.height())
            target.moveCenter(area.center())
            painter.drawPixmap(target, scaled)
            frame_rect = QRectF(target)
        else:
            painter.setPen(self.palette().windowText().color())  # QSS ``color``
            flags = Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap
            painter.drawText(area, flags, PLACEHOLDER_TEXT)

        if self._show_zone:
            pen = QPen(self._zone_colors.get(self._zone_state, self._zone_colors[""]), 2)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            zone = QRectF(
                0, 0, frame_rect.width() * _ZONE_WIDTH, frame_rect.height() * _ZONE_HEIGHT
            )
            zone.moveCenter(frame_rect.center())
            painter.drawRoundedRect(zone, 8, 8)

        overlay_fresh = time.monotonic() - self._overlay_time <= OVERLAY_TTL_S
        if self._pixmap is not None and overlay_fresh:
            if self._hand_points is not None:
                self._paint_skeleton(painter, frame_rect)
            if self._hand_label:
                self._paint_label(painter, frame_rect)
        painter.end()

    def _paint_skeleton(self, painter: QPainter, frame_rect: QRectF) -> None:
        left, top = frame_rect.left(), frame_rect.top()
        width, height = frame_rect.width(), frame_rect.height()
        points = [QPointF(left + x * width, top + y * height) for x, y in self._hand_points or ()]
        scale = max(1.0, height / 240)
        for bones, color in _FINGER_COLORS:
            pen = QPen(color, 2.4 * scale)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            for start, end in bones:
                if start < len(points) and end < len(points):
                    painter.drawLine(points[start], points[end])
        painter.setPen(QPen(QColor("#FFFFFF"), 0.8 * scale))
        painter.setBrush(QBrush(_JOINT_COLOR))
        radius = 2.8 * scale
        for point in points:
            painter.drawEllipse(point, radius, radius)

    def _paint_label(self, painter: QPainter, frame_rect: QRectF) -> None:
        font = QFont(self.font())
        font.setBold(True)
        font.setPixelSize(max(14, int(frame_rect.height() * 0.08)))
        painter.setFont(font)
        metrics = painter.fontMetrics()
        padding = font.pixelSize() * 0.4
        box = QRectF(
            frame_rect.left() + padding,
            frame_rect.top() + padding,
            metrics.horizontalAdvance(self._hand_label or "") + 2 * padding,
            metrics.height() + padding,
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(_LABEL_BACKGROUND))
        painter.drawRoundedRect(box, padding, padding)
        painter.setPen(_LABEL_TEXT_COLOR)
        painter.drawText(box, Qt.AlignmentFlag.AlignCenter, self._hand_label or "")
