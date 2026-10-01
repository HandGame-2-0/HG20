"""Pure Python tests for MolesGame - no qtbot, no Qt event loop."""

from uuid import uuid4

from handgame.core.events import GameActionEvent, GestureRecognitionEvent
from handgame.core.models import CameraId, GameMode, GameState, PlayerId
from handgame.games.game_context import GameContext, build_difficulty_profile
from handgame.games.game_result import GameEndReason
from handgame.games.moles_game import MolesGame


class RecordingSink:
    def __init__(self):
        self.actions = []
        self.results = []
        self.errors = []

    def on_state_changed(self, state):
        pass

    def on_score_changed(self, player_state):
        pass

    def on_hint_requested(self, player_id, hint):
        pass

    def on_action_ready(self, action):
        self.actions.append(action)

    def on_control_event(self, event):
        pass

    def on_finished(self, result):
        self.results.append(result)

    def on_error(self, message, recoverable):
        self.errors.append((message, recoverable))


def make_context():
    return GameContext(
        session_id=uuid4(),
        game_id=MolesGame.GAME_ID,
        mode=GameMode.SINGLEPLAYER,
        difficulty=build_difficulty_profile(1),
        player_camera_mapping={PlayerId.PLAYER_1: CameraId.CAMERA_1},
        selected_algorithms={CameraId.CAMERA_1: "MOCK_YOLO"},
    )


def view_event(context, action_type, payload=None, session_id=None):
    return GameActionEvent(
        session_id=session_id or context.session_id,
        player_id=PlayerId.PLAYER_1,
        action_type=action_type,
        payload=payload or {},
    )


def started_game():
    sink = RecordingSink()
    game = MolesGame(sink)
    context = make_context()
    game.start(context)
    return game, sink, context


def test_hit_adds_points_and_step():
    game, sink, context = started_game()

    game.handle_view_event(
        view_event(context, MolesGame.ACTION_MOLE_HIT, {"letter": "A", "points": 10})
    )

    state = game.get_player_state(PlayerId.PLAYER_1)
    assert (state.score, state.current_step, state.mistakes) == (10, 1, 0)
    assert sink.actions[-1].action_type == MolesGame.ACTION_MOLE_HIT


def test_miss_counts_mistake():
    game, _sink, context = started_game()

    game.handle_view_event(view_event(context, MolesGame.ACTION_MOLE_MISS, {"letter": "B"}))

    state = game.get_player_state(PlayerId.PLAYER_1)
    assert (state.score, state.mistakes) == (0, 1)


def test_round_over_finishes_game_with_result():
    game, sink, context = started_game()
    game.handle_view_event(
        view_event(context, MolesGame.ACTION_MOLE_HIT, {"letter": "A", "points": 10})
    )

    game.handle_view_event(view_event(context, MolesGame.ACTION_ROUND_OVER))

    assert game.get_state() == GameState.FINISHED
    (result,) = sink.results
    assert result.end_reason == GameEndReason.COMPLETED
    assert result.player_results[PlayerId.PLAYER_1].score == 10


def test_view_events_ignored_when_not_running_or_other_session():
    game, _sink, context = started_game()
    game.handle_view_event(
        view_event(context, MolesGame.ACTION_MOLE_HIT, {"points": 10}, session_id=uuid4())
    )
    game.pause()
    game.handle_view_event(view_event(context, MolesGame.ACTION_MOLE_HIT, {"points": 10}))

    assert game.get_player_state(PlayerId.PLAYER_1).score == 0


def test_gesture_is_logged_but_not_scored():
    game, sink, context = started_game()

    game.handle_gesture(
        GestureRecognitionEvent(
            session_id=context.session_id,
            player_id=PlayerId.PLAYER_1,
            camera_id=CameraId.CAMERA_1,
            algorithm_id="MOCK_YOLO",
            recognized_sign="A",
            confidence=0.9,
        )
    )

    assert sink.actions[-1].action_type == MolesGame.ACTION_TYPE_GESTURE_INPUT
    assert game.get_player_state(PlayerId.PLAYER_1).score == 0
