"""App-wide stylesheet"""

from __future__ import annotations

from importlib.resources import files

from PySide6.QtWidgets import QApplication


def load_stylesheet() -> str:
    return files("handgame.gui").joinpath("styles/styles.qss").read_text(encoding="utf-8")


def apply_theme(app: QApplication) -> None:
    app.setStyleSheet(load_stylesheet())
