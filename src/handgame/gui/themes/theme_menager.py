from __future__ import annotations
import logging
from pathlib import Path
from string import Template
from PySide6.QtCore import QObject, QSettings, Signal, Slot
from PySide6.QtWidgets import QApplication
from handgame.gui.themes.palettes import (
    DEFAULT_THEME,
    PALETTES,
    ThemeId,
    ThemeToken,
    get_tokens,
)
logger = logging.getLogger("HandGame2")
_SETTINGS_KEY = "ui/theme"
_DEFAULT_TEMPLATE = """\
QWidget {
    background-color: $background;
    color: $text;
    font-family: "$font_family";
    font-size: ${font_size_px}px;
}
QMainWindow, QStackedWidget {
    background-color: $background;
}
QPushButton {
    background-color: $accent;
    color: $accent_text;
    border: 1px solid $border;
    padding: 6px 12px;
}
QPushButton:hover {
    background-color: $surface;
    color: $text;
}
QComboBox, QSpinBox, QLineEdit, QCheckBox {
    background-color: $surface;
    color: $text;
    border: 1px solid $border;
}
QLabel {
    color: $text;
    background-color: transparent;
}
"""
class ThemeManager(QObject):
    theme_changed = Signal(object)  # ThemeId

    def __init__(
        self,
        settings: QSettings | None = None,
        template: str | None = None,
        template_path: Path | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings or QSettings("HandGame", "HandGame2")
        self._template = self._resolve_template(template, template_path)
        self._current = self._load_saved_theme()
    @property
    def current_theme(self) -> ThemeId:
        return self._current
    
    def available_themes(self) -> list[ThemeId]:
        return list(PALETTES)

    @staticmethod
    def render_stylesheet(tokens: ThemeToken, template: str) -> str:
        return Template(template).substitute(tokens.as_template_mapping())

    @Slot(object)
    def apply(self, theme_id: ThemeId | str, persist: bool = True) -> None:
        resolved = theme_id if isinstance(theme_id, ThemeId) else ThemeId(theme_id)
        tokens = get_tokens(resolved)
        stylesheet = self.render_stylesheet(tokens, self._template)
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("QApplication must exist before applying a theme.")
        app.setStyleSheet(stylesheet)
        self._current = resolved
        if persist:
            self._settings.setValue(_SETTINGS_KEY, resolved.value)
        logger.info("Zastosowano motyw: %s", resolved.value)
        self.theme_changed.emit(resolved)

    def apply_saved(self) -> None:
        self.apply(self._current, persist=False)

    def _load_saved_theme(self) -> ThemeId:
        raw = self._settings.value(_SETTINGS_KEY, DEFAULT_THEME.value)
        try:
            return ThemeId(str(raw))
        except ValueError:
            logger.warning("Nieznany motyw %r, używam %s", raw, DEFAULT_THEME.value)
            return DEFAULT_THEME

    def _resolve_template(self, template: str | None, template_path: Path | None) -> str:
        if template is not None:
            return template
        if template_path is not None:
            return template_path.read_text(encoding="utf-8")
        return _DEFAULT_TEMPLATE