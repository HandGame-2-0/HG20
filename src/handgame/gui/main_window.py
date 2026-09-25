import logging
from handgame.gui.screen import Screen
from enum import Enum

from PySide6.QtCore import QRect, Qt, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget

from handgame.gui.screens.settings import SettingWindow
from handgame.gui.ui.ui_shell import Ui_MainWindow

from handgame.gui.screens.settings import SettingWindow
from handgame.gui.ui.ui_shell import Ui_MainWindow
from handgame.gui.screens.main_menu import MainMenu
from handgame.gui.screens.game_select import GameSelectWindow
from handgame.games.game_context import DIFFICULTY_PRESETS
from handgame.games.game_controller import GAME_REGISTRY
from handgame.gui.screens.calibration import HandCalibrationScreen
from handgame.gui.screens.camera_select import CameraSelectScreen
from handgame.gui.screens.game_over import GameOverScreen
from handgame.gui.screens.gameplay import GameplayScreen
from handgame.gui.screens.minigame_select import MinigameSelectScreen, game_summaries
from handgame.gui.widgets.difficulty_modal import DifficultyModal
from handgame.core.events import CameraStatusEvent, FramePacket
from handgame.core.models import CameraState
from handgame.gui.frame_convert import frame_to_qimage
from handgame.gui.screens.calibration import CalibrationState

logger = logging.getLogger("HandGame2")



class DummyScreen(QWidget):
    """Placeholder view for testing the router before real screens exist."""

    def __init__(self, name: str, router_callback):
        super().__init__()
        layout = QVBoxLayout(self)

        label = QLabel(f"To jest ekran: {name}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; font-weight: bold; color: #0B2545;")

        btn_back = QPushButton("Wróć do Menu Głównego")
        btn_back.setFixedSize(250, 50)
        btn_back.clicked.connect(lambda: router_callback(Screen.MAIN_MENU))

        layout.addWidget(label)
        layout.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignCenter)



# Main App Window Class

class MainWindow(QMainWindow):
    def __init__(self, controller=None):
        """``controller`` - optional ``GUIIntegrationController``. Without it the
        screens still navigate, but no camera / session calls are made."""
        super().__init__()
        self.controller = controller
        self.setWindowTitle("HandGame 2.0")

        # Target RPi resolution / optimization
        self.resize(1024, 768)
        self.setMinimumSize(800, 600)
        
        # Init core modules (GUI-CORE-8)
        self._init_core_modules()

        # Init UI (layouts and router)
        self._init_ui()

        logger.info("Okienko zostało pomyślnie zainicjalizowane.")

    def _init_core_modules(self):
        """Init hook for external modules (camera, AI, session); creates manager instances."""
        logger.debug("Inicjalizacja modułów sprzętowych i logiki...")
        # TODO: self.camera_manager = CameraManager()
        # TODO: self.inference_worker = InferenceWorker()
        # TODO: self.session_manager = SessionManager()

        # Placeholders for safe_teardown
        self.camera_manager = None
        self.inference_worker = None

    def _init_ui(self):
        """Builds the main app shell (QStackedWidget)."""
        # Central widget (base for everything)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # plain QWidget: needs this for the stylesheet's navy header background
        self.ui.appHeader.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.windowGeometry = None
        self.router = self.ui.stackedWidget
        screen = self.screen()
        available = screen.availableGeometry()


        startWidth = min(1280, available.width())
        startHeight = min(720, available.height())

        self.resize(startWidth, startHeight)
        self.move(available.center()-self.frameGeometry().center())

        self._register_screens()

        self._history = []
        self._currentPage: str | None = None

        self.ui.settingsButton.clicked.connect(lambda: self.change_screen(Screen.SETTINGS))
        self.ui.backButton.clicked.connect(lambda: self.goBack())
        # Add screens to router
        

        self.settings_screen.resolutionChange.connect(self._on_resolution_change)
        self.settings_screen.fullScreenRequest.connect(self._on_fullscreen_request)
        self.settings_screen.themeChange.connect(self._on_theme_change)
        if self.themeManager is not None:
            self.settings_screen.setTheme(self.themeManager.current_theme)

        self.main_menu_screen.requestPage.connect(self.change_screen)
        self._wire_game_flow()
        # Set start screen
        self.change_screen(Screen.MAIN_MENU)

    def _register_screens(self):
        """
        Registers all views in the QStackedWidget.
        """
        logger.debug("Rejestracja ekranów w routerze...")

        self.main_menu_screen = MainMenu()
        self.settings_screen = SettingWindow()
        self.game_select = GameSelectWindow()

        self.camera_select_screen = CameraSelectScreen()
        self.calibration_screen = HandCalibrationScreen()
        self.minigame_select_screen = MinigameSelectScreen(game_summaries(GAME_REGISTRY))
        self.gameplay_screen = GameplayScreen()
        self.game_over_screen = GameOverScreen()
        self.difficulty_modal = DifficultyModal()

        self.screens = {
            Screen.MAIN_MENU: self.main_menu_screen,
            Screen.GAME_SELECT: self.minigame_select_screen,
            Screen.SETTINGS: self.settings_screen,
            Screen.CAMERA_CALIBRATION: self.calibration_screen,
            Screen.DEMO_MODE: DummyScreen("Tryb Demonstracyjny", self.change_screen),
            Screen.DEV_MODE: DummyScreen("Tryb Developerski", self.change_screen),
            Screen.RESULTS: DummyScreen("Wyniki Ostatniej Gry", self.change_screen),
            Screen.GAME_VIEW: self.gameplay_screen,
            Screen.CAMERA_SELECT: self.camera_select_screen,
            Screen.GAME_OVER: self.game_over_screen,
        }

        for screen_enum in Screen:
            if screen_enum in self.screens:
                self.router.addWidget(self.screens[screen_enum])
    def _keepOnScreen(self) -> None:
        screen = self.screen()
        available = screen.availableGeometry()
        frame = self.frameGeometry()

        x=frame.x()
        y=frame.y()

        if frame.right()>available.right():
            x=available.right() - frame.width() + 1
        if frame.bottom() > available.bottom():
            y = available.bottom() - frame.height() + 1
        if x < available.left():
            x = available.left()
        if y < available.top():
            y = available.top()
        self.move(x,y)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_F11 and self.isFullScreen():
            self.showNormal()
            self.setGeometry(self.windowGeometry)
            self.settings_screen.ui.fullScreenCheckBox.setChecked(False) 
        elif event.key() == Qt.Key.Key_F11 and not self.isFullScreen():
            self.windowGeometry = self.geometry()
            self.showFullScreen()
            self.settings_screen.ui.fullScreenCheckBox.setChecked(True) 
        else:
            super().keyPressEvent(event)

    def goBack(self) -> None:
        if not self._history:
            return
        prevId = self._history.pop()
        self._currentPage = prevId
        self.router.setCurrentIndex(prevId)

    def _keepOnScreen(self) -> None:
        screen = self.screen()
        available = screen.availableGeometry()
        frame = self.frameGeometry()

        x = frame.x()
        y = frame.y()

        if frame.right() > available.right():
            x = available.right() - frame.width() + 1
        if frame.bottom() > available.bottom():
            y = available.bottom() - frame.height() + 1
        if x < available.left():
            x = available.left()
        if y < available.top():
            y = available.top()
        self.move(x, y)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_F11 and self.isFullScreen():
            self.showNormal()
            if self.windowGeometry is not None:
                self.setGeometry(self.windowGeometry)
            self.settings_screen.ui.fullScreenCheckBox.setChecked(False)
        elif event.key() == Qt.Key.Key_F11 and not self.isFullScreen():
            self.windowGeometry = self.geometry()
            self.showFullScreen()
            self.settings_screen.ui.fullScreenCheckBox.setChecked(True)
        else:
            super().keyPressEvent(event)


    # Game Flow (camera -> calibration -> minigame -> difficulty -> game -> game over)

    def _wire_game_flow(self) -> None:
        """Screens only emit signals; navigation decisions live here."""
        self._selected_camera_id: str | None = None
        self._selected_game_id: str | None = None
        self._selected_level: int | None = None

        self.camera_select_screen.camera_confirmed.connect(self._on_camera_confirmed)

        self.calibration_screen.back_requested.connect(
            lambda: self.change_screen(Screen.CAMERA_SELECT)
        )
        self.calibration_screen.calibration_confirmed.connect(
            lambda: self.change_screen(Screen.GAME_SELECT)
        )

        self.minigame_select_screen.back_requested.connect(
            lambda: self.change_screen(Screen.CAMERA_CALIBRATION)
        )
        self.minigame_select_screen.game_selected.connect(self._on_game_selected)

        self.difficulty_modal.difficulty_confirmed.connect(self._on_difficulty_confirmed)

        self.calibration_screen.skip_requested.connect(
            lambda: self.change_screen(Screen.GAME_SELECT)
        )

        self.gameplay_screen.exit_requested.connect(self._on_gameplay_exit)
        self.gameplay_screen.pause_toggled.connect(self._on_pause_toggled)

        self.game_over_screen.play_again_requested.connect(self._start_gameplay)
        self.game_over_screen.back_to_menu_requested.connect(
            lambda: self.change_screen(Screen.GAME_SELECT)
        )

        if self.controller is not None:
            self.controller.ui_frame_ready.connect(self._on_frame_ready)
            self.controller.ui_camera_status_changed.connect(self._on_camera_status)
            self.controller.ui_game_finished.connect(self.show_game_result)

    def _call_controller(self, method: str, *args) -> bool:
        """Call ``controller.<method>(*args)``; log instead of crashing the GUI."""
        if self.controller is None:
            return False
        try:
            getattr(self.controller, method)(*args)
        except Exception:
            logger.exception(f"Wywołanie {method}{args} nie powiodło się")
            return False
        return True

    @Slot(str)
    def _on_camera_confirmed(self, camera_id: str) -> None:
        previous = self._selected_camera_id
        self._selected_camera_id = camera_id
        logger.info(f"Wybrano kamerę: {camera_id}")
        self.calibration_screen.clear_frame()
        self.gameplay_screen.preview.clear_frame()
        if self.controller is not None:
            if previous is not None and previous != camera_id:
                self._call_controller("stop_camera", previous)
            self.calibration_screen.set_state(CalibrationState.CONNECTING)
            if not self._call_controller("select_camera", camera_id, "PLAYER_1"):
                self.calibration_screen.set_state(CalibrationState.CAMERA_ERROR)
        self.change_screen(Screen.CAMERA_CALIBRATION)

    @Slot(object)
    def _on_frame_ready(self, packet: object) -> None:
        """Route the selected camera's frames to whichever preview is visible."""
        if not isinstance(packet, FramePacket) or packet.camera_id.name != self._selected_camera_id:
            return
        current = self.router.currentWidget()
        if current is self.calibration_screen:
            target = self.calibration_screen.preview
        elif current is self.gameplay_screen and self.gameplay_screen.is_preview_visible():
            target = self.gameplay_screen.preview
        else:
            return
        image = frame_to_qimage(packet.frame)
        if image is not None:  # mock worker sends no real image
            target.update_frame(QPixmap.fromImage(image))

    @Slot(object)
    def _on_camera_status(self, event: object) -> None:
        if not isinstance(event, CameraStatusEvent):
            return
        if event.camera_id.name != self._selected_camera_id:
            return
        state = {
            CameraState.CONNECTING: CalibrationState.CONNECTING,
            CameraState.STREAMING: CalibrationState.DETECTING,
            CameraState.ERROR: CalibrationState.CAMERA_ERROR,
        }.get(event.current_state)
        if state is not None:
            self.calibration_screen.set_state(state)

    @Slot(str)
    def _on_game_selected(self, game_id: str) -> None:
        self._selected_game_id = game_id
        self.difficulty_modal.open_over(self.centralWidget())

    @Slot(int)
    def _on_difficulty_confirmed(self, level: int) -> None:
        self._selected_level = level
        logger.info(f"Wybrano grę {self._selected_game_id}, poziom {level}")
        self._start_gameplay()

    def _start_gameplay(self) -> None:
        level = self._selected_level if self._selected_level is not None else 3
        self.gameplay_screen.reset(lives=DIFFICULTY_PRESETS[level].allowed_mistakes)
        self.change_screen(Screen.GAME_VIEW)
        if self._selected_game_id is not None:
            # Session auto-starts once camera + AI report ready (SessionManager).
            if self._call_controller("prepare_game", self._selected_game_id, level):
                self._call_controller("start_game")

    @Slot()
    def _on_gameplay_exit(self) -> None:
        self.change_screen(Screen.GAME_SELECT)
        self._call_controller("finish_game")

    @Slot(bool)
    def _on_pause_toggled(self, paused: bool) -> None:
        self._call_controller("pause_game" if paused else "resume_game")

    @Slot(object)
    def show_game_result(self, result: object) -> None:
        """Hook for ``GUIIntegrationController.ui_game_finished``.

        Only a game that ends while it is on screen opens GAME_OVER.
        """
        self.game_over_screen.show_result(result)
        if self.router.currentWidget() is self.gameplay_screen:
            self.change_screen(Screen.GAME_OVER)

    # Control Methods (router and state)
    @Slot(Screen)
    def change_screen(self, screen: Screen):
        """Switches the currently displayed screen."""
        if screen is Screen.SETTINGS:
            self.settings_screen.setResolution(self.width(), self.height())
        logger.info(f"Przełączanie ekranu na {screen.name}")
        self.router.setCurrentIndex(screen.value)
        if screen.value == self._currentPage:
            return
        # A finished game is not a page to go back to: Back from GAME_OVER
        # returns to wherever the player was before the game (game select).
        leaving_finished_game = (
            screen is Screen.GAME_OVER and self._currentPage == Screen.GAME_VIEW.value
        )
        if self._currentPage is not None and not leaving_finished_game:
            self._history.append(self._currentPage)
        self._currentPage = screen.value


    @Slot()
    def emergency_reset(self):
        """Emergency return handler (GUI-CORE-9 / DEMO-4).

        Stops current game/camera and returns to menu.
        """
        logger.warning("Wymuszono awaryjny reset sesji. Powrót do menu...")

        # TODO: self.session_manager.reset()
        # TODO: if self.inference_worker.isRunning(): self.inference_worker.stop()

        self.change_screen(Screen.MAIN_MENU)
        QMessageBox.warning(
            self,
            "Awaryjny Reset",
            "Sesja została awaryjnie zresetowana.\nPowrót do Menu.",
        )

    # Cleanup and Shutdown
    @Slot()
    def safe_teardown(self):
        """Stops all workers and releases camera USB ports.

        Called by app.aboutToQuit from main.py.
        """
        logger.info("Inicjowanie zamykania okienka...")

        if self.inference_worker:
            logger.info("Zatrzymywanie workera AI...")
            # self.inference_worker.stop()
            # self.inference_worker.wait(2000)

        if self.camera_manager:
            logger.info("Zwalnianie dostępu do kamer USB...")
            # self.camera_manager.release_all()
            
        logger.info("Wszystkie zasoby zostały prawidłowo zwolnione.")

    # Settings
    @Slot(int, int)
    def _on_resolution_change(self, width: int, height: int):
        if self.isFullScreen():
            self.showNormal()
        screen = self.screen()
        available = screen.availableGeometry()
        frame = self.frameGeometry()
        heightDiff = frame.height() - self.height()
        widthDiff = frame.width() - self.width()
        width = min(width, available.width()-widthDiff)
        height = min(height, available.height()-heightDiff)
        
        self.resize(width, height)
        self.windowGeometry = self.geometry()
        self._keepOnScreen()

    @Slot()
    def _on_fullscreen_request(self):
        self.showFullScreen()

    @Slot(object)
    def _on_theme_change(self, theme_id):
        if self.themeManager is not None:
            self.themeManager.apply(theme_id)
