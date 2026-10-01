"""Logic side of the MG team's whack-a-mole game ("Bicie kreta").

The game itself (moles, timers, board, scoring) is the MG team's Qt widget,
copied unchanged into ``external_games/moles`` and hosted by
``gui/game_views/moles_view.py``. Hit detection therefore happens in the view,
which reports each outcome back as a ``GameActionEvent`` via
``handle_view_event``. This class only keeps the per-player score/mistakes for
stats and builds the ``GameResult`` - see "Hosted minigames" in
``docs/game_framework.md``.
"""

from __future__ import annotations

import logging
from typing import ClassVar

from handgame.core.events import GameActionEvent, GestureRecognitionEvent
from handgame.core.models import GameState
from handgame.games.base_game import BaseGame
from handgame.games.game_context import GameContext
from handgame.games.game_result import GameEndReason, GameResult

logger = logging.getLogger(__name__)


class MolesGame(BaseGame):
    """Score keeper for the hosted whack-a-mole view."""

    GAME_ID: ClassVar[str] = "MOLES"
    DISPLAY_NAME: ClassVar[str] = "Bicie kreta"

    ACTION_TYPE_GESTURE_INPUT: ClassVar[str] = "GESTURE_INPUT"
    # Reported by the view (payloads: HIT {"letter", "points"}, MISS {"letter"}, ROUND_OVER {}).
    ACTION_MOLE_HIT: ClassVar[str] = "MOLE_HIT"
    ACTION_MOLE_MISS: ClassVar[str] = "MOLE_MISS"
    ACTION_ROUND_OVER: ClassVar[str] = "MOLE_ROUND_OVER"

    def start(self, context: GameContext) -> None:
        self._begin(context)
        self._enter_running()

    def update_frame(self, delta_ms: float) -> None:
        # Timing lives in the hosted view.
        pass

    def _on_gesture(self, event: GestureRecognitionEvent) -> None:
        # Whether a letter hit a mole is decided by the view (handle_view_event).
        self._sink.on_action_ready(
            GameActionEvent(
                session_id=event.session_id,
                player_id=event.player_id,
                action_type=self.ACTION_TYPE_GESTURE_INPUT,
                payload={"sign": event.recognized_sign, "confidence": event.confidence},
            )
        )

    def handle_view_event(self, event: GameActionEvent) -> None:
        """Apply an outcome reported by the hosted view."""
        if self._state != GameState.RUNNING:
            logger.warning("View event ignored - game not RUNNING (state=%s)", self._state)
            return
        if self._context is None or event.session_id != self._context.session_id:
            logger.warning("View event ignored - session_id mismatch")
            return
        if event.player_id not in self._players:
            logger.warning("View event ignored - unknown player %s", event.player_id)
            return

        current = self._players[event.player_id]
        if event.action_type == self.ACTION_MOLE_HIT:
            points = int(event.payload.get("points", 0))
            self._update_player(
                event.player_id,
                score=current.score + points,
                current_step=current.current_step + 1,
            )
        elif event.action_type == self.ACTION_MOLE_MISS:
            self._update_player(event.player_id, mistakes=current.mistakes + 1)
        elif event.action_type == self.ACTION_ROUND_OVER:
            self.end(GameEndReason.COMPLETED)
            return
        else:
            logger.warning("View event ignored - unknown action %s", event.action_type)
            return
        self._sink.on_action_ready(event)

    def end(self, reason: GameEndReason = GameEndReason.COMPLETED) -> GameResult:
        return self._finalize(reason)
