"""Read-only view of a ``DifficultyProfile`` as a row of progress bars + icons.

KAN-34: "render the DifficultyProfile fields as progress bars / icons".

This module only *consumes* ``DifficultyProfile`` (already defined in
``handgame.games.game_context``) - it never defines a competing difficulty
structure. ``difficulty_rows()`` is a pure function so it can be unit tested
without Qt; ``DifficultyProfileWidget`` is the thin QWidget on top of it.

Bar scaling: each numeric field is shown relative to the widest value that
field takes across ``DIFFICULTY_PRESETS`` (levels 1-5), so a bar at ~100%
means "as extreme as the hardest shipped preset". A hand-built profile that
exceeds that range simply clamps to a full bar.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QGridLayout, QLabel, QProgressBar, QWidget

from handgame.games.game_context import DIFFICULTY_PRESETS, DifficultyProfile

# Order the fields are rendered in.
_FIELDS: tuple[str, ...] = (
    "level",
    "gesture_timeout_ms",
    "hint_delay_ms",
    "hint_duration_ms",
    "sequence_length",
    "board_size",
    "allowed_mistakes",
    "speed_multiplier",
)

# Text "icons" - no image assets, readable in a terminal-style Qt theme.
ICONS: dict[str, str] = {
    "level": "\N{BAR CHART}",
    "gesture_timeout_ms": "\N{STOPWATCH}",
    "hint_delay_ms": "\N{HOURGLASS WITH FLOWING SAND}",
    "hint_duration_ms": "\N{ELECTRIC LIGHT BULB}",
    "sequence_length": "\N{INPUT SYMBOL FOR NUMBERS}",
    "board_size": "\N{BLACK SQUARE FOR STOP}",
    "allowed_mistakes": "\N{HEAVY MULTIPLICATION X}",
    "speed_multiplier": "\N{HIGH VOLTAGE SIGN}",
}

LABELS: dict[str, str] = {
    "level": "Difficulty level",
    "gesture_timeout_ms": "Gesture timeout",
    "hint_delay_ms": "Hint delay",
    "hint_duration_ms": "Hint duration",
    "sequence_length": "Sequence length",
    "board_size": "Board size",
    "allowed_mistakes": "Allowed mistakes",
    "speed_multiplier": "Speed multiplier",
}

_MS_FIELDS = frozenset({"gesture_timeout_ms", "hint_delay_ms", "hint_duration_ms"})


@dataclass(frozen=True)
class DifficultyRow:
    """One rendered line: an icon, a label, the raw value, a caption, a %."""

    key: str
    label: str
    icon: str
    value: float
    text: str
    percent: int


def difficulty_percent(value: float, bar_max: float) -> int:
    """Clamp ``value / bar_max`` into an integer 0-100 percentage."""
    if bar_max <= 0:
        return 0
    return max(0, min(100, round(value / bar_max * 100.0)))


def _scale_max(key: str, value: float) -> float:
    if key == "level":
        return 5.0
    preset_max = max(getattr(p, key) for p in DIFFICULTY_PRESETS.values())
    return max(float(preset_max), float(value), 1.0)


def _format_value(key: str, value: float) -> str:
    if key in _MS_FIELDS:
        return f"{value / 1000.0:.1f} s"
    if key == "speed_multiplier":
        return f"{value:.2f}x"
    if key == "level":
        return f"{int(value)} / 5"
    return str(int(value))


def difficulty_rows(profile: DifficultyProfile) -> list[DifficultyRow]:
    """Turn a ``DifficultyProfile`` into rendered rows (pure, no Qt)."""
    rows: list[DifficultyRow] = []
    for key in _FIELDS:
        value = getattr(profile, key)
        rows.append(
            DifficultyRow(
                key=key,
                label=LABELS[key],
                icon=ICONS[key],
                value=value,
                text=_format_value(key, value),
                percent=difficulty_percent(value, _scale_max(key, value)),
            )
        )
    return rows


class DifficultyProfileWidget(QWidget):
    """Passive display of a ``DifficultyProfile``. Call ``set_profile()``."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._grid = QGridLayout(self)
        self._bars: dict[str, QProgressBar] = {}
        self._profile: DifficultyProfile | None = None

    def set_profile(self, profile: DifficultyProfile) -> None:
        """Render ``profile``. Safe to call repeatedly - rebuilds in place."""
        self._profile = profile
        self._clear()
        for i, row in enumerate(difficulty_rows(profile)):
            self._grid.addWidget(QLabel(f"{row.icon}  {row.label}"), i, 0)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(row.percent)
            bar.setFormat(row.text)
            self._grid.addWidget(bar, i, 1)
            self._bars[row.key] = bar

    def _clear(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        self._bars.clear()

    # --- test / integration helpers ---

    def profile(self) -> DifficultyProfile | None:
        return self._profile

    def keys(self) -> list[str]:
        return list(self._bars)

    def bar(self, key: str) -> QProgressBar:
        return self._bars[key]
