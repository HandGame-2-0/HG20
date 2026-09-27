"""Camera preview: detection zone and MediaPipe hand overlay."""

from PySide6.QtGui import QPixmap

from handgame.gui.widgets.camera_preview import (
    HAND_CONNECTIONS,
    CameraPreviewWidget,
    point_in_zone,
)


def test_point_in_zone_covers_the_middle_of_the_frame():
    assert point_in_zone(0.5, 0.5)
    assert point_in_zone(0.3, 0.3)
    assert not point_in_zone(0.0, 0.0)
    assert not point_in_zone(1.0, 1.0)


def test_hand_connections_cover_all_twenty_one_landmarks():
    used = {index for pair in HAND_CONNECTIONS for index in pair}
    assert used == set(range(21))


def test_hand_overlay_stores_skeleton_and_letter(qapp):
    preview = CameraPreviewWidget()
    points = tuple((index / 20, 0.5) for index in range(21))
    preview.set_hand_overlay(points, "A 87%")
    assert preview.has_hand_overlay()
    assert preview.hand_label() == "A 87%"
    preview.clear_hand_overlay()
    assert not preview.has_hand_overlay()
    assert preview.hand_label() is None


def test_clear_frame_also_clears_the_hand_overlay(qapp):
    preview = CameraPreviewWidget()
    preview.update_frame(QPixmap(8, 8))
    preview.set_hand_overlay(((0.5, 0.5),), "B")
    preview.clear_frame()
    assert not preview.has_frame()
    assert not preview.has_hand_overlay()
