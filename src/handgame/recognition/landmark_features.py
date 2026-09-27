"""Hand landmarks -> fixed-size feature vectors for letter classifiers.

Pure numpy. Bump the matching ``*_VERSION`` whenever a transformation changes;
stored models record the feature kind and version they were trained with.
"""

from __future__ import annotations

import numpy as np

FEATURE_VERSION = 1
NUM_LANDMARKS = 21
FEATURE_SIZE = NUM_LANDMARKS * 3
WRIST = 0

LEFT_HAND = "Left"
RIGHT_HAND = "Right"

PALM_VOLUME_VERSION = 1
PALM_BASE_POINTS = (0, 5, 17)  # wrist, index MCP, pinky MCP
PALM_VOLUME_POINTS = tuple(i for i in range(NUM_LANDMARKS) if i not in PALM_BASE_POINTS)
PALM_VOLUME_SIZE = len(PALM_VOLUME_POINTS)

HAND_GEOMETRY_VERSION = 1
_PAIRS = np.triu_indices(NUM_LANDMARKS, k=1)
HAND_GEOMETRY_SIZE = PALM_VOLUME_SIZE + len(_PAIRS[0])  # 18 + 210


def landmarks_to_features(landmarks: np.ndarray, handedness: str | None = None) -> np.ndarray:
    """(21, 3) landmarks in pixel units -> (63,) float32 features.

    Invariant to hand position and size in the frame; left hands are mirrored
    onto the right-hand layout so one model covers both hands.
    """
    points = np.asarray(landmarks, dtype=np.float64)
    if points.shape != (NUM_LANDMARKS, 3):
        raise ValueError(f"Expected ({NUM_LANDMARKS}, 3) landmarks, got {points.shape}")

    points = points - points[WRIST]
    if handedness == LEFT_HAND:
        points[:, 0] = -points[:, 0]

    scale = float(np.max(np.linalg.norm(points[:, :2], axis=1)))
    if scale > 0.0:
        points = points / scale
    return points.reshape(-1).astype(np.float32)


def palm_volume_features(
    world_landmarks: np.ndarray, handedness: str | None = None
) -> np.ndarray:
    """(21, 3) MediaPipe world landmarks -> (18,) float32 signed volumes.

    Method from github.com/MagMat03/handgesture: for every non-base point
    ``p_i`` the signed volume of the tetrahedron ``(p0, p5, p17, p_i)``, i.e.
    how far and on which side of the palm plane the point lies, divided by
    ``|p17 - p5|^3`` (palm width). Invariant to position, rotation and hand
    size. Mirroring flips every sign, so left hands are negated to share one
    model with right hands.
    """
    points = np.asarray(world_landmarks, dtype=np.float64)
    if points.shape != (NUM_LANDMARKS, 3):
        raise ValueError(f"Expected ({NUM_LANDMARKS}, 3) landmarks, got {points.shape}")

    p0, p5, p17 = (points[i] for i in PALM_BASE_POINTS)
    normal = np.cross(p5 - p0, p17 - p0)
    volumes = (points[list(PALM_VOLUME_POINTS)] - p0) @ normal / 6.0
    palm_width = float(np.linalg.norm(p17 - p5))
    if palm_width > 0.0:
        volumes = volumes / palm_width**3
    if handedness == LEFT_HAND:
        volumes = -volumes
    return volumes.astype(np.float32)


def hand_geometry_features(
    world_landmarks: np.ndarray, handedness: str | None = None
) -> np.ndarray:
    """(21, 3) world landmarks -> (228,) float32: ``palm_volume_features`` plus
    all 210 pairwise 3D distances divided by palm width.

    The distances separate letters that differ mainly in how close fingertips
    are (O / S / T), which the volumes alone confuse. Used by the bundled
    ``models/pjm_static_letters.joblib``.
    """
    volumes = palm_volume_features(world_landmarks, handedness)
    points = np.asarray(world_landmarks, dtype=np.float64)
    distances = np.linalg.norm(points[_PAIRS[0]] - points[_PAIRS[1]], axis=1)
    palm_width = float(np.linalg.norm(points[17] - points[5]))
    if palm_width > 0.0:
        distances = distances / palm_width
    return np.concatenate([volumes, distances.astype(np.float32)])
