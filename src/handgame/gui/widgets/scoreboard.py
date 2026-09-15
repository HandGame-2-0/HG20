"""Live scoreboard driven by ``GameController.score_changed`` (KAN-31).

The widget subscribes to the shared game-runtime signal and renders the
per-player numbers it receives. It performs no scoring: every value shown
here is read straight off a ``PlayerGameState`` that a ``BaseGame`` subclass
already computed.
"""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from handgame.core.models import GameState, PlayerId
from handgame.games.game_context import PlayerGameState

_COLUMNS = ("Player", "Score", "Mistakes", "Hints", "Step")


def _player_name(player_id: PlayerId) -> str:
    return player_id.name.replace("_", " ").title()


class _Row:
    __slots__ = ("player_id", "name", "score", "mistakes", "hints", "step", "state")

    def __init__(
        self,
        player_id: PlayerId,
        name: QLabel,
        score: QLabel,
        mistakes: QLabel,
        hints: QLabel,
        step: QLabel,
    ) -> None:
        self.player_id = player_id
        self.name = name
        self.score = score
        self.mistakes = mistakes
        self.hints = hints
        self.step = step
        self.state: PlayerGameState | None = None

    def widgets(self) -> tuple[QLabel, ...]:
        return (self.name, self.score, self.mistakes, self.hints, self.step)


class ScoreboardWidget(QWidget):
    """One row per player: score / mistakes / hints / current step."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: dict[PlayerId, _Row] = {}

        root = QVBoxLayout(self)
        self._title = QLabel("Scoreboard")
        root.addWidget(self._title)
        self._grid = QGridLayout()
        root.addLayout(self._grid)
        root.addStretch(1)

        for col, text in enumerate(_COLUMNS):
            self._grid.addWidget(QLabel(text), 0, col)

    # --- wiring ---

    def connect_controller(self, controller: object) -> None:
        """Subscribe to a ``GameController`` (or anything with the same signals).

        Connects ``score_changed`` (mandatory) and, if present,
        ``game_state_changed`` so the header can passively reflect
        PAUSED / FINISHED. No other coupling to the controller.
        """
        controller.score_changed.connect(self._on_score_changed)  # type: ignore[attr-defined]
        game_state_changed = getattr(controller, "game_state_changed", None)
        if game_state_changed is not None:
            game_state_changed.connect(self._on_game_state_changed)

    # --- slots ---

    @Slot(object)
    def _on_score_changed(self, player_state: object) -> None:
        self.update_from_state(player_state)

    @Slot(object)
    def _on_game_state_changed(self, state: object) -> None:
        if state in (GameState.FINISHED, GameState.ERROR):
            self._title.setText("Scoreboard - final")
        elif state == GameState.PAUSED:
            self._title.setText("Scoreboard - paused")
        else:
            self._title.setText("Scoreboard")

    # --- rendering ---

    def set_players(self, player_ids: Iterable[PlayerId]) -> None:
        for player_id in player_ids:
            self._ensure_row(player_id)

    def update_from_state(self, player_state: object) -> None:
        if not isinstance(player_state, PlayerGameState):
            return
        row = self._ensure_row(player_state.player_id)
        row.state = player_state
        row.score.setText(str(player_state.score))
        row.mistakes.setText(str(player_state.mistakes))
        row.hints.setText(str(player_state.hint_count))
        row.step.setText(str(player_state.current_step))
        for widget in row.widgets():
            widget.setEnabled(bool(player_state.is_active))

    def clear(self) -> None:
        for row in self._rows.values():
            for widget in row.widgets():
                self._grid.removeWidget(widget)
                widget.deleteLater()
        self._rows.clear()

    def _ensure_row(self, player_id: PlayerId) -> _Row:
        existing = self._rows.get(player_id)
        if existing is not None:
            return existing
        grid_row = self._grid.rowCount()
        name = QLabel(_player_name(player_id))
        score, mistakes, hints, step = QLabel("0"), QLabel("0"), QLabel("0"), QLabel("0")
        row = _Row(player_id, name, score, mistakes, hints, step)
        for col, widget in enumerate(row.widgets()):
            self._grid.addWidget(widget, grid_row, col)
        self._rows[player_id] = row
        return row

    # --- test / integration helpers ---

    def player_ids(self) -> list[PlayerId]:
        return list(self._rows)

    def title_text(self) -> str:
        return self._title.text()

    def values_for(self, player_id: PlayerId) -> dict[str, object]:
        row = self._rows[player_id]
        return {
            "score": int(row.score.text()),
            "mistakes": int(row.mistakes.text()),
            "hint_count": int(row.hints.text()),
            "current_step": int(row.step.text()),
            "is_active": row.state.is_active if row.state is not None else True,
        }
