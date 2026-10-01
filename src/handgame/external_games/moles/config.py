import os
from pathlib import Path

# ==========================================
# 1. ŚCIEŻKI DO ZASOBÓW (PATHS)
# ==========================================
BASE_DIR = Path(__file__).resolve().parent

# Katalogi zasobów graficznych
ASSETS_DIR = BASE_DIR / "images"
BASKET_DIR = ASSETS_DIR / "basket"
HANDLES_DIR = ASSETS_DIR / "raczki"
TILE_DIR = BASE_DIR / "tile"

# Pliki konfiguracyjne i zasoby
DIFFICULTIES_FILE = BASE_DIR / "difficulties.json"
BG_IMAGE_PATH = ASSETS_DIR / "bg.png"
LOGO_IMAGE_PATH = ASSETS_DIR / "logo.png"
START_BTN_IMAGE_PATH = ASSETS_DIR / "start.png"
DESKA_IMAGE_PATH = ASSETS_DIR / "deska.png"
NORKA_IMAGE_PATH = TILE_DIR / "norka.png"

# ==========================================
# 2. EKRAM I WSKAŹNIKI SCALOWANIA (DISPLAY)
# ==========================================
REF_WIDTH = 1920.0
REF_HEIGHT = 1080.0
MAX_OFFSET_Y = 150

BASE_TILE_POSITIONS = [
    # Wiersz 1
    (410, 100, 170, 170),
    (645, 100, 170, 170),
    (880, 100, 170, 170),
    (1115, 100, 170, 170),
    (1350, 100, 170, 170),
    # Wiersz 2
    (350, 210, 200, 200),
    (610, 210, 200, 200),
    (865, 210, 200, 200),
    (1125, 210, 200, 200),
    (1390, 210, 200, 200),
    # Wiersz 3
    (275, 365, 220, 220),
    (565, 365, 225, 225),
    (850, 365, 230, 230),
    (1140, 365, 225, 225),
    (1435, 365, 220, 220),
    # Wiersz 4
    (170, 570, 260, 260),
    (505, 570, 265, 265),
    (830, 570, 275, 275),
    (1170, 570, 265, 265),
    (1500, 570, 260, 260),
]
BORDER_THICKNESS = 4

# ==========================================
# 3. PALETA KOLORÓW (COLORS)
# ==========================================
COLOR_OUTLINE = "#000000"  # Czarna obramówka tekstów
COLOR_LETTER_GREEN = "#4FE078"  # Główny zielony kolor litery w koszyczku
COLOR_TEXT_WHITE = "#FFFFFF"  # Biały tekst przycisków / liczników
COLOR_TEXT_RED = "#FF3333"  # Czerwony tekst przycisków wyjścia
COLOR_TITLE_GOLD = "#FFD700"  # Złoty napis 'KONIEC GRY'

# ==========================================
# 4. SKRÓTY KLAWISZOWE (CONTROLS)
# ==========================================
HOTKEY_START_OR_RESTART = "L"
HOTKEY_EXIT = "ESCAPE"

# ==========================================
# 5. DOMYŚLNE PARAMETRY GRY (GAMEPLAY DEFAULTS)
# ==========================================
DEFAULT_GAME_DURATION_SEC = 30
DEFAULT_WAIT_DURATION_MS = 1200
DEFAULT_MARGIN_MS = 200
DEFAULT_POINTS_PER_HIT = 10
BG_ANIMATION_INTERVAL_MS = 30
