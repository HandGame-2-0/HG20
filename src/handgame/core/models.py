from enum import Enum, auto


class PlayerId(Enum):
    PLAYER_1 = auto()
    PLAYER_2 = auto()


class CameraId(Enum):
    CAMERA_1 = auto()
    CAMERA_2 = auto()


class CameraState(Enum):
    DISCONNECTED = auto()
    CONNECTING = auto()
    READY = auto()
    STREAMING = auto()
    ERROR = auto()
    STOPPING = auto()


class InferenceState(Enum):
    IDLE = auto()
    STARTING = auto()
    READY = auto()
    PROCESSING = auto()
    ERROR = auto()
    STOPPING = auto()


class SessionState(Enum):
    IDLE = auto()
    PREPARING = auto()
    RUNNING = auto()
    PAUSED = auto()
    FINISHED = auto()
    ERROR = auto()


class SourceType(Enum):
    CAMERA = auto()
    INFERENCE = auto()
    SESSION = auto()
    GUI = auto()
    GAME = auto()
    STATS = auto()


class Severity(Enum):
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


class GameState(Enum):
    CREATED = auto()
    READY = auto()
    RUNNING = auto()
    PAUSED = auto()
    FINISHED = auto()
    ERROR = auto()


class GameMode(Enum):
    SINGLEPLAYER = auto()
    MULTIPLAYER = auto()
    DEMO = auto()
    DEVELOPER = auto()


class VirtualButton(Enum):
    """Gamepad-style control vocabulary that a gesture can resolve to.

    Stable across all minigames and sign vocabularies - see
    ``games/control_mapping.py`` and ``BaseGame.CONTROL_MAP``.
    """

    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    CONFIRM = auto()
    CANCEL = auto()
    ACTION_1 = auto()
    ACTION_2 = auto()
