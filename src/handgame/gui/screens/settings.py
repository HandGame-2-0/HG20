from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QPushButton, QSpinBox
from handgame.gui.themes.palettes import PALETTES, ThemeId
from handgame.gui.ui.ui_settings import Ui_Form

RESOLUTIONS = [
    (800, 600),
    (1024, 768),
    (1280, 720),
    (1600, 900),
    (1920, 1080),
]


class SettingWindow(QWidget):
    resolutionChange = Signal(int, int)
    fullScreenRequest = Signal()
    themeChange = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        for w, h in RESOLUTIONS:
            self.ui.resComboBox.addItem(f"{w} x {h}", (w, h))

        for theme_id, tokens in PALETTES.items():
            self.ui.themeComboBox.addItem(tokens.name, theme_id)

        self.ui.saveButton.clicked.connect(self.emitResolution)
        self.ui.themeComboBox.currentIndexChanged.connect(self.emitTheme)

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
        self.resolutionChange.emit(w, h)

    def setTheme(self, theme_id: ThemeId) -> None:
        for i in range(self.ui.themeComboBox.count()):
            if self.ui.themeComboBox.itemData(i) == theme_id:
                self.ui.themeComboBox.blockSignals(True)
                self.ui.themeComboBox.setCurrentIndex(i)
                self.ui.themeComboBox.blockSignals(False)
                return

    def emitTheme(self, _index: int = 0) -> None:
        theme_id = self.ui.themeComboBox.currentData()
        if theme_id is not None:
            self.themeChange.emit(theme_id)
