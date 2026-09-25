"""
Turn a ``FramePacket.frame`` into a ``QImage`` for on-screen preview.
"""

from __future__ import annotations

import numpy as np
from PySide6.QtGui import QImage


def frame_to_qimage(frame: object) -> QImage | None:
    """BGR (H, W, 3) or grayscale (H, W) ``uint8`` array -> detached ``QImage``."""
    if not isinstance(frame, np.ndarray) or frame.dtype != np.uint8 or frame.size == 0:
        return None
    if frame.ndim == 2:
        image_format = QImage.Format.Format_Grayscale8
    elif frame.ndim == 3 and frame.shape[2] == 3:
        image_format = QImage.Format.Format_BGR888
    else:
        return None

    frame = np.ascontiguousarray(frame)
    height, width = frame.shape[:2]
    image = QImage(frame.data, width, height, frame.strides[0], image_format)
    # QImage only borrows the numpy buffer - copy so it outlives the frame.
    return image.copy()
