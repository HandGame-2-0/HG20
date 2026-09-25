"""
Figma: "Wybierz minigrę".
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QGridLayout,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from handgame.gui.screens.common import (
    BACK_TEXT,
    CONFIRM_PLAY_TEXT,
    apply_card_padding,
    init_screen,
    make_footer,
    make_primary_button,
    make_title,
)


@dataclass(frozen=True)
class GameSummary:
    """What the picker grid needs to know about one registered minigame."""

    game_id: str
    display_name: str


def game_summaries(registry: Mapping[str, type]) -> list[GameSummary]:
    """Build picker entries from ``GAME_REGISTRY``.

    Uses a class-level ``DISPLAY_NAME`` when a minigame defines one, otherwise
    prettifies the id (``"EXAMPLE_GESTURE_GAME"`` -> ``"Example Gesture Game"``).
    """
    return [
        GameSummary(
            game_id,
            getattr(game_cls, "DISPLAY_NAME", None) or game_id.replace("_", " ").title(),
        )
        for game_id, game_cls in registry.items()
    ]


class MinigameSelectScreen(QWidget):
    """Grid of checkable game tiles; "Zatwierdź / Graj" emits ``game_selected``."""

    back_requested = Signal()
    game_selected = Signal(str)  # game_id

    def __init__(
        self,
        games: Iterable[GameSummary] = (),
        columns: int = 4,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        init_screen(self)
        self._columns = columns

        # Exclusive group = radio-button behaviour over checkable tiles.
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._group.buttonToggled.connect(self._sync_confirm_enabled)
        self._tiles: dict[str, QToolButton] = {}

        layout = QVBoxLayout(self)
        apply_card_padding(layout)
        layout.addWidget(make_title("Wybierz minigrę"))

        self._grid = QGridLayout()
        self._grid.setSpacing(12)
        layout.addLayout(self._grid)
        layout.addStretch(1)

        back_button = QPushButton(BACK_TEXT)
        back_button.clicked.connect(self.back_requested.emit)
        self._confirm_button = make_primary_button(CONFIRM_PLAY_TEXT)
        self._confirm_button.clicked.connect(self._emit_selected)
        layout.addLayout(make_footer(back_button, self._confirm_button))

        self.set_games(games)

    def set_games(self, games: Iterable[GameSummary]) -> None:
        """Rebuild the tile grid. Clears the current selection."""
        for tile in self._tiles.values():
            self._group.removeButton(tile)
            self._grid.removeWidget(tile)
            tile.deleteLater()
        self._tiles.clear()

        for index, game in enumerate(games):
            tile = QToolButton()
            tile.setObjectName("GameTile")
            tile.setCheckable(True)
            tile.setText(game.display_name)
            tile.setProperty("game_id", game.game_id)
            tile.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            tile.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self._group.addButton(tile)
            self._grid.addWidget(tile, index // self._columns, index % self._columns)
            self._tiles[game.game_id] = tile
        self._sync_confirm_enabled()

    def game_ids(self) -> list[str]:
        return list(self._tiles)

    def select_game(self, game_id: str) -> None:
        self._tiles[game_id].setChecked(True)

    def selected_game_id(self) -> str | None:
        checked = self._group.checkedButton()
        return None if checked is None else str(checked.property("game_id"))

    def _sync_confirm_enabled(self, *_args: object) -> None:
        self._confirm_button.setEnabled(self._group.checkedButton() is not None)

    def _emit_selected(self) -> None:
        game_id = self.selected_game_id()
        if game_id is not None:
            self.game_selected.emit(game_id)
