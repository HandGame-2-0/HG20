from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QKeyEvent


class InputHandler(QObject):
    # Sygnały emitowane niezależnie od źródła wejścia (Klawiatura / Kamera AI)
    letter_detected = Signal(str)
    action_detected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._enabled = True

    def set_enabled(self, enabled: bool):
        self._enabled = enabled

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if not self._enabled:
            return super().eventFilter(watched, event)

        if event.type() == QEvent.Type.KeyPress:
            key_event: QKeyEvent = event
            key = key_event.key()
            text = key_event.text().upper()

            # 1. Litery A-Z -> Trafienie w kreta / znak migowy
            if text and text.isalpha() and len(text) == 1:
                self.letter_detected.emit(text)
                return True

            # 2. Cyfry 1-5 -> Szybki wybór poziomu trudności w menu
            if Qt.Key.Key_1 <= key <= Qt.Key.Key_5:
                digit = key - Qt.Key.Key_0
                self.action_detected.emit(f"SELECT_{digit}")
                return True

            # 3. Klawisze funkcyjne -> Sterowanie menu/stanem gry
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
                self.action_detected.emit("CONFIRM")
                return True
            elif key == Qt.Key.Key_Escape:
                self.action_detected.emit("EXIT")
                return True
            elif key == Qt.Key.Key_R:
                self.action_detected.emit("RESTART")
                return True

        return super().eventFilter(watched, event)

    # --- PRZYSZŁA INTEGRACJA Z OPENCV / MODELIEM AI ---
    def process_frame(self, frame):
        pass
