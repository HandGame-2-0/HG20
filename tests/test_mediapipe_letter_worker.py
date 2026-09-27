"""MediaPipeLetterWorker with fake detector/classifier - no mediapipe or model files."""

from uuid import uuid4

import numpy as np

from handgame.core.events import FramePacket
from handgame.core.models import CameraId, InferenceState, PlayerId
from handgame.recognition.hand_landmarker import HandDetection
from handgame.recognition.mediapipe_letter_worker import LetterStabilizer, MediaPipeLetterWorker

ALGORITHM = "MEDIAPIPE_PJM_STATIC"


class FakeDetector:
    def __init__(self):
        self.hand = True
        self.closed = False

    def detect(self, frame, timestamp_ms):
        if not self.hand:
            return None
        return HandDetection(np.random.default_rng(0).uniform(size=(21, 3)), "Right", 0.99)

    def close(self):
        self.closed = True


class FakeClassifier:
    def __init__(self):
        self.letter = "A"
        self.confidence = 0.87
        self.fail = False

    def predict(self, hand):
        assert isinstance(hand, HandDetection) and hand.landmarks.shape == (21, 3)
        if self.fail:
            raise RuntimeError("boom")
        return self.letter, self.confidence


def _packet() -> FramePacket:
    return FramePacket(CameraId.CAMERA_1, 0, np.zeros((4, 4, 3), np.uint8), PlayerId.PLAYER_1)


def _worker(stable_frames: int = 1, detector=None, classifier=None, fail_load: bool = False):
    detector = detector or FakeDetector()
    classifier = classifier or FakeClassifier()

    def classifier_factory():
        if fail_load:
            raise FileNotFoundError("models/pjm_static_letters.joblib")
        return classifier

    worker = MediaPipeLetterWorker(
        CameraId.CAMERA_1,
        ALGORITHM,
        stable_frames=stable_frames,
        detector_factory=lambda: detector,
        classifier_factory=classifier_factory,
    )
    got = {"events": [], "states": [], "errors": [], "finished": [], "hands": []}
    worker.gesture_recognized.connect(got["events"].append)
    worker.hand_tracked.connect(got["hands"].append)
    worker.status_changed.connect(lambda e: got["states"].append(e.current_state))
    worker.error_occurred.connect(got["errors"].append)
    worker.finished.connect(got["finished"].append)
    return worker, detector, classifier, got


def test_start_loads_models_and_becomes_ready(qapp):
    worker, _, _, got = _worker()
    worker.start()
    assert got["states"] == [InferenceState.STARTING, InferenceState.READY]


def test_recognized_letter_carries_confidence_and_correctness(qapp):
    worker, _, classifier, got = _worker()
    worker.start()
    session = uuid4()
    worker.set_expected_sign(str(session), "PLAYER_1", "A")

    worker.submit_frame(_packet())
    classifier.letter = "B"
    worker.submit_frame(_packet())

    first, second = got["events"]
    assert first.recognized_sign == "A"
    assert first.confidence == 0.87
    assert first.is_correct is True
    assert first.expected_sign == "A"
    assert first.session_id == session
    assert first.player_id == PlayerId.PLAYER_1
    assert first.algorithm_id == ALGORITHM
    assert first.latency_ms is not None and first.latency_ms >= 0
    assert second.recognized_sign == "B" and second.is_correct is False
    assert got["states"][-1] == InferenceState.READY


def test_no_expected_sign_leaves_is_correct_unknown(qapp):
    worker, _, _, got = _worker()
    worker.start()
    worker.submit_frame(_packet())
    assert got["events"][0].is_correct is None
    assert got["events"][0].expected_sign is None


def test_no_hand_emits_nothing_but_returns_to_ready(qapp):
    worker, detector, _, got = _worker()
    worker.start()
    detector.hand = False
    worker.submit_frame(_packet())
    assert got["events"] == []
    assert got["hands"][0].landmarks is None
    assert got["hands"][0].letter is None
    assert got["states"][-1] == InferenceState.READY


def test_hand_tracked_carries_normalized_skeleton_and_letter(qapp):
    worker, _, _, got = _worker()
    worker.start()
    worker.submit_frame(_packet())

    event = got["hands"][0]
    assert event.camera_id == CameraId.CAMERA_1
    assert event.letter == "A"
    assert event.confidence == 0.87
    assert event.landmarks is not None
    assert len(event.landmarks) == 21
    assert all(0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 for x, y in event.landmarks)


def test_stabilizer_reports_each_held_letter_once(qapp):
    worker, detector, classifier, got = _worker(stable_frames=3)
    worker.start()

    for _ in range(10):
        worker.submit_frame(_packet())
    assert [e.recognized_sign for e in got["events"]] == ["A"]

    detector.hand = False  # hand leaves the frame -> same letter counts again
    worker.submit_frame(_packet())
    detector.hand = True
    classifier.letter = "A"
    for _ in range(3):
        worker.submit_frame(_packet())
    assert [e.recognized_sign for e in got["events"]] == ["A", "A"]


def test_stabilizer_unit():
    stabilizer = LetterStabilizer(2)
    assert [stabilizer.update(x) for x in "AABBBA"] == [False, True, False, True, False, False]
    assert all(LetterStabilizer(1).update("A") for _ in range(3))


def test_model_load_failure_reports_unrecoverable_error(qapp):
    worker, _, _, got = _worker(fail_load=True)
    worker.start()

    assert got["states"] == [InferenceState.STARTING, InferenceState.ERROR]
    assert [(e.code, e.recoverable) for e in got["errors"]] == [("INF_MODEL_LOAD", False)]
    worker.submit_frame(_packet())
    assert got["events"] == []


def test_runtime_error_is_recoverable(qapp):
    worker, _, classifier, got = _worker()
    worker.start()
    classifier.fail = True
    worker.submit_frame(_packet())

    assert [(e.code, e.recoverable) for e in got["errors"]] == [("INF_RUNTIME", True)]
    assert got["states"][-2:] == [InferenceState.ERROR, InferenceState.READY]

    classifier.fail = False
    worker.submit_frame(_packet())
    assert len(got["events"]) == 1


def test_stop_closes_detector(qapp):
    worker, detector, _, got = _worker()
    worker.start()
    worker.stop()
    assert detector.closed
    assert got["states"][-1] == InferenceState.IDLE
    assert got["finished"] == [CameraId.CAMERA_1]
