"""Backend/algorithm registries, AppConfig and the letter classifiers."""

from pathlib import Path

import numpy as np
import pytest
from sklearn.neighbors import KNeighborsClassifier

from handgame.camera.camera_manager import CAMERA_BACKENDS, CameraManager
from handgame.camera.mock_camera_worker import MockCameraWorker
from handgame.camera.opencv_camera_worker import OpenCVCameraWorker
from handgame.core.config import AppConfig
from handgame.core.models import CameraId, InferenceState
from handgame.recognition.hand_landmarker import HandDetection
from handgame.recognition.inference_manager import ALGORITHM_REGISTRY, InferenceManager
from handgame.recognition.landmark_features import PALM_VOLUME_SIZE, landmarks_to_features
from handgame.recognition.letter_classifier import (
    FEATURES_LANDMARKS,
    FEATURES_PALM_VOLUMES,
    PP2_LABELS,
    OnnxDistanceLetterClassifier,
    SklearnLetterClassifier,
    load_letter_classifier,
    pairwise_distance_features,
)
from handgame.recognition.mediapipe_letter_worker import MediaPipeLetterWorker
from handgame.recognition.mock_inference_worker import MockInferenceWorker


def test_app_config_from_env_overrides_defaults(tmp_path):
    config = AppConfig.from_env(
        {
            "HANDGAME_CAMERA_BACKEND": "MOCK",
            "HANDGAME_CAMERA_INDEX_2": "4",
            "HANDGAME_CAMERA_MIRROR": "false",
            "HANDGAME_ALGORITHM": "MOCK_YOLO",
            "HANDGAME_LETTER_MODEL": str(tmp_path / "m.joblib"),
            "HANDGAME_STABLE_FRAMES": "0",
        }
    )
    assert config.camera_backend == "mock"
    assert config.camera_device_index == {CameraId.CAMERA_1: 0, CameraId.CAMERA_2: 4}
    assert config.camera_mirror is False
    assert config.default_algorithm == "MOCK_YOLO"
    assert config.letter_model_path == tmp_path / "m.joblib"
    assert config.stable_frames == 1


def test_camera_backend_registry_builds_configured_workers():
    config = AppConfig(camera_device_index={CameraId.CAMERA_1: 7}, camera_mirror=False)
    real = CAMERA_BACKENDS["opencv"](CameraId.CAMERA_1, None, config)
    assert isinstance(real, OpenCVCameraWorker) and real.device_index == 7
    assert isinstance(CAMERA_BACKENDS["mock"](CameraId.CAMERA_1, None, config), MockCameraWorker)


def test_unknown_camera_backend_is_rejected():
    with pytest.raises(ValueError):
        CameraManager(backend="nope")


def test_algorithm_registry_builds_workers():
    config = AppConfig()
    mock = ALGORITHM_REGISTRY["MOCK_YOLO"](CameraId.CAMERA_1, "MOCK_YOLO", config)
    letters = ALGORITHM_REGISTRY["MEDIAPIPE_PJM_STATIC"](
        CameraId.CAMERA_1, "MEDIAPIPE_PJM_STATIC", config
    )
    assert isinstance(mock, MockInferenceWorker)
    assert isinstance(letters, MediaPipeLetterWorker)


def test_unknown_algorithm_reports_error(qapp):
    mgr = InferenceManager(AppConfig())
    errors: list = []
    mgr.error_occurred.connect(errors.append)
    mgr.start_algorithm(CameraId.CAMERA_1, "NOPE")
    assert [e.code for e in errors] == ["INF_UNKNOWN_ALGORITHM"]
    assert not mgr.is_algorithm_running(CameraId.CAMERA_1)


def test_missing_model_files_surface_as_inference_error(qapp, qtbot, tmp_path, monkeypatch):
    def missing(path, **_kwargs):
        raise FileNotFoundError(path)

    monkeypatch.setattr(
        "handgame.recognition.hand_landmarker.ensure_hand_landmarker",
        missing,
    )
    config = AppConfig(
        hand_model_path=tmp_path / "missing.task",
        letter_model_path=tmp_path / "missing.joblib",
    )
    mgr = InferenceManager(config)
    errors: list = []
    mgr.error_occurred.connect(errors.append)
    try:
        mgr.start_algorithm(CameraId.CAMERA_1, "MEDIAPIPE_PJM_STATIC")
        qtbot.waitUntil(lambda: bool(errors), timeout=3_000)
        assert errors[0].code == "INF_MODEL_LOAD"
        assert not errors[0].recoverable
        assert mgr._states[CameraId.CAMERA_1] == InferenceState.ERROR
    finally:
        mgr.shutdown()


def _fitted_knn(size: int = 63) -> KNeighborsClassifier:
    rng = np.random.default_rng(0)
    features = np.vstack([rng.normal(-1, 0.1, (10, size)), rng.normal(1, 0.1, (10, size))])
    return KNeighborsClassifier(n_neighbors=3).fit(features, ["A"] * 10 + ["B"] * 10)


def _hand(seed: int = 0, world: bool = True) -> HandDetection:
    rng = np.random.default_rng(seed)
    return HandDetection(
        landmarks=rng.uniform(100, 300, (21, 3)),
        handedness="Right",
        handedness_score=0.9,
        world_landmarks=rng.normal(0, 0.05, (21, 3)) if world else None,
    )


def test_sklearn_classifier_roundtrip(tmp_path: Path):
    path = tmp_path / "letters.joblib"
    SklearnLetterClassifier(_fitted_knn()).save(path)

    loaded = SklearnLetterClassifier.load(path)
    letter, confidence = loaded.predict(_hand())
    assert loaded.labels == ["A", "B"]
    assert loaded.feature_kind == FEATURES_LANDMARKS
    assert letter in ("A", "B")
    assert 0.0 <= confidence <= 1.0


def test_sklearn_palm_volume_classifier_uses_world_landmarks(tmp_path: Path):
    path = tmp_path / "palm.joblib"
    SklearnLetterClassifier(_fitted_knn(PALM_VOLUME_SIZE), FEATURES_PALM_VOLUMES).save(path)

    loaded = load_letter_classifier(path)
    assert isinstance(loaded, SklearnLetterClassifier)
    assert loaded.feature_kind == FEATURES_PALM_VOLUMES
    letter, _ = loaded.predict(_hand())
    assert letter in ("A", "B")
    with pytest.raises(ValueError, match="world landmarks"):
        loaded.predict(_hand(world=False))


def test_sklearn_classifier_rejects_other_feature_version(tmp_path: Path):
    path = tmp_path / "old.joblib"
    SklearnLetterClassifier(_fitted_knn(), feature_version=0).save(path)
    with pytest.raises(ValueError, match="feature version"):
        SklearnLetterClassifier.load(path)


def _reference_pp2_distances(normalized_xy: np.ndarray) -> np.ndarray:
    x, y = normalized_xy[:, 0], normalized_xy[:, 1]
    width, height = x.max() - x.min(), y.max() - y.min()
    out = np.empty(441)
    for i in range(21):
        for j in range(21):
            dx = (x[j] - x[i]) / (width + 1e-7)
            dy = (y[j] - y[i]) / (height + 1e-7)
            out[i * 21 + j] = np.hypot(dx, dy)
    return out


def test_pairwise_distances_match_pp2_on_raw_mediapipe_coordinates():
    rng = np.random.default_rng(1)
    normalized = rng.uniform(0.2, 0.8, (21, 3))
    frame_w, frame_h = 640, 480
    pixels = normalized * [frame_w, frame_h, frame_w]

    reference = _reference_pp2_distances(normalized)
    distances = pairwise_distance_features(pixels)
    assert distances.shape == (441,)
    np.testing.assert_allclose(distances, reference, atol=1e-4)
    for handedness in ("Right", "Left"):
        features = landmarks_to_features(pixels, handedness)
        np.testing.assert_allclose(pairwise_distance_features(features), reference, atol=1e-4)


class _FakeNet:
    def __init__(self, output: np.ndarray) -> None:
        self.output = output
        self.inputs: list[np.ndarray] = []

    def setInput(self, blob: np.ndarray) -> None:  # noqa: N802 - cv2.dnn API
        self.inputs.append(blob)

    def forward(self) -> np.ndarray:
        return self.output


def test_onnx_classifier_returns_top_label_and_probability():
    probs = np.full((1, len(PP2_LABELS)), 0.01)
    probs[0, PP2_LABELS.index("W")] = 0.8
    net = _FakeNet(probs)
    classifier = OnnxDistanceLetterClassifier(net)

    letter, confidence = classifier.predict(_hand(2))
    assert (letter, confidence) == ("W", pytest.approx(0.8))
    assert net.inputs[0].shape == (1, 441)


def test_onnx_classifier_rejects_label_count_mismatch():
    classifier = OnnxDistanceLetterClassifier(_FakeNet(np.ones((1, 3)) / 3))
    with pytest.raises(ValueError, match="classes"):
        classifier.predict(_hand())


def test_load_letter_classifier_dispatches_on_suffix(tmp_path: Path):
    path = tmp_path / "letters.joblib"
    SklearnLetterClassifier(_fitted_knn()).save(path)
    assert isinstance(load_letter_classifier(path), SklearnLetterClassifier)

    with pytest.raises(FileNotFoundError, match="Letter model not found"):
        load_letter_classifier(tmp_path / "missing.onnx")
