from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout

from app.ui.widgets.theme_toggle import ThemeToggle


class ThemePanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setStyleSheet("""
            QWidget {
                background-color: #EEF2F7;
            }
            QFrame#panelCard {
                background-color: white;
                border: 1px solid #D9E2EC;
                border-radius: 22px;
            }
            QLabel#titleLabel {
                font-size: 24px;
                font-weight: 700;
                color: #0F172A;
            }
            QLabel#descLabel {
                font-size: 15px;
                color: #475569;
            }
            QLabel#modeLabel {
                font-size: 18px;
                font-weight: 600;
                color: #1E293B;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)

        card = QFrame()
        card.setObjectName("panelCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(18)

        title = QLabel("Apariencia")
        title.setObjectName("titleLabel")

        desc = QLabel("Configura el tema visual de la aplicación.")
        desc.setObjectName("descLabel")

        mode_row = QHBoxLayout()
        mode_row.setSpacing(24)

        mode_text = QVBoxLayout()
        mode_text.setSpacing(8)

        mode_label = QLabel("Modo oscuro")
        mode_label.setObjectName("modeLabel")

        helper = QLabel("Activa una apariencia nocturna elegante para la interfaz.")
        helper.setObjectName("descLabel")
        helper.setWordWrap(True)

        mode_text.addWidget(mode_label)
        mode_text.addWidget(helper)

        self.theme_toggle = ThemeToggle(checked=False)

        mode_row.addLayout(mode_text)
        mode_row.addStretch()
        mode_row.addWidget(self.theme_toggle, alignment=Qt.AlignRight | Qt.AlignVCenter)

        card_layout.addWidget(title)
        card_layout.addWidget(desc)
        card_layout.addSpacing(12)
        card_layout.addLayout(mode_row)

        root.addWidget(card)
        root.addStretch()