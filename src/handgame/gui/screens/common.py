"""Shared building blocks for the screens translated from the Figma frames.

"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


CARD_PADDING = 24

BACK_TEXT = "\N{LEFTWARDS ARROW} powrót"
CONFIRM_PLAY_TEXT = "Zatwierdź / Graj"

CARD_MAX_WIDTH = 560


def init_screen(widget: QWidget) -> None:

    widget.setObjectName("Screen")
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)


def apply_card_padding(layout: QLayout) -> None:
    layout.setContentsMargins(CARD_PADDING, CARD_PADDING, CARD_PADDING, CARD_PADDING)


def make_title(text: str) -> QLabel:
    """H1 screen title (``QLabel#ScreenTitle``)."""
    label = QLabel(text)
    label.setObjectName("ScreenTitle")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label


def make_primary_button(text: str) -> QPushButton:
    """Accent button (``QPushButton#PrimaryButton``)."""
    button = QPushButton(text)
    button.setObjectName("PrimaryButton")
    return button


def make_card(title: str | None = None) -> tuple[QFrame, QVBoxLayout]:
    """Bordered card (``QFrame#PageCard``) with an optional H1 title inside."""
    card = QFrame()
    card.setObjectName("PageCard")
    card.setMaximumWidth(CARD_MAX_WIDTH)
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
    card_layout = QVBoxLayout(card)
    apply_card_padding(card_layout)
    card_layout.setSpacing(16)
    if title is not None:
        card_layout.addWidget(make_title(title))
    return card, card_layout


def center_in(layout: QVBoxLayout, widget: QWidget) -> None:
    """Add ``widget`` to ``layout`` centred both ways (stretch above and below)."""
    layout.addStretch(1)
    row = QHBoxLayout()
    row.addStretch(1)
    row.addWidget(widget, stretch=100)
    row.addStretch(1)
    layout.addLayout(row)
    layout.addStretch(1)


def make_stack_button(text: str) -> QPushButton:
    """Full-width option button inside a card (``QPushButton#StackButton``)."""
    button = QPushButton(text)
    button.setObjectName("StackButton")
    button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    return button


def make_footer(left: QWidget | None, right: QWidget | None) -> QHBoxLayout:
    """Bottom action row."""
    footer = QHBoxLayout()
    if left is not None:
        footer.addWidget(left)
    footer.addStretch(1)
    if right is not None:
        footer.addWidget(right)
    return footer


def set_dynamic_property(widget: QWidget, name: str, value: object) -> None:
    """Set a Qt dynamic property and force a stylesheet repolish."""
    widget.setProperty(name, value)
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()
