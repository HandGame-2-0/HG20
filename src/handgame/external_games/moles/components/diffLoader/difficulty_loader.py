import json
from pathlib import Path

from config import (
    DEFAULT_GAME_DURATION_SEC,
    DEFAULT_WAIT_DURATION_MS,
    DIFFICULTIES_FILE,
)


def load_difficulties(config_path: Path = DIFFICULTIES_FILE) -> dict:
    target_path = Path(config_path)

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[BŁĄD Loader] Nie można załadować {target_path}: {e}")
        return _get_fallback_config()


def _get_fallback_config() -> dict:
    return {
        "1": {
            "name": "Domyślny",
            "game_duration_sec": DEFAULT_GAME_DURATION_SEC,
            "wait_duration_ms": DEFAULT_WAIT_DURATION_MS,
            "max_moles": 5,
            "letters": [
                "A",
                "B",
                "C",
                "E",
                "I",
                "L",
                "M",
                "N",
                "O",
                "P",
                "R",
                "S",
                "T",
                "U",
                "V",
                "W",
                "Y",
            ],
        }
    }
