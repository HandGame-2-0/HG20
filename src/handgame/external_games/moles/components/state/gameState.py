from enum import Enum, auto


class GameState(Enum):
    START_MENU = auto()
    MODE_SELECT = auto()
    STARTING = auto()
    PLAYING = auto()
    END_GAME = auto()
