import random
from PySide6.QtCore import QObject, QTimer

from config import DEFAULT_WAIT_DURATION_MS


class MoleSpawner(QObject):
    def __init__(self, tile_manager, parent=None, spawn_interval_ms=400):
        super().__init__(parent)

        self.tile_manager = tile_manager
        self.spawn_interval_ms = spawn_interval_ms

        # Domyślne parametry
        self.max_moles = 5
        self.letters = ["A", "B", "C"]
        self.wait_duration_ms = DEFAULT_WAIT_DURATION_MS
        self.use_basket = False
        self.basket_delay_ms = 400

        self.spawn_timer = QTimer(self)
        self.spawn_timer.timeout.connect(self._try_spawn_mole)

    def set_difficulty_config(self, config: dict):
        self.max_moles = config.get("max_moles", 5)
        self.letters = config.get("letters", ["A", "B", "C"])
        self.wait_duration_ms = config.get("wait_duration_ms", DEFAULT_WAIT_DURATION_MS)
        self.use_basket = config.get("use_basket", False)
        self.basket_delay_ms = config.get("basket_delay_ms", 400)

    def start(self):
        self.stop()
        self.spawn_timer.start(self.spawn_interval_ms)

    def stop(self):
        self.spawn_timer.stop()

    def _get_active_state(self):
        free_tiles = []
        used_letters = set()

        for tile in self.tile_manager.tiles:
            if tile.is_busy():
                if tile.current_letter:
                    used_letters.add(tile.current_letter)
            else:
                free_tiles.append(tile)

        return free_tiles, used_letters

    def _try_spawn_mole(self):
        all_tiles = self.tile_manager.tiles
        free_tiles, used_letters = self._get_active_state()

        active_count = len(all_tiles) - len(free_tiles)

        if active_count >= self.max_moles or not free_tiles or not self.letters:
            return

        if random.random() < 0.75:
            selected_tile = random.choice(free_tiles)

            letter = random.choice(self.letters)
            attempts = 0
            while letter in used_letters and attempts < 10:
                letter = random.choice(self.letters)
                attempts += 1

            if letter not in used_letters:
                selected_tile.start_cycle(
                    letter=letter,
                    wait_ms=self.wait_duration_ms,
                    use_basket=self.use_basket,
                    basket_delay_ms=self.basket_delay_ms,
                )
