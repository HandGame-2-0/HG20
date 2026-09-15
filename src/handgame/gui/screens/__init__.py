"""GUI screens. GAME-3 adds the shared results screen."""

from handgame.gui.screens.results_screen import (
    ResultsScreen,
    describe_outcome,
    end_reason_text,
    format_duration,
)

__all__ = [
    "ResultsScreen",
    "describe_outcome",
    "end_reason_text",
    "format_duration",
]
