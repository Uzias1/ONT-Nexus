from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame


class CircleIndicator(QFrame):
    def __init__(self, border_color: str = "#333333", parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: 2px solid {border_color};
                border-radius: 14px;
            }}
        """)


class ToolbarView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(46)

        self.setStyleSheet("""
            QWidget {
                background-color: #EDEDED;
                border-bottom: 1px solid #BFBFBF;
            }
            QLabel {
                color: #555555;
                font-size: 16px;
                font-weight: 500;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 6, 14, 6)
        layout.setSpacing(8)

        self.title_label = QLabel("Vista principal")
        self.title_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        layout.addWidget(self.title_label)
        layout.addStretch()

        layout.addWidget(CircleIndicator("#333333"))
        layout.addWidget(CircleIndicator("#333333"))
        layout.addWidget(CircleIndicator("#2196F3"))