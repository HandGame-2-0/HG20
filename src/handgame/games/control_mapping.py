"""Pure function mapping a recognized sign to a VirtualButton.

No Qt or camera/recognition imports - safe to call from BaseGame._on_gesture.
"""

from __future__ import annotations

from collections.abc import Mapping

from handgame.core.models import VirtualButton


def resolve_virtual_button(
    recognized_sign: str | None,
    mapping: Mapping[str, VirtualButton],
) -> VirtualButton | None:
    if recognized_sign is None:
        return None
    return mapping.get(recognized_sign)
