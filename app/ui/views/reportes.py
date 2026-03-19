from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QLegend,
    QLineSeries,
    QPieSeries,
    QStackedBarSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt, QDate, QPointF, QPoint, QMargins, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPdfWriter, QPen, QBrush, QCursor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
    QGridLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
    QDialog,
    QDateEdit,
    QFormLayout,
    QMessageBox,
    QMenu,
    QScrollArea,
    QToolTip,
    QLineEdit,
)

from app.ui.data.reportes_data import (
    ReportesDataSource,
    TestResultRecord,
    normalize_status,
)
from app.ui.theme_manager import ThemeManager
from app.ui.widgets.buttons import BackButton, PrimaryButton, SecondaryButton


class HeaderActionButton(QPushButton):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        theme = ThemeManager.get_theme()
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44)
        self.setMinimumWidth(148)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.section_bg};
                color: {theme.text};
                border: 1px solid {theme.border};
                border-radius: 14px;
                padding: 0 16px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {theme.section_alt_bg};
            }}
            QPushButton:pressed {{
                background-color: {theme.input_bg};
            }}
        """)


class DateRangeDialog(QDialog):
    def __init__(self, start_date: date | None, end_date: date | None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Filtrar por rango de fechas")
        self.setModal(True)
        self.resize(420, 220)

        today = QDate.currentDate()

        self.layout_root = QVBoxLayout(self)
        self.layout_root.setContentsMargins(24, 24, 24, 24)
        self.layout_root.setSpacing(18)

        self.title = QLabel("Selecciona un rango de fechas")
        self.title.setObjectName("rangeTitle")

        self.desc = QLabel("No se permite seleccionar fechas futuras.")
        self.desc.setObjectName("rangeDesc")

        self.form = QFormLayout()
        self.form.setSpacing(14)
        self.form.setLabelAlignment(Qt.AlignLeft)

        self.start_edit = QDateEdit()
        self.start_edit.setCalendarPopup(True)
        self.start_edit.setMaximumDate(today)
        self.start_edit.setDisplayFormat("yyyy-MM-dd")

        self.end_edit = QDateEdit()
        self.end_edit.setCalendarPopup(True)
        self.end_edit.setMaximumDate(today)
        self.end_edit.setDisplayFormat("yyyy-MM-dd")

        if start_date:
            self.start_edit.setDate(QDate(start_date.year, start_date.month, start_date.day))
        else:
            self.start_edit.setDate(today.addDays(-30))

        if end_date:
            self.end_edit.setDate(QDate(end_date.year, end_date.month, end_date.day))
        else:
            self.end_edit.setDate(today)

        self.form.addRow("Desde:", self.start_edit)
        self.form.addRow("Hasta:", self.end_edit)

        self.buttons = QHBoxLayout()
        self.buttons.addStretch()

        self.btn_clear = SecondaryButton("Limpiar")
        self.btn_clear.setFixedSize(120, 46)

        self.btn_accept = PrimaryButton("Aplicar")
        self.btn_accept.setFixedSize(120, 46)

        self.buttons.addWidget(self.btn_clear)
        self.buttons.addWidget(self.btn_accept)

        self.layout_root.addWidget(self.title)
        self.layout_root.addWidget(self.desc)
        self.layout_root.addLayout(self.form)
        self.layout_root.addStretch()
        self.layout_root.addLayout(self.buttons)

        self.btn_accept.clicked.connect(self._accept)
        self.btn_clear.clicked.connect(self._clear)

        self.apply_theme()

    def apply_theme(self) -> None:
        theme = ThemeManager.get_theme()
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme.main_card_bg};
                border: 1px solid {theme.border};
                border-radius: 18px;
            }}
            QLabel#rangeTitle {{
                color: {theme.title};
                font-size: 22px;
                font-weight: 800;
                background: transparent;
            }}
            QLabel#rangeDesc {{
                color: {theme.muted_text};
                font-size: 13px;
                font-weight: 500;
                background: transparent;
            }}
            QLabel {{
                color: {theme.text};
                font-size: 14px;
                font-weight: 600;
                background: transparent;
            }}
            QDateEdit {{
                background-color: {theme.input_bg};
                color: {theme.input_text};
                border: 1px solid {theme.input_border};
                border-radius: 10px;
                padding: 8px 12px;
                min-height: 22px;
            }}
        """)

    def _accept(self) -> None:
        if self.start_edit.date() > self.end_edit.date():
            QMessageBox.warning(self, "Rango inválido", "La fecha inicial no puede ser mayor que la final.")
            return
        self.accept()

    def _clear(self) -> None:
        self.start_edit.setDate(QDate.currentDate().addDays(-30))
        self.end_edit.setDate(QDate.currentDate())
        self.accept()

    def get_range(self) -> tuple[date, date]:
        return self.start_edit.date().toPython(), self.end_edit.date().toPython()


class LegendBadge(QWidget):
    def __init__(self, color: str, text: str, parent=None) -> None:
        super().__init__(parent)
        self._color = color

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.dot = QFrame()
        self.dot.setFixedSize(14, 14)

        self.label = QLabel(text)
        self.label.setObjectName("legendBadgeLabel")

        layout.addWidget(self.dot)
        layout.addWidget(self.label)

        self.apply_theme()

    def apply_theme(self) -> None:
        theme = ThemeManager.get_theme()
        self.dot.setStyleSheet(f"""
            QFrame {{
                background-color: {self._color};
                border: 1px solid {theme.border};
                border-radius: 7px;
            }}
        """)
        self.label.setStyleSheet(f"""
            QLabel#legendBadgeLabel {{
                color: {theme.text};
                font-size: 13px;
                font-weight: 600;
                background: transparent;
            }}
        """)


class ReportesView(QWidget):
    COLUMN_DEFS = [
        ("id", "ID", 90),
        ("timestamp", "TIMESTAMP", 190),
        ("fabricante", "FABRICANTE", 170),
        ("modelo", "MODELO", 170),
        ("puerto", "PUERTO", 100),
        ("ip", "IP", 150),
        ("estatus", "ESTATUS", 130),
    ]
 
    TEST_COLUMN_DEFS = [
        ("id", "ID", 80),
        ("sn", "SN", 160),
        ("mac", "MAC", 170),
        ("ping", "PING", 120),
        ("factory_reset", "Factory Reset", 150),
        ("actualizacion_software", "Actualización de Software", 220),
        ("usb", "USB", 110),
        ("wifi_24", "Wifi 2.4", 130),
        ("wifi_5", "Wifi 5", 130),
        ("tx", "TX", 110),
        ("rx", "RX", 110),
    ]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.data_source = ReportesDataSource()
        self.start_date: date | None = date.today().replace(day=1)
        self.end_date: date | None = date.today()

        self.column_filters = {
            "fabricante": None,
            "modelo": None,
            "puerto": None,
            "ip": None,
            "estatus": None,
        }

        self.filtered_records = []
        self.ip_search_text = ""

        self.test_column_filters = {
            "sn": None,
            "mac": None,
            "ping": None,
            "factory_reset": None,
            "actualizacion_software": None,
            "usb": None,
            "wifi_24": None,
            "wifi_5": None,
            "tx": None,
            "rx": None,
        }

        self.filtered_test_records: list[TestResultRecord] = []
        self.test_sn_search_text = ""
        self.test_mac_search_text = ""
        self._test_progress_overlay_items = []
        self._build_ui()
        self._refresh_all()

    # /*************************************
    # Utilidades emergentes
    # *************************************
    def _apply_native_dark_to_window(self, widget: QWidget) -> None:
        try:
            import sys
            if sys.platform != "win32":
                return

            import ctypes
            hwnd = int(widget.winId())

            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(1 if ThemeManager.is_dark() else 0)

            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
        except Exception:
            pass

    def _show_themed_message(
        self,
        icon: QMessageBox.Icon,
        title: str,
        text: str,
    ) -> None:
        theme = ThemeManager.get_theme()

        msg = QMessageBox(self)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.Ok)

        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {theme.main_card_bg};
            }}
            QMessageBox QLabel {{
                color: {theme.text};
                font-size: 14px;
                background: transparent;
            }}
            QMessageBox QPushButton {{
                background-color: {theme.section_bg};
                color: {theme.text};
                border: 1px solid {theme.border};
                border-radius: 10px;
                min-width: 88px;
                min-height: 34px;
                padding: 4px 12px;
                font-weight: 700;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {theme.section_alt_bg};
            }}
            QMessageBox QPushButton:pressed {{
                background-color: {theme.input_bg};
            }}
        """)

        self._apply_native_dark_to_window(msg)
        msg.exec()

    def _connect_barset_tooltip(
        self,
        bar_set: QBarSet,
        status_label: str,
        values: list[float],
    ) -> None:
        def _on_hovered(status: bool, index: int) -> None:
            if not status:
                QToolTip.hideText()
                return

            if 0 <= index < len(values):
                if values[index] <= 0:
                    QToolTip.hideText()
                    return

                QToolTip.showText(
                    QCursor.pos(),
                    f"{status_label}: {values[index]:.1f}%",
                    self,
                )

        bar_set.hovered.connect(_on_hovered)

    # /*************************************
    # Helpers de cálculo para gráficas
    # *************************************
    def _success_percent(self, records: list) -> float:
        if not records:
            return 0.0
        validos = sum(1 for r in records if normalize_status(r.estatus) == "VALIDO")
        return (validos / len(records)) * 100.0

    def _build_manufacturer_success_data(self) -> list[tuple[str, float, str]]:
        manufacturer_order = [
            ("ZTE", "#FF8A2A"),
            ("HUAWEI", "#F7EA00"),
            ("FIBERHOME", "#B7E117"),
        ]

        data = []
        for name, color in manufacturer_order:
            records = [r for r in self.filtered_records if (r.fabricante or "").strip().upper() == name]
            data.append((name, self._success_percent(records), color))
        return data

    def _build_port_success_data(self) -> list[tuple[str, float, str]]:
        palette = [
            "#F9C80E",
            "#2DBE60",
            "#4F8EF7",
            "#FF8A2A",
            "#D96CFF",
            "#00C2A8",
        ]

        data = []
        for port in range(1, 25):
            records = [r for r in self.filtered_records if int(r.puerto) == port]
            color = palette[(port - 1) % len(palette)]
            data.append((str(port), self._success_percent(records), color))
        return data

    def _build_test_progress_data(self) -> dict:
        categories = [
            ("ping", "PING"),
            ("factory_reset", "FACTORY RESET"),
            ("actualizacion_software", "ACTUALIZACIÓN SOFTWARE"),
            ("usb", "USB"),
            ("wifi_24", "WIFI 2.4"),
            ("wifi_5", "WIFI 5"),
            ("tx", "TX"),
            ("rx", "RX"),
        ]

        total_records = len(self.filtered_test_records)
        status_keys = ["Pass", "Fail", "Desactivado", "No File"]
        counts_by_status = {key: [] for key in status_keys}
        totals = []

        for field_name, _ in categories:
            counter = {key: 0 for key in status_keys}
            executed = 0

            for record in self.filtered_test_records:
                value = (getattr(record, field_name) or "").strip()
                if value in counter:
                    counter[value] += 1
                    executed += 1

            for key in status_keys:
                counts_by_status[key].append(counter[key])
            totals.append(executed)

        return {
            "categories": [label for _, label in categories],
            "counts": counts_by_status,
            "totals": totals,
            "max_total": max(total_records, 1),
            "record_count": total_records,
        }

    def _clear_test_progress_overlay_labels(self) -> None:
        for item in getattr(self, "_test_progress_overlay_items", []):
            try:
                scene = self.test_progress_chart_view.scene()
                if scene is not None:
                    scene.removeItem(item)
            except Exception:
                pass
        self._test_progress_overlay_items = []

    def _draw_test_progress_top_labels(self, totals: list[int], record_count: int) -> None:
        self._clear_test_progress_overlay_labels()

        chart = self.test_progress_chart_view.chart()
        if chart is None:
            return

        plot = chart.plotArea()
        if plot.width() <= 0 or plot.height() <= 0:
            return

        scene = self.test_progress_chart_view.scene()
        if scene is None:
            return

        theme = ThemeManager.get_theme()
        category_count = len(totals)
        if category_count == 0:
            return

        step = plot.width() / category_count
        maximum = max(record_count, 1)

        for index, total in enumerate(totals):
            if total <= 0:
                continue

            pct = (total / maximum) * 100.0
            text_item = scene.addSimpleText(f"{pct:.0f}%")
            font = text_item.font()
            font.setPointSize(10)
            font.setBold(True)
            text_item.setFont(font)
            text_item.setBrush(QBrush(QColor(theme.title)))

            x = plot.left() + (step * index) + (step / 2.0) - (text_item.boundingRect().width() / 2.0)
            y = plot.bottom() - ((total / maximum) * plot.height()) - text_item.boundingRect().height() - 8
            text_item.setPos(x, y)
            self._test_progress_overlay_items.append(text_item)

    # /*************************************
    # Construcción general de la vista
    # *************************************
    def _build_ui(self) -> None:
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(20, 16, 20, 16)
        self.root_layout.setSpacing(0)

        self.main_card = QFrame()
        self.main_card.setObjectName("mainCard")

        self.main_layout = QVBoxLayout(self.main_card)
        self.main_layout.setContentsMargins(18, 18, 18, 18)
        self.main_layout.setSpacing(18)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(18)

        self.header_card = QFrame()
        self.header_card.setObjectName("headerCard")

        self.header_layout = QHBoxLayout(self.header_card)
        self.header_layout.setContentsMargins(24, 20, 24, 20)
        self.header_layout.setSpacing(12)

        self.title_block = QVBoxLayout()
        self.title_block.setSpacing(4)

        self.title = QLabel("Reportes y analítica")
        self.title.setObjectName("titleLabel")

        self.subtitle = QLabel("Consulta resultados, porcentaje de éxito y registros filtrados por fecha.")
        self.subtitle.setObjectName("subtitleLabel")
        self.subtitle.setWordWrap(True)

        self.title_block.addWidget(self.title)
        self.title_block.addWidget(self.subtitle)

        self.actions_layout = QHBoxLayout()
        self.actions_layout.setSpacing(10)

        self.btn_back = BackButton("Volver")
        self.btn_date = HeaderActionButton("Filtrar fechas")
        self.btn_export_pdf = HeaderActionButton("Exportar PDF")

        self.actions_layout.addWidget(self.btn_back)
        self.actions_layout.addWidget(self.btn_date)
        self.actions_layout.addWidget(self.btn_export_pdf)

        self.header_layout.addLayout(self.title_block, 1)
        self.header_layout.addLayout(self.actions_layout)

        self.content_layout.addWidget(self.header_card)

        self.charts_grid = QGridLayout()
        self.charts_grid.setHorizontalSpacing(18)
        self.charts_grid.setVerticalSpacing(18)

        # /*************************************
        # Gráfica 1: Distribución de estatus
        # *************************************
        self.pie_card = QFrame()
        self.pie_card.setObjectName("sectionCard")
        self.pie_card.setMinimumHeight(470)

        self.pie_layout = QVBoxLayout(self.pie_card)
        self.pie_layout.setContentsMargins(20, 18, 20, 18)
        self.pie_layout.setSpacing(10)

        self.pie_title = QLabel("Distribución de estatus")
        self.pie_title.setObjectName("sectionTitle")

        self.pie_subtitle = QLabel("Promedio visual de válidos e inválidos según los registros filtrados.")
        self.pie_subtitle.setObjectName("sectionSubtitle")
        self.pie_subtitle.setWordWrap(True)

        self.pie_chart_view = QChartView()
        self.pie_chart_view.setRenderHint(QPainter.Antialiasing)
        self.pie_chart_view.setMinimumHeight(320)
        self.pie_chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.pie_legend_row = QHBoxLayout()
        self.pie_legend_row.setSpacing(18)
        self.badge_ok = LegendBadge("#2DBE60", "Válido")
        self.badge_fail = LegendBadge("#E74C3C", "Inválido")
        self.pie_legend_row.addWidget(self.badge_ok)
        self.pie_legend_row.addWidget(self.badge_fail)
        self.pie_legend_row.addStretch()

        self.pie_layout.addWidget(self.pie_title)
        self.pie_layout.addWidget(self.pie_subtitle)
        self.pie_layout.addWidget(self.pie_chart_view, 1)
        self.pie_layout.addLayout(self.pie_legend_row)

        # /*************************************
        # Gráfica 2: % de éxito por semana
        # *************************************
        self.line_card = QFrame()
        self.line_card.setObjectName("sectionCard")
        self.line_card.setMinimumHeight(470)

        self.line_layout = QVBoxLayout(self.line_card)
        self.line_layout.setContentsMargins(20, 18, 20, 18)
        self.line_layout.setSpacing(10)

        self.line_title = QLabel("% de éxito por semana")
        self.line_title.setObjectName("sectionTitle")

        self.line_subtitle = QLabel(
            "Tres semanas anteriores con colores distintos y la semana actual en rojo. "
            "Eje X de lunes a sábado y eje Y hasta 100%."
        )
        self.line_subtitle.setObjectName("sectionSubtitle")
        self.line_subtitle.setWordWrap(True)

        self.line_chart_view = QChartView()
        self.line_chart_view.setRenderHint(QPainter.Antialiasing)
        self.line_chart_view.setMinimumHeight(320)
        self.line_chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.line_layout.addWidget(self.line_title)
        self.line_layout.addWidget(self.line_subtitle)
        self.line_layout.addWidget(self.line_chart_view, 1)

        # /*************************************
        # Gráfica 3: % de éxito por fabricante
        # *************************************
        self.fabricante_card = QFrame()
        self.fabricante_card.setObjectName("sectionCard")
        self.fabricante_card.setMinimumHeight(470)

        self.fabricante_layout = QVBoxLayout(self.fabricante_card)
        self.fabricante_layout.setContentsMargins(20, 18, 20, 18)
        self.fabricante_layout.setSpacing(10)

        self.fabricante_title = QLabel("% de éxito por fabricante")
        self.fabricante_title.setObjectName("sectionTitle")

        self.fabricante_subtitle = QLabel(
            "Eje X con ZTE, HUAWEI y FIBERHOME. "
            "Eje Y con porcentaje de éxito calculado a partir del estatus."
        )
        self.fabricante_subtitle.setObjectName("sectionSubtitle")
        self.fabricante_subtitle.setWordWrap(True)

        self.fabricante_chart_view = QChartView()
        self.fabricante_chart_view.setRenderHint(QPainter.Antialiasing)
        self.fabricante_chart_view.setMinimumHeight(320)
        self.fabricante_chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.fabricante_layout.addWidget(self.fabricante_title)
        self.fabricante_layout.addWidget(self.fabricante_subtitle)
        self.fabricante_layout.addWidget(self.fabricante_chart_view, 1)

        # /*************************************
        # Gráfica 4: % de éxito por puertos
        # *************************************
        self.puertos_card = QFrame()
        self.puertos_card.setObjectName("sectionCard")
        self.puertos_card.setMinimumHeight(470)

        self.puertos_layout = QVBoxLayout(self.puertos_card)
        self.puertos_layout.setContentsMargins(20, 18, 20, 18)
        self.puertos_layout.setSpacing(10)

        self.puertos_title = QLabel("% de éxito por puertos")
        self.puertos_title.setObjectName("sectionTitle")

        self.puertos_subtitle = QLabel(
            "Eje X con los 24 puertos. "
            "Eje Y con porcentaje de éxito calculado a partir del estatus."
        )
        self.puertos_subtitle.setObjectName("sectionSubtitle")
        self.puertos_subtitle.setWordWrap(True)

        self.puertos_chart_view = QChartView()
        self.puertos_chart_view.setRenderHint(QPainter.Antialiasing)
        self.puertos_chart_view.setMinimumHeight(320)
        self.puertos_chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.puertos_layout.addWidget(self.puertos_title)
        self.puertos_layout.addWidget(self.puertos_subtitle)
        self.puertos_layout.addWidget(self.puertos_chart_view, 1)

        self.test_progress_card = QFrame()
        self.test_progress_card.setObjectName("sectionCard")
        self.test_progress_card.setMinimumHeight(520)

        self.test_progress_layout = QVBoxLayout(self.test_progress_card)
        self.test_progress_layout.setContentsMargins(20, 18, 20, 18)
        self.test_progress_layout.setSpacing(10)

        self.test_progress_title = QLabel("Pruebas realizadas")
        self.test_progress_title.setObjectName("sectionTitle")

        self.test_progress_subtitle = QLabel(
            "La gráfica se alimenta de la tabla de resultados de prueba. Cada barra muestra la distribución de estados por prueba y el porcentaje total ejecutado."
        )
        self.test_progress_subtitle.setObjectName("sectionSubtitle")
        self.test_progress_subtitle.setWordWrap(True)

        self.test_progress_chart_view = QChartView()
        self.test_progress_chart_view.setRenderHint(QPainter.Antialiasing)
        self.test_progress_chart_view.setMinimumHeight(350)
        self.test_progress_chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.test_progress_chart_row = QHBoxLayout()
        self.test_progress_chart_row.setSpacing(10)
        self.test_progress_y_caption = QLabel("ID")
        self.test_progress_y_caption.setObjectName("chartAxisCaption")
        self.test_progress_y_caption.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        self.test_progress_y_caption.setFixedWidth(28)
        self.test_progress_chart_row.addWidget(self.test_progress_y_caption)
        self.test_progress_chart_row.addWidget(self.test_progress_chart_view, 1)

        self.test_progress_legend_row = QHBoxLayout()
        self.test_progress_legend_row.setSpacing(18)
        self.badge_pass = LegendBadge("#2DBE60", "PASS")
        self.badge_fail_test = LegendBadge("#FF2D2D", "FAIL")
        self.badge_disabled = LegendBadge("#F7EA00", "DESACTIVADO")
        self.badge_no_file = LegendBadge("#4F55E0", "NO FILE")
        self.test_progress_legend_row.addStretch()
        self.test_progress_legend_row.addWidget(self.badge_pass)
        self.test_progress_legend_row.addWidget(self.badge_fail_test)
        self.test_progress_legend_row.addWidget(self.badge_disabled)
        self.test_progress_legend_row.addWidget(self.badge_no_file)

        self.test_progress_layout.addWidget(self.test_progress_title)
        self.test_progress_layout.addWidget(self.test_progress_subtitle)
        self.test_progress_layout.addLayout(self.test_progress_chart_row, 1)
        self.test_progress_layout.addLayout(self.test_progress_legend_row)

        self.charts_grid.addWidget(self.pie_card, 0, 0)
        self.charts_grid.addWidget(self.line_card, 0, 1)
        self.charts_grid.addWidget(self.fabricante_card, 1, 0)
        self.charts_grid.addWidget(self.puertos_card, 1, 1)
        self.charts_grid.addWidget(self.test_progress_card, 2, 0, 1, 2)

        self.content_layout.addLayout(self.charts_grid)

        # /*************************************
        # Tabla de resultados
        # *************************************
        self.table_card = QFrame()
        self.table_card.setObjectName("sectionCard")
        self.table_card.setMinimumHeight(420)

        self.table_layout = QVBoxLayout(self.table_card)
        self.table_layout.setContentsMargins(20, 18, 20, 18)
        self.table_layout.setSpacing(14)

        self.table_title = QLabel("Resultados")
        self.table_title.setObjectName("sectionTitle")

        self.table_subtitle = QLabel(
            "La tabla es la fuente de datos de las gráficas. Cada columna filtrable tiene su propio botón."
        )
        self.table_subtitle.setObjectName("sectionSubtitle")
        self.table_subtitle.setWordWrap(True)

        self.range_label = QLabel("")
        self.range_label.setObjectName("rangeInfoLabel")

        self.table_layout.addWidget(self.table_title)
        self.table_layout.addWidget(self.table_subtitle)
        self.table_layout.addWidget(self.range_label)
        self.quick_filter_row = QHBoxLayout()
        self.quick_filter_row.setSpacing(12)

        self.quick_ip_label = QLabel("Filtrar IP")
        self.quick_ip_label.setObjectName("quickFilterLabel")

        self.quick_ip_input = QLineEdit()
        self.quick_ip_input.setObjectName("quickFilterInput")
        self.quick_ip_input.setPlaceholderText("Escribe una IP o fragmento...")
        self.quick_ip_input.setClearButtonEnabled(True)
        self.quick_ip_input.setMinimumWidth(280)
        self.quick_ip_input.setMaximumWidth(360)

        self.quick_ip_clear = QPushButton("Borrar filtros")
        self.quick_ip_clear.setObjectName("quickFilterClearButton")
        self.quick_ip_clear.setCursor(Qt.PointingHandCursor)
        self.quick_ip_clear.setMinimumHeight(40)

        self.quick_filter_row.addStretch(1)
        self.quick_filter_row.addWidget(self.quick_ip_label)
        self.quick_filter_row.addWidget(self.quick_ip_input)
        self.quick_filter_row.addSpacing(18)
        self.quick_filter_row.addWidget(self.quick_ip_clear)

        self.table_layout.addLayout(self.quick_filter_row)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMN_DEFS))
        self.table.setHorizontalHeaderLabels([c[1] for c in self.COLUMN_DEFS])

        vheader = self.table.verticalHeader()
        vheader.setVisible(False)
        vheader.setMinimumWidth(0)
        vheader.setFixedWidth(0)
        vheader.setDefaultSectionSize(40)

        self.table.setCornerButtonEnabled(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setShowGrid(False)
        self.table.setSortingEnabled(False)
        self.table.setMinimumHeight(260)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setMinimumHeight(48)
        header.setFixedHeight(48)

        self.table.setColumnWidth(0, 90)
        self.table.setColumnWidth(4, 100)

        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Stretch)

        self._update_table_headers()

        self.table_layout.addWidget(self.table)
        self.content_layout.addWidget(self.table_card)

          # /*************************************
        # Tabla de resultados de prueba
        # *************************************
        self.test_table_card = QFrame()
        self.test_table_card.setObjectName("sectionCard")
        self.test_table_card.setMinimumHeight(440)

        self.test_table_layout = QVBoxLayout(self.test_table_card)
        self.test_table_layout.setContentsMargins(20, 18, 20, 18)
        self.test_table_layout.setSpacing(14)

        self.test_table_title = QLabel("Resultados de prueba")
        self.test_table_title.setObjectName("sectionTitle")

        self.test_table_subtitle = QLabel(
            "Resultados mock de pruebas ejecutadas. Cada columna filtrable tiene su propio botón."
        )
        self.test_table_subtitle.setObjectName("sectionSubtitle")
        self.test_table_subtitle.setWordWrap(True)

        self.test_range_label = QLabel("")
        self.test_range_label.setObjectName("rangeInfoLabel")

        self.test_table_layout.addWidget(self.test_table_title)
        self.test_table_layout.addWidget(self.test_table_subtitle)
        self.test_table_layout.addWidget(self.test_range_label)

        self.test_quick_filter_row = QHBoxLayout()
        self.test_quick_filter_row.setSpacing(12)

        self.quick_sn_label = QLabel("Filtrar SN")
        self.quick_sn_label.setObjectName("quickFilterLabel")

        self.quick_sn_input = QLineEdit()
        self.quick_sn_input.setObjectName("quickFilterInput")
        self.quick_sn_input.setPlaceholderText("Escribe un SN o fragmento...")
        self.quick_sn_input.setClearButtonEnabled(True)
        self.quick_sn_input.setMinimumWidth(220)
        self.quick_sn_input.setMaximumWidth(280)

        self.quick_mac_label = QLabel("Filtrar MAC")
        self.quick_mac_label.setObjectName("quickFilterLabel")

        self.quick_mac_input = QLineEdit()
        self.quick_mac_input.setObjectName("quickFilterInput")
        self.quick_mac_input.setPlaceholderText("Escribe una MAC o fragmento...")
        self.quick_mac_input.setClearButtonEnabled(True)
        self.quick_mac_input.setMinimumWidth(220)
        self.quick_mac_input.setMaximumWidth(280)

        self.test_quick_clear = QPushButton("Borrar filtros")
        self.test_quick_clear.setObjectName("quickFilterClearButton")
        self.test_quick_clear.setCursor(Qt.PointingHandCursor)
        self.test_quick_clear.setMinimumHeight(40)

        self.test_quick_filter_row.addStretch(1)
        self.test_quick_filter_row.addWidget(self.quick_sn_label)
        self.test_quick_filter_row.addWidget(self.quick_sn_input)
        self.test_quick_filter_row.addWidget(self.quick_mac_label)
        self.test_quick_filter_row.addWidget(self.quick_mac_input)
        self.test_quick_filter_row.addSpacing(18)
        self.test_quick_filter_row.addWidget(self.test_quick_clear)

        self.test_table_layout.addLayout(self.test_quick_filter_row)

        self.test_table = QTableWidget()
        self.test_table.setColumnCount(len(self.TEST_COLUMN_DEFS))
        self.test_table.setHorizontalHeaderLabels([c[1] for c in self.TEST_COLUMN_DEFS])

        test_vheader = self.test_table.verticalHeader()
        test_vheader.setVisible(False)
        test_vheader.setMinimumWidth(0)
        test_vheader.setFixedWidth(0)
        test_vheader.setDefaultSectionSize(40)

        self.test_table.setCornerButtonEnabled(False)
        self.test_table.setAlternatingRowColors(True)
        self.test_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.test_table.setSelectionMode(QTableWidget.NoSelection)
        self.test_table.setFocusPolicy(Qt.NoFocus)
        self.test_table.setShowGrid(False)
        self.test_table.setSortingEnabled(False)
        self.test_table.setMinimumHeight(280)
        self.test_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.test_table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)

        test_header = self.test_table.horizontalHeader()
        test_header.setStretchLastSection(True)
        test_header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        test_header.setMinimumHeight(48)
        test_header.setFixedHeight(48)

        for index, (_, _, width) in enumerate(self.TEST_COLUMN_DEFS):
            self.test_table.setColumnWidth(index, width)
            test_header.setSectionResizeMode(index, QHeaderView.Interactive)

        self._update_test_table_headers()

        self.test_table_layout.addWidget(self.test_table)
        self.content_layout.addWidget(self.test_table_card)

        self.scroll.setWidget(self.content)
        self.main_layout.addWidget(self.scroll)
        self.root_layout.addWidget(self.main_card)

        self._connect_events()
        self.apply_theme()

    def _connect_events(self) -> None:
        self.btn_date.clicked.connect(self._open_date_filter_dialog)
        self.btn_export_pdf.clicked.connect(self._export_pdf)

        self.table.horizontalHeader().sectionClicked.connect(self._open_header_filter_from_index)
        self.test_table.horizontalHeader().sectionClicked.connect(self._open_test_header_filter_from_index)

        self.quick_ip_input.textChanged.connect(self._on_ip_search_changed)
        self.quick_ip_clear.clicked.connect(self._clear_base_filters)

        self.quick_sn_input.textChanged.connect(self._on_test_sn_search_changed)
        self.quick_mac_input.textChanged.connect(self._on_test_mac_search_changed)
        self.test_quick_clear.clicked.connect(self._clear_test_filters)

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

            QFrame#headerCard {{
                background-color: {theme.section_alt_bg};
                border: 1px solid {theme.border};
                border-radius: 20px;
            }}

            QFrame#sectionCard {{
                background-color: {theme.section_bg};
                border: 1px solid {theme.border};
                border-radius: 20px;
            }}

            QLabel#titleLabel {{
                color: {theme.title};
                font-size: 30px;
                font-weight: 800;
                background: transparent;
            }}

            QLabel#subtitleLabel {{
                color: {theme.muted_text};
                font-size: 14px;
                font-weight: 500;
                background: transparent;
            }}

            QLabel#sectionTitle {{
                color: {theme.title};
                font-size: 20px;
                font-weight: 800;
                background: transparent;
            }}

            QLabel#sectionSubtitle {{
                color: {theme.muted_text};
                font-size: 13px;
                font-weight: 500;
                background: transparent;
            }}

            QLabel#rangeInfoLabel {{
                color: {theme.primary};
                font-size: 13px;
                font-weight: 700;
                background: transparent;
            }}

            QScrollArea {{
                background: transparent;
                border: none;
            }}

            QTableWidget {{
                background-color: {theme.input_bg};
                color: {theme.input_text};
                border: 1px solid {theme.input_border};
                border-radius: 16px;
                alternate-background-color: {theme.section_alt_bg};
                gridline-color: transparent;
            }}

            QTableWidget::item {{
                padding: 8px 10px;
                border: none;
            }}

            QHeaderView::section {{
                background-color: {theme.section_alt_bg};
                color: {theme.title};
                border: none;
                border-right: 1px solid {theme.border};
                border-bottom: 1px solid {theme.border};
                padding: 10px 14px;
                font-size: 13px;
                font-weight: 800;
            }}

            QScrollBar:vertical {{
                background: {theme.section_alt_bg};
                width: 12px;
                border-radius: 6px;
                margin: 4px;
            }}

            QScrollBar::handle:vertical {{
                background: {theme.border};
                min-height: 40px;
                border-radius: 6px;
            }}

            QScrollBar:horizontal {{
                background: {theme.section_alt_bg};
                height: 12px;
                border-radius: 6px;
                margin: 4px;
            }}

            QScrollBar::handle:horizontal {{
                background: {theme.border};
                min-width: 40px;
                border-radius: 6px;
            }}

                        QLabel#quickFilterLabel {{
                color: {theme.title};
                font-size: 14px;
                font-weight: 800;
                background: transparent;
            }}

            QLineEdit#quickFilterInput {{
                background-color: {theme.input_bg};
                color: {theme.input_text};
                border: 2px solid {theme.input_border};
                border-radius: 12px;
                padding: 8px 12px;
                min-height: 24px;
                font-size: 13px;
                font-weight: 600;
            }}

            QLineEdit#quickFilterInput:focus {{
                border: 2px solid {theme.primary};
                background-color: {theme.section_bg};
            }}

            QPushButton#quickFilterClearButton {{
                background-color: {theme.section_alt_bg};
                color: {theme.title};
                border: 1px solid {theme.border};
                border-radius: 12px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 800;
            }}

            QPushButton#quickFilterClearButton:hover {{
                background-color: {theme.input_bg};
            }}

            QPushButton#quickFilterClearButton:pressed {{
                background-color: {theme.section_bg};
            }}
        """)

        self.badge_ok.apply_theme()
        self.badge_fail.apply_theme()
        self.badge_pass.apply_theme()
        self.badge_fail_test.apply_theme()
        self.badge_disabled.apply_theme()
        self.badge_no_file.apply_theme()
        self._update_chart_backgrounds()

    def _refresh_all(self) -> None:
        self.filtered_records = self.data_source.filter_records(
            start_date=self.start_date,
            end_date=self.end_date,
            fabricante=self.column_filters["fabricante"],
            modelo=self.column_filters["modelo"],
            puerto=self.column_filters["puerto"],
            ip=self.column_filters["ip"],
            estatus=self.column_filters["estatus"],
            ip_contains=self.ip_search_text,
        )

        self.filtered_test_records = self.data_source.filter_test_records(
            sn=self.test_column_filters["sn"],
            mac=self.test_column_filters["mac"],
            ping=self.test_column_filters["ping"],
            factory_reset=self.test_column_filters["factory_reset"],
            actualizacion_software=self.test_column_filters["actualizacion_software"],
            usb=self.test_column_filters["usb"],
            wifi_24=self.test_column_filters["wifi_24"],
            wifi_5=self.test_column_filters["wifi_5"],
            tx=self.test_column_filters["tx"],
            rx=self.test_column_filters["rx"],
            sn_contains=self.test_sn_search_text,
            mac_contains=self.test_mac_search_text,
        )

        self._update_table_headers()
        self._update_range_label()
        self._load_table()

        self._update_test_table_headers()
        self._update_test_range_label()
        self._load_test_table()

        self._build_pie_chart()
        self._build_line_chart()
        self._build_manufacturer_chart()
        self._build_ports_chart()
        self._build_test_progress_chart()

    def _update_table_headers(self) -> None:
        labels = []

        for field_name, header_text, _ in self.COLUMN_DEFS:
            if field_name == "id":
                labels.append(header_text)
                continue

            if field_name == "timestamp":
                labels.append(f"{header_text}  ⏷")
                continue

            active = self.column_filters.get(field_name) is not None
            suffix = "  ⏷●" if active else "  ⏷"
            labels.append(f"{header_text}{suffix}")

        self.table.setHorizontalHeaderLabels(labels)

    def _update_range_label(self) -> None:
        start_txt = self.start_date.isoformat() if self.start_date else "Sin límite"
        end_txt = self.end_date.isoformat() if self.end_date else "Sin límite"
        self.range_label.setText(f"Rango actual: {start_txt} → {end_txt} | Registros: {len(self.filtered_records)}")

    def _update_test_table_headers(self) -> None:
        labels = []

        for field_name, header_text, _ in self.TEST_COLUMN_DEFS:
            if field_name == "id":
                labels.append(header_text)
                continue

            active = self.test_column_filters.get(field_name) is not None
            suffix = "  ⏷●" if active else "  ⏷"
            labels.append(f"{header_text}{suffix}")

        self.test_table.setHorizontalHeaderLabels(labels)

    def _update_test_range_label(self) -> None:
        total = len(self.data_source.get_all_test_records())
        current = len(self.filtered_test_records)
        self.test_range_label.setText(f"Registros mock: {current} de {total}")

    # /*************************************
    # Gráfica 1: Distribución de estatus
    # *************************************
    def _build_pie_chart(self) -> None:
        theme = ThemeManager.get_theme()
        summary = self.data_source.build_status_summary(self.filtered_records)
        validos = summary["VALIDO"]
        invalidos = summary["INVALIDO"]
        total = validos + invalidos

        if total == 0:
            validos = 1
            invalidos = 0
            total = 1

        series = QPieSeries()
        series.setPieSize(0.78)

        slice_ok = series.append(f"Válido ({(validos / total) * 100:.1f}%)", validos)
        slice_fail = series.append(f"Inválido ({(invalidos / total) * 100:.1f}%)", invalidos)

        slice_ok.setColor(QColor("#2DBE60"))
        slice_fail.setColor(QColor("#E74C3C"))

        slice_ok.setBorderColor(QColor(theme.title))
        slice_fail.setBorderColor(QColor(theme.title))

        slice_ok.setLabelVisible(True)
        slice_fail.setLabelVisible(True)

        slice_ok.setLabelColor(QColor(theme.title))
        slice_fail.setLabelColor(QColor(theme.title))

        slice_ok.setLabelArmLengthFactor(0.15)
        slice_fail.setLabelArmLengthFactor(0.15)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("")
        chart.legend().hide()
        chart.setMargins(QMargins(0, 0, 0, 0))
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setBackgroundVisible(True)
        chart.setBackgroundBrush(QBrush(QColor(theme.section_bg)))

        self.pie_chart_view.setChart(chart)
        self._update_chart_backgrounds()

    # /*************************************
    # Gráfica 2: % de éxito por semana
    # *************************************
    def _build_line_chart(self) -> None:
        series_data = self.data_source.build_weekly_success_series(self.filtered_records)
        chart = QChart()
        chart.setTitle("")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.legend().setMarkerShape(QLegend.MarkerShapeFromSeries)
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setMargins(QMargins(10, 10, 10, 10))

        x_axis = QBarCategoryAxis()
        x_axis.append(["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"])

        y_axis = QValueAxis()
        y_axis.setRange(0, 100)
        y_axis.setTickCount(6)
        y_axis.setLabelFormat("%d%%")

        chart.addAxis(x_axis, Qt.AlignBottom)
        chart.addAxis(y_axis, Qt.AlignLeft)

        if ThemeManager.is_dark():
            previous_colors = ["#7DD3FC", "#FBBF24", "#A7F3D0"]
        else:
            previous_colors = ["#1D4ED8", "#B45309", "#0F766E"]

        previous_index = 0

        for item in series_data:
            line = QLineSeries()
            line.setName(item["label"])

            pen = QPen()
            pen.setWidth(3)

            if item["is_current"]:
                pen.setColor(QColor("#E74C3C"))
            else:
                pen.setColor(QColor(previous_colors[previous_index % len(previous_colors)]))
                previous_index += 1

            line.setPen(pen)

            for x, y in item["points"]:
                line.append(QPointF(x, y))

            chart.addSeries(line)
            line.attachAxis(x_axis)
            line.attachAxis(y_axis)

        self.line_chart_view.setChart(chart)
        self._update_chart_backgrounds()

    # /*************************************
    # Gráfica 3: % de éxito por fabricante
    # *************************************
    def _build_manufacturer_chart(self) -> None:
        data = self._build_manufacturer_success_data()

        chart = QChart()
        chart.setTitle("")
        chart.legend().hide()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setMargins(QMargins(10, 10, 10, 10))

        categories = [label for label, _, _ in data]
        values = [value for _, value, _ in data]

        series = QBarSeries()

        for i, (label, value, color) in enumerate(data):
            single_set = QBarSet(label)
            bar_values = []
            for j in range(len(data)):
                bar_values.append(value if i == j else 0.0)

            for v in bar_values:
                single_set.append(v)

            single_set.setColor(QColor(color))
            single_set.setBorderColor(QColor(color))
            self._connect_barset_tooltip(single_set, label, bar_values)
            series.append(single_set)

        chart.addSeries(series)

        x_axis = QBarCategoryAxis()
        x_axis.append(categories)

        y_axis = QValueAxis()
        y_axis.setRange(0, 100)
        y_axis.setTickCount(6)
        y_axis.setLabelFormat("%d%%")

        chart.addAxis(x_axis, Qt.AlignBottom)
        chart.addAxis(y_axis, Qt.AlignLeft)
        series.attachAxis(x_axis)
        series.attachAxis(y_axis)

        self.fabricante_chart_view.setChart(chart)
        self._update_chart_backgrounds()

    # /*************************************
    # Gráfica 4: % de éxito por puertos
    # *************************************
    def _build_ports_chart(self) -> None:
        data = self._build_port_success_data()

        chart = QChart()
        chart.setTitle("")
        chart.legend().hide()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setMargins(QMargins(10, 10, 10, 10))

        categories = [label for label, _, _ in data]

        series = QBarSeries()

        for i, (label, value, color) in enumerate(data):
            single_set = QBarSet(label)
            bar_values = []
            for j in range(len(data)):
                bar_values.append(value if i == j else 0.0)

            for v in bar_values:
                single_set.append(v)

            single_set.setColor(QColor(color))
            single_set.setBorderColor(QColor(color))
            self._connect_barset_tooltip(single_set, label, bar_values)
            series.append(single_set)

        chart.addSeries(series)

        x_axis = QBarCategoryAxis()
        x_axis.append(categories)

        y_axis = QValueAxis()
        y_axis.setRange(0, 100)
        y_axis.setTickCount(6)
        y_axis.setLabelFormat("%d%%")

        chart.addAxis(x_axis, Qt.AlignBottom)
        chart.addAxis(y_axis, Qt.AlignLeft)
        series.attachAxis(x_axis)
        series.attachAxis(y_axis)

        self.puertos_chart_view.setChart(chart)
        self._update_chart_backgrounds()

    # /*************************************
    # Gráfica 5: Pruebas realizadas
    # *************************************
    def _build_test_progress_chart(self) -> None:
        theme = ThemeManager.get_theme()
        data = self._build_test_progress_data()

        categories = data["categories"]
        counts = data["counts"]
        totals = data["totals"]
        record_count = data["record_count"]

        chart = QChart()
        chart.setTitle("")
        chart.legend().hide()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setMargins(QMargins(10, 10, 10, 20))

        series = QStackedBarSeries()

        set_pass = QBarSet("PASS")
        set_fail = QBarSet("FAIL")
        set_disabled = QBarSet("DESACTIVADO")
        set_no_file = QBarSet("NO FILE")

        pass_values = counts["Pass"]
        fail_values = counts["Fail"]
        disabled_values = counts["Desactivado"]
        no_file_values = counts["No File"]

        for value in pass_values:
            set_pass.append(value)
        for value in fail_values:
            set_fail.append(value)
        for value in disabled_values:
            set_disabled.append(value)
        for value in no_file_values:
            set_no_file.append(value)

        set_pass.setColor(QColor("#2DBE60"))
        set_fail.setColor(QColor("#FF2D2D"))
        set_disabled.setColor(QColor("#F7EA00"))
        set_no_file.setColor(QColor("#4F55E0"))

        for bar_set, label, values in [
            (set_pass, "PASS", pass_values),
            (set_fail, "FAIL", fail_values),
            (set_disabled, "DESACTIVADO", disabled_values),
            (set_no_file, "NO FILE", no_file_values),
        ]:
            self._connect_barset_tooltip(bar_set, label, values)
            series.append(bar_set)

        chart.addSeries(series)

        x_axis = QBarCategoryAxis()
        x_axis.append(categories)

        y_axis = QValueAxis()
        y_axis.setRange(0, max(record_count, 1))
        y_axis.setTickCount(min(max(record_count, 2), 6))
        y_axis.setLabelFormat("%d")
        y_axis.setTitleText("")

        chart.addAxis(x_axis, Qt.AlignBottom)
        chart.addAxis(y_axis, Qt.AlignLeft)
        series.attachAxis(x_axis)
        series.attachAxis(y_axis)

        self.test_progress_chart_view.setChart(chart)
        self._update_chart_backgrounds()
        QTimer.singleShot(0, lambda: self._draw_test_progress_top_labels(totals, record_count))

    def _update_chart_backgrounds(self) -> None:
        theme = ThemeManager.get_theme()

        for view in [
            self.pie_chart_view,
            self.line_chart_view,
            self.fabricante_chart_view,
            self.puertos_chart_view,
            self.test_progress_chart_view,
        ]:
            chart = view.chart()
            if chart is None:
                continue

            chart.setBackgroundVisible(True)
            chart.setBackgroundBrush(QBrush(QColor(theme.section_bg)))
            chart.setPlotAreaBackgroundVisible(False)
            chart.setTitleBrush(QColor(theme.title))
            chart.legend().setLabelColor(QColor(theme.text))

            for axis in chart.axes():
                axis.setLabelsColor(QColor(theme.text))
                axis.setLinePenColor(QColor(theme.border))
                axis.setGridLineColor(QColor(theme.border))
                axis.setTitleBrush(QColor(theme.title))

            for series in chart.series():
                if isinstance(series, QPieSeries):
                    for pie_slice in series.slices():
                        pie_slice.setLabelColor(QColor(theme.title))
                        pie_slice.setBorderColor(QColor(theme.title))

    # /*************************************
    # Tabla y filtros
    # *************************************
    def _load_table(self) -> None:
        self.table.setRowCount(len(self.filtered_records))

        for row_idx, record in enumerate(self.filtered_records):
            values = [
                str(record.id),
                record.timestamp.isoformat(sep=" ", timespec="seconds"),
                record.fabricante,
                record.modelo,
                str(record.puerto),
                record.ip,
                normalize_status(record.estatus),
            ]

            for col_idx, value in enumerate(values):
                item = QTableWidgetItem(value)

                if col_idx in (0, 4):
                    item.setTextAlignment(Qt.AlignCenter)

                if col_idx == 6:
                    color = "#2DBE60" if normalize_status(record.estatus) == "VALIDO" else "#E74C3C"
                    item.setForeground(QColor(color))

                self.table.setItem(row_idx, col_idx, item)

    def _load_test_table(self) -> None:
        self.test_table.setRowCount(len(self.filtered_test_records))

        for row_idx, record in enumerate(self.filtered_test_records):
            values = [
                str(record.id),
                record.sn,
                record.mac,
                record.ping,
                record.factory_reset,
                record.actualizacion_software,
                record.usb,
                record.wifi_24,
                record.wifi_5,
                record.tx,
                record.rx,
            ]

            for col_idx, value in enumerate(values):
                item = QTableWidgetItem(value)

                if col_idx == 0:
                    item.setTextAlignment(Qt.AlignCenter)

                if col_idx >= 3:
                    if value == "Pass":
                        item.setForeground(QColor("#2DBE60"))
                    elif value == "Fail":
                        item.setForeground(QColor("#E74C3C"))
                    elif value == "Desactivado":
                        item.setForeground(QColor("#B38B00"))
                    elif value == "No File":
                        item.setForeground(QColor("#4F8EF7"))

                self.test_table.setItem(row_idx, col_idx, item)

    def _open_date_filter_dialog(self) -> None:
        dialog = DateRangeDialog(self.start_date, self.end_date, self)
        self._apply_native_dark_to_window(dialog)
        if dialog.exec():
            self.start_date, self.end_date = dialog.get_range()
            self._refresh_all()

    def _open_header_filter_from_index(self, logical_index: int) -> None:
        field_name = self.COLUMN_DEFS[logical_index][0]
        if field_name == "id":
            return
        if field_name == "timestamp":
            self._open_date_filter_dialog()
            return
        self._open_column_filter_menu(field_name, logical_index)

    def _open_column_filter_menu(self, field_name: str, logical_index: int | None = None) -> None:
        menu = QMenu(self)
        theme = ThemeManager.get_theme()

        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {theme.main_card_bg};
                color: {theme.text};
                border: 1px solid {theme.border};
                padding: 6px;
            }}
            QMenu::item {{
                padding: 8px 18px;
                border-radius: 8px;
            }}
            QMenu::item:selected {{
                background-color: {theme.primary};
                color: white;
            }}
        """)

        clear_action = menu.addAction("Todos")
        clear_action.triggered.connect(lambda: self._set_column_filter(field_name, None))
        menu.addSeparator()

        current_records = self.data_source.filter_records(
            start_date=self.start_date,
            end_date=self.end_date,
        )
        options = self.data_source.get_unique_values(current_records, field_name)

        for option in options:
            action = menu.addAction(option)
            action.triggered.connect(
                lambda checked=False, f=field_name, o=option: self._set_column_filter(f, o)
            )

        if logical_index is None:
            menu.exec(self.mapToGlobal(self.rect().center()))
            return

        header = self.table.horizontalHeader()
        global_pos = header.mapToGlobal(header.rect().bottomLeft())
        menu.exec(
            QPoint(
                global_pos.x() + header.sectionViewportPosition(logical_index),
                global_pos.y(),
            )
        )

    def _set_column_filter(self, field_name: str, value: str | None) -> None:
        self.column_filters[field_name] = value
        self._refresh_all()

    def _on_ip_search_changed(self, text: str) -> None:
        self.ip_search_text = text.strip()
        self._refresh_all()

    def _on_test_sn_search_changed(self, text: str) -> None:
        self.test_sn_search_text = text.strip()
        self._refresh_all()

    def _on_test_mac_search_changed(self, text: str) -> None:
        self.test_mac_search_text = text.strip()
        self._refresh_all()

    def _clear_base_filters(self) -> None:
        self.column_filters = {
            "fabricante": None,
            "modelo": None,
            "puerto": None,
            "ip": None,
            "estatus": None,
        }
        self.ip_search_text = ""
        self.quick_ip_input.blockSignals(True)
        self.quick_ip_input.clear()
        self.quick_ip_input.blockSignals(False)
        self._refresh_all()

    def _open_test_header_filter_from_index(self, logical_index: int) -> None:
        field_name = self.TEST_COLUMN_DEFS[logical_index][0]
        if field_name == "id":
            return
        self._open_test_column_filter_menu(field_name, logical_index)

    def _open_test_column_filter_menu(self, field_name: str, logical_index: int | None = None) -> None:
        menu = QMenu(self)
        theme = ThemeManager.get_theme()

        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {theme.main_card_bg};
                color: {theme.text};
                border: 1px solid {theme.border};
                padding: 6px;
            }}
            QMenu::item {{
                padding: 8px 18px;
                border-radius: 8px;
            }}
            QMenu::item:selected {{
                background-color: {theme.primary};
                color: white;
            }}
        """)

        clear_action = menu.addAction("Todos")
        clear_action.triggered.connect(lambda: self._set_test_column_filter(field_name, None))
        menu.addSeparator()

        current_records = self.data_source.get_all_test_records()
        options = self.data_source.get_unique_test_values(current_records, field_name)

        for option in options:
            action = menu.addAction(option)
            action.triggered.connect(
                lambda checked=False, f=field_name, o=option: self._set_test_column_filter(f, o)
            )

        if logical_index is None:
            menu.exec(self.mapToGlobal(self.rect().center()))
            return

        header = self.test_table.horizontalHeader()
        global_pos = header.mapToGlobal(header.rect().bottomLeft())
        menu.exec(
            QPoint(
                global_pos.x() + header.sectionViewportPosition(logical_index),
                global_pos.y(),
            )
        )

    def _set_test_column_filter(self, field_name: str, value: str | None) -> None:
        self.test_column_filters[field_name] = value
        self._refresh_all()

    def _clear_test_filters(self) -> None:
        self.test_column_filters = {
            "sn": None,
            "mac": None,
            "ping": None,
            "factory_reset": None,
            "actualizacion_software": None,
            "usb": None,
            "wifi_24": None,
            "wifi_5": None,
            "tx": None,
            "rx": None,
        }
        self.test_sn_search_text = ""
        self.test_mac_search_text = ""

        self.quick_sn_input.blockSignals(True)
        self.quick_mac_input.blockSignals(True)
        self.quick_sn_input.clear()
        self.quick_mac_input.clear()
        self.quick_sn_input.blockSignals(False)
        self.quick_mac_input.blockSignals(False)

        self._refresh_all()

    # /*************************************
    # Exportación PDF
    # *************************************
    def _export_pdf(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar reporte PDF",
            str(Path.home() / "reporte_ont_nexus.pdf"),
            "PDF Files (*.pdf)",
        )
        if not path:
            return

        writer = QPdfWriter(path)
        writer.setResolution(120)

        painter = QPainter(writer)
        if not painter.isActive():
            self._show_themed_message(
                QMessageBox.Warning,
                "Error",
                "No se pudo crear el PDF.",
            )
            return

        try:
            theme = ThemeManager.get_theme()
            summary = self.data_source.build_status_summary(self.filtered_records)

            painter.setPen(QColor(theme.title))
            title_font = QFont()
            title_font.setPointSize(18)
            title_font.setBold(True)
            painter.setFont(title_font)
            painter.drawText(60, 80, "Reporte ONT Nexus")

            body_font = QFont()
            body_font.setPointSize(10)
            painter.setFont(body_font)
            painter.setPen(QColor(theme.text))

            start_txt = self.start_date.isoformat() if self.start_date else "Sin límite"
            end_txt = self.end_date.isoformat() if self.end_date else "Sin límite"

            y = 130
            painter.drawText(60, y, f"Rango: {start_txt} a {end_txt}")
            y += 24
            painter.drawText(60, y, f"Registros filtrados: {len(self.filtered_records)}")
            y += 24
            painter.drawText(60, y, f"Válidos: {summary['VALIDO']}")
            y += 24
            painter.drawText(60, y, f"Inválidos: {summary['INVALIDO']}")
            y += 36

            headers = ["ID", "TIMESTAMP", "FABRICANTE", "MODELO", "PUERTO", "IP", "ESTATUS"]
            x_positions = [60, 100, 250, 370, 485, 560, 670]

            painter.setPen(QColor(theme.title))
            for x, header_text in zip(x_positions, headers):
                painter.drawText(x, y, header_text)

            y += 18
            painter.setPen(QColor(theme.border))
            painter.drawLine(60, y, 780, y)
            y += 18

            painter.setPen(QColor(theme.text))
            export_rows = self.filtered_records[:20]

            for record in export_rows:
                if y > 1120:
                    writer.newPage()
                    y = 80

                row_values = [
                    str(record.id),
                    record.timestamp.isoformat(sep=" ", timespec="seconds"),
                    record.fabricante,
                    record.modelo,
                    str(record.puerto),
                    record.ip,
                    normalize_status(record.estatus),
                ]

                for x, value in zip(x_positions, row_values):
                    painter.drawText(x, y, value[:22])

                y += 22

            self._show_themed_message(
                QMessageBox.Information,
                "PDF exportado",
                "El reporte se exportó correctamente.",
            )
        finally:
            painter.end()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

        w = max(self.width(), 1000)

        title_size = min(max(int(w / 42), 24), 34)
        section_title_size = min(max(int(w / 75), 17), 22)
        subtitle_size = min(max(int(w / 100), 12), 14)

        title_font = self.title.font()
        title_font.setPointSize(title_size)
        title_font.setWeight(QFont.Bold)
        self.title.setFont(title_font)

        for label in [
            self.pie_title,
            self.line_title,
            self.fabricante_title,
            self.puertos_title,
            self.test_progress_title,
            self.table_title,
            self.test_table_title,
        ]:
            font = label.font()
            font.setPointSize(section_title_size)
            font.setWeight(QFont.Bold)
            label.setFont(font)

        for label in [
            self.subtitle,
            self.pie_subtitle,
            self.line_subtitle,
            self.fabricante_subtitle,
            self.puertos_subtitle,
            self.test_progress_subtitle,
            self.table_subtitle,
            self.test_table_subtitle,
        ]:
            font = label.font()
            font.setPointSize(subtitle_size)
            label.setFont(font)

        if self.width() < 1200:
            self.pie_card.setMinimumHeight(500)
            self.line_card.setMinimumHeight(500)
            self.fabricante_card.setMinimumHeight(500)
            self.puertos_card.setMinimumHeight(500)
            self.test_progress_card.setMinimumHeight(560)

            self.pie_chart_view.setMinimumHeight(340)
            self.line_chart_view.setMinimumHeight(340)
            self.fabricante_chart_view.setMinimumHeight(340)
            self.puertos_chart_view.setMinimumHeight(340)
            self.test_progress_chart_view.setMinimumHeight(360)

            self.table_card.setMinimumHeight(430)
            self.test_table_card.setMinimumHeight(450)
        else:
            self.pie_card.setMinimumHeight(470)
            self.line_card.setMinimumHeight(470)
            self.fabricante_card.setMinimumHeight(470)
            self.puertos_card.setMinimumHeight(470)
            self.test_progress_card.setMinimumHeight(520)

            self.pie_chart_view.setMinimumHeight(320)
            self.line_chart_view.setMinimumHeight(320)
            self.fabricante_chart_view.setMinimumHeight(320)
            self.puertos_chart_view.setMinimumHeight(320)
            self.test_progress_chart_view.setMinimumHeight(350)

            self.table_card.setMinimumHeight(420)
            self.test_table_card.setMinimumHeight(440)

        QTimer.singleShot(0, lambda: self._draw_test_progress_top_labels(self._build_test_progress_data()["totals"], len(self.filtered_test_records)))
