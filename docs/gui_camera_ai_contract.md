# GUI <-> Camera <-> AI <-> Session <-> Minigame <-> Stats Contract

This document is the source of truth for how the pieces of HandGame 2.0 talk
to each other: what events exist, what each component's states mean, the
threading rules every worker must follow, and the startup/shutdown lifecycle.
Read this before touching `camera/`, `recognition/`, `session/`, `games/`,
`stats/`, or `gui/integration_controller.py`.

## Component map

```
GUI (widgets)
  -> GUIIntegrationController          (facade; no QtWidgets import)
       -> CameraManager                (owns CameraWorkerHandle + QThread per camera)
            -> OpenCVCameraWorker / MockCameraWorker   (BaseCameraWorker, picked via CAMERA_BACKENDS)
       -> InferenceManager             (owns InferenceWorkerHandle + QThread per camera)
            -> MediaPipeLetterWorker / MockInferenceWorker  (BaseInferenceWorker, via ALGORITHM_REGISTRY)
       -> SessionManager               (session state machine)
            -> GameController          (owns the active BaseGame instance)
                 -> BaseGame subclass  (pure Python, no Qt)
                      -> optional GameEventSink.on_control_event -> ui_control_event
       -> StatsSink                    (in-memory now, SQLite-ready seam)
```

`GUIIntegrationController` is the only object the GUI layer talks to.
`SessionManager` never references `CameraManager`/`InferenceManager` directly
- it only exposes slots (`handle_camera_status`, `handle_inference_status`,
`handle_gesture_event`) that the controller wires up. This keeps
`SessionManager` fully testable without any camera/AI machinery running.

## Backends, algorithms and configuration

`core/config.py` defines `AppConfig`. Managers and `GUIIntegrationController`
default to `AppConfig.from_env()`, so every value can be overridden with an
environment variable:

| Variable | Default | Meaning |
|---|---|---|
| `HANDGAME_CAMERA_BACKEND` | `opencv` | `opencv` (real webcam) or `mock` (no hardware) - key in `CAMERA_BACKENDS` (`camera/camera_manager.py`). |
| `HANDGAME_CAMERA_INDEX_1` / `_2` | `0` / `1` | OpenCV device index for `CameraId.CAMERA_1` / `CAMERA_2`. |
| `HANDGAME_CAMERA_FPS` | `30` | Frame polling rate. |
| `HANDGAME_CAMERA_MIRROR` | `true` | Flip frames horizontally (selfie view). |
| `HANDGAME_ALGORITHM` | `MEDIAPIPE_PJM_STATIC` | Algorithm `select_camera` starts - key in `ALGORITHM_REGISTRY` (`recognition/inference_manager.py`). `MOCK_YOLO` = mock. |
| `HANDGAME_HAND_MODEL` | `models/hand_landmarker.task` | MediaPipe hand landmarker (not committed; downloaded from Google on first use if missing). |
| `HANDGAME_LETTER_MODEL` | `models/pjm_static_letters.joblib` (bundled) | Letter classifier: `.joblib` = sklearn bundle, `.onnx` = PP2Project net. |
| `HANDGAME_STABLE_FRAMES` | `5` | Frames a letter must stay top-1 before it is reported (`1` = every frame). |

The test-suite forces `mock` / `MOCK_YOLO` in `tests/conftest.py`.

### `MEDIAPIPE_PJM_STATIC` (static PJM letters)

`MediaPipeLetterWorker` (`recognition/mediapipe_letter_worker.py`) runs per
frame: `MediaPipeHandDetector` (MediaPipe Tasks `HandLandmarker`, VIDEO mode,
one hand) -> `HandDetection` (21 image landmarks in pixels, 21 world landmarks
in metres, handedness) -> `LetterClassifier.predict(hand)` ->
`(letter, probability)`. Each classifier computes its own features from the
detection. The event carries `recognized_sign`, `confidence` (the classifier
probability), `is_correct` (vs. `expected_sign`, `None` if none is set) and
`latency_ms`.

`load_letter_classifier(path)` (`recognition/letter_classifier.py`) picks the
classifier by file suffix:

- `.joblib` -> `SklearnLetterClassifier`. The bundle stores `feature_kind`
  and its version:
  - `hand_geometry` (bundled `models/pjm_static_letters.joblib`, MLP, letters
    `A B C E I L M N O P R S T U V W Y`): `hand_geometry_features` =
    `palm_volume_features` + 210 pairwise world-landmark distances / palm
    width (228 floats).
  - `palm_volumes` (method from
    [MagMat03/handgesture](https://github.com/MagMat03/handgesture)): for the
    18 landmarks outside the palm base (0, 5, 17), the signed tetrahedron
    volume vs. the palm plane divided by palm width cubed, from world
    landmarks; left hands negated. Invariant to position, rotation and hand
    size.
  - `landmarks`: `landmarks_to_features`, 63 wrist-relative image coordinates.
- `.onnx` -> `OnnxDistanceLetterClassifier` (alternative): pretrained net from
  [worthy11/PP2Project](https://github.com/worthy11/PP2Project) run with
  `cv2.dnn`. Input: 441 pairwise landmark distances normalized by the hand
  bounding box (`pairwise_distance_features`), output: softmax over
  `PP2_LABELS` = `A B C D E F G H I K L M N O P R S U W Y Z` (no `T`, and
  D F G H K Z are extra vs. `STATIC_LETTERS`). The source repo has no license
  - local/educational use only, never commit the file.

Games draw letters from `core/pjm_alphabet.STATIC_LETTERS`
(`A B C E I L M N O P R S T U V W Y`, the letters of the bundled model).

- No hand in view -> no event (the worker just returns to `READY`).
- `LetterStabilizer`: one event per held letter, after `stable_frames`
  consecutive identical predictions; removing the hand re-arms it, so the
  same letter can be shown twice in a row.
- Models are loaded in `start()` (inside the worker thread). The hand
  landmarker is downloaded to `hand_model_path` if that file is missing. A
  failed download or incompatible letter model -> `InferenceState.ERROR` +
  `ApplicationErrorEvent(code="INF_MODEL_LOAD", recoverable=False)`, which
  `MainWindow` shows as a message box; the session never starts.
- A failure while processing a frame -> `INF_RUNTIME` (recoverable), worker
  goes back to `READY`.

**Plugging in the target model:** either implement the `LetterClassifier`
protocol (`predict(hand: HandDetection) -> (letter, probability)`) and pass it
via `classifier_factory`, or write a new `BaseInferenceWorker` and register it
under a new id in `ALGORITHM_REGISTRY`. Nothing outside `recognition/` has to
change. Stored sklearn bundles record the feature kind and version
(`FEATURE_VERSION`, `PALM_VOLUME_VERSION`); bump the version whenever its
feature function changes, and old models are rejected.

### `OpenCVCameraWorker`

Opens `cv2.VideoCapture(index)` (DirectShow on Windows) in `start_stream()`
and polls it from a `QTimer` in the worker thread, emitting BGR `ndarray`
frames. Failing to open -> `CameraState.ERROR` + `CAM_OPEN_FAILED`; 30
consecutive failed reads -> `ERROR` + `CAM_READ_FAILED` (reported once), and
the first good frame afterwards returns it to `STREAMING`. `stop_stream()`
stops the timer, releases the capture, then emits `finished`.

## Events (`core/events.py`)

All frozen dataclasses. One file - do not add a competing event type
elsewhere.

| Event | Key fields | Notes |
|---|---|---|
| `FramePacket` | `camera_id`, `frame_id`, `frame`, `player_id?`, `timestamp` | `frame` is a transient in-memory object (e.g. `np.ndarray`). **Never** persisted - not to `StatsSink`, not to logs, not to SQLite. |
| `GestureRecognitionEvent` | `session_id`, `player_id`, `camera_id`, `algorithm_id`, `expected_sign?`, `recognized_sign?`, `confidence?`, `is_correct?`, `latency_ms?` | `confidence` in `[0, 1]`; `latency_ms >= 0`; `expected_sign`/`recognized_sign`, if given, cannot be `""`. |
| `CameraStatusEvent` | `camera_id`, `previous_state`, `current_state`, `player_id?`, `message?` | |
| `InferenceStatusEvent` | `algorithm_id`, `previous_state`, `current_state`, `camera_id?`, `message?` | |
| `SessionStatusEvent` | `session_id`, `previous_state`, `current_state`, `message?` | |
| `ApplicationErrorEvent` | `source: SourceType`, `severity: Severity`, `code`, `message`, `recoverable`, `camera_id?`, `player_id?`, `exception_type?` | The one uniform error channel every manager funnels into. |
| `GameActionEvent` | `session_id`, `player_id`, `action_type`, `payload`, `timestamp` | `payload` is frozen (`MappingProxyType`) in `__post_init__` - construct it once, never mutate after. |
| `ControlEvent` | `session_id`, `player_id`, `button: VirtualButton`, `source_event_id`, `recognized_sign?`, `confidence?` | Optional, opt-in per minigame; resolved from `GestureRecognitionEvent.recognized_sign` via `BaseGame._resolve_button` (`docs/game_framework.md` "Virtual buttons"). Not persisted to `StatsSink` by default. |
| `SessionMetricsEvent` | `session_id`, `game_id`, `difficulty_level` (1-5), `player_id?`, `score?`, `mistakes?`, `hint_count?`, `reaction_time_ms?` | Never carries frame/image data - it structurally can't. |

## States

- `CameraState`: `DISCONNECTED -> CONNECTING -> READY -> STREAMING -> ERROR / STOPPING`
- `InferenceState`: `IDLE -> STARTING -> READY -> PROCESSING -> ERROR / STOPPING`
- `SessionState`: `IDLE -> PREPARING -> RUNNING <-> PAUSED -> FINISHED / ERROR`
- `GameState`: see `docs/game_framework.md` (`CREATED -> READY -> RUNNING <-> PAUSED -> FINISHED / ERROR`)

`SessionState.RUNNING` is only reachable once both the required camera(s) are
`STREAMING` and the required inference worker(s) are `READY`
(`SessionManager._check_auto_start`).

## Signal typing convention

**Every cross-object `Signal` in this codebase carries `object`, and every
receiving slot is `@Slot(object)`.** The concrete payload type is documented
next to the `Signal(object)` declaration (as a comment) and enforced by
tests, not by the Qt meta-object system.

This applies uniformly at the worker level (`BaseCameraWorker`,
`BaseInferenceWorker`) and the manager/controller level
(`CameraManager`, `InferenceManager`, `GameController`, `SessionManager`,
`GUIIntegrationController`). Earlier revisions of this codebase mixed
strongly-typed `Signal(SomeDataclass)` at the worker level with `Signal(object)`
at the manager level; that inconsistency has been removed. Passing a Python
object through a `Signal(object)` connection works identically to a typed
signal at runtime (Qt only checks parameter count/compatibility for queued
delivery) - the only thing given up is compile-time Qt-side type checking,
which nothing else in this codebase relied on either.

**Never** use `QMetaObject.invokeMethod(worker, "some_slot", ...)` with a
string slot name to reach across threads. Use a `*Handle` proxy object (see
below) with real `Signal`/`Slot` connections instead - it's just as safe
cross-thread and gives you static analysis and refactor-safety that a string
literal doesn't.

## Thread safety rules

1. One `QThread` per camera, one `QThread` per AI worker (per camera). The
   main/GUI thread never reads a camera, never runs inference, never blocks
   on I/O.
2. A worker is a `QObject` moved via `moveToThread()` - never a `QThread`
   subclass carrying business logic.
3. **Do not parent a `QThread` to its owning manager** (`QThread(self)`).
   Ownership must be exactly one mechanism, not two: `worker.finished ->
   thread.quit()` / `thread.finished -> thread.deleteLater()` already fully
   owns the thread's lifecycle. Parenting it to `self` *as well* creates a
   double-ownership race - if the manager itself is destroyed (e.g. via
   Python's GC) before the thread has processed its own queued
   `deleteLater()`, the C++ parent-child cascade deletes the thread
   synchronously on the wrong thread while a stale `deleteLater()` event for
   the *same* object is still sitting in the main thread's queue. The next
   `processEvents()` call then dispatches that stale event against an
   already-freed object - a real, reproducible segfault, not a theoretical
   one (see the fix in `camera_manager.py` / `inference_manager.py`:
   `thread = QThread()`, no parent).
4. All requests from a manager *into* a worker's thread go through a `*Handle`
   proxy object (`CameraWorkerHandle`, `InferenceWorkerHandle`) that lives in
   the manager's thread, with every connection to the worker made with
   explicit `Qt.ConnectionType.QueuedConnection`. Never call
   `worker.stop_stream()`, `worker.submit_frame()`, etc. directly from the
   manager - always go through the handle's signals.
5. Every `QTimer` a worker owns (e.g. `MockCameraWorker`'s frame-emission
   timer) must be created, started, and stopped from inside that worker's
   own thread - i.e. from within a slot that only ever runs after
   `moveToThread()`, never from `__init__`.
6. `worker.finished` triggers, in this order: `thread.quit()`, then
   `worker.deleteLater()`. `thread.finished` triggers `thread.deleteLater()`.
   A worker's `stop_*()` slot must stop its own `QTimer` *before* emitting
   `finished` - never emit `finished` while a timer could still fire.

## Latest-frame-wins

`InferenceManager.process_frame()` (the pattern every future per-camera
worker manager should copy) never queues frames. It tracks one `_is_busy`
flag per camera:

```python
if self._states.get(camera_id) != InferenceState.READY:
    return
if self._is_busy.get(camera_id, False):
    return
self._is_busy[camera_id] = True
runtime.handle.frame_requested.emit(packet)
```

A frame arriving while the previous one is still being processed is silently
dropped - there is no buffer, no backlog, ever. `_is_busy` is cleared on
`gesture_recognized`, on a worker error, and when status transitions to
`ERROR`, so a stuck-busy state can never permanently block new frames.

## Lifecycle: start / stop / shutdown

`CameraManager`/`InferenceManager` both follow the identical shape:

- `start_camera()` / `start_algorithm()`: build worker + `QThread` (unparented,
  see rule 3 above) + `*Handle`, wire everything with `QueuedConnection`,
  `thread.start()`. The runtime (`thread`, `worker`, `handle`) is stored in a
  single dict keyed by `CameraId`, never split across multiple dicts.
- `stop_camera()` / `stop_algorithm()`: idempotent (checks the current state
  is not already `STOPPING` before acting), emits `handle.stop_requested`.
  **Never** mutates the runtime dict here - only the request is sent.
- `_cleanup_runtime()`: the *only* place that pops the runtime dict entry.
  Connected to `thread.finished`, so it only ever runs once the `QThread` has
  genuinely stopped.
- `shutdown(timeout_ms=3000)`: stops everything, then waits for each thread
  via `wait_for_thread_stopped()` (`core/qt_utils.py`) - **not** a bare
  `thread.wait(timeout_ms)`. A bare `wait()` blocks the calling thread
  without pumping its own event loop, which means the queued
  `worker.finished -> thread.quit()` call (a cross-thread `QueuedConnection`)
  can never be delivered while `wait()` is blocking - every `shutdown()`
  would silently eat the *entire* timeout on every call, every time, even
  though the worker actually finished in milliseconds. `wait_for_thread_stopped()`
  alternates `QCoreApplication.processEvents()` with short polls so the
  queued call actually gets a chance to run, and returns as soon as the
  thread is genuinely done. If a thread still hasn't stopped after the full
  timeout, the fallback calls `thread.quit()` directly (bypassing the queue)
  and does one more short `wait()` - `thread.terminate()` is never used.
  Finally, a sweep pops any runtime whose thread is confirmed not running,
  covering the case where a test has no running Qt event loop pumping
  `thread.finished` on its own.
- `shutdown()` is idempotent: calling it twice (or calling `stop_camera()`
  twice) must never raise, warn, or hang. Both managers' `stop_*()` methods
  guard on current state; `shutdown()`'s loops simply no-op over an empty
  runtime dict on a second call.

`GUIIntegrationController.shutdown()` calls, in order:
`session_mgr.finish_session()` -> `camera_mgr.shutdown()` ->
`inference_mgr.shutdown()`. Tests must always call this in a `finally` block
or fixture teardown (see `tests/conftest.py`'s `controller` fixture).

## Full data flow

1. GUI calls `GUIIntegrationController.select_camera(camera_id, player_id)`
   and `select_algorithm(camera_id, algorithm_id)` (or the default
   `select_camera` auto-starts `AppConfig.default_algorithm`) - these also register the
   player<->camera and camera<->algorithm mappings on `SessionManager`.
2. GUI calls `prepare_game(game_id, difficulty, mode)`.
   `SessionManager.prepare_session()` creates `session_id`, stores
   `game_id`/`mode`, builds a `DifficultyProfile` via
   `build_difficulty_profile(difficulty)`, transitions to `PREPARING`.
3. `CameraManager.start_camera()` / `InferenceManager.start_algorithm()` spin
   up their workers (steps 1-2 usually trigger this already).
4. Camera worker emits `CameraStatusEvent` (`CONNECTING -> READY -> STREAMING`).
5. AI worker emits `InferenceStatusEvent` (`STARTING -> READY`).
6. Once both `_sys_camera_ready` and `_sys_ai_ready` are true,
   `SessionManager` builds a `GameContext` and calls
   `GameController.create_game(game_id, context)`, which looks the game up
   in `GAME_REGISTRY`, instantiates it, and calls `BaseGame.start(context)`.
   Only then does `SessionManager` transition to `RUNNING`.
7. `SessionManager._push_expected_signs()` reads each player's current
   `get_expected_sign()` from the game and forwards it through
   `expected_sign_ready` -> `GUIIntegrationController` ->
   `InferenceManager.set_expected_sign(...)`, so the AI worker knows what
   sign each player's camera should be looking for next.
8. `CameraWorker` emits `FramePacket` -> `CameraManager.frame_ready` ->
   `InferenceManager.process_frame()` (latest-frame-wins, see above).
9. `InferenceWorker` emits `GestureRecognitionEvent` ->
   `InferenceManager.gesture_recognized` -> `SessionManager.handle_gesture_event()`.
10. `SessionManager` delegates to `GameController.handle_gesture()`, which
    delegates to `BaseGame.handle_gesture()` (filters + `_on_gesture` hook),
    then builds and emits a `SessionMetricsEvent`.
11. The minigame emits `GameActionEvent` (correct/incorrect gesture, score
    change, etc.) via `GameEventSink.on_action_ready` -> `GameController` ->
    `SessionManager.game_action_ready` -> `GUIIntegrationController.ui_game_action`.
    A minigame that opts into virtual buttons may also emit `ControlEvent`
    via `GameEventSink.on_control_event` -> `GameController.control_event_ready`
    -> `SessionManager.control_event_ready` -> `GUIIntegrationController.ui_control_event`.
12. `SessionManager` re-pushes expected signs (step 7) for the next gesture.
13. `StatsSink.record_metrics()` / `record_gesture()` save only the fields
    listed in the events table above - no frame data, ever.
14. When the minigame's sequence completes, it calls `self.end(...)`,
    producing a `GameResult`, which flows through `GameController.game_finished`
    -> `SessionManager.game_finished` -> `GUIIntegrationController.ui_game_finished`
    and `StatsSink.record_result()`.
15. `GUIIntegrationController.shutdown()` (wired to `app.aboutToQuit`, and
    called explicitly by tests) stops games, cameras, and AI workers with no
    orphaned `QThread`s left behind.

## Error handling

Every manager funnels its errors into a single `ApplicationErrorEvent` and
its own `error_occurred` signal. `GUIIntegrationController` fans all of them
out to `ui_error_occurred` (for the GUI to show a message) and
`EventBus.global_error` (diagnostic/logging sink). Covered failure modes:

- Missing/disconnected camera mid-session -> `CameraState.DISCONNECTED` while
  `RUNNING` forces `SessionState.ERROR` (unrecoverable without a reset).
- Recoverable camera fault -> `CameraState.ERROR` while `RUNNING` pauses the
  session (`SessionState.PAUSED`) instead of hard-failing it, since the
  underlying worker stays alive and can recover.
- Frame read / inference error -> the mock workers' `force_error()` /
  `configure_mock_result(is_error=True)` hooks simulate this in tests;
  real workers should emit `ApplicationErrorEvent(source=SourceType.CAMERA
  or INFERENCE, recoverable=...)` the same way.
- No gesture recognized -> `GestureRecognitionEvent.recognized_sign` can be
  `None` (never `""`); a minigame's `_on_gesture` should treat that as "no
  match" the same as any other wrong answer.
- Start attempted before camera/AI ready -> `SessionManager.start_session()`
  no-ops and emits a recoverable error instead of transitioning.
- Invalid state transition -> `SessionManager.prepare_session()` raises
  `InvalidStateTransitionError`; `BaseGame._transition()` logs + reports via
  `on_error` without raising (a stray GUI click must never crash a game).
- Unknown `game_id` -> `GameController.create_game()` raises `KeyError`,
  caught by `SessionManager.start_session()`, reported as an error, session
  stays in `PREPARING`.

## APIs that must not change without consulting the GUI lead

- `GUIIntegrationController`'s public method signatures: `select_camera`,
  `select_algorithm`, `prepare_game`, `start_game`, `pause_game`,
  `resume_game`, `finish_game`, `reset_game`, `shutdown`.
- All `ui_*` signals on `GUIIntegrationController`: `ui_camera_status_changed`,
  `ui_session_status_changed`, `ui_inference_status_changed`,
  `ui_gesture_result`, `ui_game_action`, `ui_game_finished`,
  `ui_error_occurred`.
- The event dataclasses in `core/events.py` and the state enums in
  `core/models.py` - these are the shared vocabulary every team (camera, AI,
  minigame, GUI) codes against.

## Instructions per team

- **Camera team**: `OpenCVCameraWorker` is the reference `BaseCameraWorker`;
  a new backend is one more entry in `CAMERA_BACKENDS`. You must
  provide `start_stream`/`stop_stream`/`restart_stream` as `@Slot()` methods
  that only ever run inside the worker's own thread (post-`moveToThread`),
  emit `frame_captured`/`status_changed`/`error_occurred` as `Signal(object)`,
  and never build an unbounded frame buffer - if `CameraManager` can't keep
  up, drop frames, don't queue them.
- **AI team**: `MediaPipeLetterWorker` is the reference
  `BaseInferenceWorker`; see "Plugging in the target model" above. Real
  inference will likely block for real time inside `submit_frame` - that's
  fine, it runs in its own thread, but it must never call back into the GUI
  thread synchronously, and must respect `stop()` being requested mid-inference
  (check a cancellation flag between blocking chunks if the model API allows it).
- **Minigame team**: read `docs/game_framework.md`. You only ever touch
  `games/`, never `camera/`, `recognition/`, `gui/`.
- **GUI team**: only ever call methods on `GUIIntegrationController` and
  connect to its `ui_*` signals, in the main thread. Never reach into
  `camera_mgr`/`inference_mgr`/`session_mgr` directly.
