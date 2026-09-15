"""Tests for the live ScoreboardWidget.

No camera, no AI, no game loop: the widget is fed ``PlayerGameState`` values
directly, or via a real ``GameController``'s ``score_changed`` signal.
"""

from handgame.core.models import GameState, PlayerId
from handgame.games.game_context import PlayerGameState
from handgame.games.game_controller import GameController
from handgame.gui.widgets.scoreboard import ScoreboardWidget


def _state(player_id, **kwargs):
    return PlayerGameState(player_id=player_id, **kwargs)


def test_update_from_state_renders_numbers(qapp):
    board = ScoreboardWidget()
    board.update_from_state(
        _state(PlayerId.PLAYER_1, score=3, mistakes=1, hint_count=2, current_step=3)
    )
    assert board.values_for(PlayerId.PLAYER_1) == {
        "score": 3,
        "mistakes": 1,
        "hint_count": 2,
        "current_step": 3,
        "is_active": True,
    }


def test_two_players_tracked_independently(qapp):
    board = ScoreboardWidget()
    board.update_from_state(_state(PlayerId.PLAYER_1, score=5))
    board.update_from_state(_state(PlayerId.PLAYER_2, score=2, mistakes=4))
    assert board.values_for(PlayerId.PLAYER_1)["score"] == 5
    assert board.values_for(PlayerId.PLAYER_2)["mistakes"] == 4
    assert set(board.player_ids()) == {PlayerId.PLAYER_1, PlayerId.PLAYER_2}


def test_score_changed_signal_from_controller_updates_board(qapp):
    board = ScoreboardWidget()
    controller = GameController()
    board.connect_controller(controller)

    # on_score_changed is GameController's GameEventSink hook - it emits
    # score_changed, exactly as a running BaseGame would.
    controller.on_score_changed(_state(PlayerId.PLAYER_1, score=7, current_step=7))

    assert board.values_for(PlayerId.PLAYER_1)["score"] == 7
    assert board.values_for(PlayerId.PLAYER_1)["current_step"] == 7


def test_game_state_changed_updates_title_passively(qapp):
    board = ScoreboardWidget()
    controller = GameController()
    board.connect_controller(controller)

    controller.on_state_changed(GameState.PAUSED)
    assert "paused" in board.title_text().lower()

    controller.on_state_changed(GameState.FINISHED)
    assert "final" in board.title_text().lower()


def test_inactive_player_row_is_disabled(qapp):
    board = ScoreboardWidget()
    board.update_from_state(_state(PlayerId.PLAYER_1, score=1, is_active=False))
    assert board.values_for(PlayerId.PLAYER_1)["is_active"] is False


def test_non_player_payload_is_ignored(qapp):
    board = ScoreboardWidget()
    board.update_from_state(object())
    board.update_from_state(None)
    assert board.player_ids() == []


def test_clear_removes_rows(qapp):
    board = ScoreboardWidget()
    board.update_from_state(_state(PlayerId.PLAYER_1, score=1))
    board.clear()
    assert board.player_ids() == []
