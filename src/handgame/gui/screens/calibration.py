"""Figma: "Kalibracja Dłoni" (frames 2, 6, 7 - one widget, several states)."""

from __future__ import annotations

from enum import Enum, auto

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from handgame.gui.screens.common import (
    BACK_TEXT,
    apply_card_padding,
    init_screen,
    make_primary_button,
    make_title,
    set_dynamic_property,
)
from handgame.gui.widgets.camera_preview import CameraPreviewWidget

SKIP_TEXT = "Pomiń"


class CalibrationState(Enum):
    CONNECTING = auto()  # camera selected, stream not up yet
    DETECTING = auto()  # frame 2: neutral, searching for a hand
    OUT_OF_ZONE = auto()  # frame 6: "dłoń poza strefą"
    RECOGNITION_ERROR = auto()  # frame 7: "błąd rozpoznawania"
    CAMERA_ERROR = auto()  # camera reported CameraState.ERROR
    LOCKED = auto()  # hand centred and recognised, ready to continue

    @property
    def status_text(self) -> str:
        # Accessibility rule: never signal state through colour alone - every
        # error/success state carries an explicit glyph plus text.
        return _STATUS_TEXT[self]

    @property
    def is_error(self) -> bool:
        return self in (
            CalibrationState.OUT_OF_ZONE,
            CalibrationState.RECOGNITION_ERROR,
            CalibrationState.CAMERA_ERROR,
        )

    @property
    def qss_state(self) -> str:
        """Value of the ``state`` dynamic property the stylesheet selects on."""
        if self.is_error:
            return "error"
        if self is CalibrationState.LOCKED:
            return "locked"
        return ""


_STATUS_TEXT: dict[CalibrationState, str] = {
    CalibrationState.CONNECTING: "Łączenie z kamerą\N{HORIZONTAL ELLIPSIS}",
    CalibrationState.DETECTING: "Ustaw dłoń w wyznaczonej strefie",
    CalibrationState.OUT_OF_ZONE: "\N{BALLOT X} dłoń poza strefą",
    CalibrationState.RECOGNITION_ERROR: "\N{BALLOT X} błąd rozpoznawania",
    CalibrationState.CAMERA_ERROR: "\N{BALLOT X} brak obrazu z kamery",
    CalibrationState.LOCKED: "\N{CHECK MARK} dłoń wykryta poprawnie",
}


class HandCalibrationScreen(QWidget):
    """Camera preview + status line.

    "OK" unlocks only once the hand is locked. "Pomiń" always lets the player
    continue - hand detection is not wired yet, and a player must never get
    stuck on this screen.
    """

    back_requested = Signal()
    calibration_confirmed = Signal()
    skip_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        init_screen(self)

        layout = QVBoxLayout(self)
        apply_card_padding(layout)
        layout.addWidget(make_title("Kalibracja Dłoni"))

        self._preview = CameraPreviewWidget()
        layout.addWidget(self._preview, stretch=1)

        self._status_label = QLabel()
        self._status_label.setObjectName("CalibrationStatus")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)

        back_button = QPushButton(BACK_TEXT)
        back_button.clicked.connect(self.back_requested.emit)
        self._skip_button = QPushButton(SKIP_TEXT)
        self._skip_button.clicked.connect(self.skip_requested.emit)
        self._ok_button = make_primary_button("OK")
        self._ok_button.clicked.connect(self.calibration_confirmed.emit)

        footer = QHBoxLayout()
        footer.addWidget(back_button)
        footer.addStretch(1)
        footer.addWidget(self._skip_button)
        footer.addWidget(self._ok_button)
        layout.addLayout(footer)

        self._state = CalibrationState.DETECTING
        self.set_state(CalibrationState.DETECTING)

    @property
    def preview(self) -> CameraPreviewWidget:
        return self._preview

    def state(self) -> CalibrationState:
        return self._state

    def status_text(self) -> str:
        return self._status_label.text()

    def is_confirm_enabled(self) -> bool:
        return self._ok_button.isEnabled()

    def set_state(self, state: CalibrationState) -> None:
        self._state = state
        self._preview.set_zone_state(state.qss_state)
        self._status_label.setText(state.status_text)
        set_dynamic_property(self._status_label, "state", state.qss_state)
        self._ok_button.setEnabled(state is CalibrationState.LOCKED)

    def update_frame(self, pixmap: QPixmap) -> None:
        self._preview.update_frame(pixmap)

    def clear_frame(self) -> None:
        self._preview.clear_frame()
