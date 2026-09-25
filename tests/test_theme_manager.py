"""ThemeManager + palettes: every palette must render the shared QSS template."""

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor

from handgame.gui.themes.palettes import DEFAULT_THEME, NAVY, PALETTES, ThemeId
from handgame.gui.themes.theme_menager import ThemeManager
from handgame.gui.widgets.camera_preview import CameraPreviewWidget


@pytest.fixture
def manager(qapp, tmp_path):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    yield ThemeManager(settings=settings)
    qapp.setStyleSheet("")


def test_navy_is_the_default_theme():
    assert DEFAULT_THEME is ThemeId.NAVY
    assert PALETTES[DEFAULT_THEME] is NAVY


@pytest.mark.parametrize("theme_id", list(PALETTES))
def test_every_palette_fills_the_template(manager, theme_id):
    # Template.substitute raises KeyError on any token a palette can't provide.
    qss = ThemeManager.render_stylesheet(PALETTES[theme_id], manager._template)
    assert "$" not in qss
    assert "QPushButton#PrimaryButton" in qss
    assert 'CameraPreviewWidget[state="error"]' in qss


def test_apply_saves_choice_and_emits(manager):
    received = []
    manager.theme_changed.connect(received.append)

    manager.apply(ThemeId.DARK)

    assert manager.current_theme is ThemeId.DARK
    assert received == [ThemeId.DARK]
    assert manager._settings.value("ui/theme") == "dark"


def test_preview_zone_colours_follow_the_theme(qapp, manager):
    preview = CameraPreviewWidget()
    manager.apply(ThemeId.PROTANOPIA, persist=False)
    preview.ensurePolished()

    tokens = PALETTES[ThemeId.PROTANOPIA]
    assert preview.zoneErrorColor == QColor(tokens.error)
    assert preview.zoneLockedColor == QColor(tokens.success)
