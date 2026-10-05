"""Qt views for hosted minigames, keyed by ``GAME_ID``.

A game listed here brings its own view; ``MainWindow`` embeds it in
``GameplayScreen``. Games not listed use the plain gameplay screen.
"""

from handgame.games.moles_game import MolesGame
from handgame.gui.game_views.hosted_view import HostedGameView
from handgame.gui.game_views.moles_view import MolesView

GAME_VIEWS: dict[str, type[HostedGameView]] = {
    MolesGame.GAME_ID: MolesView,
}

__all__ = ["GAME_VIEWS", "HostedGameView", "MolesView"]
