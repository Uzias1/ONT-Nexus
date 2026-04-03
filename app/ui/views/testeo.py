from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QGridLayout,
    QDialog,
    QSizePolicy,
    QScrollArea,
)

from app.ui.theme_manager import ThemeManager
from app.ui.widgets.buttons import BackButton, HelpCircleButton

#Helpers para los assets
ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
CHECK_COLOR_PATH = ASSETS_DIR / "check_color.png"
CHECK_GRAY_PATH = ASSETS_DIR / "check_gris.png"

class StatusCircle(QWidget):
    def __init__(self, color: str = "#F8FBFE", border: str = "#8FA8BC", diameter: int = 30, parent=None) -> None:
        super().__init__(parent)
        self._color = QColor(color)
        self._border = QColor(border)
        self._diameter = diameter
        self.setFixedSize(diameter, diameter)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def set_colors(self, fill: str, border: str) -> None:
        self._color = QColor(fill)
        self._border = QColor(border)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(self._border)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(QBrush(self._color))
        painter.drawEllipse(2, 2, self.width() - 4, self.height() - 4)


class PortRow(QFrame):
    def __init__(self, port_name: str, parent=None) -> None:
        super().__init__(parent)
        self.port_name = port_name
        self.circles = []
        self._check_size = 54
        self._check_completed = False
        self._build_ui()

    def _build_ui(self) -> None:
        self.setObjectName("portRow")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(84)

        root = QHBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(18)

        self.circles_wrap = QWidget()
        self.circles_wrap.setStyleSheet("background: transparent;")

        self.circles_layout = QHBoxLayout(self.circles_wrap)
        self.circles_layout.setContentsMargins(0, 0, 0, 0)
        self.circles_layout.setSpacing(14)

        for _ in range(8):
            circle = StatusCircle()
            self.circles.append(circle)
            self.circles_layout.addWidget(circle, 0, Qt.AlignVCenter)

        self.circles_layout.addStretch()

        self.check_label = QLabel(self)
        self.check_label.setObjectName("completionCheck")
        self.check_label.setAlignment(Qt.AlignCenter)
        self.check_label.setFixedSize(self._check_size, self._check_size)
        self._apply_check_pixmap()

        self.port_label = QLabel(self.port_name)
        self.port_label.setObjectName("portLabel")
        self.port_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.port_label.setMinimumWidth(86)

        root.addWidget(self.circles_wrap, 1)
        root.addWidget(self.check_label, 0, Qt.AlignVCenter)
        root.addWidget(self.port_label, 0, Qt.AlignRight | Qt.AlignVCenter)

    def apply_theme(self) -> None:
        theme = ThemeManager.get_theme()

        for circle in self.circles:
            circle.set_colors(theme.input_bg, theme.border)

        self.setStyleSheet(f"""
            QFrame#portRow {{
                background-color: {theme.section_bg};
                border: 1px solid {theme.border};
                border-radius: 18px;
            }}

            QLabel#portLabel {{
                background: transparent;
                color: {theme.text};
                font-size: 15px;
                font-weight: 700;
                padding-left: 8px;
            }}
        """)

    def set_scale(self, circle_diameter: int, font_size: int) -> None:
        for circle in self.circles:
            circle.setFixedSize(circle_diameter, circle_diameter)
            circle._diameter = circle_diameter
            circle.update()

        font = self.port_label.font()
        font.setPointSize(font_size)
        font.setWeight(QFont.DemiBold)
        self.port_label.setFont(font)

        self._check_size = max(circle_diameter + 14, 40)
        self.check_label.setFixedSize(self._check_size, self._check_size)
        self._apply_check_pixmap()

    def set_completion_state(self, completed: bool) -> None:
        self._check_completed = completed
        self._apply_check_pixmap()

    def _apply_check_pixmap(self) -> None:
        image_path = CHECK_COLOR_PATH if self._check_completed else CHECK_GRAY_PATH

        if not image_path.exists():
            self.check_label.clear()
            return

        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            self.check_label.clear()
            return

        scaled = pixmap.scaled(
            self._check_size,
            self._check_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.check_label.setPixmap(scaled)

    def set_circle_states(self, states: list[str]) -> None:
        for circle, state in zip(self.circles, states, strict=False):
            fill, border = self._map_colors(state)
            circle.set_colors(fill, border)

    @staticmethod
    def _map_colors(state: str) -> tuple[str, str]:
        mapping = {
            "IDLE": ("#F1F5F9", "#8AA4BE"),
            "RUNNING": ("#FF9D2E", "#C77810"),
            "COMPLETED": ("#FF9D2E", "#C77810"),
            "PASS": ("#19FF19", "#138A13"),
            "FAIL": ("#FF1E14", "#B91C1C"),
            "OFFLINE": ("#4A4A4A", "#2A2A2A"),
            "EXPECTED_RESET": ("#8A18FF", "#6414B8"),
            "EXPECTED_UPDATE": ("#1118B8", "#0B0F78"),
            "ERROR": ("#000000", "#2A2A2A"),
        }
        return mapping.get(state, ("#F1F5F9", "#8AA4BE"))

class LegendItem(QWidget):
    def __init__(self, color: str, text: str, border: str = "#2A2A2A", parent=None) -> None:
        super().__init__(parent)
        self._build_ui(color, text, border)

    def _build_ui(self, color: str, text: str, border: str) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self.circle = StatusCircle(color=color, border=border, diameter=34)
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setObjectName("legendText")

        layout.addWidget(self.circle, 0, Qt.AlignTop)
        layout.addWidget(self.label, 1)

    def apply_theme(self) -> None:
        theme = ThemeManager.get_theme()
        self.label.setStyleSheet(f"""
            QLabel#legendText {{
                background: transparent;
                color: {theme.text};
                font-size: 15px;
                font-weight: 500;
            }}
        """)


class LegendDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Simbología")
        self.resize(520, 520)
        self._build_ui()
        self.apply_theme()

    def _build_ui(self) -> None:
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(24, 24, 24, 24)
        self.root.setSpacing(18)

        self.title = QLabel("Simbología")
        self.title.setObjectName("legendTitle")

        self.subtitle = QLabel("Estados visuales de las pruebas durante la ejecución.")
        self.subtitle.setObjectName("legendSubtitle")
        self.subtitle.setWordWrap(True)

        self.content = QVBoxLayout()
        self.content.setSpacing(16)

        items = [
            ("#19FF19", "Prueba terminada - Status: OK", "#2B2B2B"),
            ("#FF1E14", "Prueba terminada - Status: FAIL", "#2B2B2B"),
            ("#F1F1F1", "Prueba omitida", "#7A8FA3"),
            ("#4A4A4A", "Desconexión total del dispositivo", "#2B2B2B"),
            ("#8A18FF", "Reiniciando a fábrica", "#2B2B2B"),
            ("#1118B8", "Actualizando software", "#2B2B2B"),
            ("#FF9D2E", "Prueba completada (actualización progresiva)", "#2B2B2B"),
            ("#000000", "ERROR interno", "#2B2B2B"),
        ]

        self.legend_items = []
        for color, text, border in items:
            item = LegendItem(color, text, border)
            self.legend_items.append(item)
            self.content.addWidget(item)

        self.content.addStretch()

        self.close_button = BackButton("Cerrar")
        self.close_button.clicked.connect(self.accept)

        self.root.addWidget(self.title)
        self.root.addWidget(self.subtitle)
        self.root.addSpacing(4)
        self.root.addLayout(self.content)
        self.root.addWidget(self.close_button, 0, Qt.AlignRight)

    def apply_theme(self) -> None:
        theme = ThemeManager.get_theme()

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme.main_card_bg};
                border: 1px solid {theme.border};
                border-radius: 20px;
            }}

            QLabel#legendTitle {{
                color: {theme.title};
                font-size: 26px;
                font-weight: 800;
                background: transparent;
            }}

            QLabel#legendSubtitle {{
                color: {theme.muted_text};
                font-size: 14px;
                font-weight: 500;
                background: transparent;
            }}
        """)

        for item in self.legend_items:
            item.apply_theme()


class TesteoHeader(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        self.setObjectName("testeoHeader")

        self.layout_root = QVBoxLayout(self)
        self.layout_root.setContentsMargins(22, 18, 22, 18)
        self.layout_root.setSpacing(14)

        self.topbar = QHBoxLayout()
        self.topbar.setContentsMargins(0, 0, 0, 0)
        self.topbar.setSpacing(12)

        self.btn_back = BackButton("Volver")
        self.btn_help = HelpCircleButton("?")

        self.topbar.addWidget(self.btn_back, 0, Qt.AlignLeft)
        self.topbar.addStretch()
        self.topbar.addWidget(self.btn_help, 0, Qt.AlignRight)

        self.title = QLabel("Monitoreo de pruebas por puerto")
        self.title.setObjectName("titleLabel")

        self.subtitle = QLabel("Visualización general del estado de ejecución en los 24 puertos.")
        self.subtitle.setObjectName("subtitleLabel")

        self.success_row = QHBoxLayout()
        self.success_row.setContentsMargins(0, 0, 0, 0)
        self.success_row.setSpacing(0)
        self.success_row.addStretch()

        self.success_label = QLabel("Pruebas exitosas:")
        self.success_label.setObjectName("successLabel")
        self.success_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.success_row.addWidget(self.success_label, 0, Qt.AlignRight)

        self.layout_root.addLayout(self.topbar)
        self.layout_root.addWidget(self.title)
        self.layout_root.addWidget(self.subtitle)
        self.layout_root.addLayout(self.success_row)

    def apply_theme(self) -> None:
        theme = ThemeManager.get_theme()
        self.setStyleSheet(f"""
            QFrame#testeoHeader {{
                background-color: {theme.section_alt_bg};
                border: 1px solid {theme.border};
                border-radius: 20px;
            }}

            QLabel#titleLabel {{
                color: {theme.title};
                font-size: 28px;
                font-weight: 800;
                background: transparent;
                border: none;
            }}

            QLabel#subtitleLabel {{
                color: {theme.muted_text};
                font-size: 14px;
                font-weight: 500;
                background: transparent;
                border: none;
            }}

            QLabel#successLabel {{
                color: {theme.text};
                font-size: 15px;
                font-weight: 800;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            }}
        """)


class TesteoView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.left_rows = []
        self.right_rows = []
        self.rows_by_port_index: dict[int, PortRow] = {}
        self._build_ui()
        self._apply_responsive_sizes()

    def _build_ui(self) -> None:
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(20, 16, 20, 16)
        self.root_layout.setSpacing(0)

        self.card = QFrame()
        self.card.setObjectName("mainCard")

        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(24, 22, 24, 24)
        self.card_layout.setSpacing(18)

        self.header = TesteoHeader()
        self.card_layout.addWidget(self.header)

        self.body_container = QWidget()
        self.body_container.setStyleSheet("background: transparent;")

        self.body_layout = QGridLayout(self.body_container)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setHorizontalSpacing(24)
        self.body_layout.setVerticalSpacing(12)
        self.body_layout.setColumnStretch(0, 1)
        self.body_layout.setColumnStretch(1, 1)

        self.left_column_widget = QWidget()
        self.left_column_widget.setStyleSheet("background: transparent;")
        self.left_column_layout = QVBoxLayout(self.left_column_widget)
        self.left_column_layout.setContentsMargins(0, 0, 0, 0)
        self.left_column_layout.setSpacing(12)

        self.right_column_widget = QWidget()
        self.right_column_widget.setStyleSheet("background: transparent;")
        self.right_column_layout = QVBoxLayout(self.right_column_widget)
        self.right_column_layout.setContentsMargins(0, 0, 0, 0)
        self.right_column_layout.setSpacing(12)

        for i in range(1, 13):
            row = PortRow(f"Puerto {i}")
            self.left_rows.append(row)
            self.rows_by_port_index[i] = row
            self.left_column_layout.addWidget(row)

        for i in range(13, 25):
            row = PortRow(f"Puerto {i}")
            self.right_rows.append(row)
            self.rows_by_port_index[i] = row
            self.right_column_layout.addWidget(row)

        self.left_column_layout.addStretch()
        self.right_column_layout.addStretch()

        self.body_layout.addWidget(self.left_column_widget, 0, 0)
        self.body_layout.addWidget(self.right_column_widget, 0, 1)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setWidget(self.body_container)

        self.card_layout.addWidget(self.scroll, 1)
        self.root_layout.addWidget(self.card)

        self.header.btn_help.clicked.connect(self._open_legend)

        self.apply_theme()

    def _open_legend(self) -> None:
        dialog = LegendDialog(self)
        dialog.exec()

    def apply_theme(self) -> None:
        theme = ThemeManager.get_theme()

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme.app_bg};
            }}

            QFrame#mainCard {{
                background-color: {theme.main_card_bg};
                border: 1px solid {theme.border};
                border-radius: 26px;
            }}

            QScrollArea {{
                background: transparent;
                border: none;
            }}

            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
        """)

        self.header.apply_theme()

        for row in self.left_rows + self.right_rows:
            row.apply_theme()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_responsive_sizes()

    def _apply_responsive_sizes(self) -> None:
        w = max(self.width(), 1100)

        title_size = min(max(int(w / 44), 22), 34)
        subtitle_size = min(max(int(w / 95), 12), 15)
        success_size = min(max(int(w / 82), 13), 17)
        port_font_size = min(max(int(w / 95), 12), 17)
        circle_diameter = min(max(int(w / 42), 24), 34)
        circle_spacing = min(max(int(w / 78), 10), 16)
        column_spacing = min(max(int(w / 50), 18), 32)

        self.body_layout.setHorizontalSpacing(column_spacing)

        title_font = self.header.title.font()
        title_font.setPointSize(title_size)
        title_font.setWeight(QFont.Bold)
        self.header.title.setFont(title_font)

        subtitle_font = self.header.subtitle.font()
        subtitle_font.setPointSize(subtitle_size)
        self.header.subtitle.setFont(subtitle_font)

        success_font = self.header.success_label.font()
        success_font.setPointSize(success_size)
        success_font.setWeight(QFont.Bold)
        self.header.success_label.setFont(success_font)

        for row in self.left_rows + self.right_rows:
            row.set_scale(circle_diameter, port_font_size)
            row.circles_layout.setSpacing(circle_spacing)

    def get_row_by_port_index(self, port_index: int) -> PortRow | None:
        return self.rows_by_port_index.get(port_index)

    def set_port_circle_states(self, port_index: int, states: list[str]) -> None:
        row = self.get_row_by_port_index(port_index)
        if row is None:
            return
        row.set_circle_states(states)

    def set_port_completion_state(self, port_index: int, completed: bool) -> None:
        row = self.get_row_by_port_index(port_index)
        if row is None:
            return
        row.set_completion_state(completed)

    def set_success_count(self, count: int) -> None:
        self.header.success_label.setText(f"Pruebas exitosas: {count}")

    def reset_all_ports(self) -> None:
        for port_index, row in self.rows_by_port_index.items():
            _ = port_index
            base_states = ["IDLE"] * 8
            base_states[0] = "OFFLINE"
            row.set_circle_states(base_states)
            row.set_completion_state(False)