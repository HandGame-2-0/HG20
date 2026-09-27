"""Runtime configuration for the camera / recognition backends.

Defaults target real hardware; every value can be overridden with a
``HANDGAME_*`` environment variable (e.g. ``HANDGAME_CAMERA_BACKEND=mock``
runs the app without a webcam).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from handgame.core.models import CameraId

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = PROJECT_ROOT / "models"

CAMERA_BACKEND_OPENCV = "opencv"
CAMERA_BACKEND_MOCK = "mock"
ALGORITHM_MEDIAPIPE_PJM_STATIC = "MEDIAPIPE_PJM_STATIC"
ALGORITHM_MOCK = "MOCK_YOLO"


def _default_device_index() -> dict[CameraId, int]:
    return {CameraId.CAMERA_1: 0, CameraId.CAMERA_2: 1}


@dataclass(frozen=True)
class AppConfig:
    camera_backend: str = CAMERA_BACKEND_OPENCV
    camera_device_index: Mapping[CameraId, int] = field(default_factory=_default_device_index)
    camera_fps: int = 30
    camera_mirror: bool = True
    default_algorithm: str = ALGORITHM_MEDIAPIPE_PJM_STATIC
    hand_model_path: Path = MODELS_DIR / "hand_landmarker.task"
    # Bundled with the repo. ``.onnx`` -> PP2Project net, other ``.joblib`` ->
    # sklearn letter classifier.
    letter_model_path: Path = MODELS_DIR / "pjm_static_letters.joblib"
    # A letter is reported only after it has been the top prediction for this
    # many consecutive frames (1 = report every frame).
    stable_frames: int = 5

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> AppConfig:
        env = os.environ if env is None else env
        defaults = cls()
        device_index = dict(defaults.camera_device_index)
        for index, camera in enumerate(CameraId, start=1):
            value = env.get(f"HANDGAME_CAMERA_INDEX_{index}")
            if value is not None:
                device_index[camera] = int(value)
        return cls(
            camera_backend=env.get("HANDGAME_CAMERA_BACKEND", defaults.camera_backend).lower(),
            camera_device_index=device_index,
            camera_fps=int(env.get("HANDGAME_CAMERA_FPS", defaults.camera_fps)),
            camera_mirror=_parse_bool(env.get("HANDGAME_CAMERA_MIRROR"), defaults.camera_mirror),
            default_algorithm=env.get("HANDGAME_ALGORITHM", defaults.default_algorithm),
            hand_model_path=Path(env.get("HANDGAME_HAND_MODEL", defaults.hand_model_path)),
            letter_model_path=Path(env.get("HANDGAME_LETTER_MODEL", defaults.letter_model_path)),
            stable_frames=max(1, int(env.get("HANDGAME_STABLE_FRAMES", defaults.stable_frames))),
        )


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")
