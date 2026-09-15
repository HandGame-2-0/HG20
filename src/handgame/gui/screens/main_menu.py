from PySide6.QtWidgets import QWidget
from handgame.gui.ui.ui_main_menu import Ui_Form
from PySide6.QtCore import Signal

from handgame.gui.screen import Screen

class MainMenu(QWidget):

    requestPage = Signal(Screen)
    def __init__(self) -> None:
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.resultsButton.clicked.connect(lambda: self.requestPage.emit(Screen.RESULTS))
        self.ui.playButton.clicked.connect(lambda: self.requestPage.emit(Screen.GAME_SELECT))
        self.ui.gameButton2.clicked.connect(lambda: self.requestPage.emit(Screen.CAMERA_CALIBRATION))