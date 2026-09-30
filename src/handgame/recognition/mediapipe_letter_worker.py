import logging
import time
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any
from uuid import uuid4

from PySide6.QtCore import Slot

from handgame.core.events import (
    ApplicationErrorEvent,
    FramePacket,
    GestureRecognitionEvent,
    HandTrackingEvent,
    InferenceStatusEvent,
)
from handgame.core.models import CameraId, InferenceState, PlayerId, Severity, SourceType
from handgame.recognition.hand_landmarker import (
    HandDetection,
    HandDetector,
    MediaPipeHandDetector,
)
from handgame.recognition.inference_worker import BaseInferenceWorker
from handgame.recognition.letter_classifier import LetterClassifier, load_letter_classifier

logger = logging.getLogger(__name__)


def _normalized_points(detection: HandDetection, frame: Any) -> tuple[tuple[float, float], ...]:
    height, width = frame.shape[:2]
    return tuple((float(x) / width, float(y) / height) for x, y, _ in detection.landmarks)


class LetterStabilizer:
    """Lets a letter through once it has been the top prediction for
    ``stable_frames`` consecutive frames, and only once per hold - so a game
    sees one event per shown letter instead of ~30 per second.
    ``stable_frames == 1`` disables filtering (every frame passes)."""

    def __init__(self, stable_frames: int) -> None:
        self.stable_frames = max(1, stable_frames)
        self.reset()

    def reset(self) -> None:
        self._candidate: str | None = None
        self._count = 0
        self._last_emitted: str | None = None

    def update(self, letter: str) -> bool:
        if self.stable_frames == 1:
            return True
        if letter == self._candidate:
            self._count += 1
        else:
            self._candidate = letter
            self._count = 1
        if self._count >= self.stable_frames and letter != self._last_emitted:
            self._last_emitted = letter
            return True
        return False


class MediaPipeLetterWorker(BaseInferenceWorker):
    """Static PJM letters: MediaPipe hand landmarks -> LetterClassifier."""

    def __init__(
        self,
        camera_id: CameraId,
        algorithm_id: str,
        *,
        hand_model_path: Path | None = None,
        letter_model_path: Path | None = None,
        stable_frames: int = 5,
        detector_factory: Callable[[], HandDetector] | None = None,
        classifier_factory: Callable[[], LetterClassifier] | None = None,
    ):
        super().__init__(camera_id, algorithm_id)
        if detector_factory is None:
            if hand_model_path is None:
                raise ValueError("hand_model_path or detector_factory is required")
            detector_factory = partial(MediaPipeHandDetector, Path(hand_model_path))
        if classifier_factory is None:
            if letter_model_path is None:
                raise ValueError("letter_model_path or classifier_factory is required")
            classifier_factory = partial(load_letter_classifier, Path(letter_model_path))
        self._detector_factory = detector_factory
        self._classifier_factory = classifier_factory
        self._detector: HandDetector | None = None
        self._classifier: LetterClassifier | None = None
        self._stabilizer = LetterStabilizer(stable_frames)
        self._state = InferenceState.IDLE

    def _set_state(self, new_state: InferenceState, msg: str = "") -> None:
        old = self._state
        self._state = new_state
        self.status_changed.emit(
            InferenceStatusEvent(self.algorithm_id, old, new_state, self.camera_id, msg)
        )

    def _emit_error(self, code: str, message: str, exc: Exception, recoverable: bool) -> None:
        self.error_occurred.emit(
            ApplicationErrorEvent(
                source=SourceType.INFERENCE,
                severity=Severity.ERROR,
                code=code,
                message=message,
                recoverable=recoverable,
                camera_id=self.camera_id,
                exception_type=type(exc).__name__,
            )
        )

    @Slot()
    def start(self) -> None:
        self._set_state(InferenceState.STARTING, "Loading hand and letter models...")
        try:
            self._detector = self._detector_factory()
            self._classifier = self._classifier_factory()
        except Exception as exc:
            logger.exception("Loading recognition models failed for %s", self.camera_id)
            self._close_detector()
            message = f"Nie można załadować modelu rozpoznawania: {exc}"
            self._set_state(InferenceState.ERROR, message)
            self._emit_error("INF_MODEL_LOAD", message, exc, recoverable=False)
            return
        self._stabilizer.reset()
        self._set_state(InferenceState.READY)
        logger.info("Letter recognition worker %s ready.", self.camera_id)

    @Slot()
    def stop(self) -> None:
        self._set_state(InferenceState.STOPPING)
        self._close_detector()
        self._classifier = None
        self._set_state(InferenceState.IDLE)
        self.finished.emit(self.camera_id)
        logger.info("Letter recognition worker %s stopped.", self.camera_id)

    def _close_detector(self) -> None:
        if self._detector is not None:
            try:
                self._detector.close()
            except Exception:
                logger.exception("Closing hand detector failed")
            self._detector = None

    @Slot(object)
    def submit_frame(self, packet: FramePacket) -> None:
        if self._state not in (InferenceState.READY, InferenceState.PROCESSING):
            return
        if self._detector is None or self._classifier is None:
            return
        self._set_state(InferenceState.PROCESSING)
        started = time.perf_counter()

        try:
            detection = self._detector.detect(packet.frame, int(time.monotonic() * 1000))
            if detection is None:
                # No hand in view: next shown letter counts as a new one.
                self._stabilizer.reset()
                self.hand_tracked.emit(HandTrackingEvent(packet.camera_id, packet.frame_id))
                self._set_state(InferenceState.READY)
                return
            letter, confidence = self._classifier.predict(detection)
        except Exception as exc:
            logger.exception("Letter recognition failed for %s", self.camera_id)
            message = f"Błąd rozpoznawania: {exc}"
            self._set_state(InferenceState.ERROR, message)
            self._emit_error("INF_RUNTIME", message, exc, recoverable=True)
            self._set_state(InferenceState.READY)
            return

        self.hand_tracked.emit(
            HandTrackingEvent(
                camera_id=packet.camera_id,
                frame_id=packet.frame_id,
                landmarks=_normalized_points(detection, packet.frame),
                handedness=detection.handedness,
                letter=letter,
                confidence=confidence,
            )
        )
        if not self._stabilizer.update(letter):
            self._set_state(InferenceState.READY)
            return

        expected = self.expected_sign or None
        self.gesture_recognized.emit(
            GestureRecognitionEvent(
                session_id=self.current_session or uuid4(),
                player_id=packet.player_id or self.current_player or PlayerId.PLAYER_1,
                camera_id=packet.camera_id,
                algorithm_id=self.algorithm_id,
                expected_sign=expected,
                recognized_sign=letter,
                confidence=confidence,
                is_correct=None if expected is None else letter == expected,
                latency_ms=(time.perf_counter() - started) * 1000.0,
            )
        )
        self._set_state(InferenceState.READY)
