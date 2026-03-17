from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout


class StatusBarView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addStretch()

        self.datetime_label = QLabel()
        self.datetime_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.datetime_label.setStyleSheet("""
            QLabel {
                color: #222222;
                font-size: 15px;
                font-weight: 500;
            }
        """)

        layout.addWidget(self.datetime_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time)
        self.timer.start(1000)

        self._update_time()

    def _update_time(self) -> None:
        now = datetime.now()
        text = now.strftime("%a %b %d %Y %H:%M:%S")
        self.datetime_label.setText(text)