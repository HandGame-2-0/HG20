"""Tests for the DifficultyProfile view - mostly pure, one thin widget test."""

from handgame.games.game_context import DifficultyProfile, build_difficulty_profile
from handgame.gui.widgets.difficulty_view import (
    DifficultyProfileWidget,
    difficulty_percent,
    difficulty_rows,
)

_ALL_KEYS = {
    "level",
    "gesture_timeout_ms",
    "hint_delay_ms",
    "hint_duration_ms",
    "sequence_length",
    "board_size",
    "allowed_mistakes",
    "speed_multiplier",
}


def test_rows_cover_every_profile_field():
    rows = difficulty_rows(build_difficulty_profile(3))
    assert {r.key for r in rows} == _ALL_KEYS
    assert all(r.icon and r.label and r.text for r in rows)


def test_percent_is_clamped():
    assert difficulty_percent(50, 100) == 50
    assert difficulty_percent(-5, 100) == 0
    assert difficulty_percent(999, 100) == 100
    assert difficulty_percent(5, 0) == 0


def test_level_row_is_out_of_five():
    row = next(r for r in difficulty_rows(build_difficulty_profile(2)) if r.key == "level")
    assert row.value == 2
    assert row.percent == 40
    assert "2" in row.text


def test_rows_report_raw_profile_values():
    profile = build_difficulty_profile(5)
    by_key = {r.key: r for r in difficulty_rows(profile)}
    assert by_key["gesture_timeout_ms"].value == profile.gesture_timeout_ms
    assert by_key["allowed_mistakes"].value == profile.allowed_mistakes
    assert by_key["speed_multiplier"].value == profile.speed_multiplier


def test_value_beyond_preset_range_clamps_to_full_bar():
    profile = DifficultyProfile(
        level=3,
        gesture_timeout_ms=999_999,
        hint_delay_ms=0,
        hint_duration_ms=0,
        sequence_length=3,
        board_size=3,
        allowed_mistakes=2,
    )
    row = {r.key: r for r in difficulty_rows(profile)}["gesture_timeout_ms"]
    assert row.percent == 100


def test_widget_builds_one_bar_per_field_and_rebuilds(qapp):
    widget = DifficultyProfileWidget()
    widget.set_profile(build_difficulty_profile(1))
    assert set(widget.keys()) == _ALL_KEYS

    widget.set_profile(build_difficulty_profile(4))
    assert set(widget.keys()) == _ALL_KEYS  # no duplicated rows
    assert widget.bar("level").value() == 80
    assert widget.bar("level").format() == "4 / 5"
