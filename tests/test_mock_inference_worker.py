from uuid import uuid4

from handgame.core.events import FramePacket
from handgame.core.models import CameraId, InferenceState, PlayerId
from handgame.recognition.mock_inference_worker import MockInferenceWorker, MockResultSpec


def _packet() -> FramePacket:
    return FramePacket(camera_id=CameraId.CAMERA_1, frame_id=0, frame=None, player_id=PlayerId.PLAYER_1)


def _started_worker(results: list) -> MockInferenceWorker:
    worker = MockInferenceWorker(CameraId.CAMERA_1, "MOCK_YOLO")
    worker.gesture_recognized.connect(results.append)
    worker.start()
    return worker


def test_unconfigured_mock_recognises_nothing(qapp):
    """The mock must not play (and finish) a minigame by itself."""
    results: list = []
    worker = _started_worker(results)
    worker.set_expected_sign(str(uuid4()), "PLAYER_1", "A")  # a sign is expected...
    statuses: list = []
    worker.status_changed.connect(statuses.append)

    for _ in range(30):
        worker.submit_frame(_packet())

    assert results == []
    # InferenceManager clears its busy flag on READY, so every frame must end there.
    assert statuses[-1].current_state == InferenceState.READY


def test_queued_results_are_emitted_in_order(qapp):
    results: list = []
    worker = _started_worker(results)
    for sign in ("A", "B", "C"):
        worker.configure_mock_result(MockResultSpec(recognized_sign=sign))
    for _ in range(5):
        worker.submit_frame(_packet())
    assert [r.recognized_sign for r in results] == ["A", "B", "C"]
