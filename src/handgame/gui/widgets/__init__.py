"""GUI widgets (GUI-CORE-5 / KAN-31, KAN-34).

These widgets are pure presentation: they render numbers and difficulty
parameters that other layers have already computed. They never calculate a
score, count a mistake, run gesture recognition, or own a QTimer.
"""

from handgame.gui.widgets.difficulty_view import (
    DifficultyProfileWidget,
    DifficultyRow,
    difficulty_percent,
    difficulty_rows,
)
from handgame.gui.widgets.scoreboard import ScoreboardWidget

__all__ = [
    "DifficultyProfileWidget",
    "DifficultyRow",
    "ScoreboardWidget",
    "difficulty_percent",
    "difficulty_rows",
]
