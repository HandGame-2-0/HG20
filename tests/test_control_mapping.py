"""Pure function tests for resolve_virtual_button."""

from handgame.core.models import VirtualButton
from handgame.games.control_mapping import resolve_virtual_button


def test_none_sign_resolves_to_none():
    assert resolve_virtual_button(None, {"A": VirtualButton.CONFIRM}) is None


def test_empty_mapping_resolves_to_none():
    assert resolve_virtual_button("A", {}) is None


def test_known_sign_resolves_to_mapped_button():
    mapping = {"A": VirtualButton.CONFIRM}
    assert resolve_virtual_button("A", mapping) == VirtualButton.CONFIRM


def test_unmapped_sign_resolves_to_none_not_keyerror():
    mapping = {"A": VirtualButton.CONFIRM}
    assert resolve_virtual_button("Z", mapping) is None
