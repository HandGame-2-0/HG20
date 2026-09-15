import logging
from handgame.gui.screen import Screen
from enum import Enum

from PySide6.QtCore import QRect, Qt, Slot
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget

from handgame.gui.screens.settings import SettingWindow
from handgame.gui.ui.ui_shell import Ui_MainWindow

from handgame.gui.screens.settings import SettingWindow
from handgame.gui.ui.ui_shell import Ui_MainWindow
from handgame.gui.screens.main_menu import MainMenu
from handgame.gui.screens.game_select import GameSelectWindow

logger = logging.getLogger("HandGame2")


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


# =====================================================================
# 2. VIEW PLACEHOLDERS (to be replaced by Kamil's and Oskar's final classes)
# =====================================================================
# Note: once real screens exist, import them here
# (e.g. from gui.views.main_menu import MainMenu) and swap in.
class DummyScreen(QWidget):
    """Placeholder view for testing the router before real screens exist."""

    def __init__(self, name: str, router_callback):
        super().__init__()
        layout = QVBoxLayout(self)

        label = QLabel(f"To jest ekran: {name}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; font-weight: bold;")

        btn_back = QPushButton("Wróć do Menu Głównego")
        btn_back.setFixedSize(250, 50)
        btn_back.clicked.connect(lambda: router_callback(Screen.MAIN_MENU))

        layout.addWidget(label)
        layout.addWidget(btn_back, alignment=Qt.AlignmentFlag.AlignCenter)


# =====================================================================
# 3. MAIN APPLICATION WINDOW CLASS (GUI-CORE-3)
# =====================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HandGame 2.0")

        # Target RPi resolution / optimization
        self.resize(1024, 768)
        self.setMinimumSize(800, 600)
        
        # 1. Init core modules (GUI-CORE-8)
        self._init_core_modules()

        # 2. Init UI (layouts and router)
        self._init_ui()

        logger.info("MainWindow zostało pomyślnie zainicjalizowane.")

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
        self.main_menu_screen.requestPage.connect(self.change_screen)
        # Set start screen
        self.change_screen(Screen.MAIN_MENU)

    def _register_screens(self):
        """Registers all views in the QStackedWidget (GUI-CORE-4).

        Order must match the Screen enum values.
        """
        logger.debug("Rejestracja ekranów w routerze...")

        # Kamil will wire in his real classes here:
        # e.g. self.main_menu = MainMenu(router_callback=self.change_screen)
        self.main_menu_screen = MainMenu()
        self.settings_screen = SettingWindow()
        self.game_select = GameSelectWindow()
        self.screens = {
            Screen.MAIN_MENU: self.main_menu_screen,
            Screen.GAME_SELECT:  DummyScreen("Wybór gry", self.change_screen),#self.game_select,
        self.settings_screen = SettingWindow()
        self.screens = {
            Screen.MAIN_MENU: DummyScreen("Menu Główne", self.change_screen),
            Screen.GAME_SELECT: DummyScreen("Wybór Gry", self.change_screen),
            Screen.SETTINGS: self.settings_screen,
            Screen.CAMERA_CALIBRATION: DummyScreen("Kalibracja Kamery", self.change_screen),
            Screen.DEMO_MODE: DummyScreen("Tryb Demonstracyjny", self.change_screen),
            Screen.DEV_MODE: DummyScreen("Tryb Developerski", self.change_screen),
            Screen.RESULTS: DummyScreen("Wyniki Ostatniej Gry", self.change_screen),
            Screen.GAME_VIEW: DummyScreen("Widok Minigry", self.change_screen),
        }

        # Add widgets to router in correct order
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

    # =====================================================================
    # CONTROL METHODS (ROUTER AND STATE)
    # =====================================================================
    @Slot(Screen)
    def change_screen(self, screen: Screen):
        """Switches the currently displayed screen."""
        if screen is Screen.SETTINGS:
            self.settings_screen.setResolution(self.width(), self.height())
        logger.info(f"Przełączanie ekranu na: {screen.name}")
        self.router.setCurrentIndex(screen.value)
        if screen.value == self._currentPage:
            return
        if self._currentPage is not None:
            self._history.append(self._currentPage)
        self._currentPage = screen.value


    @Slot()
    def emergency_reset(self):
        """Emergency return handler (GUI-CORE-9 / DEMO-4).

        Stops current game/camera and returns to menu.
        """
        logger.warning("Wymuszono awaryjny reset sesji! Powrót do menu...")

        # TODO: self.session_manager.reset()
        # TODO: if self.inference_worker.isRunning(): self.inference_worker.stop()

        self.change_screen(Screen.MAIN_MENU)
        QMessageBox.warning(
            self,
            "Awaryjny Reset",
            "Sesja została awaryjnie zresetowana.\nPowrót do Menu Głównego.",
        )

    # =====================================================================
    # CLEANUP AND SHUTDOWN (GRACEFUL SHUTDOWN)
    # =====================================================================
    @Slot()
    def safe_teardown(self):
        """Stops all workers and releases camera USB ports.

        Called by app.aboutToQuit from main.py.
        """
        logger.info("Inicjowanie procedury bezpiecznego zamykania z MainWindow (Teardown)...")

        if self.inference_worker:
            logger.info("Zatrzymywanie workera AI...")
            # self.inference_worker.stop()
            # self.inference_worker.wait(2000)

        if self.camera_manager:
            logger.info("Zwalnianie dostępu do kamer USB...")
            # self.camera_manager.release_all()
            
        logger.info("Wszystkie zasoby zostały prawidłowo zwolnione.")

        logger.info("Wszystkie zasoby zostały prawidłowo zwolnione.")

    # =====================================================================
    # SETTINGS
    # =====================================================================
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
        height_diff = frame.height() - self.height()
        width_diff = frame.width() - self.width()
        width = min(width, available.width() - width_diff)
        height = min(height, available.height() - height_diff)

        self.resize(width, height)
        self.windowGeometry = self.geometry()
        self._keepOnScreen()

    @Slot()
    def _on_fullscreen_request(self):
        self.showFullScreen()
