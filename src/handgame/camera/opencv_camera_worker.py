import logging
import sys
from collections.abc import Callable
from typing import Any, Protocol

import cv2
from PySide6.QtCore import QTimer, Slot

from handgame.core.events import ApplicationErrorEvent, CameraStatusEvent, FramePacket
from handgame.core.models import CameraId, CameraState, PlayerId, Severity, SourceType

from .camera_worker import BaseCameraWorker

logger = logging.getLogger(__name__)


class VideoCaptureLike(Protocol):
    def isOpened(self) -> bool: ...  # noqa: N802 - cv2.VideoCapture API

    def read(self) -> tuple[bool, Any]: ...

    def set(self, prop_id: int, value: float) -> bool: ...

    def release(self) -> None: ...


def open_video_capture(device_index: int) -> VideoCaptureLike:
    # DirectShow opens webcams much faster than the default MSMF backend on Windows.
    api = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
    return cv2.VideoCapture(device_index, api)


class OpenCVCameraWorker(BaseCameraWorker):
    """Real webcam worker: polls ``cv2.VideoCapture`` from a QTimer in its own thread."""

    MAX_CONSECUTIVE_READ_FAILURES = 30

    def __init__(
        self,
        camera_id: CameraId,
        player_id: PlayerId | None = None,
        *,
        device_index: int = 0,
        fps: int = 30,
        mirror: bool = True,
        frame_size: tuple[int, int] = (640, 480),
        capture_factory: Callable[[int], VideoCaptureLike] = open_video_capture,
    ):
        super().__init__(camera_id)
        self.player_id = player_id
        self.device_index = device_index
        self._fps = max(1, fps)
        self._mirror = mirror
        self._frame_size = frame_size
        self._capture_factory = capture_factory
        self._capture: VideoCaptureLike | None = None
        self._timer: QTimer | None = None
        self._state = CameraState.DISCONNECTED
        self._frame_count = 0
        self._read_failures = 0

    def _set_state(self, new_state: CameraState, msg: str = "") -> None:
        old_state = self._state
        self._state = new_state
        self.status_changed.emit(
            CameraStatusEvent(self.camera_id, old_state, new_state, self.player_id, msg)
        )

    def _emit_error(self, code: str, message: str, exc: Exception | None = None) -> None:
        self.error_occurred.emit(
            ApplicationErrorEvent(
                source=SourceType.CAMERA,
                severity=Severity.ERROR,
                code=code,
                message=message,
                recoverable=True,
                camera_id=self.camera_id,
                player_id=self.player_id,
                exception_type=type(exc).__name__ if exc is not None else None,
            )
        )

    @Slot()
    def start_stream(self) -> None:
        self._set_state(CameraState.CONNECTING, f"Opening camera device {self.device_index}...")
        try:
            capture = self._capture_factory(self.device_index)
        except Exception as exc:
            logger.exception("Opening camera device %s failed", self.device_index)
            self._fail_open(f"Nie można otworzyć kamery (urządzenie {self.device_index}).", exc)
            return
        if not capture.isOpened():
            capture.release()
            self._fail_open(f"Nie można otworzyć kamery (urządzenie {self.device_index}).")
            return

        width, height = self._frame_size
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self._capture = capture
        self._read_failures = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.capture_frame)
        self._timer.start(1000 // self._fps)
        self._set_state(CameraState.READY)
        self._set_state(CameraState.STREAMING, "Camera stream started")
        logger.info("%s streaming from device %s.", self.camera_id, self.device_index)

    def _fail_open(self, message: str, exc: Exception | None = None) -> None:
        self._set_state(CameraState.ERROR, message)
        self._emit_error("CAM_OPEN_FAILED", message, exc)

    @Slot()
    def stop_stream(self) -> None:
        self._set_state(CameraState.STOPPING, "Stopping camera...")
        self._release()
        self._set_state(CameraState.DISCONNECTED, "Camera disconnected")
        self.finished.emit(self.camera_id)
        logger.info("%s worker stopped.", self.camera_id)

    @Slot()
    def restart_stream(self) -> None:
        self._release()
        self.start_stream()

    @Slot(object)
    def force_error(self, message: str) -> None:
        self._set_state(CameraState.ERROR, message)
        self._emit_error("CAM_FORCED_ERR", message)

    def _release(self) -> None:
        # Timer first: a tick must never hit a released capture.
        if self._timer is not None:
            self._timer.stop()
            self._timer.deleteLater()
            self._timer = None
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    @Slot()
    def capture_frame(self) -> None:
        """Timer tick (or manual call in tests): read one frame and emit it."""
        if self._capture is None or self._state not in (CameraState.STREAMING, CameraState.ERROR):
            return
        ok, frame = self._capture.read()
        if not ok or frame is None:
            self._read_failures += 1
            if (
                self._read_failures == self.MAX_CONSECUTIVE_READ_FAILURES
                and self._state == CameraState.STREAMING
            ):
                message = "Kamera przestała przesyłać obraz."
                self._set_state(CameraState.ERROR, message)
                self._emit_error("CAM_READ_FAILED", message)
            return

        self._read_failures = 0
        if self._state == CameraState.ERROR:
            self._set_state(CameraState.STREAMING, "Camera stream recovered")
        if self._mirror:
            frame = cv2.flip(frame, 1)
        self._frame_count += 1
        self.frame_captured.emit(
            FramePacket(
                camera_id=self.camera_id,
                frame_id=self._frame_count,
                frame=frame,
                player_id=self.player_id,
            )
        )
