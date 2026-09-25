"""frame_to_qimage: camera FramePacket.frame -> QImage for the preview."""

import numpy as np
import pytest

from handgame.gui.frame_convert import frame_to_qimage


def test_bgr_frame_converts(qapp):
    frame = np.zeros((4, 6, 3), dtype=np.uint8)
    frame[..., 2] = 255  # red in BGR
    image = frame_to_qimage(frame)
    assert image is not None
    assert (image.width(), image.height()) == (6, 4)
    assert image.pixelColor(0, 0).red() == 255


def test_grayscale_frame_converts(qapp):
    image = frame_to_qimage(np.full((4, 4), 128, dtype=np.uint8))
    assert image is not None
    assert image.pixelColor(0, 0).red() == 128


def test_non_contiguous_frame_converts(qapp):
    frame = np.zeros((8, 8, 3), dtype=np.uint8)[::2, ::2]
    image = frame_to_qimage(frame)
    assert image is not None and image.width() == 4


@pytest.mark.parametrize(
    "frame",
    [
        "MOCK_NDARRAY_DATA",
        None,
        np.zeros((4, 4, 3), dtype=np.float32),
        np.zeros((4, 4, 4), dtype=np.uint8),
        np.zeros((0, 0, 3), dtype=np.uint8),
    ],
)
def test_non_images_return_none(frame):
    assert frame_to_qimage(frame) is None
