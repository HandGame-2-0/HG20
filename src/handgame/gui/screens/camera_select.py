"""Figma: "Wybór Kamery"."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QRadioButton, QVBoxLayout, QWidget

from handgame.core.models import CameraId
from handgame.gui.screens.common import (
    apply_card_padding,
    init_screen,
    make_footer,
    make_primary_button,
    make_title,
)


@dataclass(frozen=True)
class CameraOption:
    camera_id: str  # CameraId member name, e.g. "CAMERA_1"
    label: str


def default_camera_options() -> list[CameraOption]:
    """One option per ``CameraId`` known to the camera layer."""
    return [
        CameraOption(camera.name, f"Kamera {index}")
        for index, camera in enumerate(CameraId, start=1)
    ]


class CameraSelectScreen(QWidget):
    """Single-choice camera list with an "OK" button.

    Emits ``camera_confirmed(camera_id)`` - the id is a ``CameraId`` member
    name, ready for ``GUIIntegrationController.select_camera``.
    """

    camera_confirmed = Signal(str)

    def __init__(
        self,
        cameras: Iterable[CameraOption] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        init_screen(self)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        layout = QVBoxLayout(self)
        apply_card_padding(layout)
        layout.addWidget(make_title("Wybór Kamery"))

        self._options_box = QVBoxLayout()
        self._options_box.setSpacing(10)
        layout.addLayout(self._options_box)
        layout.addStretch(1)

        self._ok_button = make_primary_button("OK")
        self._ok_button.clicked.connect(self._emit_confirmed)
        layout.addLayout(make_footer(None, self._ok_button))

        self._group.buttonToggled.connect(self._sync_ok_enabled)
        self.set_cameras(default_camera_options() if cameras is None else cameras)

    def set_cameras(self, cameras: Iterable[CameraOption]) -> None:
        """Replace the listed cameras; the first one is preselected."""
        for button in self._group.buttons():
            self._group.removeButton(button)
            self._options_box.removeWidget(button)
            button.deleteLater()

        for index, camera in enumerate(cameras):
            radio = QRadioButton(camera.label)
            radio.setProperty("camera_id", camera.camera_id)
            self._group.addButton(radio)
            self._options_box.addWidget(radio)
            if index == 0:
                radio.setChecked(True)
        self._sync_ok_enabled()

    def selected_camera_id(self) -> str | None:
        checked = self._group.checkedButton()
        return None if checked is None else str(checked.property("camera_id"))

    def _sync_ok_enabled(self, *_args: object) -> None:
        self._ok_button.setEnabled(self._group.checkedButton() is not None)

    def _emit_confirmed(self) -> None:
        camera_id = self.selected_camera_id()
        if camera_id is not None:
            self.camera_confirmed.emit(camera_id)
