"""Tests for the screens ported from the Figma frames.

Widget tests only drive public signals / setters; no camera, AI or event loop.
"""

from datetime import UTC, datetime
from uuid import uuid4

import numpy as np
import pytest
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QWidget

from handgame.core.models import CameraId, GameState, PlayerId
from handgame.games.example_gesture_game import ExampleGestureGame
from handgame.games.game_context import DIFFICULTY_PRESETS, PlayerGameState
from handgame.games.game_controller import GAME_REGISTRY
from handgame.games.game_result import GameEndReason, GameResult
from handgame.gui.screen import Screen
from handgame.gui.screens.calibration import CalibrationState, HandCalibrationScreen
from handgame.gui.screens.camera_select import CameraOption, CameraSelectScreen
from handgame.gui.screens.game_over import GameOverScreen, accuracy_percent, format_points
from handgame.gui.screens.gameplay import HEART_EMPTY, HEART_FULL, GameplayScreen, format_clock
from handgame.gui.screens.minigame_select import (
    GameSummary,
    MinigameSelectScreen,
    game_summaries,
)
from handgame.gui.widgets.difficulty_modal import LEVEL_LABELS, DifficultyModal


def _collect(signal):
    received = []
    signal.connect(lambda *args: received.append(args))
    return received


# --- helpers ---


def test_game_summaries_prettify_registry_ids():
    summaries = game_summaries(GAME_REGISTRY)
    assert GameSummary(ExampleGestureGame.GAME_ID, "Example Gesture Game") in summaries


def test_format_clock_and_points():
    assert format_clock(75) == "01:15"
    assert format_clock(-3) == "00:00"
    assert format_points(12345) == "12 345"


def test_accuracy_percent():
    states = [PlayerGameState(PlayerId.PLAYER_1, current_step=3, mistakes=1)]
    assert accuracy_percent(states) == pytest.approx(75.0)
    assert accuracy_percent([PlayerGameState(PlayerId.PLAYER_1)]) is None


def test_every_difficulty_preset_has_a_label():
    assert set(DIFFICULTY_PRESETS) <= set(LEVEL_LABELS)


# --- camera select ---


def test_camera_select_defaults_to_camera_ids(qapp):
    screen = CameraSelectScreen()
    received = _collect(screen.camera_confirmed)
    assert screen.selected_camera_id() == CameraId.CAMERA_1.name
    screen._ok_button.click()
    assert received == [(CameraId.CAMERA_1.name,)]


def test_camera_select_set_cameras_replaces_options(qapp):
    screen = CameraSelectScreen([CameraOption("A", "a")])
    screen.set_cameras([CameraOption("B", "b"), CameraOption("C", "c")])
    assert screen.selected_camera_id() == "B"
    assert len(screen._group.buttons()) == 2


def test_camera_select_without_cameras_disables_ok(qapp):
    screen = CameraSelectScreen([])
    assert not screen._ok_button.isEnabled()


# --- calibration ---


@pytest.mark.parametrize(
    ("state", "qss", "can_confirm"),
    [
        (CalibrationState.CONNECTING, "", False),
        (CalibrationState.DETECTING, "", False),
        (CalibrationState.CAMERA_ERROR, "error", False),
        (CalibrationState.OUT_OF_ZONE, "error", False),
        (CalibrationState.RECOGNITION_ERROR, "error", False),
        (CalibrationState.LOCKED, "locked", True),
    ],
)
def test_calibration_states(qapp, state, qss, can_confirm):
    screen = HandCalibrationScreen()
    screen.set_state(state)
    assert screen.state() is state
    assert screen.status_text() == state.status_text
    assert screen.preview.property("state") == qss
    assert screen.is_confirm_enabled() is can_confirm


def test_calibration_status_never_colour_only():
    for state in (
        CalibrationState.OUT_OF_ZONE,
        CalibrationState.RECOGNITION_ERROR,
        CalibrationState.CAMERA_ERROR,
    ):
        assert state.status_text.startswith("\N{BALLOT X}")
    assert CalibrationState.LOCKED.status_text.startswith("\N{CHECK MARK}")


def test_calibration_preview_placeholder_until_frame(qapp):
    screen = HandCalibrationScreen()
    assert not screen.preview.has_frame()
    screen.update_frame(QPixmap(64, 48))
    assert screen.preview.has_frame()
    screen.preview.grab()  # paints frame + zone without error
    screen.clear_frame()
    assert not screen.preview.has_frame()
    screen.preview.grab()  # paints placeholder without error


def test_calibration_skip_always_available(qapp):
    screen = HandCalibrationScreen()
    received = _collect(screen.skip_requested)
    screen.set_state(CalibrationState.CAMERA_ERROR)
    assert not screen.is_confirm_enabled()
    screen._skip_button.click()
    assert received == [()]


# --- minigame select ---


def test_minigame_select_is_single_choice(qapp):
    screen = MinigameSelectScreen([GameSummary("A", "Game A"), GameSummary("B", "Game B")])
    received = _collect(screen.game_selected)
    assert not screen._confirm_button.isEnabled()

    screen.select_game("A")
    screen.select_game("B")
    assert screen.selected_game_id() == "B"
    assert not screen._tiles["A"].isChecked()

    screen._confirm_button.click()
    assert received == [("B",)]


def test_minigame_select_set_games_rebuilds(qapp):
    screen = MinigameSelectScreen([GameSummary("A", "Game A")])
    screen.select_game("A")
    screen.set_games([GameSummary("C", "Game C")])
    assert screen.game_ids() == ["C"]
    assert screen.selected_game_id() is None
    assert not screen._confirm_button.isEnabled()


# --- difficulty modal ---


def test_difficulty_modal_covers_host_and_confirms(qapp):
    host = QWidget()
    host.resize(400, 300)
    host.show()  # hidden widgets defer resize events
    modal = DifficultyModal()
    received = _collect(modal.difficulty_confirmed)

    modal.open_over(host)
    assert modal.parentWidget() is host
    assert modal.geometry() == host.rect()
    assert not modal.isHidden()

    host.resize(500, 350)
    assert modal.geometry() == host.rect()

    assert modal.levels() == sorted(DIFFICULTY_PRESETS)
    assert modal.button_for(4).text() == "Trudne"
    modal.button_for(4).click()
    assert received == [(4,)]
    assert modal.isHidden()


def test_difficulty_modal_escape_goes_back(qapp):
    host = QWidget()
    modal = DifficultyModal()
    received = _collect(modal.back_requested)
    modal.open_over(host)
    QTest.keyClick(modal, Qt.Key.Key_Escape)
    assert received == [()]
    assert modal.isHidden()


# --- gameplay ---


def test_gameplay_hud_setters(qapp):
    screen = GameplayScreen(lives=3)
    screen.set_points(7)
    screen.set_time_remaining(65)
    screen.set_lives(1)
    assert screen.points_text() == "Punkty 007"
    assert screen.timer_text() == "Czas: 01:05"
    assert screen.hearts_text() == HEART_FULL + HEART_EMPTY * 2


def test_gameplay_pause_toggles(qapp):
    screen = GameplayScreen()
    received = _collect(screen.pause_toggled)
    screen._pause_button.click()
    screen._pause_button.click()
    assert received == [(True,), (False,)]
    assert not screen.is_paused()


def test_gameplay_reset_and_game_widget(qapp):
    screen = GameplayScreen(lives=5)
    screen.set_points(40)
    screen.set_paused(True)
    screen.reset(lives=2, seconds=30)
    assert screen.hearts_text() == HEART_FULL * 2
    assert screen.points_text() == "Punkty 000"
    assert not screen.is_paused()

    screen.set_preview_visible(False)
    assert not screen.is_preview_visible()
    screen._preview_button.click()
    assert screen.is_preview_visible()

    game_view = QWidget()
    screen.set_game_widget(game_view)
    assert game_view.parentWidget() is screen._gameplay_area
    assert screen._placeholder.isHidden()
    screen.set_game_widget(None)
    assert not screen._placeholder.isHidden()


# --- game over ---


def test_game_over_shows_result(qapp):
    now = datetime.now(UTC)
    result = GameResult(
        session_id=uuid4(),
        game_id=ExampleGestureGame.GAME_ID,
        final_state=GameState.FINISHED,
        end_reason=GameEndReason.COMPLETED,
        player_results={
            PlayerId.PLAYER_1: PlayerGameState(
                PlayerId.PLAYER_1, score=3, current_step=3, mistakes=1
            )
        },
        started_at=now,
        finished_at=now,
        duration_ms=65_000,
    )
    screen = GameOverScreen()
    screen.show_result(result)
    assert screen.result() is result
    assert screen.value_text("points") == "3"
    assert screen.value_text("accuracy") == "75%"
    assert screen.value_text("time") == "1:05"


def test_game_over_buttons(qapp):
    screen = GameOverScreen()
    menu = _collect(screen.back_to_menu_requested)
    replay = _collect(screen.play_again_requested)
    assert screen._menu_button.text() == "Powrót do wyboru gier"
    screen._menu_button.click()
    screen._replay_button.click()
    assert menu == [()] and replay == [()]


def test_game_over_ignores_non_results(qapp):
    screen = GameOverScreen()
    screen.show_result("nope")
    assert screen.result() is None
    assert screen.value_text("points") == "--"


# --- main window flow ---


def test_main_window_game_flow(qapp):
    from handgame.gui.main_window import MainWindow

    window = MainWindow()
    current = window.router.currentWidget

    window.main_menu_screen.ui.playButton.click()
    assert current() is window.camera_select_screen

    window.camera_select_screen._ok_button.click()
    assert current() is window.calibration_screen

    window.calibration_screen._skip_button.click()
    assert current() is window.minigame_select_screen

    window.minigame_select_screen.game_selected.emit(ExampleGestureGame.GAME_ID)
    assert window.difficulty_modal.parentWidget() is window.centralWidget()
    window.difficulty_modal.button_for(2).click()
    assert current() is window.gameplay_screen
    assert window.gameplay_screen.hearts_text() == HEART_FULL * (
        DIFFICULTY_PRESETS[2].allowed_mistakes
    )

    now = datetime.now(UTC)
    window.show_game_result(
        GameResult(
            session_id=uuid4(),
            game_id=ExampleGestureGame.GAME_ID,
            final_state=GameState.FINISHED,
            end_reason=GameEndReason.COMPLETED,
            player_results={PlayerId.PLAYER_1: PlayerGameState(PlayerId.PLAYER_1)},
            started_at=now,
            finished_at=now,
            duration_ms=0,
        )
    )
    assert current() is window.game_over_screen
    assert window.router.currentIndex() == Screen.GAME_OVER.value


class _FakeController(QObject):
    """Just the GUIIntegrationController surface MainWindow uses."""

    ui_frame_ready = Signal(object)
    ui_camera_status_changed = Signal(object)
    ui_game_finished = Signal(object)

    def __init__(self):
        super().__init__()
        self.calls = []

    def __getattr__(self, name):
        if name.startswith("_") or name in ("calls",):
            raise AttributeError(name)
        return lambda *args: self.calls.append((name, *args))


def test_main_window_uses_controller(qapp):
    from handgame.core.events import CameraStatusEvent, FramePacket
    from handgame.core.models import CameraState
    from handgame.gui.main_window import MainWindow

    controller = _FakeController()
    window = MainWindow(controller)

    window.camera_select_screen._ok_button.click()
    assert ("select_camera", "CAMERA_1", "PLAYER_1") in controller.calls
    assert window.calibration_screen.state() is CalibrationState.CONNECTING

    controller.ui_camera_status_changed.emit(
        CameraStatusEvent(CameraId.CAMERA_1, CameraState.READY, CameraState.STREAMING)
    )
    assert window.calibration_screen.state() is CalibrationState.DETECTING

    # Mock frames (not an image) keep the placeholder; real ndarray frames show.
    controller.ui_frame_ready.emit(FramePacket(CameraId.CAMERA_1, 1, "MOCK_NDARRAY_DATA"))
    assert not window.calibration_screen.preview.has_frame()
    controller.ui_frame_ready.emit(
        FramePacket(CameraId.CAMERA_1, 2, np.zeros((4, 4, 3), dtype=np.uint8))
    )
    assert window.calibration_screen.preview.has_frame()

    controller.ui_camera_status_changed.emit(
        CameraStatusEvent(CameraId.CAMERA_1, CameraState.STREAMING, CameraState.ERROR)
    )
    assert window.calibration_screen.state() is CalibrationState.CAMERA_ERROR

    window.calibration_screen._skip_button.click()
    window.minigame_select_screen.game_selected.emit(ExampleGestureGame.GAME_ID)
    window.difficulty_modal.button_for(1).click()
    assert ("prepare_game", ExampleGestureGame.GAME_ID, 1) in controller.calls
    assert ("start_game",) in controller.calls

    window.gameplay_screen._pause_button.click()
    assert controller.calls[-1] == ("pause_game",)

    window.gameplay_screen.exit_requested.emit()
    assert controller.calls[-1] == ("finish_game",)
    assert window.router.currentWidget() is window.minigame_select_screen


def test_back_from_game_over_skips_finished_game(qapp):
    from handgame.gui.main_window import MainWindow

    window = MainWindow()
    window.change_screen(Screen.GAME_SELECT)
    window.minigame_select_screen.game_selected.emit(ExampleGestureGame.GAME_ID)
    window.difficulty_modal.button_for(3).click()
    assert window.router.currentWidget() is window.gameplay_screen

    window.show_game_result(object())  # not a GameResult: screen still switches
    assert window.router.currentWidget() is window.game_over_screen

    window.ui.backButton.click()
    assert window.router.currentWidget() is window.minigame_select_screen
