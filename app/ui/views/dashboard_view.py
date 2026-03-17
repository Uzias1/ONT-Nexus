from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGridLayout,
    QSizePolicy,
    QFrame,
)

from app.ui.theme_manager import ThemeManager
from app.ui.views.status_bar import StatusBarView
from app.ui.widgets.buttons import PrimaryButton
from app.ui.widgets.toggle_switch import ToggleSwitch


class TestRow(QWidget):
    def __init__(self, label_text: str, checked: bool = True, parent=None) -> None:
        super().__init__(parent)

        self.setStyleSheet("background: transparent;")

        self._label_text = label_text

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self.label = QLabel(label_text)
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.toggle = ToggleSwitch(checked=checked)
        self.toggle.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout.addWidget(self.label, 0, Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.toggle, 0, Qt.AlignLeft | Qt.AlignVCenter)
        layout.addStretch()

        self.apply_theme()

    def apply_theme(self) -> None:
        theme = ThemeManager.get_theme()
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {theme.text};
                font-weight: 600;
                background: transparent;
            }}
        """)

    def set_scale(self, font_size: int) -> None:
        font = self.label.font()
        font.setPointSize(font_size)
        font.setWeight(QFont.DemiBold)
        self.label.setFont(font)

    def set_label_width(self, width: int) -> None:
        self.label.setFixedWidth(width)

    def text_width(self) -> int:
        metrics = QFontMetrics(self.label.font())
        return metrics.horizontalAdvance(self._label_text)


class DashboardView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.test_rows = []
        self._build_ui()
        self._apply_responsive_sizes()

    def _build_ui(self) -> None:
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(20, 16, 20, 16)
        self.root_layout.setSpacing(0)

        self.card = QFrame()
        self.card.setObjectName("mainCard")

        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(28, 20, 28, 28)
        self.card_layout.setSpacing(18)

        self.status_bar = StatusBarView()
        self.card_layout.addWidget(self.status_bar)

        self.title = QLabel("Seleccione las pruebas a realizar")
        self.title.setObjectName("titleLabel")
        self.card_layout.addWidget(self.title)

        self.tests_panel = QFrame()
        self.tests_panel.setObjectName("testsPanel")

        self.tests_panel_layout = QVBoxLayout(self.tests_panel)
        self.tests_panel_layout.setContentsMargins(22, 22, 22, 22)
        self.tests_panel_layout.setSpacing(0)

        self.tests_grid = QGridLayout()
        self.tests_grid.setHorizontalSpacing(140)
        self.tests_grid.setVerticalSpacing(20)
        self.tests_grid.setColumnStretch(0, 1)
        self.tests_grid.setColumnStretch(1, 1)

        self.left_column = QVBoxLayout()
        self.left_column.setSpacing(22)

        self.right_column = QVBoxLayout()
        self.right_column.setSpacing(22)

        self.row_ping = TestRow("PING", checked=True)
        self.row_factory = TestRow("FACTORY RESET", checked=True)
        self.row_software = TestRow("SOFTWARE UPDATE", checked=True)
        self.row_usb = TestRow("USB PORT", checked=True)

        self.row_tx = TestRow("TX", checked=True)
        self.row_rx = TestRow("RX", checked=True)
        self.row_wifi24 = TestRow("WIFI 2.4gHZ", checked=True)
        self.row_wifi5 = TestRow("WIFI 5gHZ", checked=True)

        # PING siempre habilitado y sin interacción del usuario
        self.row_ping.toggle.setChecked(True)
        self.row_ping.toggle.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.row_ping.toggle.setFocusPolicy(Qt.NoFocus)

        self.test_rows = [
            self.row_ping,
            self.row_factory,
            self.row_software,
            self.row_usb,
            self.row_tx,
            self.row_rx,
            self.row_wifi24,
            self.row_wifi5,
        ]

        self.left_column.addWidget(self.row_ping)
        self.left_column.addWidget(self.row_factory)
        self.left_column.addWidget(self.row_software)
        self.left_column.addWidget(self.row_usb)
        self.left_column.addStretch()

        self.right_column.addWidget(self.row_tx)
        self.right_column.addWidget(self.row_rx)
        self.right_column.addWidget(self.row_wifi24)
        self.right_column.addWidget(self.row_wifi5)
        self.right_column.addStretch()

        self.left_widget = QWidget()
        self.left_widget.setStyleSheet("background: transparent;")
        self.left_widget.setLayout(self.left_column)

        self.right_widget = QWidget()
        self.right_widget.setStyleSheet("background: transparent;")
        self.right_widget.setLayout(self.right_column)

        self.tests_grid.addWidget(self.left_widget, 0, 0)
        self.tests_grid.addWidget(self.right_widget, 0, 1)

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid_container.setLayout(self.tests_grid)

        self.tests_panel_layout.addWidget(self.grid_container)
        self.card_layout.addWidget(self.tests_panel)

        self.card_layout.addStretch()

        self.buttons_panel = QFrame()
        self.buttons_panel.setObjectName("buttonsPanel")

        self.buttons_layout = QHBoxLayout(self.buttons_panel)
        self.buttons_layout.setContentsMargins(22, 18, 22, 18)
        self.buttons_layout.setSpacing(28)
        self.buttons_layout.setAlignment(Qt.AlignHCenter)

        self.btn_testear = PrimaryButton("Testear")
        self.btn_modificar = PrimaryButton("Modificar parámetros")
        self.btn_reportes = PrimaryButton("Reportes")

        self.buttons_layout.addWidget(self.btn_testear)
        self.buttons_layout.addWidget(self.btn_modificar)
        self.buttons_layout.addWidget(self.btn_reportes)

        self.buttons_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.card_layout.addWidget(self.buttons_panel)

        self.root_layout.addWidget(self.card)

        self.apply_theme()

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

            QFrame#testsPanel {{
                background-color: {theme.section_bg};
                border: 1px solid {theme.border};
                border-radius: 18px;
            }}

            QFrame#buttonsPanel {{
                background-color: {theme.section_alt_bg};
                border: 1px solid {theme.border};
                border-radius: 18px;
            }}

            QLabel#titleLabel {{
                color: {theme.title};
                font-weight: 800;
                background: transparent;
            }}
        """)

        for row in self.test_rows:
            row.apply_theme()

        self.status_bar.apply_theme()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_responsive_sizes()

    def _apply_responsive_sizes(self) -> None:
        w = max(self.width(), 900)
        h = max(self.height(), 620)

        title_size = min(max(int(w / 42), 22), 38)
        row_font_size = min(max(int(w / 85), 14), 22)
        status_font_size = min(max(int(w / 100), 12), 18)
        button_width = min(max(int(w / 5.5), 190), 300)
        button_height = min(max(int(h / 12), 58), 78)

        horizontal_spacing = min(max(int(w / 10), 90), 260)
        self.tests_grid.setHorizontalSpacing(horizontal_spacing)

        title_font = self.title.font()
        title_font.setPointSize(title_size)
        title_font.setWeight(QFont.Bold)
        self.title.setFont(title_font)

        for row in self.test_rows:
            row.set_scale(row_font_size)

        # Alinear todos los toggles usando el ancho máximo del texto
        max_label_width = max(row.text_width() for row in self.test_rows) + 12
        for row in self.test_rows:
            row.set_label_width(max_label_width)

        self.status_bar.set_scale(status_font_size)

        for btn in [self.btn_testear, self.btn_modificar, self.btn_reportes]:
            btn.setFixedSize(button_width, button_height)