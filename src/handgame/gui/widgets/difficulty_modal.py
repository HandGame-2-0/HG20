"""Difficulty picker - wireframe.

A card over a dimmed screen with one full-width button per level; clicking a
level confirms it straight away. There is no back button in the wireframe, so
Esc or a click on the dimmed backdrop outside the card goes back.

It is an in-window overlay (a child widget covering its host) rather than a
separate top-level ``QDialog`` - a dialog is its own window and cannot dim the
screen behind it. Being on top of its host, the overlay also swallows every
click meant for the widgets underneath, which gives the same "modal" behaviour.

Levels come from ``DIFFICULTY_PRESETS`` (1-5).
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget

from handgame.games.game_context import DIFFICULTY_PRESETS
from handgame.gui.screens.common import make_card, make_stack_button

LEVEL_LABELS: dict[int, str] = {
    1: "Bardzo łatwe",
    2: "Łatwe",
    3: "Normalne",
    4: "Trudne",
    5: "Bardzo trudne",
}


class DifficultyModal(QFrame):
    """Dimmed overlay with a column of level buttons. Show it with ``open_over(host)``."""

    difficulty_confirmed = Signal(int)  # DifficultyProfile.level
    back_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ModalBackdrop")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.hide()

        levels = sorted(DIFFICULTY_PRESETS)
        missing = set(levels) - set(LEVEL_LABELS)
        if missing:
            raise ValueError(f"LEVEL_LABELS has no label for levels {sorted(missing)}")

        self._card, card_layout = make_card()
        self._card.setObjectName("ModalCard")

        heading = QLabel("Poziom trudności")
        heading.setObjectName("SectionHeading")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(heading)

        self._buttons: dict[int, QPushButton] = {}
        for level in levels:
            button = make_stack_button(LEVEL_LABELS[level])
            button.clicked.connect(lambda _checked=False, lvl=level: self._on_confirm(lvl))
            card_layout.addWidget(button)
            self._buttons[level] = button

        outer = QVBoxLayout(self)
        outer.addWidget(self._card, alignment=Qt.AlignmentFlag.AlignCenter)

    # --- showing / hiding ---

    def open_over(self, host: QWidget) -> None:
        """Cover ``host`` entirely and focus the middle level."""
        if self.parentWidget() is not None:
            self.parentWidget().removeEventFilter(self)
        self.setParent(host)
        host.installEventFilter(self)
        self.setGeometry(host.rect())
        self.show()
        self.raise_()
        levels = sorted(self._buttons)
        self._buttons[levels[len(levels) // 2]].setFocus()

    def close_overlay(self) -> None:
        if self.parentWidget() is not None:
            self.parentWidget().removeEventFilter(self)
        self.hide()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802 - Qt override
        if watched is self.parentWidget() and event.type() == QEvent.Type.Resize:
            self.setGeometry(self.parentWidget().rect())
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 - Qt override
        if event.key() == Qt.Key.Key_Escape:
            self._on_back()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt override
        if not self._card.geometry().contains(event.position().toPoint()):
            self._on_back()
        else:
            super().mousePressEvent(event)

    # --- helpers (tests / integration) ---

    def levels(self) -> list[int]:
        return list(self._buttons)

    def button_for(self, level: int) -> QPushButton:
        return self._buttons[level]

    def _on_back(self) -> None:
        self.close_overlay()
        self.back_requested.emit()

    def _on_confirm(self, level: int) -> None:
        self.close_overlay()
        self.difficulty_confirmed.emit(level)
