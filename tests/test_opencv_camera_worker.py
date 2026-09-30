"""OpenCVCameraWorker driven directly (no QThread) with a fake VideoCapture."""

import numpy as np

from handgame.camera.opencv_camera_worker import OpenCVCameraWorker
from handgame.core.models import CameraId, CameraState, PlayerId


class FakeCapture:
    def __init__(self, opened: bool = True):
        self.opened = opened
        self.fail_reads = False
        self.released = False
        self.frame = np.zeros((2, 3, 3), dtype=np.uint8)
        self.frame[:, 0] = 255  # left column white -> right column after mirroring

    def isOpened(self):  # noqa: N802
        return self.opened

    def read(self):
        if self.fail_reads:
            return False, None
        return True, self.frame.copy()

    def set(self, prop_id, value):
        return True

    def release(self):
        self.released = True


def _worker(capture: FakeCapture, **kwargs) -> tuple[OpenCVCameraWorker, dict]:
    opened_with: list[int] = []

    def factory(index: int) -> FakeCapture:
        opened_with.append(index)
        return capture

    worker = OpenCVCameraWorker(
        CameraId.CAMERA_1, PlayerId.PLAYER_1, device_index=3, capture_factory=factory, **kwargs
    )
    collected = {"states": [], "frames": [], "errors": [], "finished": [], "opened": opened_with}
    worker.status_changed.connect(lambda e: collected["states"].append(e.current_state))
    worker.frame_captured.connect(collected["frames"].append)
    worker.error_occurred.connect(collected["errors"].append)
    worker.finished.connect(collected["finished"].append)
    return worker, collected


def test_start_reaches_streaming_and_emits_mirrored_frames(qapp):
    capture = FakeCapture()
    worker, got = _worker(capture)
    worker.start_stream()
    try:
        assert got["opened"] == [3]
        assert got["states"] == [CameraState.CONNECTING, CameraState.READY, CameraState.STREAMING]

        worker.capture_frame()
        worker.capture_frame()
        assert [p.frame_id for p in got["frames"]] == [1, 2]
        packet = got["frames"][0]
        assert packet.player_id == PlayerId.PLAYER_1
        assert packet.frame[0, 2, 0] == 255 and packet.frame[0, 0, 0] == 0
    finally:
        worker.stop_stream()


def test_mirroring_can_be_disabled(qapp):
    worker, got = _worker(FakeCapture(), mirror=False)
    worker.start_stream()
    worker.capture_frame()
    worker.stop_stream()
    assert got["frames"][0].frame[0, 0, 0] == 255


def test_open_failure_reports_error_without_streaming(qapp):
    capture = FakeCapture(opened=False)
    worker, got = _worker(capture)
    worker.start_stream()

    assert got["states"] == [CameraState.CONNECTING, CameraState.ERROR]
    assert [e.code for e in got["errors"]] == ["CAM_OPEN_FAILED"]
    assert capture.released
    worker.capture_frame()
    assert got["frames"] == []


def test_repeated_read_failures_enter_error_then_recover(qapp):
    capture = FakeCapture()
    worker, got = _worker(capture)
    worker.start_stream()
    capture.fail_reads = True
    for _ in range(OpenCVCameraWorker.MAX_CONSECUTIVE_READ_FAILURES * 2):
        worker.capture_frame()

    assert got["states"][-1] == CameraState.ERROR
    assert [e.code for e in got["errors"]] == ["CAM_READ_FAILED"]  # reported once

    capture.fail_reads = False
    worker.capture_frame()
    assert got["states"][-1] == CameraState.STREAMING
    assert len(got["frames"]) == 1
    worker.stop_stream()


def test_stop_releases_capture_and_emits_finished(qapp):
    capture = FakeCapture()
    worker, got = _worker(capture)
    worker.start_stream()
    worker.stop_stream()

    assert capture.released
    assert got["states"][-2:] == [CameraState.STOPPING, CameraState.DISCONNECTED]
    assert got["finished"] == [CameraId.CAMERA_1]
    worker.capture_frame()
    assert got["frames"] == []
