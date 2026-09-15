"""GAME-3: shared results screen.

Reads a finished ``GameResult`` (``session_id``, ``final_state``,
``end_reason``, ``player_results``, ``duration_ms``) and presents it for one
or two players.

Design notes / contract:

* This screen only *displays* a ``GameResult``. It never computes a score, a
  mistake count or a hint count - those arrive already computed inside
  ``result.player_results``. Comparing two players' final scores to name a
  winner is a display decision, not scoring logic.
* It must not assume it is the only place results are ever shown. A minigame
  may have rendered its own end state in-widget before calling ``end()``. The
  only guaranteed contract is "``end()`` was called and produced a
  ``GameResult``". ``show_result()`` is therefore fully self-contained and
  idempotent: it rebuilds from the passed result every call and depends on no
  external game state. Pass ``inline_end_already_shown=True`` to soften the
  heading when the game already showed its own summary.
* It owns no ``QTimer`` and never queries the clock; ``duration_ms`` is taken
  verbatim from the result.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from handgame.core.models import GameState, PlayerId
from handgame.games.game_context import PlayerGameState
from handgame.games.game_result import GameEndReason, GameResult

_END_REASON_TEXT: dict[GameEndReason, str] = {
    GameEndReason.COMPLETED: "Completed",
    GameEndReason.TIMEOUT: "Timed out",
    GameEndReason.ABORTED: "Aborted",
    GameEndReason.ERROR: "Error",
}

_CARD_FIELDS: tuple[tuple[str, str], ...] = (
    ("score", "Score"),
    ("mistakes", "Mistakes"),
    ("hint_count", "Hints used"),
    ("current_step", "Steps"),
)


def _player_name(player_id: PlayerId) -> str:
    return player_id.name.replace("_", " ").title()


def format_duration(duration_ms: float) -> str:
    """``65000`` -> ``"1:05"``. Negative / sub-second -> ``"0:00"``."""
    total_seconds = max(0, round(duration_ms / 1000.0))
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


def end_reason_text(reason: GameEndReason) -> str:
    return _END_REASON_TEXT.get(reason, reason.name.title())


def describe_outcome(player_results: Mapping[PlayerId, PlayerGameState]) -> str:
    """Human summary line. Winner = highest already-computed score."""
    items = list(player_results.items())
    if not items:
        return "No results recorded"
    if len(items) == 1:
        player_id, state = items[0]
        return f"{_player_name(player_id)} - {state.score} pts"
    ranked = sorted(items, key=lambda kv: kv[1].score, reverse=True)
    (top_id, top_state), (_, runner_state) = ranked[0], ranked[1]
    if top_state.score == runner_state.score:
        return "It's a draw!"
    return f"{_player_name(top_id)} wins!"


class ResultsScreen(QWidget):
    """Shared end-of-game screen for 1 and 2 players.

    ``router_callback`` - optional; when given, a "Back to menu" button is
    shown that invokes it with no arguments.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        router_callback: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self._router_callback = router_callback
        self._last_result: GameResult | None = None
        self._is_error = False
        self._card_state: dict[PlayerId, PlayerGameState] = {}

        root = QVBoxLayout(self)

        self._heading = QLabel("Game Results")
        self._heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._heading.setStyleSheet("font-size: 24px; font-weight: bold;")
        root.addWidget(self._heading)

        self._meta = QLabel("")
        self._meta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._meta)

        self._outcome = QLabel("")
        self._outcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._outcome.setStyleSheet("font-size: 18px; font-weight: bold;")
        root.addWidget(self._outcome)

        self._error_label = QLabel("The game ended with an error.")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setStyleSheet("color: #c0392b; font-weight: bold;")
        self._error_label.setVisible(False)
        root.addWidget(self._error_label)

        self._cards_row = QHBoxLayout()
        root.addLayout(self._cards_row)
        root.addStretch(1)

        if router_callback is not None:
            back = QPushButton("Back to menu")
            back.clicked.connect(lambda: router_callback())
            root.addWidget(back, alignment=Qt.AlignmentFlag.AlignCenter)

    # --- wiring ---

    def connect_controller(self, controller: object) -> None:
        """Subscribe to ``ui_game_finished`` (GUIIntegrationController) or
        ``game_finished`` (GameController / SessionManager)."""
        signal = getattr(controller, "ui_game_finished", None) or getattr(
            controller, "game_finished", None
        )
        if signal is None:
            raise AttributeError("controller exposes no game-finished signal")
        signal.connect(self._on_game_finished)

    @Slot(object)
    def _on_game_finished(self, result: object) -> None:
        if isinstance(result, GameResult):
            self.show_result(result)

    # --- rendering ---

    def show_result(self, result: GameResult, *, inline_end_already_shown: bool = False) -> None:
        """Render ``result``. Self-contained and safe to call repeatedly."""
        self._last_result = result
        self._heading.setText("Summary" if inline_end_already_shown else "Game Results")
        self._meta.setText(
            f"Session {str(result.session_id)[:8]}  ·  "
            f"{end_reason_text(result.end_reason)}  ·  "
            f"{format_duration(result.duration_ms)}"
        )
        self._outcome.setText(describe_outcome(result.player_results))

        self._is_error = (
            result.final_state == GameState.ERROR or result.end_reason == GameEndReason.ERROR
        )
        self._error_label.setVisible(self._is_error)

        self._rebuild_cards(result.player_results)

    def _rebuild_cards(self, player_results: Mapping[PlayerId, PlayerGameState]) -> None:
        while self._cards_row.count():
            item = self._cards_row.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        self._card_state.clear()

        ranked = sorted(player_results.items(), key=lambda kv: (-kv[1].score, kv[0].name))
        scores = [state.score for _, state in ranked]
        winner_id = ranked[0][0] if len(ranked) >= 2 and scores.count(max(scores)) == 1 else None
        for player_id, state in ranked:
            self._card_state[player_id] = state
            self._cards_row.addWidget(
                self._make_card(player_id, state, is_winner=player_id == winner_id)
            )

    @staticmethod
    def _make_card(player_id: PlayerId, state: PlayerGameState, *, is_winner: bool) -> QFrame:
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        box = QVBoxLayout(card)

        title = _player_name(player_id)
        if is_winner:
            title += "  \N{WHITE MEDIUM STAR}"
        header = QLabel(title)
        header.setStyleSheet("font-weight: bold;")
        box.addWidget(header)

        for attr, label in _CARD_FIELDS:
            box.addWidget(QLabel(f"{label}: {getattr(state, attr)}"))
        if not state.is_active:
            box.addWidget(QLabel("(left the game)"))
        return card

    # --- test / integration helpers ---

    def result(self) -> GameResult | None:
        return self._last_result

    def is_error(self) -> bool:
        return self._is_error

    def heading_text(self) -> str:
        return self._heading.text()

    def meta_text(self) -> str:
        return self._meta.text()

    def outcome_text(self) -> str:
        return self._outcome.text()

    def player_ids(self) -> list[PlayerId]:
        return list(self._card_state)

    def card_value(self, player_id: PlayerId, field: str) -> int:
        return int(getattr(self._card_state[player_id], field))
