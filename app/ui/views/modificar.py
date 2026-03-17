from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QLineEdit,
    QSizePolicy,
    QDialog,
)

from app.ui.theme_manager import ThemeManager
from app.ui.widgets.buttons import SuccessButton, DangerButton, WarningButton
from app.ui.widgets.confirm_dialog import ConfirmChangesDialog, ConfirmResetDialog
from app.ui.widgets.theme_toggle import ThemeToggle


class ParamRow(QWidget):
    def __init__(self, label_text: str, placeholder: str = "", parent=None) -> None:
        super().__init__(parent)

        self.setStyleSheet("background: transparent;")

        self.layout_root = QHBoxLayout(self)
        self.layout_root.setContentsMargins(0, 0, 0, 0)
        self.layout_root.setSpacing(18)

        self.label = QLabel(label_text)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.layout_root.addWidget(self.label, 3, alignment=Qt.AlignVCenter)
        self.layout_root.addWidget(self.input, 2, alignment=Qt.AlignVCenter)

        self.apply_theme()

    def apply_theme(self) -> None:
        theme = ThemeManager.get_theme()

        self.label.setStyleSheet(f"""
            QLabel {{
                color: {theme.text};
                font-weight: 600;
                background: transparent;
                padding: 0px;
                margin: 0px;
            }}
        """)

        self.input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme.input_bg};
                color: {theme.input_text};
                border: 1px solid {theme.input_border};
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 16px;
            }}
            QLineEdit:focus {{
                border: 2px solid {theme.primary};
            }}
        """)

    def set_scale(
        self,
        label_size: int,
        input_size: int,
        input_height: int,
        label_min_width: int,
        input_width: int,
    ) -> None:
        label_font = self.label.font()
        label_font.setPointSize(label_size)
        label_font.setWeight(QFont.DemiBold)
        self.label.setFont(label_font)

        input_font = self.input.font()
        input_font.setPointSize(input_size)
        self.input.setFont(input_font)

        self.label.setMinimumWidth(label_min_width)
        self.label.setFixedHeight(max(28, input_height - 8))

        self.input.setFixedWidth(input_width)
        self.input.setFixedHeight(input_height)


class ThemeModeRow(QWidget):
    theme_toggled = Signal(bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.layout_root = QHBoxLayout(self)
        self.layout_root.setContentsMargins(0, 0, 0, 0)
        self.layout_root.setSpacing(18)

        self.title = QLabel("Modo claro / oscuro")
        self.title.setWordWrap(True)
        self.title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.toggle = ThemeToggle(checked=ThemeManager.is_dark())
        self.toggle.toggled.connect(self.theme_toggled.emit)

        self.layout_root.addWidget(self.title, 1)
        self.layout_root.addStretch()
        self.layout_root.addWidget(self.toggle, 0, alignment=Qt.AlignRight | Qt.AlignVCenter)

        self.apply_theme()

    def apply_theme(self) -> None:
        theme = ThemeManager.get_theme()

        self.title.setStyleSheet(f"""
            QLabel {{
                color: {theme.text};
                font-weight: 700;
                background: transparent;
            }}
        """)

    def set_scale(self, title_size: int, small_mode: bool = False) -> None:
        title_font = self.title.font()
        title_font.setPointSize(title_size)
        title_font.setWeight(QFont.Bold)
        self.title.setFont(title_font)

        if small_mode:
            self.toggle.set_toggle_size(108, 52)
        else:
            self.toggle.set_toggle_size(140, 68)


class ModificarView(QWidget):
    theme_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.param_rows = []
        self._build_ui()
        self._apply_responsive_sizes()

    def _build_ui(self) -> None:
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(20, 16, 20, 16)
        self.root_layout.setSpacing(0)

        self.main_card = QFrame()
        self.main_card.setObjectName("mainCard")

        self.main_layout = QVBoxLayout(self.main_card)
        self.main_layout.setContentsMargins(28, 24, 28, 28)
        self.main_layout.setSpacing(20)

        self.page_title = QLabel("Modificar parámetros")
        self.page_title.setObjectName("pageTitle")
        self.main_layout.addWidget(self.page_title)

        self.form_panel = QFrame()
        self.form_panel.setObjectName("formPanel")

        self.form_layout = QVBoxLayout(self.form_panel)
        self.form_layout.setContentsMargins(28, 24, 28, 24)
        self.form_layout.setSpacing(22)

        self.theme_row = ThemeModeRow()
        self.theme_row.theme_toggled.connect(self._on_theme_toggled)
        self.form_layout.addWidget(self.theme_row)

        self.row_wifi = ParamRow("Porcentaje mínimo de aceptación wifi:", "Ej. 80")
        self.row_tx_min = ParamRow("Valor mínimo de Tx:", "Ej. -8.00")
        self.row_rx_min = ParamRow("Valor mínimo de Rx:", "Ej. -27.00")
        self.row_tx_max = ParamRow("Valor máximo de Tx:", "Ej. 3.00")
        self.row_rx_max = ParamRow("Valor máximo de Rx:", "Ej. -8.00")

        self.param_rows = [
            self.row_wifi,
            self.row_tx_min,
            self.row_rx_min,
            self.row_tx_max,
            self.row_rx_max,
        ]

        for row in self.param_rows:
            self.form_layout.addWidget(row)

        self.main_layout.addWidget(self.form_panel)
        self.main_layout.addStretch()

        self.buttons_panel = QFrame()
        self.buttons_panel.setObjectName("buttonsPanel")

        self.buttons_layout = QHBoxLayout(self.buttons_panel)
        self.buttons_layout.setContentsMargins(24, 18, 24, 18)
        self.buttons_layout.setSpacing(26)
        self.buttons_layout.setAlignment(Qt.AlignHCenter)

        self.btn_aceptar = SuccessButton("Aceptar")
        self.btn_cancelar = DangerButton("Cancelar")
        self.btn_restablecer = WarningButton("Reestablecer")

        self.buttons_layout.addWidget(self.btn_aceptar)
        self.buttons_layout.addWidget(self.btn_cancelar)
        self.buttons_layout.addWidget(self.btn_restablecer)

        self.main_layout.addWidget(self.buttons_panel)
        self.root_layout.addWidget(self.main_card)

        self.apply_theme()

    def _on_theme_toggled(self, checked: bool) -> None:
        ThemeManager.set_dark(checked)
        self.theme_changed.emit()

    def apply_theme(self) -> None:
        theme = ThemeManager.get_theme()

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme.app_bg};
            }}

            QFrame#mainCard {{
                background-color: {theme.main_card_bg};
                border: 1px solid {theme.border};
                border-radius: 24px;
            }}

            QFrame#formPanel {{
                background-color: {theme.section_bg};
                border: 1px solid {theme.border};
                border-radius: 18px;
            }}

            QFrame#buttonsPanel {{
                background-color: {theme.section_alt_bg};
                border: 1px solid {theme.border};
                border-radius: 18px;
            }}

            QLabel#pageTitle {{
                color: {theme.title};
                font-weight: 800;
                background: transparent;
            }}
        """)

        for row in self.param_rows:
            row.apply_theme()

        self.theme_row.apply_theme()

    def get_current_values(self) -> dict[str, str]:
        return {
            "Porcentaje mínimo de aceptación wifi": self.row_wifi.input.text(),
            "Valor mínimo de Tx": self.row_tx_min.input.text(),
            "Valor mínimo de Rx": self.row_rx_min.input.text(),
            "Valor máximo de Tx": self.row_tx_max.input.text(),
            "Valor máximo de Rx": self.row_rx_max.input.text(),
        }

    def confirm_changes(self) -> bool:
        dialog = ConfirmChangesDialog(self.get_current_values(), self)
        return dialog.exec() == QDialog.Accepted

    def confirm_reset(self) -> bool:
        dialog = ConfirmResetDialog(self)
        return dialog.exec() == QDialog.Accepted

    def reset_default_values(self) -> None:
        self.row_wifi.input.setText("80")
        self.row_tx_min.input.setText("-8.00")
        self.row_rx_min.input.setText("-27.00")
        self.row_tx_max.input.setText("3.00")
        self.row_rx_max.input.setText("-8.00")

    def clear_fields(self) -> None:
        for row in self.param_rows:
            row.input.clear()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_responsive_sizes()

    def _apply_responsive_sizes(self) -> None:
        w = max(self.width(), 760)
        h = max(self.height(), 620)

        title_size = min(max(int(w / 42), 22), 36)
        theme_title_size = min(max(int(w / 65), 15), 22)
        row_label_size = min(max(int(w / 100), 11), 18)
        row_input_size = min(max(int(w / 110), 10), 17)
        input_height = min(max(int(h / 16), 32), 38)

        label_min_width = min(max(int(w / 3.1), 220), 420)
        input_width = min(max(int(w / 3), 150), 200)

        button_width = min(max(int(w / 6.2), 160), 260)
        button_height = min(max(int(h / 12), 56), 76)

        title_font = self.page_title.font()
        title_font.setPointSize(title_size)
        title_font.setWeight(QFont.Bold)
        self.page_title.setFont(title_font)

        small_mode = w < 1020
        self.theme_row.set_scale(theme_title_size, small_mode=small_mode)

        for row in self.param_rows:
            row.set_scale(
                row_label_size,
                row_input_size,
                input_height,
                label_min_width,
                input_width,
            )

        for btn in [self.btn_aceptar, self.btn_cancelar, self.btn_restablecer]:
            btn.setFixedSize(button_width, button_height)