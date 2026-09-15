"""Tests for the GAME-3 shared results screen.

Pure helpers are tested without Qt; the widget tests build a GameResult
(either by hand or by driving ExampleGestureGame to completion) and assert
on what the screen renders. No camera / AI / event loop.
"""

from datetime import UTC, datetime
from uuid import uuid4

from PySide6.QtCore import QObject, Signal

from handgame.core.models import GameState, PlayerId
from handgame.games.example_gesture_game import ExampleGestureGame
from handgame.games.game_context import PlayerGameState
from handgame.games.game_result import GameEndReason, GameResult
from handgame.gui.screens.results_screen import (
    ResultsScreen,
    describe_outcome,
    end_reason_text,
    format_duration,
)
from test_base_game import RecordingSink, make_context, make_gesture


def _result(
    player_results,
    *,
    end_reason=GameEndReason.COMPLETED,
    final_state=GameState.FINISHED,
    duration_ms=65_000,
):
    now = datetime.now(UTC)
    return GameResult(
        session_id=uuid4(),
        game_id=ExampleGestureGame.GAME_ID,
        final_state=final_state,
        end_reason=end_reason,
        player_results=player_results,
        started_at=now,
        finished_at=now,
        duration_ms=duration_ms,
    )


def test_format_duration():
    assert format_duration(0) == "0:00"
    assert format_duration(-10) == "0:00"
    assert format_duration(65_000) == "1:05"
    assert format_duration(600_000) == "10:00"


def test_end_reason_text_covers_all_reasons():
    assert {end_reason_text(r) for r in GameEndReason} == {
        "Completed",
        "Timed out",
        "Aborted",
        "Error",
    }


def test_describe_outcome_variants():
    p1 = PlayerGameState(player_id=PlayerId.PLAYER_1, score=3)
    p2 = PlayerGameState(player_id=PlayerId.PLAYER_2, score=5)
    tie = PlayerGameState(player_id=PlayerId.PLAYER_2, score=3)

    assert describe_outcome({}) == "No results recorded"
    assert "3" in describe_outcome({PlayerId.PLAYER_1: p1})
    assert describe_outcome({PlayerId.PLAYER_1: p1, PlayerId.PLAYER_2: p2}) == "Player 2 wins!"
    assert describe_outcome({PlayerId.PLAYER_1: p1, PlayerId.PLAYER_2: tie}) == "It's a draw!"


def test_show_result_single_player(qapp):
    screen = ResultsScreen()
    p1 = PlayerGameState(
        player_id=PlayerId.PLAYER_1, score=4, mistakes=1, hint_count=2, current_step=4
    )
    screen.show_result(_result({PlayerId.PLAYER_1: p1}))

    assert screen.player_ids() == [PlayerId.PLAYER_1]
    assert screen.card_value(PlayerId.PLAYER_1, "score") == 4
    assert screen.card_value(PlayerId.PLAYER_1, "mistakes") == 1
    assert screen.card_value(PlayerId.PLAYER_1, "hint_count") == 2
    assert "1:05" in screen.meta_text()
    assert screen.is_error() is False


def test_show_result_two_players_names_winner(qapp):
    screen = ResultsScreen()
    p1 = PlayerGameState(player_id=PlayerId.PLAYER_1, score=2)
    p2 = PlayerGameState(player_id=PlayerId.PLAYER_2, score=6)
    screen.show_result(_result({PlayerId.PLAYER_1: p1, PlayerId.PLAYER_2: p2}))

    assert set(screen.player_ids()) == {PlayerId.PLAYER_1, PlayerId.PLAYER_2}
    assert screen.outcome_text() == "Player 2 wins!"


def test_error_result_flags_error(qapp):
    screen = ResultsScreen()
    p1 = PlayerGameState(player_id=PlayerId.PLAYER_1, score=0)
    screen.show_result(
        _result(
            {PlayerId.PLAYER_1: p1},
            end_reason=GameEndReason.ERROR,
            final_state=GameState.ERROR,
        )
    )
    assert screen.is_error() is True


def test_show_result_is_idempotent(qapp):
    screen = ResultsScreen()
    p1 = PlayerGameState(player_id=PlayerId.PLAYER_1, score=1)
    result = _result({PlayerId.PLAYER_1: p1})

    screen.show_result(result)
    screen.show_result(result)
    screen.show_result(result, inline_end_already_shown=True)

    assert screen.player_ids() == [PlayerId.PLAYER_1]
    assert screen.heading_text() == "Summary"


def test_show_result_from_a_real_finished_game(qapp):
    sink = RecordingSink()
    game = ExampleGestureGame(sink)
    context = make_context(sequence_length=3)
    game.start(context)
    for _ in range(3):
        expected = game.get_expected_sign(PlayerId.PLAYER_1)
        game.handle_gesture(make_gesture(context, expected))
    result = game.get_result()
    assert result is not None

    screen = ResultsScreen()
    screen.show_result(result)
    assert screen.card_value(PlayerId.PLAYER_1, "score") == 3
    assert screen.outcome_text()


def test_connect_controller_renders_on_ui_game_finished(qapp):
    class StubController(QObject):
        ui_game_finished = Signal(object)

    stub = StubController()
    screen = ResultsScreen()
    screen.connect_controller(stub)

    p1 = PlayerGameState(player_id=PlayerId.PLAYER_1, score=9)
    stub.ui_game_finished.emit(_result({PlayerId.PLAYER_1: p1}))

    assert screen.card_value(PlayerId.PLAYER_1, "score") == 9
