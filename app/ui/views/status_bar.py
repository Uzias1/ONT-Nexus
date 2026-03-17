from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout

from app.ui.theme_manager import ThemeManager


class StatusBarView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addStretch()

        self.datetime_label = QLabel()
        self.datetime_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(self.datetime_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)

        self._update_time()
        self.set_scale(15)
        self.apply_theme()

    def _update_time(self) -> None:
        now = datetime.now()
        text = now.strftime("%I:%M %p  %d %B %Y")
        self.datetime_label.setText(text)

    def set_scale(self, font_size: int) -> None:
        font = self.datetime_label.font()
        font.setPointSize(font_size)
        font.setWeight(QFont.Medium)
        self.datetime_label.setFont(font)

    def apply_theme(self) -> None:
        theme = ThemeManager.get_theme()
        self.datetime_label.setStyleSheet(f"""
            QLabel {{
                color: {theme.text};
                font-weight: 500;
                background: transparent;
            }}
        """)