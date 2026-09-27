"""Thin wrapper over the MediaPipe Tasks ``HandLandmarker`` (VIDEO mode).

``mediapipe`` is imported lazily in ``MediaPipeHandDetector.__init__`` so the
rest of the app (and the test-suite) does not need it installed.
"""

from __future__ import annotations

import logging
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from handgame.recognition.landmark_features import NUM_LANDMARKS

logger = logging.getLogger(__name__)

HAND_LANDMARKER_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
)


@dataclass(frozen=True)
class HandDetection:
    landmarks: np.ndarray  # (21, 3), x/y in pixels, z scaled like x
    handedness: str | None  # "Left" / "Right" as reported by MediaPipe
    handedness_score: float
    world_landmarks: np.ndarray | None = None  # (21, 3) metres, origin between the MCPs


class HandDetector(Protocol):
    def detect(self, frame_bgr: Any, timestamp_ms: int) -> HandDetection | None: ...

    def close(self) -> None: ...


def ensure_hand_landmarker(
    path: Path,
    *,
    url: str = HAND_LANDMARKER_URL,
    fetch: Callable[[str, str], object] = urllib.request.urlretrieve,
) -> Path:
    """Return ``path``, downloading the official MediaPipe model if it is missing."""
    path = Path(path)
    if path.is_file():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".part")
    logger.info("Downloading hand landmarker to %s", path)
    try:
        fetch(url, str(partial))
        partial.replace(path)
    except Exception as exc:
        if partial.exists():
            partial.unlink()
        raise FileNotFoundError(
            f"Hand landmarker model not found: {path} (download from {url} failed)"
        ) from exc
    return path


def is_bgr_frame(frame: Any) -> bool:
    return (
        isinstance(frame, np.ndarray)
        and frame.dtype == np.uint8
        and frame.ndim == 3
        and frame.shape[2] == 3
        and frame.size > 0
    )


class MediaPipeHandDetector:
    """Detects a single hand; must be created and used from one thread."""

    def __init__(
        self,
        model_path: Path,
        *,
        min_detection_confidence: float = 0.5,
        min_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        model_path = ensure_hand_landmarker(Path(model_path))

        import cv2
        import mediapipe as mp
        from mediapipe.tasks.python import vision

        self._cv2 = cv2
        self._mp = mp
        options = vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=min_detection_confidence,
            min_hand_presence_confidence=min_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self._last_timestamp_ms = -1

    def detect(self, frame_bgr: Any, timestamp_ms: int) -> HandDetection | None:
        if not is_bgr_frame(frame_bgr):
            return None
        # VIDEO mode rejects non-increasing timestamps.
        timestamp_ms = max(int(timestamp_ms), self._last_timestamp_ms + 1)
        self._last_timestamp_ms = timestamp_ms

        rgb = self._cv2.cvtColor(frame_bgr, self._cv2.COLOR_BGR2RGB)
        image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect_for_video(image, timestamp_ms)
        if not result.hand_landmarks:
            return None

        height, width = frame_bgr.shape[:2]
        points = result.hand_landmarks[0]
        landmarks = np.array([[p.x * width, p.y * height, p.z * width] for p in points])
        if landmarks.shape != (NUM_LANDMARKS, 3):
            return None

        world = None
        if result.hand_world_landmarks:
            world = np.array([[p.x, p.y, p.z] for p in result.hand_world_landmarks[0]])
            if world.shape != (NUM_LANDMARKS, 3):
                world = None

        category = result.handedness[0][0] if result.handedness and result.handedness[0] else None
        return HandDetection(
            landmarks=landmarks,
            handedness=category.category_name if category is not None else None,
            handedness_score=float(category.score) if category is not None else 0.0,
            world_landmarks=world,
        )

    def close(self) -> None:
        self._landmarker.close()
