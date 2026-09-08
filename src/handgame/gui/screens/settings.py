from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QPushButton, QSpinBox
from handgame.gui.ui.ui_settings import Ui_Form

RESOLUTIONS = [
    (800, 600),
    (1024, 768),
    (1280, 720),
    (1600, 900),
    (1920, 1080),
]
class SettingWindow(QWidget):
    resolutionChange = Signal(int,int)
    fullScreenRequest = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        for w, h in RESOLUTIONS:
            self.ui.resComboBox.addItem(f"{w} x {h}",(w,h))
        
        self.ui.saveButton.clicked.connect(self.emitResolution)

    def setResolution(self, width: int, height: int) -> None:
        target = (width, height)
        for i in range(self.ui.resComboBox.count()):
            if self.ui.resComboBox.itemData(i) == target:
                self.ui.resComboBox.setCurrentIndex(i)
                return
        self.ui.resComboBox.setCurrentIndex(0)
    def emitResolution(self) -> None:
        if self.ui.fullScreenCheckBox.isChecked():
            self.fullScreenRequest.emit()
            return
        w, h = self.ui.resComboBox.currentData()
        self.resolutionChange.emit(w,h)