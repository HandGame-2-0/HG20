"""Pure Python tests for BaseGame/ExampleGestureGame - no qtbot, no Qt event loop."""

from uuid import uuid4

from handgame.core.events import ControlEvent, GestureRecognitionEvent
from handgame.core.models import CameraId, GameMode, GameState, PlayerId, VirtualButton
from handgame.games.base_game import BaseGame
from handgame.games.example_gesture_game import ExampleGestureGame
from handgame.games.game_context import GameContext, build_difficulty_profile
from handgame.games.game_result import GameEndReason


class RecordingSink:
    """Stub GameEventSink that records everything it receives."""

    def __init__(self):
        self.states = []
        self.scores = []
        self.hints = []
        self.actions = []
        self.controls = []
        self.results = []
        self.errors = []

    def on_state_changed(self, state):
        self.states.append(state)

    def on_score_changed(self, player_state):
        self.scores.append(player_state)

    def on_hint_requested(self, player_id, hint):
        self.hints.append((player_id, hint))

    def on_action_ready(self, action):
        self.actions.append(action)

    def on_control_event(self, event):
        self.controls.append(event)

    def on_finished(self, result):
        self.results.append(result)

    def on_error(self, message, recoverable):
        self.errors.append((message, recoverable))


def make_context(sequence_length=3):
    difficulty = build_difficulty_profile(1)
    difficulty = type(difficulty)(
        level=difficulty.level,
        gesture_timeout_ms=difficulty.gesture_timeout_ms,
        hint_delay_ms=difficulty.hint_delay_ms,
        hint_duration_ms=difficulty.hint_duration_ms,
        sequence_length=sequence_length,
        board_size=difficulty.board_size,
        allowed_mistakes=difficulty.allowed_mistakes,
        speed_multiplier=difficulty.speed_multiplier,
    )
    return GameContext(
        session_id=uuid4(),
        game_id=ExampleGestureGame.GAME_ID,
        mode=GameMode.SINGLEPLAYER,
        difficulty=difficulty,
        player_camera_mapping={PlayerId.PLAYER_1: CameraId.CAMERA_1},
        selected_algorithms={CameraId.CAMERA_1: "MOCK_YOLO"},
    )


def make_gesture(context, recognized_sign, player_id=PlayerId.PLAYER_1):
    return GestureRecognitionEvent(
        session_id=context.session_id,
        player_id=player_id,
        camera_id=context.player_camera_mapping[player_id],
        algorithm_id="MOCK_YOLO",
        recognized_sign=recognized_sign,
        confidence=0.9,
    )


def test_handle_gesture_before_start_is_rejected():
    sink = RecordingSink()
    game = ExampleGestureGame(sink)
    context = make_context()
    event = make_gesture(context, "A")

    game.handle_gesture(event)

    assert sink.errors
    assert game.get_state() == GameState.CREATED


def test_state_transitions_created_ready_running_finished():
    sink = RecordingSink()
    game = ExampleGestureGame(sink)
    assert game.get_state() == GameState.CREATED
    # sequence_length clamped to min 3 by ExampleGestureGame.
    context = make_context(sequence_length=3)

    game.start(context)
    assert game.get_state() == GameState.RUNNING
    assert GameState.READY in sink.states
    assert GameState.RUNNING in sink.states

    for _ in range(3):
        expected = game.get_expected_sign(PlayerId.PLAYER_1)
        game.handle_gesture(make_gesture(context, expected))

    assert game.get_state() == GameState.FINISHED
    assert len(sink.results) == 1
    assert sink.results[0].end_reason == GameEndReason.COMPLETED


def test_correct_and_incorrect_gesture_scoring():
    sink = RecordingSink()
    game = ExampleGestureGame(sink)
    context = make_context(sequence_length=3)
    game.start(context)

    wrong_sign = "ZZZ_NOT_IN_POOL"
    game.handle_gesture(make_gesture(context, wrong_sign))
    state = game.get_player_state(PlayerId.PLAYER_1)
    assert state.mistakes == 1
    assert state.score == 0

    expected = game.get_expected_sign(PlayerId.PLAYER_1)
    game.handle_gesture(make_gesture(context, expected))
    state = game.get_player_state(PlayerId.PLAYER_1)
    assert state.score == 1
    assert state.current_step == 1

    assert sink.actions[-1].payload["is_correct"] is True
    assert sink.actions[0].payload["is_correct"] is False


def test_full_sequence_completion_returns_game_result():
    sink = RecordingSink()
    game = ExampleGestureGame(sink)
    context = make_context(sequence_length=3)
    game.start(context)

    for _ in range(3):
        expected = game.get_expected_sign(PlayerId.PLAYER_1)
        game.handle_gesture(make_gesture(context, expected))

    assert game.get_state() == GameState.FINISHED
    result = game.get_result()
    assert result is not None
    assert result.player_results[PlayerId.PLAYER_1].score == 3
    assert result.end_reason == GameEndReason.COMPLETED


class ButtonGame(BaseGame):
    """Minimal BaseGame subclass exercising _resolve_button/on_control_event."""

    GAME_ID = "BUTTON_GAME"
    CONTROL_MAP = {"A": VirtualButton.CONFIRM}

    def start(self, context):
        self._begin(context)
        self._enter_running()

    def update_frame(self, delta_ms):
        pass

    def end(self, reason=GameEndReason.COMPLETED):
        return self._finalize(reason)

    def _on_gesture(self, event):
        button = self._resolve_button(event)
        if button is not None:
            self._sink.on_control_event(
                ControlEvent(
                    session_id=event.session_id,
                    player_id=event.player_id,
                    button=button,
                    source_event_id=event.event_id,
                    recognized_sign=event.recognized_sign,
                    confidence=event.confidence,
                )
            )


def make_button_context(control_mapping=None):
    difficulty = build_difficulty_profile(1)
    kwargs = dict(
        session_id=uuid4(),
        game_id=ButtonGame.GAME_ID,
        mode=GameMode.SINGLEPLAYER,
        difficulty=difficulty,
        player_camera_mapping={PlayerId.PLAYER_1: CameraId.CAMERA_1},
        selected_algorithms={CameraId.CAMERA_1: "MOCK_YOLO"},
    )
    if control_mapping is not None:
        kwargs["control_mapping"] = control_mapping
    return GameContext(**kwargs)


def test_resolve_button_known_sign_fires_control_event():
    sink = RecordingSink()
    game = ButtonGame(sink)
    context = make_button_context()
    game.start(context)

    game.handle_gesture(make_gesture(context, "A"))

    assert len(sink.controls) == 1
    control = sink.controls[0]
    assert control.button == VirtualButton.CONFIRM
    assert control.session_id == context.session_id
    assert control.player_id == PlayerId.PLAYER_1


def test_resolve_button_unknown_sign_fires_nothing():
    sink = RecordingSink()
    game = ButtonGame(sink)
    context = make_button_context()
    game.start(context)

    game.handle_gesture(make_gesture(context, "ZZZ_NOT_MAPPED"))

    assert sink.controls == []


def test_resolve_button_none_sign_fires_nothing():
    sink = RecordingSink()
    game = ButtonGame(sink)
    context = make_button_context()
    game.start(context)

    game.handle_gesture(make_gesture(context, None))

    assert sink.controls == []


def test_context_control_mapping_overrides_class_control_map():
    sink = RecordingSink()
    game = ButtonGame(sink)
    context = make_button_context(control_mapping={"B": VirtualButton.CANCEL})
    game.start(context)

    # "A" is only in the class-level CONTROL_MAP - context override replaces it wholesale.
    game.handle_gesture(make_gesture(context, "A"))
    assert sink.controls == []

    game.handle_gesture(make_gesture(context, "B"))
    assert len(sink.controls) == 1
    assert sink.controls[0].button == VirtualButton.CANCEL


def test_rejected_gesture_never_reaches_resolve_button():
    sink = RecordingSink()
    game = ButtonGame(sink)
    context = make_button_context()
    # Game never started - handle_gesture's guard rejects before _on_gesture runs.
    game.handle_gesture(make_gesture(context, "A"))

    assert sink.controls == []
    assert sink.errors
