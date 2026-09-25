"""Gameplay - "Punkty / Czas / Pauza" + hearts frames, laid out
per wireframe ``docs/appearance/image1.png``: game area on the left, camera
preview panel on the right. The preview can be hidden, and the game then takes
the whole width.

This is the shell around whatever minigame view is running. The HUD (points,
timer, pause, lives) is owned by the GUI; ``set_game_widget`` embeds the
minigame's own view into the "GAMEPLAY AREA" placeholder. The screen only
reacts to setters fed from the GameController -> SessionManager ->
GUIIntegrationController signal chain - it owns no QTimer and computes no
score.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from handgame.gui.screens.common import init_screen
from handgame.gui.widgets.camera_preview import CameraPreviewWidget

HEART_FULL = "\N{BLACK HEART SUIT}"
HEART_EMPTY = "\N{WHITE HEART SUIT}"
PAUSE_TEXT = "Pauza \N{HEAVY VERTICAL BAR}\N{HEAVY VERTICAL BAR}"
RESUME_TEXT = "Wznów \N{BLACK RIGHT-POINTING TRIANGLE}"
HIDE_PREVIEW_TEXT = "Ukryj podgląd"
SHOW_PREVIEW_TEXT = "Pokaż podgląd"


def format_clock(seconds: int) -> str:
    """``75`` -> ``"01:15"``; negative clamps to ``"00:00"``."""
    minutes, secs = divmod(max(0, seconds), 60)
    return f"{minutes:02d}:{secs:02d}"


class GameplayScreen(QWidget):
    exit_requested = Signal()
    pause_toggled = Signal(bool)  # True = paused

    def __init__(self, lives: int = 5, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        init_screen(self)
        self._paused = False
        self._game_widget: QWidget | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        hud = QWidget()
        hud.setObjectName("HudBar")
        hud.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        hud_layout = QHBoxLayout(hud)
        hud_layout.setContentsMargins(16, 12, 16, 12)  # bar, not a card
        hud_layout.setSpacing(24)

        self._points_label = QLabel()
        self._points_label.setObjectName("HudPoints")
        hud_layout.addWidget(self._points_label)

        self._timer_label = QLabel()
        self._timer_label.setObjectName("HudTimer")
        hud_layout.addWidget(self._timer_label)

        hud_layout.addStretch(1)

        self._hearts_row = QHBoxLayout()
        hud_layout.addLayout(self._hearts_row)
        self._heart_labels: list[QLabel] = []

        self._preview_button = QPushButton(HIDE_PREVIEW_TEXT)
        self._preview_button.clicked.connect(
            lambda: self.set_preview_visible(not self.is_preview_visible())
        )
        hud_layout.addWidget(self._preview_button)

        self._pause_button = QPushButton(PAUSE_TEXT)
        self._pause_button.clicked.connect(self._toggle_pause)
        hud_layout.addWidget(self._pause_button)

        exit_button = QPushButton("\N{LEFTWARDS ARROW} Wyjdź")
        exit_button.clicked.connect(self.exit_requested.emit)
        hud_layout.addWidget(exit_button)

        outer.addWidget(hud)

        body = QHBoxLayout()
        body.setContentsMargins(16, 16, 16, 16)
        body.setSpacing(24)

        self._gameplay_area = QFrame()
        self._gameplay_area.setObjectName("GameplayArea")
        self._gameplay_area_layout = QVBoxLayout(self._gameplay_area)
        self._placeholder = QLabel("GRA")
        self._placeholder.setObjectName("SectionHeading")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._gameplay_area_layout.addWidget(self._placeholder)
        body.addWidget(self._gameplay_area, stretch=3)

        self._preview_panel = QFrame()
        self._preview_panel.setObjectName("PreviewPanel")
        panel_layout = QVBoxLayout(self._preview_panel)
        panel_layout.setContentsMargins(16, 16, 16, 16)
        panel_title = QLabel("Podgląd kamery")
        panel_title.setObjectName("SectionHeading")
        panel_layout.addWidget(panel_title)
        self._preview = CameraPreviewWidget(show_zone=False)
        self._preview.setMinimumSize(160, 120)
        panel_layout.addWidget(self._preview, stretch=1)
        body.addWidget(self._preview_panel, stretch=1)

        outer.addLayout(body, stretch=1)

        self.reset(lives=lives)

    # --- minigame view ---

    def set_game_widget(self, widget: QWidget | None) -> None:
        """Embed a minigame view (``None`` restores the placeholder)."""
        if self._game_widget is not None:
            self._gameplay_area_layout.removeWidget(self._game_widget)
            self._game_widget.setParent(None)
        self._game_widget = widget
        self._placeholder.setVisible(widget is None)
        if widget is not None:
            self._gameplay_area_layout.addWidget(widget)

    # --- camera preview panel ---

    @property
    def preview(self) -> CameraPreviewWidget:
        return self._preview

    def update_frame(self, pixmap: QPixmap) -> None:
        self._preview.update_frame(pixmap)

    def is_preview_visible(self) -> bool:
        return not self._preview_panel.isHidden()

    def set_preview_visible(self, visible: bool) -> None:
        """Hide the preview - let the game fill the whole width."""
        self._preview_panel.setVisible(visible)
        self._preview_button.setText(HIDE_PREVIEW_TEXT if visible else SHOW_PREVIEW_TEXT)

    # --- HUD setters ---

    def reset(self, *, lives: int, seconds: int = 0) -> None:
        """Prepare the HUD for a fresh round."""
        self.set_max_lives(lives)
        self.set_points(0)
        self.set_time_remaining(seconds)
        self.set_paused(False)

    def set_points(self, points: int) -> None:
        self._points_label.setText(f"Punkty {points:03d}")

    def set_time_remaining(self, seconds: int) -> None:
        self._timer_label.setText(f"Czas: {format_clock(seconds)}")

    def set_max_lives(self, lives: int) -> None:
        while self._heart_labels:
            heart = self._heart_labels.pop()
            self._hearts_row.removeWidget(heart)
            heart.deleteLater()
        for _ in range(lives):
            heart = QLabel(HEART_FULL)
            heart.setObjectName("HeartIcon")
            self._hearts_row.addWidget(heart)
            self._heart_labels.append(heart)
        self.set_lives(lives)

    def set_lives(self, remaining: int) -> None:
        total = len(self._heart_labels)
        for index, heart in enumerate(self._heart_labels):
            heart.setText(HEART_FULL if index < remaining else HEART_EMPTY)
            # Accessible text so the state is not carried by the glyph alone.
            heart.setAccessibleName(f"Życia: {remaining} z {total}")

    def set_paused(self, paused: bool) -> None:
        self._paused = paused
        self._pause_button.setText(RESUME_TEXT if paused else PAUSE_TEXT)

    # --- read helpers (tests / integration) ---

    def is_paused(self) -> bool:
        return self._paused

    def points_text(self) -> str:
        return self._points_label.text()

    def timer_text(self) -> str:
        return self._timer_label.text()

    def hearts_text(self) -> str:
        return "".join(heart.text() for heart in self._heart_labels)

    def _toggle_pause(self) -> None:
        self.set_paused(not self._paused)
        self.pause_toggled.emit(self._paused)
