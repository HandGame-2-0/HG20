from enum import Enum
# =====================================================================
# 1. ENUM DEFINING AVAILABLE SCREENS (GUI-CORE-4)
# =====================================================================

class Screen(Enum):
    MAIN_MENU = 0
    GAME_SELECT = 1
    SETTINGS = 2
    CAMERA_CALIBRATION = 3
    DEMO_MODE = 4
    DEV_MODE = 5
    RESULTS = 6
    GAME_VIEW = 7