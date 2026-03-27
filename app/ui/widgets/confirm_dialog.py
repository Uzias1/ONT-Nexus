from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QWidget,
)

from app.ui.theme_manager import ThemeManager
from app.ui.widgets.buttons import SuccessButton, DangerButton, WarningButton


class BaseConfirmDialog(QDialog):
    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(title)
        self.setMinimumWidth(560)

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(18, 18, 18, 18)

        self.card = QFrame()
        self.card.setObjectName("dialogCard")

        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(24, 22, 24, 22)
        self.card_layout.setSpacing(18)

        self.title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self.title_label.setFont(title_font)

        self.card_layout.addWidget(self.title_label)
        self.root_layout.addWidget(self.card)

        self._apply_base_theme()

    def _apply_base_theme(self) -> None:
        theme = ThemeManager.get_theme()

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme.app_bg};
            }}
            QFrame#dialogCard {{
                background-color: {theme.main_card_bg};
                border: 1px solid {theme.border};
                border-radius: 18px;
            }}
            QLabel {{
                color: {theme.text};
                background: transparent;
            }}
        """)


class ConfirmChangesDialog(BaseConfirmDialog):
    def __init__(self, values: dict[str, str], parent=None) -> None:
        super().__init__("Confirmar cambios", parent)

        self.info = QLabel("Verifica los nuevos valores antes de confirmar.")
        self.info.setWordWrap(True)
        self.card_layout.addWidget(self.info)

        self.values_frame = QFrame()
        self.values_frame.setObjectName("valuesFrame")

        self.values_layout = QVBoxLayout(self.values_frame)
        self.values_layout.setContentsMargins(16, 16, 16, 16)
        self.values_layout.setSpacing(10)

        for key, value in values.items():
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(12)

            key_label = QLabel(f"{key}:")
            key_font = key_label.font()
            key_font.setBold(True)
            key_label.setFont(key_font)

            value_label = QLabel(value.strip() if value.strip() else "(vacío)")
            value_label.setWordWrap(True)

            row_layout.addWidget(key_label, 2)
            row_layout.addWidget(value_label, 3)

            self.values_layout.addWidget(row)

        self.card_layout.addWidget(self.values_frame)

        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.card_layout.addWidget(self.result_label)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(16)
        buttons_row.setAlignment(Qt.AlignHCenter)

        self.btn_confirmar = SuccessButton("Confirmar")
        self.btn_cancelar = DangerButton("Cancelar")

        self.btn_confirmar.clicked.connect(self._confirm)
        self.btn_cancelar.clicked.connect(self.reject)

        buttons_row.addWidget(self.btn_confirmar)
        buttons_row.addWidget(self.btn_cancelar)

        self.card_layout.addLayout(buttons_row)

        self.apply_theme()

    def _confirm(self) -> None:
        self.result_label.setText("Cambio confirmado")
        self.result_label.setStyleSheet("color: #7BBE3C; font-weight: 700;")
        self.accept()

    def apply_theme(self) -> None:
        self._apply_base_theme()
        theme = ThemeManager.get_theme()

        self.values_frame.setStyleSheet(f"""
            QFrame#valuesFrame {{
                background-color: {theme.section_bg};
                border: 1px solid {theme.border};
                border-radius: 12px;
            }}
        """)


class ConfirmResetDialog(BaseConfirmDialog):
    def __init__(self, parent=None) -> None:
        super().__init__("Reestablecer valores", parent)

        self.message = QLabel("¿Seguro que desea reestablecer los valores?")
        self.message.setWordWrap(True)
        self.message.setAlignment(Qt.AlignCenter)
        self.card_layout.addWidget(self.message)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(16)
        buttons_row.setAlignment(Qt.AlignHCenter)

        self.btn_si = WarningButton("Sí, reestablecer")
        self.btn_no = DangerButton("No")

        self.btn_si.clicked.connect(self.accept)
        self.btn_no.clicked.connect(self.reject)

        buttons_row.addWidget(self.btn_si)
        buttons_row.addWidget(self.btn_no)

        self.card_layout.addLayout(buttons_row)