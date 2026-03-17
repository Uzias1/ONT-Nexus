from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGridLayout,
    QSizePolicy,
)

from ui.views.toolbar_view import ToolbarView
from ui.views.status_bar import StatusBarView
from ui.widgets.buttons import PrimaryButton
from ui.widgets.toggle_switch import ToggleSwitch


class TestRow(QWidget):
    def __init__(self, label_text: str, checked: bool = True, parent=None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self.label = QLabel(label_text)
        self.label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                color: #222222;
                font-weight: 500;
            }
        """)
        self.label.setMinimumWidth(170)

        self.toggle = ToggleSwitch(checked=checked)

        layout.addWidget(self.label)
        layout.addWidget(self.toggle)
        layout.addStretch()


class DashboardView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setStyleSheet("""
            QWidget {
                background-color: #F4F4F4;
            }
        """)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 8, 10, 10)
        root_layout.setSpacing(0)

        self.toolbar = ToolbarView()
        root_layout.addWidget(self.toolbar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 20)
        content_layout.setSpacing(18)

        self.status_bar = StatusBarView()
        content_layout.addWidget(self.status_bar)

        self.title = QLabel("Seleccione las pruebas a realizar")
        self.title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 700;
                color: #000000;
            }
        """)
        content_layout.addWidget(self.title)

        tests_grid = QGridLayout()
        tests_grid.setHorizontalSpacing(120)
        tests_grid.setVerticalSpacing(24)

        left_column = QVBoxLayout()
        left_column.setSpacing(20)
        left_column.addWidget(TestRow("PING", checked=False))
        left_column.addWidget(TestRow("FACTORY RESET", checked=True))
        left_column.addWidget(TestRow("SOFTWARE UPDATE", checked=True))
        left_column.addWidget(TestRow("USB PORT", checked=True))
        left_column.addWidget(TestRow("TX", checked=True))
        left_column.addStretch()

        right_column = QVBoxLayout()
        right_column.setSpacing(20)
        right_column.addWidget(TestRow("RX", checked=True))
        right_column.addWidget(TestRow("WIFI 2.4gHZ", checked=True))
        right_column.addWidget(TestRow("WIFI 5gHZ", checked=True))
        right_column.addStretch()

        left_widget = QWidget()
        left_widget.setLayout(left_column)

        right_widget = QWidget()
        right_widget.setLayout(right_column)

        tests_grid.addWidget(left_widget, 0, 0)
        tests_grid.addWidget(right_widget, 0, 1)

        grid_container = QWidget()
        grid_container.setLayout(tests_grid)
        content_layout.addWidget(grid_container)

        content_layout.addStretch()

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(32)
        buttons_layout.setAlignment(Qt.AlignHCenter)

        self.btn_testear = PrimaryButton("Testear")
        self.btn_modificar = PrimaryButton("Modificar\nparámetros")
        self.btn_reportes = PrimaryButton("Reportes")

        buttons_layout.addWidget(self.btn_testear)
        buttons_layout.addWidget(self.btn_modificar)
        buttons_layout.addWidget(self.btn_reportes)

        buttons_container = QWidget()
        buttons_container.setLayout(buttons_layout)
        buttons_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        content_layout.addWidget(buttons_container)

        root_layout.addWidget(content)