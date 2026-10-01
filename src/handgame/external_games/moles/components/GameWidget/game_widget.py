from PySide6.QtCore import QCoreApplication, QRect, Qt, QTimer
from PySide6.QtGui import QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from config import (
    BG_ANIMATION_INTERVAL_MS,
    BG_IMAGE_PATH,
    BORDER_THICKNESS,
    COLOR_TEXT_RED,
    DEFAULT_GAME_DURATION_SEC,
    DEFAULT_POINTS_PER_HIT,
    MAX_OFFSET_Y,
    REF_HEIGHT,
    REF_WIDTH,
)
from ..diffLoader import load_difficulties
from ..end_game import DeskaButton, EndGameOverlay
from ..input import InputHandler
from ..logo import GameLogo
from ..score import ScoreCounter
from ..startButton import StartButton
from ..state import GameState
from ..diffMenu import DiffMenu
from ..timer import GameTimer

from .layout_scaler import LayoutScaler
from .mole_spawner import MoleSpawner
from .tile_manager import TileManager


class GameWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.GameState = GameState.START_MENU
        self.scaler = LayoutScaler(REF_WIDTH, REF_HEIGHT)

        self.difficulties = load_difficulties()
        self.points_per_hit = DEFAULT_POINTS_PER_HIT

        # Wczytanie grafiki tła z config.py
        self.bg_pixmap = QPixmap(str(BG_IMAGE_PATH))
        self.bg_x = 0
        self.bg_y = 0
        self.bg_direction = 1

        self.bg_timer = QTimer(self)
        self.bg_timer.timeout.connect(self._animate_background)
        self.bg_timer.start(BG_ANIMATION_INTERVAL_MS)

        self.tile_manager = TileManager(parent_widget=self)
        self.mole_spawner = MoleSpawner(tile_manager=self.tile_manager, parent=self)

        self.start_button = StartButton(parent=self)
        self.start_button.clicked.connect(self._on_start_clicked)
        self.start_button.show()
        self.start_button.raise_()

        self.menu_exit_button = DeskaButton(
            "Wyjdź z gry [ESC]", text_color=COLOR_TEXT_RED, parent=self
        )
        self.menu_exit_button.clicked.connect(self._on_exit_game)
        self.menu_exit_button.show()
        self.menu_exit_button.raise_()

        self.logo = GameLogo(parent=self)
        self.logo.show()
        self.logo.raise_()

        self.sub_menu = DiffMenu(parent=self)
        self.sub_menu.set_button_names(self.difficulties)
        self.sub_menu.button_clicked.connect(self._on_sub_menu_clicked)

        self.score_counter = ScoreCounter(parent=self)

        self.game_timer = GameTimer(parent=self, duration_sec=DEFAULT_GAME_DURATION_SEC)
        self.game_timer.timeout_signal.connect(self._on_game_over)

        self.end_game_overlay = EndGameOverlay(parent=self)
        self.end_game_overlay.restart_signal.connect(self._on_restart_game)
        self.end_game_overlay.exit_signal.connect(self._on_exit_game)

        self.input_handler = InputHandler(parent=self)
        QCoreApplication.instance().installEventFilter(self.input_handler)
        self.input_handler.letter_detected.connect(self._on_letter_input)
        self.input_handler.action_detected.connect(self._on_action_input)

        self._update_layout()

    def _update_layout(self):
        margin = BORDER_THICKNESS
        avail_w = max(0, self.width() - 2 * margin)
        avail_h = max(0, self.height() - 2 * margin)

        self.scaler.update(avail_w, avail_h)
        self.scaler.offset_x += margin
        self.scaler.offset_y += margin

        self.tile_manager.update_positions(self.scaler, self.bg_y)

        board_w = REF_WIDTH * self.scaler.scale
        center_x = self.scaler.center_x
        center_y = self.scaler.center_y

        start_y = center_y + int(20 * self.scaler.scale)
        self.start_button.update_position(board_w, center_x, start_y)

        exit_w = int(340 * self.scaler.scale)
        exit_h = int(100 * self.scaler.scale)
        exit_x = int(center_x - exit_w / 2.0)
        exit_y = int(start_y + self.start_button.height() + int(15 * self.scaler.scale))

        self.menu_exit_button.setGeometry(exit_x, exit_y, exit_w, exit_h)

        self.logo.update_position(
            board_w, center_x, self.start_button.y(), self.scaler.scale
        )

        self.sub_menu.update_scale(board_w, center_x, center_y, self.scaler.scale)

        self.game_timer.update_scale(
            self.scaler.scale,
            self.scaler.offset_x,
            self.scaler.offset_y,
            REF_WIDTH,
            REF_HEIGHT,
        )

        self.score_counter.update_scale(
            self.scaler.scale,
            self.scaler.offset_x,
            self.scaler.offset_y,
            REF_WIDTH,
            REF_HEIGHT,
        )

        self.end_game_overlay.update_scale(
            self.scaler.scale,
            self.scaler.offset_x,
            self.scaler.offset_y,
            REF_WIDTH,
            REF_HEIGHT,
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_layout()

    def _on_letter_input(self, letter: str):
        letter_upper = letter.upper()

        if self.GameState == GameState.START_MENU:
            if letter_upper == "L":
                self._on_start_clicked()

        elif self.GameState == GameState.MODE_SELECT:
            for mode_id_str, config in self.difficulties.items():
                if config.get("hotkey", "").upper() == letter_upper:
                    self._on_sub_menu_clicked(int(mode_id_str))
                    break

        elif self.GameState == GameState.PLAYING:
            for tile in self.tile_manager.tiles:
                if (
                    tile.is_busy()
                    and tile.show_letter
                    and tile.current_letter == letter_upper
                ):
                    tile.play_oberwal()
                    self.score_counter.add_points(self.points_per_hit)
                    break

        elif self.GameState == GameState.END_GAME:
            if letter_upper == "L":
                self._on_restart_game()

    def _on_action_input(self, action: str):
        if self.GameState == GameState.START_MENU:
            if action in ("CONFIRM", "SELECT_1"):
                self._on_start_clicked()
            elif action == "EXIT":
                self._on_exit_game()

        elif self.GameState == GameState.MODE_SELECT:
            if action.startswith("SELECT_"):
                mode_id = int(action.split("_")[1])
                self._on_sub_menu_clicked(mode_id)
            elif action == "EXIT":
                self._on_restart_game()

        elif self.GameState == GameState.PLAYING:
            if action == "EXIT":
                self._on_game_over()

        elif self.GameState == GameState.END_GAME:
            if action in ("CONFIRM", "RESTART"):
                self._on_restart_game()
            elif action == "EXIT":
                self._on_exit_game()

    def _on_start_clicked(self):
        self.start_button.hide()
        self.menu_exit_button.hide()
        self.logo.hide()

        self.GameState = GameState.MODE_SELECT
        self.sub_menu.show()
        self.sub_menu.raise_()
        self._update_layout()

    def _on_sub_menu_clicked(self, button_id: int):
        mode_key = str(button_id)
        selected_config = self.difficulties.get(mode_key, self.difficulties.get("1"))

        self.points_per_hit = selected_config.get(
            "points_per_hit", DEFAULT_POINTS_PER_HIT
        )
        self.mole_spawner.set_difficulty_config(selected_config)
        self.game_timer.set_duration(
            selected_config.get("game_duration_sec", DEFAULT_GAME_DURATION_SEC)
        )

        self.sub_menu.hide()
        self.GameState = GameState.STARTING

    def start_gameplay(self):
        self.score_counter.reset_score()
        self.score_counter.show()
        self.score_counter.raise_()

        self.game_timer.start_timer()
        self.game_timer.show()
        self.game_timer.raise_()

        self.mole_spawner.start()

    def _on_game_over(self):
        self.GameState = GameState.END_GAME
        self.mole_spawner.stop()

        self.end_game_overlay.set_score(self.score_counter.score)

        self.game_timer.stop_timer()
        self.game_timer.hide()
        self.score_counter.hide()

        self.tile_manager.reset_all()

        self.end_game_overlay.show()
        self.end_game_overlay.raise_()
        self._update_layout()

    def _on_restart_game(self):
        self.end_game_overlay.hide()
        self.sub_menu.hide()

        self.score_counter.hide()
        self.game_timer.hide()

        self.mole_spawner.stop()
        self.game_timer.stop_timer()

        self.GameState = GameState.START_MENU
        self.bg_y = 0

        self.tile_manager.reset_all()
        self._update_layout()

        self.start_button.show()
        self.start_button.raise_()

        self.menu_exit_button.show()
        self.menu_exit_button.raise_()

        self.logo.show()
        self.logo.raise_()

        self.update()

    def _on_exit_game(self):
        if self.window():
            self.window().close()

    def _animate_background(self):
        if self.bg_pixmap.isNull():
            return

        if self.GameState == GameState.STARTING:
            self.bg_y += 4 * self.bg_direction

            if self.bg_y >= MAX_OFFSET_Y:
                self.bg_y = MAX_OFFSET_Y
                self.GameState = GameState.PLAYING
                self.start_gameplay()

            self.tile_manager.update_positions(self.scaler, self.bg_y)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        target_rect = QRect(
            int(self.scaler.offset_x),
            int(self.scaler.offset_y),
            int(REF_WIDTH * self.scaler.scale),
            int(REF_HEIGHT * self.scaler.scale),
        )

        if not self.bg_pixmap.isNull():
            source_rect = QRect(
                int(self.bg_x),
                int(self.bg_y),
                int(REF_WIDTH),
                int(REF_HEIGHT),
            )
            painter.drawPixmap(target_rect, self.bg_pixmap, source_rect)
        else:
            super().paintEvent(event)

        pen = QPen(Qt.GlobalColor.white, BORDER_THICKNESS)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        border_offset = BORDER_THICKNESS // 2
        border_rect = target_rect.adjusted(
            -border_offset, -border_offset, border_offset, border_offset
        )
        painter.drawRect(border_rect)
        painter.end()
