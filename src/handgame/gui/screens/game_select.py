from PySide6.QtWidgets import QWidget, QPushButton, QSpinBox
from handgame.gui.ui.ui_game_select import Ui_Form

class GameSelectWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

