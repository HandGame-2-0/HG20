"""Base for minigames that bring their own Qt view (see "Hosted minigames"
in ``docs/game_framework.md``).

``MainWindow`` embeds the view in ``GameplayScreen`` and drives it from
session status changes and recognized letters; the view reports outcomes
through ``view_event`` (-> ``GUIIntegrationController.report_view_event``).
"""

from __future__ import annotations

from uuid import UUID

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from handgame.core.models import PlayerId


class HostedGameView(QWidget):
    view_event = Signal(object)  # GameActionEvent for the active game
    points_changed = Signal(int)  # HUD points
    time_changed = Signal(int)  # HUD seconds remaining

    @classmethod
    def level_labels(cls) -> dict[int, str] | None:
        """The game's own names for levels 1-5, shown in the difficulty picker."""
        return None

    def begin(self, session_id: UUID, player_id: PlayerId, level: int) -> None:
        """Session is RUNNING - start the round at ``level`` (1-5). Called once."""
        raise NotImplementedError

    def handle_letter(self, sign: str | None) -> None:
        """A recognized letter (AI or keyboard fallback)."""
        raise NotImplementedError

    def pause(self) -> None:
        raise NotImplementedError

    def resume(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        """Session is over - stop all timers; the view is discarded afterwards."""
        raise NotImplementedError
