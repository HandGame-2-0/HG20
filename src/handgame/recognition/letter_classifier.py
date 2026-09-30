"""Pluggable letter classifier: detected hand -> (letter, probability).

``MediaPipeLetterWorker`` depends only on the ``LetterClassifier`` protocol,
so models can be swapped without touching the worker. Each classifier derives
its own features from the ``HandDetection``.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from handgame.recognition.hand_landmarker import HandDetection
from handgame.recognition.landmark_features import (
    FEATURE_VERSION,
    HAND_GEOMETRY_VERSION,
    PALM_VOLUME_VERSION,
    hand_geometry_features,
    landmarks_to_features,
    palm_volume_features,
)


class LetterClassifier(Protocol):
    def predict(self, hand: HandDetection) -> tuple[str, float]:
        """Return the most likely letter and its probability in ``[0, 1]``."""
        ...


def load_letter_classifier(path: Path) -> LetterClassifier:
    """``.onnx`` -> OnnxDistanceLetterClassifier, anything else -> sklearn bundle."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Letter model not found: {path}")
    if path.suffix.lower() == ".onnx":
        return OnnxDistanceLetterClassifier.load(path)
    return SklearnLetterClassifier.load(path)


# ---------------------------------------------------------------- features

FEATURES_LANDMARKS = "landmarks"  # 63 image-landmark coordinates
FEATURES_PALM_VOLUMES = "palm_volumes"  # 18 palm-plane volumes from world landmarks
FEATURES_HAND_GEOMETRY = "hand_geometry"  # palm volumes + 210 world distances


def _from_world(
    function: Callable[[np.ndarray, str | None], np.ndarray],
) -> Callable[[HandDetection], np.ndarray]:
    def extract(hand: HandDetection) -> np.ndarray:
        if hand.world_landmarks is None:
            raise ValueError(f"{function.__name__} needs world landmarks")
        return function(hand.world_landmarks, hand.handedness)

    return extract


FEATURE_EXTRACTORS: dict[str, Callable[[HandDetection], np.ndarray]] = {
    FEATURES_LANDMARKS: lambda hand: landmarks_to_features(hand.landmarks, hand.handedness),
    FEATURES_PALM_VOLUMES: _from_world(palm_volume_features),
    FEATURES_HAND_GEOMETRY: _from_world(hand_geometry_features),
}
FEATURE_VERSIONS: dict[str, int] = {
    FEATURES_LANDMARKS: FEATURE_VERSION,
    FEATURES_PALM_VOLUMES: PALM_VOLUME_VERSION,
    FEATURES_HAND_GEOMETRY: HAND_GEOMETRY_VERSION,
}


# ---------------------------------------------------------- pretrained ONNX

# Class order of the pretrained PJM model from github.com/worthy11/PP2Project
# (data/net/pjmrecognizer.onnx, labels in src/model.cpp).
PP2_LABELS: tuple[str, ...] = tuple("ABCDEFGHIKLMNOPRSUWYZ")
_PP2_EPS = 1e-7


def pairwise_distance_features(landmarks: np.ndarray) -> np.ndarray:
    """(21, 3) image landmarks -> 441 pairwise 2D distances, normalized per
    axis by the hand bounding box (port of PP2Project ``ComputeDistances``).

    Translation, per-axis scale and x-mirroring cancel out, so pixel, raw
    normalized or ``landmarks_to_features`` coordinates all give the same result.
    """
    points = np.asarray(landmarks, dtype=np.float64).reshape(-1, 3)
    x, y = points[:, 0], points[:, 1]
    dx = (x[np.newaxis, :] - x[:, np.newaxis]) / (np.ptp(x) + _PP2_EPS)
    dy = (y[np.newaxis, :] - y[:, np.newaxis]) / (np.ptp(y) + _PP2_EPS)
    return np.sqrt(dx**2 + dy**2).reshape(-1)


class OnnxDistanceLetterClassifier:
    """Pretrained PJM letter net (441 distances -> softmax) run with ``cv2.dnn``.

    Must be created in the thread that uses it (``cv2.dnn.Net`` is not
    thread-safe) - the worker does this in ``start()``.
    """

    def __init__(self, net: Any, labels: Sequence[str] = PP2_LABELS) -> None:
        self._net = net
        self.labels = list(labels)

    @classmethod
    def load(cls, path: Path, labels: Sequence[str] = PP2_LABELS) -> OnnxDistanceLetterClassifier:
        import cv2

        return cls(cv2.dnn.readNetFromONNX(str(path)), labels)

    def predict(self, hand: HandDetection) -> tuple[str, float]:
        distances = pairwise_distance_features(hand.landmarks).reshape(1, -1)
        self._net.setInput(distances)
        probabilities = np.asarray(self._net.forward()).reshape(-1)
        if probabilities.shape[0] != len(self.labels):
            raise ValueError(
                f"Model returned {probabilities.shape[0]} classes, expected {len(self.labels)}"
            )
        best = int(np.argmax(probabilities))
        return self.labels[best], float(np.clip(probabilities[best], 0.0, 1.0))


# ------------------------------------------------------------------ sklearn


class SklearnLetterClassifier:
    """Wraps any fitted sklearn estimator exposing ``predict_proba``/``classes_``."""

    def __init__(
        self,
        model: Any,
        feature_kind: str = FEATURES_LANDMARKS,
        feature_version: int | None = None,
    ) -> None:
        if not hasattr(model, "predict_proba"):
            raise TypeError("Letter model must implement predict_proba()")
        if feature_kind not in FEATURE_EXTRACTORS:
            raise ValueError(f"Unknown feature kind {feature_kind!r}")
        self.model = model
        self.feature_kind = feature_kind
        self.feature_version = (
            FEATURE_VERSIONS[feature_kind] if feature_version is None else feature_version
        )
        self._extract = FEATURE_EXTRACTORS[feature_kind]

    @property
    def labels(self) -> Sequence[str]:
        return [str(label) for label in self.model.classes_]

    def predict(self, hand: HandDetection) -> tuple[str, float]:
        vector = np.asarray(self._extract(hand), dtype=np.float32).reshape(1, -1)
        probabilities = self.model.predict_proba(vector)[0]
        best = int(np.argmax(probabilities))
        confidence = float(np.clip(probabilities[best], 0.0, 1.0))
        return str(self.model.classes_[best]), confidence

    def save(self, path: Path) -> None:
        import joblib

        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "model": self.model,
                "feature_kind": self.feature_kind,
                "feature_version": self.feature_version,
                "labels": self.labels,
            },
            path,
        )

    @classmethod
    def load(cls, path: Path) -> SklearnLetterClassifier:
        import joblib

        bundle = joblib.load(path)
        if not isinstance(bundle, dict) or "model" not in bundle:
            raise ValueError(f"{path} is not a HandGame letter model bundle")
        kind = bundle.get("feature_kind", FEATURES_LANDMARKS)
        if kind not in FEATURE_VERSIONS:
            raise ValueError(f"{path} uses unknown feature kind {kind!r}")
        version = bundle.get("feature_version")
        if version != FEATURE_VERSIONS[kind]:
            raise ValueError(
                f"{path} was trained on {kind} feature version {version}, "
                f"runtime uses {FEATURE_VERSIONS[kind]} - retrain the model"
            )
        return cls(bundle["model"], feature_kind=kind, feature_version=version)
