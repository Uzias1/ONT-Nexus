from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QSizePolicy


class PrimaryButton(QPushButton):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)

        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(52)
        self.setMinimumWidth(150)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.setStyleSheet("""
            QPushButton {
                background-color: #0D6EFD;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                padding: 10px 18px;
            }
            QPushButton:hover {
                background-color: #0B5ED7;
            }
            QPushButton:pressed {
                background-color: #0A58CA;
            }
            QPushButton:disabled {
                background-color: #9BBEF9;
                color: #EAF2FF;
            }
        """)


class SecondaryButton(QPushButton):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)

        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(52)
        self.setMinimumWidth(150)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #0D6EFD;
                border: 2px solid #0D6EFD;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                padding: 10px 18px;
            }
            QPushButton:hover {
                background-color: #F2F7FF;
            }
            QPushButton:pressed {
                background-color: #E4EEFF;
            }
        """)