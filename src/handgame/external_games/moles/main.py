import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget

from components.GameWidget import GameWidget


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gra - Kontener")

        # 1. Różowe tło okna głównego dla rozróżnienia
        self.setStyleSheet("background-color: #FFB6C1;")

        # Uruchomienie w trybie pełnoekranowym
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.showFullScreen()

        # 2. Główny layout (placeholder na widget gry)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            20, 20, 300, 120
        )  # Marginesy pokazujące różowy kontener

        # 3. Wstawienie widgetu gry do kontenera
        self.game_widget = GameWidget(parent=self)
        layout.addWidget(self.game_widget)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
