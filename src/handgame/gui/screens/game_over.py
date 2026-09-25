"""Game over - wireframe.
A centred card: title, a compact results table, then two stacked buttons.
"""

from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from handgame.games.game_context import PlayerGameState
from handgame.games.game_result import GameResult
from handgame.gui.screens.common import (
    apply_card_padding,
    center_in,
    init_screen,
    make_card,
    make_stack_button,
)
from handgame.gui.screens.results_screen import format_duration

MENU_TEXT = "Powrót do wyboru gier"
REPLAY_TEXT = "Zagraj jeszcze raz"

_ROWS: tuple[tuple[str, str], ...] = (
    ("points", "Punkty"),
    ("accuracy", "Dokładność"),
    ("time", "Czas"),
)


def accuracy_percent(states: Iterable[PlayerGameState]) -> float | None:
    """Correct steps / all attempts, in percent. ``None`` when nothing was attempted."""
    correct = mistakes = 0
    for state in states:
        correct += state.current_step
        mistakes += state.mistakes
    attempts = correct + mistakes
    return None if attempts == 0 else correct / attempts * 100.0


def format_points(points: int) -> str:
    """``12345`` -> ``"12 345"`` (Polish separator)."""
    return f"{points:,}".replace(",", " ")


class GameOverScreen(QWidget):
    play_again_requested = Signal()
    back_to_menu_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        init_screen(self)
        self._last_result: GameResult | None = None

        layout = QVBoxLayout(self)
        apply_card_padding(layout)
        card, card_layout = make_card("Koniec gry")

        results = QFrame()
        results.setObjectName("ResultsCard")
        results_layout = QVBoxLayout(results)
        results_layout.setContentsMargins(16, 12, 16, 12)

        self._values: dict[str, QLabel] = {}
        for key, caption in _ROWS:
            row = QHBoxLayout()
            label = QLabel(caption)
            label.setObjectName("ResultLabel")
            value = QLabel("--")
            value.setObjectName("ResultValue")
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(label)
            row.addStretch(1)
            row.addWidget(value)
            results_layout.addLayout(row)
            self._values[key] = value
        card_layout.addWidget(results)

        self._menu_button = make_stack_button(MENU_TEXT)
        self._menu_button.clicked.connect(self.back_to_menu_requested.emit)
        card_layout.addWidget(self._menu_button)
        self._replay_button = make_stack_button(REPLAY_TEXT)
        self._replay_button.clicked.connect(self.play_again_requested.emit)
        card_layout.addWidget(self._replay_button)

        center_in(layout, card)

    @Slot(object)
    def show_result(self, result: object) -> None:
        """Render a ``GameResult``; anything else is ignored."""
        if not isinstance(result, GameResult):
            return
        self._last_result = result
        states = list(result.player_results.values())
        self.set_values(
            points=sum(state.score for state in states),
            accuracy_pct=accuracy_percent(states),
            duration_ms=result.duration_ms,
        )

    def set_values(self, *, points: int, accuracy_pct: float | None, duration_ms: float) -> None:
        self._values["points"].setText(format_points(points))
        self._values["accuracy"].setText("--" if accuracy_pct is None else f"{accuracy_pct:.0f}%")
        self._values["time"].setText(format_duration(duration_ms))

    def result(self) -> GameResult | None:
        return self._last_result

    def value_text(self, key: str) -> str:
        return self._values[key].text()
