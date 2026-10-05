"""Hosts the MG team's whack-a-mole widget (``external_games/moles``) unchanged.

Everything that does not fit HandGame is handled here instead of in their code:
- their absolute imports (``config``, ``components``) are loaded in isolation,
- their app-wide key filter is removed (it swallowed every letter key),
- their exit button no longer closes the whole application window,
- their start/difficulty menus are skipped - the round starts at our level,
- recognized letters go into their own ``InputHandler.letter_detected`` signal,
- a hit is detected from their score counter and reported as MOLE_HIT/MISS.
"""

from __future__ import annotations

import functools
import importlib
import json
import logging
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QVBoxLayout, QWidget

from handgame.core.events import GameActionEvent
from handgame.core.models import PlayerId
from handgame.games.moles_game import MolesGame
from handgame.gui.game_views.hosted_view import HostedGameView

logger = logging.getLogger(__name__)

MOLES_DIR = Path(__file__).resolve().parents[2] / "external_games" / "moles"


def _is_mg_module(name: str) -> bool:
    return name in ("config", "components") or name.startswith("components.")


@functools.cache
def load_moles_widget_class() -> Any:
    """Import the MG ``GameWidget`` without leaving ``config``/``components``
    in ``sys.modules`` (next MG game will use the same names)."""
    saved = {name: sys.modules.pop(name) for name in list(sys.modules) if _is_mg_module(name)}
    sys.path.insert(0, str(MOLES_DIR))
    try:
        module = importlib.import_module("components.GameWidget")
    finally:
        sys.path.remove(str(MOLES_DIR))
        for name in [name for name in sys.modules if _is_mg_module(name)]:
            del sys.modules[name]
        sys.modules.update(saved)

    class HostedMolesWidget(module.GameWidget):  # type: ignore[name-defined]
        def _on_exit_game(self) -> None:
            # Original closes self.window() - that is the whole HandGame window.
            pass

    return HostedMolesWidget


class MolesView(HostedGameView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._session_id: UUID | None = None
        self._player_id: PlayerId | None = None
        self._paused = False
        self._stopped = False

        self._game = load_moles_widget_class()(parent=self)
        app = QCoreApplication.instance()
        if app is not None:
            app.removeEventFilter(self._game.input_handler)
        self._game.game_timer.timeout_signal.connect(self._on_round_over)
        self._game.game_timer.timer.timeout.connect(self._emit_time)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._game)

    @classmethod
    def level_labels(cls) -> dict[int, str] | None:
        """Level names from their ``difficulties.json`` ("Łatwy" ... "Ekspert")."""
        try:
            with open(MOLES_DIR / "difficulties.json", encoding="utf-8") as file:
                levels = json.load(file)
            return {int(key): str(config["name"]) for key, config in levels.items()}
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            logger.warning("Cannot read moles level names", exc_info=True)
            return None

    @property
    def game_widget(self) -> QWidget:
        return self._game

    def begin(self, session_id: UUID, player_id: PlayerId, level: int) -> None:
        if self._session_id is not None or self._stopped:
            return
        self._session_id = session_id
        self._player_id = player_id
        # Same as the player pressing "start" and picking the level in their menu.
        self._game._on_start_clicked()
        self._game._on_sub_menu_clicked(level)
        self.points_changed.emit(0)
        self.time_changed.emit(self._game.game_timer.duration_sec)
        self.setFocus()

    def handle_letter(self, sign: str | None) -> None:
        if self._session_id is None or self._paused or self._stopped:
            return
        if not sign or len(sign) != 1 or not sign.isalpha():
            return
        if self._game.GameState.name != "PLAYING":
            return
        letter = sign.upper()
        before = self._game.score_counter.score
        self._game.input_handler.letter_detected.emit(letter)  # synchronous
        after = self._game.score_counter.score
        if after > before:
            self._emit(MolesGame.ACTION_MOLE_HIT, {"letter": letter, "points": after - before})
            self.points_changed.emit(after)
        else:
            self._emit(MolesGame.ACTION_MOLE_MISS, {"letter": letter})

    def pause(self) -> None:
        if self._session_id is None or self._paused or self._stopped:
            return
        self._paused = True
        self._game.bg_timer.stop()
        self._game.mole_spawner.stop()
        self._game.game_timer.stop_timer()

    def resume(self) -> None:
        if not self._paused or self._stopped:
            return
        self._paused = False
        self._game.bg_timer.start()
        if self._game.GameState.name == "PLAYING":
            # Not start_timer(): that one resets the remaining time.
            self._game.game_timer.timer.start(1000)
            self._game.mole_spawner.start()

    def stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True
        self._game.bg_timer.stop()
        self._game.mole_spawner.stop()
        self._game.game_timer.stop_timer()
        self._game.tile_manager.reset_all()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        """Keyboard fallback for testing without a camera: letters only."""
        text = event.text()
        if len(text) == 1 and text.isascii() and text.isalpha():
            self.handle_letter(text)
            event.accept()
            return
        super().keyPressEvent(event)

    def _on_round_over(self) -> None:
        if not self._stopped:
            self._emit(MolesGame.ACTION_ROUND_OVER, {})

    def _emit_time(self) -> None:
        self.time_changed.emit(self._game.game_timer.remaining_sec)

    def _emit(self, action_type: str, payload: dict[str, object]) -> None:
        if self._session_id is None or self._player_id is None:
            return
        self.view_event.emit(
            GameActionEvent(
                session_id=self._session_id,
                player_id=self._player_id,
                action_type=action_type,
                payload=payload,
            )
        )
