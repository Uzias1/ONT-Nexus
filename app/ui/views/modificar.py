from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from app.ui.theme_manager import ThemeManager
from app.ui.widgets.buttons import BackButton
from app.ui.widgets.theme_toggle import ThemeToggle


class MiniActionButton(QPushButton):
    def __init__(self, text: str, bg: str, hover: str, pressed: str, border: str, parent=None) -> None:
        super().__init__(text, parent)
        self._bg = bg
        self._hover = hover
        self._pressed = pressed
        self._border = border

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(56, 38)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._apply_style()

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._bg};
                color: white;
                border: 1px solid {self._border};
                border-radius: 10px;
                font-size: 18px;
                font-weight: 800;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {self._hover};
            }}
            QPushButton:pressed {{
                background-color: {self._pressed};
            }}
        """)


class CrudModeButton(QPushButton):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self._selected = False
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.apply_theme()

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.apply_theme()

    def apply_theme(self) -> None:
        theme = ThemeManager.get_theme()

        bg = theme.section_bg
        border = theme.border
        text = theme.text
        hover = theme.section_alt_bg

        if self._selected:
            bg = "#B8E61B"
            border = "#8CAA12"
            text = "#111111"
            hover = "#A9D615"

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                font-weight: 800;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
        """)
class SweetAlertDialog(QDialog):
    def __init__(
        self,
        title: str,
        message: str,
        details: list[tuple[str, str]] | None = None,
        confirm_text: str = "Confirmar",
        cancel_text: str = "Cancelar",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setWindowTitle(title)
        details = details or []
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        card = QFrame()
        card.setObjectName("sweetCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(14)
        lbl_title = QLabel(title)
        lbl_title.setObjectName("sweetTitle")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setWordWrap(True)
        lbl_message = QLabel(message)
        lbl_message.setObjectName("sweetMessage")
        lbl_message.setAlignment(Qt.AlignCenter)
        lbl_message.setWordWrap(True)
        card_layout.addWidget(lbl_title)
        card_layout.addWidget(lbl_message)
        if details:
            details_box = QFrame()
            details_box.setObjectName("detailsBox")
            details_layout = QVBoxLayout(details_box)
            details_layout.setContentsMargins(14, 14, 14, 14)
            details_layout.setSpacing(8)
            for label, value in details:
                item = QLabel(f"<b>{label}:</b> {value if value else '—'}")
                item.setWordWrap(True)
                details_layout.addWidget(item)
            card_layout.addWidget(details_box)
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(16)
        buttons_row.setAlignment(Qt.AlignCenter)
        self.btn_ok = QPushButton(confirm_text)
        self.btn_ok.setObjectName("sweetOkButton")
        self.btn_cancel = QPushButton(cancel_text)
        self.btn_cancel.setObjectName("sweetCancelButton")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        buttons_row.addWidget(self.btn_ok)
        buttons_row.addWidget(self.btn_cancel)
        card_layout.addLayout(buttons_row)
        root.addWidget(card)
        self._apply_styles()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._apply_titlebar_theme()

    def _apply_titlebar_theme(self) -> None:
        try:
            import sys
            import ctypes
            if sys.platform != "win32":
                return
            hwnd = int(self.winId())
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

    def _apply_styles(self) -> None:
        theme = ThemeManager.get_theme()
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme.app_bg};
            }}
            QFrame#sweetCard {{
                background-color: {theme.main_card_bg};
                border: 1px solid {theme.border};
                border-radius: 16px;
            }}
            QLabel#sweetTitle {{
                color: {theme.title}; font-size: 20px; font-weight: 800; background: transparent;
            }}
            QLabel#sweetMessage {{
                color: {theme.text}; font-size: 14px; background: transparent;
            }}
            QFrame#detailsBox {{
                background-color: {theme.section_bg};
                border: 1px solid {theme.border}; border-radius: 12px;
            }}
            QFrame#detailsBox QLabel {{
                color: {theme.text}; background: transparent; font-size: 13px;
            }}
            QPushButton#sweetOkButton {{
                min-width: 130px; min-height: 42px; border-radius: 12px;
                font-size: 14px; font-weight: 700; padding: 8px 14px;
                background-color: #7BBE3C; color: white; border: 1px solid #4D7F1F;
            }}
            QPushButton#sweetOkButton:hover  {{ background-color: #6FAE34; }}
            QPushButton#sweetOkButton:pressed {{ background-color: #629C2E; }}
            QPushButton#sweetCancelButton {{
                min-width: 130px; min-height: 42px; border-radius: 12px;
                font-size: 14px; font-weight: 700; padding: 8px 14px;
                background-color: #E95A52; color: white; border: 1px solid #A73732;
            }}
            QPushButton#sweetCancelButton:hover  {{ background-color: #D94B44; }}
            QPushButton#sweetCancelButton:pressed {{ background-color: #C93C36; }}
        """)

    def __init__(
        self,
        title: str,
        message: str,
        details: list[tuple[str, str]] | None = None,
        confirm_text: str = "Confirmar",
        cancel_text: str = "Cancelar",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setWindowTitle(title)

        details = details or []

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)

        card = QFrame()
        card.setObjectName("sweetCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(14)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("sweetTitle")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setWordWrap(True)

        lbl_message = QLabel(message)
        lbl_message.setObjectName("sweetMessage")
        lbl_message.setAlignment(Qt.AlignCenter)
        lbl_message.setWordWrap(True)

        card_layout.addWidget(lbl_title)
        card_layout.addWidget(lbl_message)

        if details:
            details_box = QFrame()
            details_box.setObjectName("detailsBox")
            details_layout = QVBoxLayout(details_box)
            details_layout.setContentsMargins(14, 14, 14, 14)
            details_layout.setSpacing(8)

            for label, value in details:
                item = QLabel(f"<b>{label}:</b> {value if value else '—'}")
                item.setWordWrap(True)
                details_layout.addWidget(item)

            card_layout.addWidget(details_box)

        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(16)
        buttons_row.setAlignment(Qt.AlignCenter)

        self.btn_ok = QPushButton(confirm_text)
        self.btn_ok.setObjectName("sweetOkButton")

        self.btn_cancel = QPushButton(cancel_text)
        self.btn_cancel.setObjectName("sweetCancelButton")

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        buttons_row.addWidget(self.btn_ok)
        buttons_row.addWidget(self.btn_cancel)
        card_layout.addLayout(buttons_row)

        root.addWidget(card)

        theme = ThemeManager.get_theme()
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme.app_bg};
            }}
            QFrame#sweetCard {{
                background-color: {theme.main_card_bg};
                border: 1px solid {theme.border};
                border-radius: 16px;
            }}
            QLabel#sweetTitle {{
                color: {theme.title};
                font-size: 20px;
                font-weight: 800;
                background: transparent;
            }}
            QLabel#sweetMessage {{
                color: {theme.text};
                font-size: 14px;
                background: transparent;
            }}
            QFrame#detailsBox {{
                background-color: {theme.section_bg};
                border: 1px solid {theme.border};
                border-radius: 12px;
            }}
            QFrame#detailsBox QLabel {{
                color: {theme.text};
                background: transparent;
                font-size: 13px;
            }}
            QPushButton#sweetOkButton {{
                min-width: 130px;
                min-height: 42px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 700;
                padding: 8px 14px;
                background-color: #7BBE3C;
                color: white;
                border: 1px solid #4D7F1F;
            }}
            QPushButton#sweetOkButton:hover {{
                background-color: #6FAE34;
            }}
            QPushButton#sweetOkButton:pressed {{
                background-color: #629C2E;
            }}
            QPushButton#sweetCancelButton {{
                min-width: 130px;
                min-height: 42px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 700;
                padding: 8px 14px;
                background-color: #E95A52;
                color: white;
                border: 1px solid #A73732;
            }}
            QPushButton#sweetCancelButton:hover {{
                background-color: #D94B44;
            }}
            QPushButton#sweetCancelButton:pressed {{
                background-color: #C93C36;
            }}
        """)


class ThemeModeRow(QWidget):
    theme_toggled = Signal(bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout_root = QHBoxLayout(self)
        layout_root.setContentsMargins(0, 0, 0, 0)
        layout_root.setSpacing(18)

        self.title = QLabel("Modo claro / oscuro")
        self.title.setWordWrap(True)
        self.title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.toggle = ThemeToggle(checked=ThemeManager.is_dark())
        self.toggle.toggled.connect(self.theme_toggled.emit)

        layout_root.addWidget(self.title, 1)
        layout_root.addStretch()
        layout_root.addWidget(self.toggle, 0, alignment=Qt.AlignRight | Qt.AlignVCenter)

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


class FormFieldRow(QWidget):
    def __init__(self, label_text: str, placeholder: str, parent=None) -> None:
        super().__init__(parent)

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.root.setSpacing(8)

        self.label = QLabel(label_text)
        self.label.setObjectName("fieldLabel")

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setObjectName("panelInput")

        self.root.addWidget(self.label)
        self.root.addWidget(self.input)

    def clear(self) -> None:
        self.input.clear()


class PanelForm(QWidget):
    submitted = Signal()
    cancelled = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.root.setSpacing(14)

        self.fields_container = QWidget()
        self.fields_container.setStyleSheet("background: transparent;")

        self.fields_layout = QVBoxLayout(self.fields_container)
        self.fields_layout.setContentsMargins(0, 0, 0, 0)
        self.fields_layout.setSpacing(12)

        self.actions = QHBoxLayout()
        self.actions.setContentsMargins(0, 4, 0, 0)
        self.actions.setSpacing(14)
        self.actions.setAlignment(Qt.AlignCenter)

        self.btn_ok     = MiniActionButton("✓", "#7BBE3C", "#6FAE34", "#629C2E", "#4D7F1F")
        self.btn_cancel = MiniActionButton("✕", "#E95A52", "#D94B44", "#C93C36", "#A73732")

        self.btn_ok.clicked.connect(self.submitted.emit)
        self.btn_cancel.clicked.connect(self.cancelled.emit)

        self.actions.addWidget(self.btn_ok)
        self.actions.addWidget(self.btn_cancel)

        self.root.addWidget(self.fields_container, 0, alignment=Qt.AlignTop)
        self.root.addStretch(1)
        self.root.addLayout(self.actions)

        self.rows: list[FormFieldRow] = []

    def set_rows(self, rows: list[tuple[str, str]]) -> None:
        while self.fields_layout.count():
            item = self.fields_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.rows.clear()

        for label_text, placeholder in rows:
            row = FormFieldRow(label_text, placeholder)
            self.fields_layout.addWidget(row)
            self.rows.append(row)

    def clear_fields(self) -> None:
        for row in self.rows:
            row.clear()

    def get_values(self) -> list[tuple[str, str]]:
        return [(row.label.text(), row.input.text().strip()) for row in self.rows]
class FilterableTableWidget(QTableWidget):
    def __init__(self, columns: list[str], filterable_columns: list[bool] | None = None, parent=None) -> None:
        super().__init__(0, len(columns), parent)
        self.columns = columns
        self.filterable_columns = filterable_columns or [False] * len(columns)
        self.raw_rows: list[list[str]] = []
        self.filters: dict[int, str | None] = {i: None for i in range(len(columns))}

        header_labels = [
            f"{name} ▼" if self.filterable_columns[i] else name
            for i, name in enumerate(columns)
        ]
        self.setHorizontalHeaderLabels(header_labels)

        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionMode(QTableWidget.NoSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setStretchLastSection(True)
        header.sectionClicked.connect(self._on_section_clicked)

        self.apply_theme()

    def apply_theme(self) -> None:
        theme = ThemeManager.get_theme()
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: rgba(255, 255, 255, 0.04);
                color: {theme.text};
                border: none;
                border-radius: 8px;
                gridline-color: transparent;
                selection-background-color: transparent;
                alternate-background-color: rgba(255, 255, 255, 0.05);
                padding: 4px;
            }}
            QTableWidget::item {{
                background: transparent;
                padding: 6px 8px;
            }}
            QHeaderView::section {{
                background-color: {theme.section_alt_bg};
                color: {theme.title};
                border: none;
                border-right: 1px solid {theme.border};
                border-bottom: 1px solid {theme.border};
                padding: 10px 12px;
                font-weight: 800;
            }}
        """)

    def set_rows(self, rows: list[list[str]]) -> None:
        self.raw_rows = rows
        self._apply_filters()

    def _on_section_clicked(self, column: int) -> None:
        if not self.filterable_columns[column]:
            return

        unique_values = sorted({str(row[column]) for row in self.raw_rows})
        menu = QMenu(self)

        theme = ThemeManager.get_theme()
        menu_bg     = "#0F1720" if ThemeManager.is_dark() else "#A9BCD0"
        menu_border = theme.border
        menu_text   = "#F4F7FB" if ThemeManager.is_dark() else "#17324D"
        menu_hover  = theme.section_alt_bg if ThemeManager.is_dark() else "#8EA8C1"

        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {menu_bg};
                color: {menu_text};
                border: 1px solid {menu_border};
                padding: 6px;
            }}
            QMenu::item {{
                background-color: transparent;
                color: {menu_text};
                padding: 8px 14px;
                border-radius: 6px;
                margin: 2px 4px;
            }}
            QMenu::item:selected {{
                background-color: {menu_hover};
                color: {menu_text};
            }}
            QMenu::separator {{
                height: 1px;
                background: {menu_border};
                margin: 6px 8px;
            }}
        """)

        current_value = self.filters.get(column)

        action_all = menu.addAction("Todos")
        if current_value is None:
            action_all.setCheckable(True)
            action_all.setChecked(True)
        action_all.triggered.connect(lambda: self._set_filter(column, None))
        menu.addSeparator()

        for value in unique_values:
            action = menu.addAction(value)
            action.setCheckable(True)
            action.setChecked(current_value == value)
            action.triggered.connect(lambda checked=False, col=column, val=value: self._set_filter(col, val))

        header = self.horizontalHeader()
        x = header.sectionPosition(column)
        pos = header.mapToGlobal(QPoint(x + 10, header.height()))
        menu.exec(pos)

    def _set_filter(self, column: int, value: str | None) -> None:
        self.filters[column] = value
        self._apply_filters()

    def _apply_filters(self) -> None:
        filtered_rows: list[list[str]] = []

        for row in self.raw_rows:
            ok = True
            for col, selected in self.filters.items():
                if selected is not None and str(row[col]) != str(selected):
                    ok = False
                    break
            if ok:
                filtered_rows.append(row)

        self.setRowCount(len(filtered_rows))

        for row_index, row_values in enumerate(filtered_rows):
            for col_index, value in enumerate(row_values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.setItem(row_index, col_index, item)

        self.resizeRowsToContents()


class CrudPanel(QFrame):
    create_requested = Signal(str, dict)

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.panel_title_text = title
        self.current_mode: str | None = None
        self.current_widget: QWidget | None = None
        self.form: PanelForm | None = None

        self.setObjectName("crudPanel")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(24, 18, 24, 18)
        self.root.setSpacing(14)

        self.title = QLabel(title)
        self.title.setObjectName("panelTitle")
        self.title.setAlignment(Qt.AlignHCenter)

        self.body = QFrame()
        self.body.setObjectName("panelBody")

        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(18, 16, 18, 16)
        self.body_layout.setSpacing(10)

        self.root.addWidget(self.title)
        self.root.addWidget(self.body, 1)

        self._show_message("Seleccione un modo del CRUD primero")
        self.apply_theme()

    def _clear_body(self) -> None:
        while self.body_layout.count():
            item = self.body_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
            elif item.layout() is not None:
                self._clear_layout(item.layout())
        self.current_widget = None
        self.form = None

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
            elif item.layout() is not None:
                self._clear_layout(item.layout())

        while self.body_layout.count():
            item = self.body_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.current_widget = None
        self.form = None

    def _show_message(self, text: str) -> None:
        self._clear_body()

        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(12, 18, 12, 18)
        wrapper_layout.setSpacing(0)

        label = QLabel(text)
        label.setObjectName("panelMessage")
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        wrapper_layout.addStretch(1)
        wrapper_layout.addWidget(label, 20, alignment=Qt.AlignCenter)
        wrapper_layout.addStretch(1)

        self.body_layout.addWidget(wrapper, 1)
        self.current_widget = label

    def _show_form(self, rows: list[tuple[str, str]]) -> None:
        self._clear_body()

        form = PanelForm()
        form.set_rows(rows)
        form.submitted.connect(self._submit_form)
        form.cancelled.connect(self._cancel_form)

        self.body_layout.addWidget(form, 1)
        self.form = form
        self.current_widget = form

    def _show_parametros_read(self, valores: dict) -> None:
        self._clear_body()

        container = QWidget()
        layout = QGridLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(16)

        labels = [
            ("Porcentaje mínimo de aceptación wifi", str(valores.get("porcentaje_minimo_aceptacion_wifi", ""))),
            ("Valor mínimo de TX",  str(valores.get("valor_minimo_tx", ""))),
            ("Valor máximo de TX",  str(valores.get("valor_maximo_tx", ""))),
            ("Valor mínimo de RX",  str(valores.get("valor_minimo_rx", ""))),
            ("Valor máximo de RX",  str(valores.get("valor_maximo_rx", ""))),
            ("Última fecha de modificación", str(valores.get("ultima_modificacion", "N/A"))),
        ]

        for i, (label_text, value_text) in enumerate(labels):
            lbl = QLabel(label_text)
            lbl.setObjectName("fieldLabel")

            val = QLabel(value_text)
            val.setObjectName("valueLabel")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            layout.addWidget(lbl, i, 0)
            layout.addWidget(val, i, 1)

        layout.setColumnStretch(0, 3)
        layout.setColumnStretch(1, 1)

        self.body_layout.addWidget(container, 1)
        self.current_widget = container

    def _wrap_table_widget(self, table: QTableWidget) -> QWidget:
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(8, 8, 8, 8)
        wrapper_layout.setSpacing(0)
        wrapper_layout.addWidget(table, 1)
        return wrapper

    def _show_table(self, columns: list[str], rows: list[list[str]], filterable: list[bool]) -> None:
        self._clear_body()

        table = FilterableTableWidget(columns, filterable)
        table.set_rows(rows)

        wrapper = self._wrap_table_widget(table)
        self.body_layout.addWidget(wrapper, 1)
        self.current_widget = table

    def _show_simple_table(self, columns: list[str], rows: list[list[str]]) -> None:
        self._clear_body()

        table = QTableWidget(0, len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.setWordWrap(False)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setStretchLastSection(True)

        table.setRowCount(len(rows))
        for row_index, row_values in enumerate(rows):
            for col_index, value in enumerate(row_values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row_index, col_index, item)

        table.resizeRowsToContents()

        wrapper = self._wrap_table_widget(table)
        self.body_layout.addWidget(wrapper, 1)
        self.current_widget = table
    # ── UPDATE helpers ─────────────────────────────────────────────────────

    def _make_update_buttons(self, on_accept, on_cancel, on_reset) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(14)
        row.setAlignment(Qt.AlignCenter)

        btn_ok     = MiniActionButton("✓", "#7BBE3C", "#6FAE34", "#629C2E", "#4D7F1F")
        btn_reset  = MiniActionButton("↺", "#4A90D9", "#3A7FC9", "#2A6FB9", "#1A5FA9")
        btn_cancel = MiniActionButton("✕", "#E95A52", "#D94B44", "#C93C36", "#A73732")

        btn_ok.clicked.connect(on_accept)
        btn_reset.clicked.connect(on_reset)
        btn_cancel.clicked.connect(on_cancel)

        row.addWidget(btn_ok)
        row.addWidget(btn_reset)
        row.addWidget(btn_cancel)
        return row

    # ── UPDATE Parámetros ───────────────────────────────────────────────────

    def _show_parametros_update(self, valores: dict) -> None:
        self._clear_body()
        self._update_original_parametros = dict(valores)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        fields_meta = [
            ("porcentaje_minimo_aceptacion_wifi", "Porcentaje mínimo de aceptación wifi"),
            ("valor_minimo_tx",  "Valor mínimo de TX"),
            ("valor_maximo_tx",  "Valor máximo de TX"),
            ("valor_minimo_rx",  "Valor mínimo de RX"),
            ("valor_maximo_rx",  "Valor máximo de RX"),
        ]
        self._update_parametros_inputs: dict[str, QLineEdit] = {}

        for key, label_text in fields_meta:
            row_w = QWidget()
            row_w.setStyleSheet("background: transparent;")
            row_layout = QGridLayout(row_w)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setHorizontalSpacing(12)

            lbl = QLabel(label_text)
            lbl.setObjectName("fieldLabel")

            inp = QLineEdit()
            inp.setObjectName("panelInput")
            inp.setPlaceholderText(str(valores.get(key, "")))
            inp.setAlignment(Qt.AlignRight)

            row_layout.addWidget(lbl, 0, 0)
            row_layout.addWidget(inp, 0, 1)
            row_layout.setColumnStretch(0, 3)
            row_layout.setColumnStretch(1, 1)

            layout.addWidget(row_w)
            self._update_parametros_inputs[key] = inp

        layout.addStretch(1)
        scroll.setWidget(container)
        self.body_layout.addWidget(scroll, 1)

        btn_row = self._make_update_buttons(
            self._submit_parametros_update,
            self._cancel_parametros_update,
            self._reset_parametros_update,
        )
        self.body_layout.addLayout(btn_row)

    def _submit_parametros_update(self) -> None:
        orig = self._update_original_parametros
        changes = []
        for key, inp in self._update_parametros_inputs.items():
            text = inp.text().strip()
            if text:
                changes.append((key, f"{orig.get(key, '?')}  →  {text}"))

        if not changes:
            SweetAlertDialog(
                title="Sin cambios",
                message="No has escrito ningún valor nuevo.",
                confirm_text="Entendido",
                cancel_text="Cerrar",
                parent=self,
            ).exec()
            return

        dlg = SweetAlertDialog(
            title="Confirmar actualización",
            message="Se actualizarán los siguientes parámetros:",
            details=changes,
            confirm_text="Sí, actualizar",
            cancel_text="Cancelar",
            parent=self,
        )
        if dlg.exec() != QDialog.Accepted:
            return

        SweetAlertDialog(
            title="Actualizado correctamente",
            message="Los parámetros han sido actualizados.",
            details=changes,
            confirm_text="Aceptar",
            cancel_text="Cerrar",
            parent=self,
        ).exec()
        for inp in self._update_parametros_inputs.values():
            inp.clear()

    def _cancel_parametros_update(self) -> None:
        dlg = SweetAlertDialog(
            title="Cancelar edición",
            message="¿Deseas cancelar? Los cambios no guardados se perderán.",
            confirm_text="Sí, cancelar",
            cancel_text="Seguir editando",
            parent=self,
        )
        if dlg.exec() == QDialog.Accepted:
            for inp in self._update_parametros_inputs.values():
                inp.clear()

    def _reset_parametros_update(self) -> None:
        dlg = SweetAlertDialog(
            title="Restablecer valores",
            message="¿Deseas restablecer los campos a sus valores originales?",
            confirm_text="Sí, restablecer",
            cancel_text="Cancelar",
            parent=self,
        )
        if dlg.exec() == QDialog.Accepted:
            for inp in self._update_parametros_inputs.values():
                inp.clear()

    # ── UPDATE Modelos ──────────────────────────────────────────────────────

    def _show_modelos_update(self, modelos: list) -> None:
        self._clear_body()
        self._update_modelos_all: list[dict] = modelos

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        search_row = QHBoxLayout()
        search_row.setSpacing(10)
        lbl_search = QLabel("Filtrar nombre:")
        lbl_search.setObjectName("fieldLabel")
        self._modelos_search = QLineEdit()
        self._modelos_search.setObjectName("panelInput")
        self._modelos_search.setPlaceholderText("Escribe un nombre o fragmento...")
        self._modelos_search.textChanged.connect(self._filter_modelos_update)
        search_row.addWidget(lbl_search)
        search_row.addWidget(self._modelos_search, 1)

        search_widget = QWidget()
        search_widget.setStyleSheet("background: transparent;")
        search_widget.setLayout(search_row)
        outer.addWidget(search_widget)

        self._modelos_scroll_area = QScrollArea()
        self._modelos_scroll_area.setWidgetResizable(True)
        self._modelos_scroll_area.setFrameShape(QFrame.NoFrame)
        self._modelos_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._modelos_container = QWidget()
        self._modelos_container.setStyleSheet("background: transparent;")
        self._modelos_rows_layout = QVBoxLayout(self._modelos_container)
        self._modelos_rows_layout.setSpacing(6)
        self._modelos_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._modelos_scroll_area.setWidget(self._modelos_container)
        outer.addWidget(self._modelos_scroll_area, 1)

        wrap = QWidget()
        wrap.setStyleSheet("background: transparent;")
        wrap.setLayout(outer)
        self.body_layout.addWidget(wrap, 1)

        btn_row = self._make_update_buttons(
            self._submit_modelos_update,
            self._cancel_modelos_update,
            self._reset_modelos_update,
        )
        self.body_layout.addLayout(btn_row)
        self._build_modelos_update_rows(modelos)

    def _build_modelos_update_rows(self, modelos: list) -> None:
        while self._modelos_rows_layout.count():
            item = self._modelos_rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._modelos_inputs: list[dict[str, QLineEdit]] = []

        headers_widget = QWidget()
        headers_widget.setStyleSheet("background: transparent;")
        h_layout = QGridLayout(headers_widget)
        h_layout.setContentsMargins(4, 0, 4, 0)
        for col, text in enumerate(["Nombre", "Versión de software", "Fabricante"]):
            lbl = QLabel(text)
            lbl.setObjectName("fieldLabel")
            lbl.setAlignment(Qt.AlignCenter)
            h_layout.addWidget(lbl, 0, col)
        self._modelos_rows_layout.addWidget(headers_widget)

        for item in modelos:
            row_w = QWidget()
            row_w.setStyleSheet("background: transparent;")
            row_l = QGridLayout(row_w)
            row_l.setContentsMargins(2, 2, 2, 2)
            row_l.setSpacing(6)

            inp_nombre  = QLineEdit()
            inp_nombre.setObjectName("panelInput")
            inp_nombre.setPlaceholderText(str(item.get("nombre", "")))

            inp_version = QLineEdit()
            inp_version.setObjectName("panelInput")
            inp_version.setPlaceholderText(str(item.get("version_software", "")))

            inp_fab = QLineEdit()
            inp_fab.setObjectName("panelInput")
            inp_fab.setPlaceholderText(str(item.get("fabricante", "")))

            row_l.addWidget(inp_nombre,  0, 0)
            row_l.addWidget(inp_version, 0, 1)
            row_l.addWidget(inp_fab,     0, 2)
            self._modelos_rows_layout.addWidget(row_w)
            self._modelos_inputs.append({
                "original": item,
                "nombre": inp_nombre,
                "version_software": inp_version,
                "fabricante": inp_fab,
            })

        self._modelos_rows_layout.addStretch(1)

    def _filter_modelos_update(self, text: str) -> None:
        filtered = [m for m in self._update_modelos_all
                    if text.lower() in m.get("nombre", "").lower()] if text else self._update_modelos_all
        self._build_modelos_update_rows(filtered)

    def _submit_modelos_update(self) -> None:
        changes = []
        for entry in self._modelos_inputs:
            orig = entry["original"]
            for field in ["nombre", "version_software", "fabricante"]:
                new_val = entry[field].text().strip()
                if new_val and new_val != str(orig.get(field, "")):
                    changes.append((f"{orig.get('nombre','')} → {field}", new_val))

        if not changes:
            SweetAlertDialog("Sin cambios", "No has modificado ningún valor.",
                confirm_text="Entendido", cancel_text="Cerrar", parent=self).exec()
            return

        dlg = SweetAlertDialog("Confirmar actualización",
            "Se actualizarán los siguientes modelos:",
            details=changes, confirm_text="Sí, actualizar",
            cancel_text="Cancelar", parent=self)
        if dlg.exec() != QDialog.Accepted:
            return

        SweetAlertDialog("Actualizado", "Los modelos fueron actualizados correctamente.",
            details=changes, confirm_text="Aceptar", cancel_text="Cerrar", parent=self).exec()
        for entry in self._modelos_inputs:
            for field in ["nombre", "version_software", "fabricante"]:
                entry[field].clear()

    def _cancel_modelos_update(self) -> None:
        dlg = SweetAlertDialog("Cancelar edición",
            "¿Deseas cancelar? Los cambios no guardados se perderán.",
            confirm_text="Sí, cancelar", cancel_text="Seguir editando", parent=self)
        if dlg.exec() == QDialog.Accepted:
            for entry in self._modelos_inputs:
                for field in ["nombre", "version_software", "fabricante"]:
                    entry[field].clear()

    def _reset_modelos_update(self) -> None:
        dlg = SweetAlertDialog("Restablecer valores",
            "¿Restablecer todos los campos a su valor original?",
            confirm_text="Sí, restablecer", cancel_text="Cancelar", parent=self)
        if dlg.exec() == QDialog.Accepted:
            for entry in self._modelos_inputs:
                for field in ["nombre", "version_software", "fabricante"]:
                    entry[field].clear()
    # ── UPDATE Fabricante ───────────────────────────────────────────────────

    def _show_fabricante_update(self, fabricantes: list) -> None:
        self._clear_body()
        self._update_fabricantes_all: list[dict] = fabricantes

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        search_row = QHBoxLayout()
        search_row.setSpacing(10)
        lbl_s = QLabel("Filtrar fabricante:")
        lbl_s.setObjectName("fieldLabel")
        self._fab_search = QLineEdit()
        self._fab_search.setObjectName("panelInput")
        self._fab_search.setPlaceholderText("Escribe un fabricante o fragmento...")
        self._fab_search.textChanged.connect(self._filter_fabricante_update)
        search_row.addWidget(lbl_s)
        search_row.addWidget(self._fab_search, 1)

        sw = QWidget()
        sw.setStyleSheet("background: transparent;")
        sw.setLayout(search_row)
        outer.addWidget(sw)

        self._fab_scroll = QScrollArea()
        self._fab_scroll.setWidgetResizable(True)
        self._fab_scroll.setFrameShape(QFrame.NoFrame)
        self._fab_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._fab_container = QWidget()
        self._fab_container.setStyleSheet("background: transparent;")
        self._fab_rows_layout = QVBoxLayout(self._fab_container)
        self._fab_rows_layout.setSpacing(6)
        self._fab_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._fab_scroll.setWidget(self._fab_container)
        outer.addWidget(self._fab_scroll, 1)

        wrap = QWidget()
        wrap.setStyleSheet("background: transparent;")
        wrap.setLayout(outer)
        self.body_layout.addWidget(wrap, 1)

        btn_row = self._make_update_buttons(
            self._submit_fabricante_update,
            self._cancel_fabricante_update,
            self._reset_fabricante_update,
        )
        self.body_layout.addLayout(btn_row)
        self._build_fabricante_update_rows(fabricantes)

    def _build_fabricante_update_rows(self, fabricantes: list) -> None:
        while self._fab_rows_layout.count():
            item = self._fab_rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._fab_inputs: list[dict] = []

        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(4, 0, 4, 0)
        grid.setSpacing(6)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        grid.setColumnMinimumWidth(0, 60)

        lbl_h0 = QLabel("Nº fila")
        lbl_h0.setObjectName("fieldLabel")
        lbl_h0.setAlignment(Qt.AlignCenter)
        lbl_h1 = QLabel("Fabricante")
        lbl_h1.setObjectName("fieldLabel")
        lbl_h1.setAlignment(Qt.AlignCenter)
        grid.addWidget(lbl_h0, 0, 0)
        grid.addWidget(lbl_h1, 0, 1)

        for row_idx, item in enumerate(fabricantes, start=1):
            lbl_num = QLabel(str(item.get("numero_fila", "")))
            lbl_num.setObjectName("valueLabel")
            lbl_num.setAlignment(Qt.AlignCenter)

            inp_fab = QLineEdit()
            inp_fab.setObjectName("panelInput")
            inp_fab.setPlaceholderText(str(item.get("fabricante", "")))

            grid.addWidget(lbl_num, row_idx, 0)
            grid.addWidget(inp_fab, row_idx, 1)
            self._fab_inputs.append({"original": item, "fabricante": inp_fab})

        self._fab_rows_layout.addWidget(grid_widget)
        self._fab_rows_layout.addStretch(1)

    def _filter_fabricante_update(self, text: str) -> None:
        filtered = [f for f in self._update_fabricantes_all
                    if text.lower() in f.get("fabricante", "").lower()] if text else self._update_fabricantes_all
        self._build_fabricante_update_rows(filtered)

    def _submit_fabricante_update(self) -> None:
        changes = []
        for entry in self._fab_inputs:
            new_val  = entry["fabricante"].text().strip()
            orig_val = str(entry["original"].get("fabricante", ""))
            if new_val and new_val != orig_val:
                changes.append((f"Fila {entry['original'].get('numero_fila','')}", f"{orig_val} → {new_val}"))

        if not changes:
            SweetAlertDialog("Sin cambios", "No has modificado ningún fabricante.",
                confirm_text="Entendido", cancel_text="Cerrar", parent=self).exec()
            return

        dlg = SweetAlertDialog("Confirmar actualización",
            "Se actualizarán los siguientes fabricantes:",
            details=changes, confirm_text="Sí, actualizar",
            cancel_text="Cancelar", parent=self)
        if dlg.exec() != QDialog.Accepted:
            return

        SweetAlertDialog("Actualizado", "Los fabricantes fueron actualizados.",
            details=changes, confirm_text="Aceptar", cancel_text="Cerrar", parent=self).exec()
        for entry in self._fab_inputs:
            entry["fabricante"].clear()

    def _cancel_fabricante_update(self) -> None:
        dlg = SweetAlertDialog("Cancelar edición",
            "¿Deseas cancelar los cambios?",
            confirm_text="Sí, cancelar", cancel_text="Seguir editando", parent=self)
        if dlg.exec() == QDialog.Accepted:
            for entry in self._fab_inputs:
                entry["fabricante"].clear()

    def _reset_fabricante_update(self) -> None:
        dlg = SweetAlertDialog("Restablecer valores",
            "¿Restablecer todos los fabricantes a su valor original?",
            confirm_text="Sí, restablecer", cancel_text="Cancelar", parent=self)
        if dlg.exec() == QDialog.Accepted:
            for entry in self._fab_inputs:
                entry["fabricante"].clear()

    # ── UPDATE Puertos ──────────────────────────────────────────────────────

    def _show_puertos_update(self, puertos: list) -> None:
        self._clear_body()
        self._update_puertos_all: list[dict] = puertos

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        search_row = QHBoxLayout()
        search_row.setSpacing(10)
        lbl_s = QLabel("Filtrar IP:")
        lbl_s.setObjectName("fieldLabel")
        self._puertos_search = QLineEdit()
        self._puertos_search.setObjectName("panelInput")
        self._puertos_search.setPlaceholderText("Escribe una IP o fragmento...")
        self._puertos_search.textChanged.connect(self._filter_puertos_update)
        search_row.addWidget(lbl_s)
        search_row.addWidget(self._puertos_search, 1)

        sw = QWidget()
        sw.setStyleSheet("background: transparent;")
        sw.setLayout(search_row)
        outer.addWidget(sw)

        self._puertos_scroll = QScrollArea()
        self._puertos_scroll.setWidgetResizable(True)
        self._puertos_scroll.setFrameShape(QFrame.NoFrame)
        self._puertos_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._puertos_container = QWidget()
        self._puertos_container.setStyleSheet("background: transparent;")
        self._puertos_rows_layout = QVBoxLayout(self._puertos_container)
        self._puertos_rows_layout.setSpacing(6)
        self._puertos_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._puertos_scroll.setWidget(self._puertos_container)
        outer.addWidget(self._puertos_scroll, 1)

        wrap = QWidget()
        wrap.setStyleSheet("background: transparent;")
        wrap.setLayout(outer)
        self.body_layout.addWidget(wrap, 1)

        btn_row = self._make_update_buttons(
            self._submit_puertos_update,
            self._cancel_puertos_update,
            self._reset_puertos_update,
        )
        self.body_layout.addLayout(btn_row)
        self._build_puertos_update_rows(puertos)

    def _build_puertos_update_rows(self, puertos: list) -> None:
        while self._puertos_rows_layout.count():
            item = self._puertos_rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._puertos_inputs: list[dict] = []

        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(4, 0, 4, 0)
        grid.setSpacing(6)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        grid.setColumnMinimumWidth(0, 80)

        lbl_h0 = QLabel("Nº Puerto")
        lbl_h0.setObjectName("fieldLabel")
        lbl_h0.setAlignment(Qt.AlignCenter)
        lbl_h1 = QLabel("IP asignada")
        lbl_h1.setObjectName("fieldLabel")
        lbl_h1.setAlignment(Qt.AlignCenter)
        grid.addWidget(lbl_h0, 0, 0)
        grid.addWidget(lbl_h1, 0, 1)

        for row_idx, item in enumerate(puertos, start=1):
            lbl_num = QLabel(str(item.get("numero_puerto", "")))
            lbl_num.setObjectName("valueLabel")
            lbl_num.setAlignment(Qt.AlignCenter)

            inp_ip = QLineEdit()
            inp_ip.setObjectName("panelInput")
            inp_ip.setPlaceholderText(str(item.get("ip_asignada", "")))

            grid.addWidget(lbl_num, row_idx, 0)
            grid.addWidget(inp_ip,  row_idx, 1)
            self._puertos_inputs.append({"original": item, "ip_asignada": inp_ip})

        self._puertos_rows_layout.addWidget(grid_widget)
        self._puertos_rows_layout.addStretch(1)


    def _filter_puertos_update(self, text: str) -> None:
        filtered = [p for p in self._update_puertos_all
                    if text.lower() in p.get("ip_asignada", "").lower()] if text else self._update_puertos_all
        self._build_puertos_update_rows(filtered)

    def _submit_puertos_update(self) -> None:
        changes = []
        for entry in self._puertos_inputs:
            new_val  = entry["ip_asignada"].text().strip()
            orig_val = str(entry["original"].get("ip_asignada", ""))
            if new_val and new_val != orig_val:
                changes.append((f"Puerto {entry['original'].get('numero_puerto','')}", f"{orig_val} → {new_val}"))

        if not changes:
            SweetAlertDialog("Sin cambios", "No has modificado ningún puerto.",
                confirm_text="Entendido", cancel_text="Cerrar", parent=self).exec()
            return

        dlg = SweetAlertDialog("Confirmar actualización",
            "Se actualizarán los siguientes puertos:",
            details=changes, confirm_text="Sí, actualizar",
            cancel_text="Cancelar", parent=self)
        if dlg.exec() != QDialog.Accepted:
            return

        SweetAlertDialog("Actualizado", "Los puertos fueron actualizados correctamente.",
            details=changes, confirm_text="Aceptar", cancel_text="Cerrar", parent=self).exec()
        for entry in self._puertos_inputs:
            entry["ip_asignada"].clear()

    def _cancel_puertos_update(self) -> None:
        dlg = SweetAlertDialog("Cancelar edición",
            "¿Deseas cancelar los cambios?",
            confirm_text="Sí, cancelar", cancel_text="Seguir editando", parent=self)
        if dlg.exec() == QDialog.Accepted:
            for entry in self._puertos_inputs:
                entry["ip_asignada"].clear()

    def _reset_puertos_update(self) -> None:
        dlg = SweetAlertDialog("Restablecer valores",
            "¿Restablecer todas las IPs a su valor original?",
            confirm_text="Sí, restablecer", cancel_text="Cancelar", parent=self)
        if dlg.exec() == QDialog.Accepted:
            for entry in self._puertos_inputs:
                entry["ip_asignada"].clear()
    def set_mode(self, mode: str | None, data: dict) -> None:
        self.current_mode = mode

        if mode is None:
            self._show_message("Seleccione un modo del CRUD primero")
            return

        if mode == "C":
            if self.panel_title_text == "Parámetros":
                self._show_message("Parámetros no está habilitado para Create")
            elif self.panel_title_text == "Modelos":
                self._show_form([
                    ("Nombre", "Ej. HG8145V5"),
                    ("Versión de software", "Ej. V5R021C00S123"),
                    ("Fabricante", "Ej. Huawei"),
                ])
            elif self.panel_title_text == "Fabricante":
                self._show_form([
                    ("Nuevo fabricante", "Ej. Huawei"),
                ])
            elif self.panel_title_text == "Puertos":
                self._show_form([
                    ("Número de puerto", "Ej. 4"),
                    ("IP asignada", "Ej. 192.168.100.10"),
                ])
            elif self.panel_title_text == "Resultados de la base de datos":
                self._show_message("Resultados de la base de datos no está habilitado para Create")
            return

        if mode == "R":
            if self.panel_title_text == "Parámetros":
                self._show_parametros_read(data.get("parametros", {}))
            elif self.panel_title_text == "Modelos":
                rows = [
                    [
                        str(item.get("nombre", "")),
                        str(item.get("version_software", "")),
                        str(item.get("fabricante", "")),
                    ]
                    for item in data.get("modelos", [])
                ]
                self._show_table(
                    ["Nombre", "Versión de software", "Fabricante"],
                    rows,
                    [True, True, True],
                )
            elif self.panel_title_text == "Fabricante":
                rows = [
                    [
                        str(item.get("numero_fila", "")),
                        str(item.get("fabricante", "")),
                    ]
                    for item in data.get("fabricantes", [])
                ]
                self._show_simple_table(
                    ["Número de fila", "Fabricante"],
                    rows,
                )
            elif self.panel_title_text == "Puertos":
                rows = [
                    [
                        str(item.get("numero_puerto", "")),
                        str(item.get("ip_asignada", "")),
                    ]
                    for item in data.get("puertos", [])
                ]
                self._show_table(
                    ["Número de puerto", "IP asignada"],
                    rows,
                    [True, True],
                )
            elif self.panel_title_text == "Resultados de la base de datos":
                rows = [
                    [
                        str(item.get("id", "")),
                        str(item.get("id_modelos", "")),
                        str(item.get("id_settings", "")),
                        str(item.get("id_puertos", "")),
                        str(item.get("id_pruebas", "")),
                        str(item.get("timestamp", "")),
                        str(item.get("sn", "")),
                        str(item.get("mac", "")),
                    ]
                    for item in data.get("resultados_base_datos", [])
                ]
                self._show_table(
                    ["ID", "ID Modelos", "ID Settings", "ID Puertos",
                     "ID Pruebas", "TimeStamp", "SN", "MAC"],
                    rows,
                    [True, True, False, False, False, False, True, False],
                )
            return

        if mode == "U":
            if self.panel_title_text == "Parámetros":
                self._show_parametros_update(data.get("parametros", {}))
            elif self.panel_title_text == "Modelos":
                self._show_modelos_update(data.get("modelos", []))
            elif self.panel_title_text == "Fabricante":
                self._show_fabricante_update(data.get("fabricantes", []))
            elif self.panel_title_text == "Puertos":
                self._show_puertos_update(data.get("puertos", []))
            elif self.panel_title_text == "Resultados de la base de datos":
                self._show_message("Resultados de la base de datos no está habilitado para Update")
            return

        self._show_message(f"Modo {mode} disponible próximamente")

    def _submit_form(self) -> None:
        if self.form is None:
            return
        values = {label: value for label, value in self.form.get_values()}
        self.create_requested.emit(self.panel_title_text, values)

    def _cancel_form(self) -> None:
        if self.form is not None:
            self.form.clear_fields()

    def clear_inputs(self) -> None:
        if self.form is not None:
            self.form.clear_fields()

    def apply_theme(self) -> None:
        theme = ThemeManager.get_theme()

        self.setStyleSheet(f"""
            QFrame#crudPanel {{
                background-color: {theme.section_bg};
                border: 1px solid {theme.border};
                border-radius: 12px;
            }}
            QFrame#panelBody {{
                background-color: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 10px;
            }}
            QLabel#panelTitle {{
                color: {theme.title};
                background: transparent;
                font-weight: 800;
            }}
            QLabel#panelMessage {{
                color: {theme.text};
                background: transparent;
                font-weight: 700;
            }}
            QLabel#fieldLabel {{
                color: {theme.text};
                background: transparent;
                font-weight: 700;
            }}
            QLabel#valueLabel {{
                color: {theme.text};
                background: transparent;
                font-weight: 700;
            }}
            QLineEdit#panelInput {{
                background-color: {theme.input_bg};
                color: {theme.input_text};
                border: 1px solid {theme.input_border};
                border-radius: 10px;
                padding: 8px 10px;
                font-size: 14px;
            }}
            QLineEdit#panelInput:focus {{
                border: 2px solid {theme.primary};
            }}
            QTableWidget {{
                background-color: rgba(255, 255, 255, 0.04);
                color: {theme.text};
                border: none;
                border-radius: 8px;
                gridline-color: transparent;
                selection-background-color: transparent;
                alternate-background-color: rgba(255, 255, 255, 0.05);
                padding: 4px;
            }}
            QTableWidget::item {{
                background: transparent;
                padding: 6px 8px;
            }}
            QHeaderView::section {{
                background-color: {theme.section_alt_bg};
                color: {theme.title};
                border: none;
                border-right: 1px solid {theme.border};
                border-bottom: 1px solid {theme.border};
                padding: 10px 12px;
                font-weight: 800;
            }}
        """)

        if isinstance(self.current_widget, FilterableTableWidget):
            self.current_widget.apply_theme()

    def set_scale(
        self,
        title_size: int,
        message_size: int,
        field_size: int,
        input_size: int,
        input_height: int,
    ) -> None:
        title_font = self.title.font()
        title_font.setPointSize(title_size)
        title_font.setWeight(QFont.Bold)
        self.title.setFont(title_font)

        if isinstance(self.current_widget, QLabel):
            message_font = self.current_widget.font()
            message_font.setPointSize(message_size)
            message_font.setWeight(QFont.DemiBold)
            self.current_widget.setFont(message_font)

        if self.form is not None:
            for row in self.form.rows:
                lbl_font = row.label.font()
                lbl_font.setPointSize(field_size)
                lbl_font.setWeight(QFont.DemiBold)
                row.label.setFont(lbl_font)

                inp_font = row.input.font()
                inp_font.setPointSize(input_size)
                row.input.setFont(inp_font)
                row.input.setFixedHeight(input_height)

        # ── DELETE Modelos ──────────────────────────────────────────────────────

    def _show_modelos_delete(self, modelos: list) -> None:
        self._clear_body()
        self._delete_modelos_all: list[dict] = modelos
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        search_row = QHBoxLayout()
        search_row.setSpacing(10)
        lbl_s = QLabel("Filtrar nombre:")
        lbl_s.setObjectName("fieldLabel")
        self._modelos_delete_search = QLineEdit()
        self._modelos_delete_search.setObjectName("panelInput")
        self._modelos_delete_search.setPlaceholderText("Escribe un nombre o fragmento...")
        self._modelos_delete_search.textChanged.connect(self._filter_modelos_delete)
        search_row.addWidget(lbl_s)
        search_row.addWidget(self._modelos_delete_search, 1)
        sw = QWidget()
        sw.setStyleSheet("background: transparent;")
        sw.setLayout(search_row)
        outer.addWidget(sw)

        self._modelos_delete_scroll = QScrollArea()
        self._modelos_delete_scroll.setWidgetResizable(True)
        self._modelos_delete_scroll.setFrameShape(QFrame.NoFrame)
        self._modelos_delete_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._modelos_delete_container = QWidget()
        self._modelos_delete_container.setStyleSheet("background: transparent;")
        self._modelos_delete_rows_layout = QVBoxLayout(self._modelos_delete_container)
        self._modelos_delete_rows_layout.setSpacing(6)
        self._modelos_delete_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._modelos_delete_scroll.setWidget(self._modelos_delete_container)
        outer.addWidget(self._modelos_delete_scroll, 1)

        wrap = QWidget()
        wrap.setStyleSheet("background: transparent;")
        wrap.setLayout(outer)
        self.body_layout.addWidget(wrap, 1)
        self._build_modelos_delete_rows(modelos)

    def _build_modelos_delete_rows(self, modelos: list) -> None:
        while self._modelos_delete_rows_layout.count():
            item = self._modelos_delete_rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Header
        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(4, 0, 4, 0)
        grid.setSpacing(6)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 0)

        for col, text in enumerate(["Nombre", "Versión de software", "Fabricante", ""]):
            lbl = QLabel(text)
            lbl.setObjectName("fieldLabel")
            lbl.setAlignment(Qt.AlignCenter)
            grid.addWidget(lbl, 0, col)

        for row_idx, item in enumerate(modelos, start=1):
            lbl_nombre  = QLabel(str(item.get("nombre", "")))
            lbl_nombre.setObjectName("valueLabel")
            lbl_nombre.setAlignment(Qt.AlignCenter)

            lbl_version = QLabel(str(item.get("version_software", "")))
            lbl_version.setObjectName("valueLabel")
            lbl_version.setAlignment(Qt.AlignCenter)

            lbl_fab = QLabel(str(item.get("fabricante", "")))
            lbl_fab.setObjectName("valueLabel")
            lbl_fab.setAlignment(Qt.AlignCenter)

            btn_del = MiniActionButton("✕", "#E95A52", "#D94B44", "#C93C36", "#A73732")
            btn_del.setFixedSize(36, 30)
            btn_del.clicked.connect(lambda checked=False, i=item: self._confirm_modelo_delete(i))

            grid.addWidget(lbl_nombre,  row_idx, 0)
            grid.addWidget(lbl_version, row_idx, 1)
            grid.addWidget(lbl_fab,     row_idx, 2)
            grid.addWidget(btn_del,     row_idx, 3, alignment=Qt.AlignCenter)

        self._modelos_delete_rows_layout.addWidget(grid_widget)
        self._modelos_delete_rows_layout.addStretch(1)

    def _filter_modelos_delete(self, text: str) -> None:
        filtered = [m for m in self._delete_modelos_all
                    if text.lower() in m.get("nombre", "").lower()] if text else self._delete_modelos_all
        self._build_modelos_delete_rows(filtered)

    def _confirm_modelo_delete(self, item: dict) -> None:
        details = [
            ("Nombre",              str(item.get("nombre", ""))),
            ("Versión de software", str(item.get("version_software", ""))),
            ("Fabricante",          str(item.get("fabricante", ""))),
        ]
        dlg = SweetAlertDialog(
            title="¿Eliminar modelo?",
            message="Se eliminará el siguiente modelo permanentemente:",
            details=details,
            confirm_text="Sí, eliminar",
            cancel_text="Cancelar",
            parent=self,
        )
        if dlg.exec() != QDialog.Accepted:
            return
        dlg2 = SweetAlertDialog(
            title="Confirmar eliminación",
            message="¿Estás completamente seguro? Esta acción no se puede deshacer.",
            details=details,
            confirm_text="Eliminar definitivamente",
            cancel_text="Cancelar",
            parent=self,
        )
        if dlg2.exec() == QDialog.Accepted:
            SweetAlertDialog(
                title="Eliminado",
                message="El modelo fue eliminado correctamente.",
                details=details,
                confirm_text="Aceptar",
                cancel_text="Cerrar",
                parent=self,
            ).exec()
    # ── DELETE Fabricante ───────────────────────────────────────────────────

    def _show_fabricante_delete(self, fabricantes: list) -> None:
        self._clear_body()
        self._delete_fabricantes_all: list[dict] = fabricantes
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        search_row = QHBoxLayout()
        search_row.setSpacing(10)
        lbl_s = QLabel("Filtrar fabricante:")
        lbl_s.setObjectName("fieldLabel")
        self._fab_delete_search = QLineEdit()
        self._fab_delete_search.setObjectName("panelInput")
        self._fab_delete_search.setPlaceholderText("Escribe un fabricante o fragmento...")
        self._fab_delete_search.textChanged.connect(self._filter_fabricante_delete)
        search_row.addWidget(lbl_s)
        search_row.addWidget(self._fab_delete_search, 1)
        sw = QWidget()
        sw.setStyleSheet("background: transparent;")
        sw.setLayout(search_row)
        outer.addWidget(sw)

        self._fab_delete_scroll = QScrollArea()
        self._fab_delete_scroll.setWidgetResizable(True)
        self._fab_delete_scroll.setFrameShape(QFrame.NoFrame)
        self._fab_delete_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._fab_delete_container = QWidget()
        self._fab_delete_container.setStyleSheet("background: transparent;")
        self._fab_delete_rows_layout = QVBoxLayout(self._fab_delete_container)
        self._fab_delete_rows_layout.setSpacing(6)
        self._fab_delete_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._fab_delete_scroll.setWidget(self._fab_delete_container)
        outer.addWidget(self._fab_delete_scroll, 1)

        wrap = QWidget()
        wrap.setStyleSheet("background: transparent;")
        wrap.setLayout(outer)
        self.body_layout.addWidget(wrap, 1)
        self._build_fabricante_delete_rows(fabricantes)

    def _build_fabricante_delete_rows(self, fabricantes: list) -> None:
        while self._fab_delete_rows_layout.count():
            item = self._fab_delete_rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(4, 0, 4, 0)
        grid.setSpacing(6)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 0)
        grid.setColumnMinimumWidth(0, 60)

        for col, text in enumerate(["Nº fila", "Fabricante", ""]):
            lbl = QLabel(text)
            lbl.setObjectName("fieldLabel")
            lbl.setAlignment(Qt.AlignCenter)
            grid.addWidget(lbl, 0, col)

        for row_idx, item in enumerate(fabricantes, start=1):
            lbl_num = QLabel(str(item.get("numero_fila", "")))
            lbl_num.setObjectName("valueLabel")
            lbl_num.setAlignment(Qt.AlignCenter)

            lbl_fab = QLabel(str(item.get("fabricante", "")))
            lbl_fab.setObjectName("valueLabel")
            lbl_fab.setAlignment(Qt.AlignCenter)

            btn_del = MiniActionButton("✕", "#E95A52", "#D94B44", "#C93C36", "#A73732")
            btn_del.setFixedSize(36, 30)
            btn_del.clicked.connect(lambda checked=False, i=item: self._confirm_fabricante_delete(i))

            grid.addWidget(lbl_num, row_idx, 0)
            grid.addWidget(lbl_fab, row_idx, 1)
            grid.addWidget(btn_del, row_idx, 2, alignment=Qt.AlignCenter)

        self._fab_delete_rows_layout.addWidget(grid_widget)
        self._fab_delete_rows_layout.addStretch(1)

    def _filter_fabricante_delete(self, text: str) -> None:
        filtered = [f for f in self._delete_fabricantes_all
                    if text.lower() in f.get("fabricante", "").lower()] if text else self._delete_fabricantes_all
        self._build_fabricante_delete_rows(filtered)

    def _confirm_fabricante_delete(self, item: dict) -> None:
        details = [
            ("Nº fila",    str(item.get("numero_fila", ""))),
            ("Fabricante", str(item.get("fabricante", ""))),
        ]
        dlg = SweetAlertDialog(
            title="¿Eliminar fabricante?",
            message="Se eliminará el siguiente fabricante permanentemente:",
            details=details,
            confirm_text="Sí, eliminar",
            cancel_text="Cancelar",
            parent=self,
        )
        if dlg.exec() != QDialog.Accepted:
            return
        dlg2 = SweetAlertDialog(
            title="Confirmar eliminación",
            message="¿Estás completamente seguro? Esta acción no se puede deshacer.",
            details=details,
            confirm_text="Eliminar definitivamente",
            cancel_text="Cancelar",
            parent=self,
        )
        if dlg2.exec() == QDialog.Accepted:
            SweetAlertDialog(
                title="Eliminado",
                message="El fabricante fue eliminado correctamente.",
                details=details,
                confirm_text="Aceptar",
                cancel_text="Cerrar",
                parent=self,
            ).exec()

    # ── DELETE Puertos ──────────────────────────────────────────────────────

    def _show_puertos_delete(self, puertos: list) -> None:
        self._clear_body()
        self._delete_puertos_all: list[dict] = puertos
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        search_row = QHBoxLayout()
        search_row.setSpacing(10)
        lbl_s = QLabel("Filtrar IP:")
        lbl_s.setObjectName("fieldLabel")
        self._puertos_delete_search = QLineEdit()
        self._puertos_delete_search.setObjectName("panelInput")
        self._puertos_delete_search.setPlaceholderText("Escribe una IP o fragmento...")
        self._puertos_delete_search.textChanged.connect(self._filter_puertos_delete)
        search_row.addWidget(lbl_s)
        search_row.addWidget(self._puertos_delete_search, 1)
        sw = QWidget()
        sw.setStyleSheet("background: transparent;")
        sw.setLayout(search_row)
        outer.addWidget(sw)

        self._puertos_delete_scroll = QScrollArea()
        self._puertos_delete_scroll.setWidgetResizable(True)
        self._puertos_delete_scroll.setFrameShape(QFrame.NoFrame)
        self._puertos_delete_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._puertos_delete_container = QWidget()
        self._puertos_delete_container.setStyleSheet("background: transparent;")
        self._puertos_delete_rows_layout = QVBoxLayout(self._puertos_delete_container)
        self._puertos_delete_rows_layout.setSpacing(6)
        self._puertos_delete_rows_layout.setContentsMargins(0, 0, 0, 0)
        self._puertos_delete_scroll.setWidget(self._puertos_delete_container)
        outer.addWidget(self._puertos_delete_scroll, 1)

        wrap = QWidget()
        wrap.setStyleSheet("background: transparent;")
        wrap.setLayout(outer)
        self.body_layout.addWidget(wrap, 1)
        self._build_puertos_delete_rows(puertos)

    def _build_puertos_delete_rows(self, puertos: list) -> None:
        while self._puertos_delete_rows_layout.count():
            item = self._puertos_delete_rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(4, 0, 4, 0)
        grid.setSpacing(6)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 0)
        grid.setColumnMinimumWidth(0, 80)
        

        for col, text in enumerate(["Nº Puerto", "IP asignada", ""]):
            lbl = QLabel(text)
            lbl.setObjectName("fieldLabel")
            lbl.setAlignment(Qt.AlignCenter)
            grid.addWidget(lbl, 0, col)

        for row_idx, item in enumerate(puertos, start=1):
            lbl_num = QLabel(str(item.get("numero_puerto", "")))
            lbl_num.setObjectName("valueLabel")
            lbl_num.setAlignment(Qt.AlignCenter)

            lbl_ip = QLabel(str(item.get("ip_asignada", "")))
            lbl_ip.setObjectName("valueLabel")
            lbl_ip.setAlignment(Qt.AlignCenter)

            btn_del = MiniActionButton("✕", "#E95A52", "#D94B44", "#C93C36", "#A73732")
            btn_del.setFixedSize(36, 30)
            btn_del.clicked.connect(lambda checked=False, i=item: self._confirm_puerto_delete(i))

            grid.addWidget(lbl_num, row_idx, 0)
            grid.addWidget(lbl_ip,  row_idx, 1)
            grid.addWidget(btn_del, row_idx, 2, alignment=Qt.AlignCenter)

        self._puertos_delete_rows_layout.addWidget(grid_widget)
        self._puertos_delete_rows_layout.addStretch(1)

    def _filter_puertos_delete(self, text: str) -> None:
        filtered = [p for p in self._delete_puertos_all
                    if text.lower() in p.get("ip_asignada", "").lower()] if text else self._delete_puertos_all
        self._build_puertos_delete_rows(filtered)

    def _confirm_puerto_delete(self, item: dict) -> None:
        details = [
            ("Nº Puerto",   str(item.get("numero_puerto", ""))),
            ("IP asignada", str(item.get("ip_asignada", ""))),
        ]
        dlg = SweetAlertDialog(
            title="¿Eliminar puerto?",
            message="Se eliminará el siguiente puerto permanentemente:",
            details=details,
            confirm_text="Sí, eliminar",
            cancel_text="Cancelar",
            parent=self,
        )
        if dlg.exec() != QDialog.Accepted:
            return
        dlg2 = SweetAlertDialog(
            title="Confirmar eliminación",
            message="¿Estás completamente seguro? Esta acción no se puede deshacer.",
            details=details,
            confirm_text="Eliminar definitivamente",
            cancel_text="Cancelar",
            parent=self,
        )
        if dlg2.exec() == QDialog.Accepted:
            SweetAlertDialog(
                title="Eliminado",
                message="El puerto fue eliminado correctamente.",
                details=details,
                confirm_text="Aceptar",
                cancel_text="Cerrar",
                parent=self,
            ).exec()
    def set_mode(self, mode: str | None, data: dict) -> None:
        self.current_mode = mode
        if mode is None:
            self._show_message("Seleccione un modo del CRUD primero")
            return

        # ── CREATE ──────────────────────────────────────────────────────────
        if mode == "C":
            if self.panel_title_text == "Parámetros":
                self._show_message("Parámetros no está habilitado para Create")
            elif self.panel_title_text == "Modelos":
                self._show_form([
                    ("Nombre", "Ej. HG8145V5"),
                    ("Versión de software", "Ej. V5R021C00S123"),
                    ("Fabricante", "Ej. Huawei"),
                ])
            elif self.panel_title_text == "Fabricante":
                self._show_form([("Nuevo fabricante", "Ej. Huawei")])
            elif self.panel_title_text == "Puertos":
                self._show_form([
                    ("Número de puerto", "Ej. 4"),
                    ("IP asignada", "Ej. 192.168.100.10"),
                ])
            elif self.panel_title_text == "Resultados de la base de datos":
                self._show_message("Resultados de la base de datos no está habilitado para Create")
            return

        # ── READ ─────────────────────────────────────────────────────────────
        if mode == "R":
            if self.panel_title_text == "Parámetros":
                self._show_parametros_read(data.get("parametros", {}))
            elif self.panel_title_text == "Modelos":
                rows = [
                    [str(item.get("nombre", "")), str(item.get("version_software", "")), str(item.get("fabricante", ""))]
                    for item in data.get("modelos", [])
                ]
                self._show_table(["Nombre", "Versión de software", "Fabricante"], rows, [True, True, True])
            elif self.panel_title_text == "Fabricante":
                rows = [
                    [str(item.get("numero_fila", "")), str(item.get("fabricante", ""))]
                    for item in data.get("fabricantes", [])
                ]
                self._show_simple_table(["Número de fila", "Fabricante"], rows)
            elif self.panel_title_text == "Puertos":
                rows = [
                    [str(item.get("numero_puerto", "")), str(item.get("ip_asignada", ""))]
                    for item in data.get("puertos", [])
                ]
                self._show_table(["Número de puerto", "IP asignada"], rows, [True, True])
            elif self.panel_title_text == "Resultados de la base de datos":
                rows = [
                    [
                        str(item.get("id", "")),          str(item.get("id_modelos", "")),
                        str(item.get("id_settings", "")), str(item.get("id_puertos", "")),
                        str(item.get("id_pruebas", "")),  str(item.get("timestamp", "")),
                        str(item.get("sn", "")),          str(item.get("mac", "")),
                    ]
                    for item in data.get("resultados_base_datos", [])
                ]
                self._show_table(
                    ["ID", "ID Modelos", "ID Settings", "ID Puertos", "ID Pruebas", "TimeStamp", "SN", "MAC"],
                    rows,
                    [True, True, False, False, False, False, True, False],
                )
            return

        # ── UPDATE ───────────────────────────────────────────────────────────
        if mode == "U":
            if self.panel_title_text == "Parámetros":
                self._show_parametros_update(data.get("parametros", {}))
            elif self.panel_title_text == "Modelos":
                self._show_modelos_update(data.get("modelos", []))
            elif self.panel_title_text == "Fabricante":
                self._show_fabricante_update(data.get("fabricantes", []))
            elif self.panel_title_text == "Puertos":
                self._show_puertos_update(data.get("puertos", []))
            elif self.panel_title_text == "Resultados de la base de datos":
                self._show_message("Resultados de la base de datos no está habilitado para Update")
            return

        # ── DELETE ───────────────────────────────────────────────────────────
        if mode == "D":
            if self.panel_title_text == "Parámetros":
                self._show_message("Parámetros no está habilitado para Delete")
            elif self.panel_title_text == "Modelos":
                self._show_modelos_delete(data.get("modelos", []))
            elif self.panel_title_text == "Fabricante":
                self._show_fabricante_delete(data.get("fabricantes", []))
            elif self.panel_title_text == "Puertos":
                self._show_puertos_delete(data.get("puertos", []))
            elif self.panel_title_text == "Resultados de la base de datos":
                self._show_message("Resultados de la base de datos no está habilitado para Delete")
            return

        self._show_message(f"Modo {mode} disponible próximamente")

class ModificarView(QWidget):
    theme_changed = Signal()
    back_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.current_mode: str | None = None
        self.crud_buttons: dict[str, CrudModeButton] = {}
        self.panels: list[CrudPanel] = []
        self.mock_data = self._load_mock_data()

        self._build_ui()
        self._apply_responsive_sizes()

    def _load_mock_data(self) -> dict:
        file_path = Path(__file__).resolve().parents[3] / "data" / "modificar_mock_data.json"

        fallback = {
            "parametros": {
                "porcentaje_minimo_aceptacion_wifi": 80,
                "valor_minimo_tx": -8.0,
                "valor_maximo_tx": 3.0,
                "valor_minimo_rx": -27.0,
                "valor_maximo_rx": -8.0,
            },
            "modelos": [
                {"nombre": "HG6145F1", "version_software": "V1R001C10S101", "fabricante": "FIBERHOME"},
                {"nombre": "HG8145V5", "version_software": "V5R021C00S123", "fabricante": "HUAWEI"},
                {"nombre": "F670L",    "version_software": "V6.0.10P3N12",  "fabricante": "ZTE"},
            ],
            "fabricantes": [
                {"numero_fila": 1, "fabricante": "FIBERHOME"},
                {"numero_fila": 2, "fabricante": "HUAWEI"},
                {"numero_fila": 3, "fabricante": "ZTE"},
            ],
            "puertos": [
                {"numero_puerto": 1, "ip_asignada": "192.168.100.10"},
                {"numero_puerto": 2, "ip_asignada": "192.168.100.11"},
                {"numero_puerto": 3, "ip_asignada": "192.168.100.12"},
                {"numero_puerto": 4, "ip_asignada": "192.168.100.13"},
            ],
            "resultados_base_datos": [
                {
                    "id": 1, "id_modelos": 1, "id_settings": 1,
                    "id_puertos": 1, "id_pruebas": 1,
                    "timestamp": "2026-03-21 09:00:00",
                    "sn": "SN000001", "mac": "AA:BB:CC:DD:EE:01",
                },
                {
                    "id": 2, "id_modelos": 2, "id_settings": 1,
                    "id_puertos": 2, "id_pruebas": 2,
                    "timestamp": "2026-03-21 09:02:00",
                    "sn": "SN000002", "mac": "AA:BB:CC:DD:EE:02",
                },
            ],
        }

        try:
            if file_path.exists():
                with file_path.open("r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass

        return fallback

    def _build_ui(self) -> None:
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(20, 16, 20, 16)
        self.root_layout.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.scroll_content = QWidget()
        self.scroll.setWidget(self.scroll_content)

        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(0)

        self.main_card = QFrame()
        self.main_card.setObjectName("mainCard")

        self.main_layout = QVBoxLayout(self.main_card)
        self.main_layout.setContentsMargins(28, 24, 28, 24)
        self.main_layout.setSpacing(18)

        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(14)

        self.page_title = QLabel("Modificar parámetros")
        self.page_title.setObjectName("pageTitle")

        self.btn_back = BackButton("Volver")
        self.btn_back.clicked.connect(self.back_requested.emit)

        self.header_layout.addWidget(self.page_title, 1, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.btn_back, 0, alignment=Qt.AlignRight | Qt.AlignTop)

        self.main_layout.addLayout(self.header_layout)

        self.theme_panel = QFrame()
        self.theme_panel.setObjectName("topSectionPanel")

        self.theme_layout = QVBoxLayout(self.theme_panel)
        self.theme_layout.setContentsMargins(18, 16, 18, 16)
        self.theme_layout.setSpacing(0)

        self.theme_row = ThemeModeRow()
        self.theme_row.theme_toggled.connect(self._on_theme_toggled)

        self.theme_layout.addWidget(self.theme_row)
        self.main_layout.addWidget(self.theme_panel)

        self.crud_row = QWidget()
        self.crud_row.setStyleSheet("background: transparent;")
        self.crud_layout = QHBoxLayout(self.crud_row)
        self.crud_layout.setContentsMargins(0, 4, 0, 10)
        self.crud_layout.setSpacing(18)
        self.crud_layout.setAlignment(Qt.AlignHCenter)

        for key in ["C", "R", "U", "D"]:
            btn = CrudModeButton(key)
            btn.clicked.connect(lambda _=False, mode=key: self._set_mode(mode))
            self.crud_buttons[key] = btn
            self.crud_layout.addWidget(btn)

        self.main_layout.addWidget(self.crud_row)

        self.panels_grid = QGridLayout()
        self.panels_grid.setContentsMargins(0, 8, 0, 0)
        self.panels_grid.setHorizontalSpacing(18)
        self.panels_grid.setVerticalSpacing(18)
        self.panels_grid.setAlignment(Qt.AlignTop)

        panel_titles = ["Parámetros", "Modelos", "Fabricante", "Puertos"]
        positions    = [(0, 0), (0, 1), (1, 0), (1, 1)]

        for title, (row, col) in zip(panel_titles, positions):
            panel = CrudPanel(title)
            panel.create_requested.connect(self._handle_create_request)
            self.panels.append(panel)
            self.panels_grid.addWidget(panel, row, col)

        self.results_panel = CrudPanel("Resultados de la base de datos")
        self.results_panel.create_requested.connect(self._handle_create_request)
        self.panels.append(self.results_panel)
        self.panels_grid.addWidget(self.results_panel, 2, 0, 1, 2)
        self.results_panel.hide()

        self.panels_grid.setColumnStretch(0, 1)
        self.panels_grid.setColumnStretch(1, 1)

        self.main_layout.addLayout(self.panels_grid)
        self.main_layout.addStretch(1)

        self.scroll_layout.addWidget(self.main_card)
        self.root_layout.addWidget(self.scroll)

        self._set_mode(None)
        self.apply_theme()

    def _on_theme_toggled(self, checked: bool) -> None:
        ThemeManager.set_dark(checked)
        self.apply_theme()
        self.theme_changed.emit()

    def _set_mode(self, mode: str | None) -> None:
        self.current_mode = mode

        for key, btn in self.crud_buttons.items():
            btn.set_selected(key == mode)

        self.results_panel.setVisible(mode == "R")

        for panel in self.panels:
            panel.set_mode(mode, self.mock_data)

        self._apply_responsive_sizes()

    def _handle_create_request(self, panel_name: str, values: dict) -> None:
        non_empty = [(k, v) for k, v in values.items() if v]

        if not non_empty:
            SweetAlertDialog(
                title="Campo vacío",
                message=f"Debes capturar la información para {panel_name}.",
                confirm_text="Entendido",
                cancel_text="Cerrar",
                parent=self,
            ).exec()
            return

        summary = [("Panel", panel_name)] + non_empty

        dialog_confirm = SweetAlertDialog(
            title="Confirmar creación",
            message="Se crearán los siguientes datos:",
            details=summary,
            confirm_text="Sí, crear",
            cancel_text="Cancelar",
            parent=self,
        )

        if dialog_confirm.exec() != QDialog.Accepted:
            return

        SweetAlertDialog(
            title="Creado correctamente",
            message="Gracias. Los registros fueron creados correctamente.",
            details=summary,
            confirm_text="Aceptar",
            cancel_text="Cerrar",
            parent=self,
        ).exec()

        for panel in self.panels:
            panel.clear_inputs()

    def apply_theme(self) -> None:
        theme = ThemeManager.get_theme()

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme.app_bg};
            }}
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: transparent;
            }}
            QFrame#mainCard {{
                background-color: {theme.main_card_bg};
                border: 1px solid {theme.border};
                border-radius: 24px;
            }}
            QFrame#topSectionPanel {{
                background-color: {theme.section_bg};
                border: 1px solid {theme.border};
                border-radius: 14px;
            }}
            QLabel#pageTitle {{
                color: {theme.title};
                font-weight: 800;
                background: transparent;
            }}
        """)

        self.theme_row.apply_theme()

        for btn in self.crud_buttons.values():
            btn.apply_theme()

        for panel in self.panels:
            panel.apply_theme()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._apply_responsive_sizes()

    def _apply_responsive_sizes(self) -> None:
        w = max(self.width(), 980)
        h = max(self.height(), 700)

        title_size  = min(max(int(w / 34),  24), 38)
        back_w      = min(max(int(w / 8),  130), 170)
        back_h      = min(max(int(h / 16),  42),  50)

        theme_title_size = min(max(int(w / 74), 15), 21)

        crud_size = min(max(int(w / 12),  78),  98)
        crud_font = min(max(int(w / 70),  16),  22)

        panel_title_size  = min(max(int(w / 72),  15), 21)
        panel_msg_size    = min(max(int(w / 110), 10), 15)
        field_label_size  = min(max(int(w / 110), 10), 15)
        input_size        = min(max(int(w / 118), 10), 15)
        input_height      = min(max(int(h / 18),  38), 46)

        title_font = self.page_title.font()
        title_font.setPointSize(title_size)
        title_font.setWeight(QFont.Bold)
        self.page_title.setFont(title_font)

        self.btn_back.setFixedSize(back_w, back_h)

        small_mode = w < 1080
        self.theme_row.set_scale(theme_title_size, small_mode=small_mode)

        for btn in self.crud_buttons.values():
            btn.setFixedSize(crud_size, crud_size)
            font = btn.font()
            font.setPointSize(crud_font)
            font.setWeight(QFont.Bold)
            btn.setFont(font)

        panel_min_h         = min(max(int(h / 3.2), 240), 330)
        results_panel_min_h = min(max(int(h / 2.5), 280), 380)

        for panel in self.panels:
            if panel is self.results_panel:
                panel.setMinimumHeight(results_panel_min_h)
            else:
                panel.setMinimumHeight(panel_min_h)

            panel.setMaximumHeight(16777215)
            panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            panel.set_scale(
                panel_title_size,
                panel_msg_size,
                field_label_size,
                input_size,
                input_height,
            )
