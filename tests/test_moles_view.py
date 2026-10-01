"""MolesView hosting the unchanged MG widget (headless Qt)."""

import sys
from uuid import uuid4

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QLineEdit, QMainWindow

from handgame.core.models import PlayerId
from handgame.games.moles_game import MolesGame
from handgame.gui.game_views import MolesView


@pytest.fixture
def view(qapp):
    window = QMainWindow()
    view = MolesView()
    window.setCentralWidget(view)
    window.resize(1280, 720)
    window.show()
    events = []
    view.view_event.connect(events.append)
    yield view, window, events
    view.stop()
    window.close()


def _arm_mole(view, letter):
    game = view.game_widget
    game.GameState = type(game.GameState).PLAYING  # skip the intro animation
    tile = game.tile_manager.tiles[0]
    tile.start_cycle(letter=letter, wait_ms=5000, use_basket=False, basket_delay_ms=0)
    tile.show_letter = True


def test_mg_modules_do_not_leak_into_sys_modules(view):
    assert not [name for name in sys.modules if name == "config" or name.startswith("components")]


def test_begin_starts_round_at_level(view):
    view, _window, _events = view

    view.begin(uuid4(), PlayerId.PLAYER_1, 5)

    game = view.game_widget
    assert game.GameState.name == "STARTING"
    assert game.game_timer.duration_sec == 20  # "Ekspert" in difficulties.json


def test_letter_on_mole_is_hit_other_letter_is_miss(view):
    view, _window, events = view
    view.begin(uuid4(), PlayerId.PLAYER_1, 1)
    _arm_mole(view, "A")

    view.handle_letter("a")
    view.handle_letter("B")

    assert [e.action_type for e in events] == [
        MolesGame.ACTION_MOLE_HIT,
        MolesGame.ACTION_MOLE_MISS,
    ]
    assert events[0].payload["points"] == 10


def test_letters_ignored_while_paused(view):
    view, _window, events = view
    view.begin(uuid4(), PlayerId.PLAYER_1, 1)
    _arm_mole(view, "A")

    view.pause()
    view.handle_letter("A")

    assert events == []


def test_round_over_reported_on_mg_timeout(view):
    view, _window, events = view
    view.begin(uuid4(), PlayerId.PLAYER_1, 1)

    view.game_widget.game_timer.timeout_signal.emit()

    assert events[-1].action_type == MolesGame.ACTION_ROUND_OVER


def test_mg_key_filter_removed_and_exit_keeps_window(view):
    view, window, _events = view
    line = QLineEdit(window)
    line.show()

    QCoreApplication.sendEvent(
        line, QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_X, Qt.KeyboardModifier.NoModifier, "x")
    )
    view.game_widget._on_exit_game()

    assert line.text() == "x"  # MG's app-wide filter would have swallowed it
    assert window.isVisible()
