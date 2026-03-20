from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QScrollArea,
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
        self.btn_cancel = QPushButton(cancel_text)

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

            QPushButton {{
                min-width: 130px;
                min-height: 42px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 700;
                padding: 8px 14px;
            }}

            QPushButton:first-of-type {{
                background-color: #7BBE3C;
                color: white;
                border: 1px solid #4D7F1F;
            }}
            QPushButton:first-of-type:hover {{
                background-color: #6FAE34;
            }}

            QPushButton:last-of-type {{
                background-color: #E95A52;
                color: white;
                border: 1px solid #A73732;
            }}
            QPushButton:last-of-type:hover {{
                background-color: #D94B44;
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

        self.btn_ok = MiniActionButton("✓", "#7BBE3C", "#6FAE34", "#629C2E", "#4D7F1F")
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
            if item.spacerItem() is not None:
                continue
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


class CrudPanel(QFrame):
    create_requested = Signal(str, dict)

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.panel_title_text = title
        self.current_mode = None

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

        self.message = QLabel("Seleccione un modo del CRUD primero")
        self.message.setObjectName("panelMessage")
        self.message.setAlignment(Qt.AlignCenter)
        self.message.setWordWrap(True)

        self.form = PanelForm()
        self.form.submitted.connect(self._submit_form)
        self.form.cancelled.connect(self._cancel_form)

        self.body_layout.addWidget(self.message, 1, alignment=Qt.AlignCenter)
        self.body_layout.addWidget(self.form, 1)

        self.root.addWidget(self.title)
        self.root.addWidget(self.body, 1)

        self._show_message("Seleccione un modo del CRUD primero")
        self.apply_theme()

    def _show_message(self, text: str) -> None:
        self.message.setText(text)
        self.message.show()
        self.form.hide()

    def _show_form(self, rows: list[tuple[str, str]]) -> None:
        self.form.set_rows(rows)
        self.message.hide()
        self.form.show()

    def set_mode(self, mode: str | None) -> None:
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
            return

        self._show_message(f"Modo {mode} disponible próximamente")

    def _submit_form(self) -> None:
        values = {label: value for label, value in self.form.get_values()}
        self.create_requested.emit(self.panel_title_text, values)

    def _cancel_form(self) -> None:
        self.form.clear_fields()

    def clear_inputs(self) -> None:
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
        """)

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

        message_font = self.message.font()
        message_font.setPointSize(message_size)
        message_font.setWeight(QFont.DemiBold)
        self.message.setFont(message_font)

        for row in self.form.rows:
            lbl_font = row.label.font()
            lbl_font.setPointSize(field_size)
            lbl_font.setWeight(QFont.DemiBold)
            row.label.setFont(lbl_font)

            inp_font = row.input.font()
            inp_font.setPointSize(input_size)
            row.input.setFont(inp_font)
            row.input.setFixedHeight(input_height)


class ModificarView(QWidget):
    theme_changed = Signal()
    back_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.current_mode: str | None = None
        self.crud_buttons: dict[str, CrudModeButton] = {}
        self.panels: list[CrudPanel] = []

        self._build_ui()
        self._apply_responsive_sizes()

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
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]

        for title, (row, col) in zip(panel_titles, positions):
            panel = CrudPanel(title)
            panel.create_requested.connect(self._handle_create_request)
            self.panels.append(panel)
            self.panels_grid.addWidget(panel, row, col)

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

        for panel in self.panels:
            panel.set_mode(mode)

        self._apply_responsive_sizes()

    def _handle_create_request(self, panel_name: str, values: dict) -> None:
        non_empty = [(k, v) for k, v in values.items() if v]

        if not non_empty:
            dialog = SweetAlertDialog(
                title="Campo vacío",
                message=f"Debes capturar la información para {panel_name}.",
                confirm_text="Entendido",
                cancel_text="Cerrar",
                parent=self,
            )
            dialog.exec()
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

        dialog_ok = SweetAlertDialog(
            title="Creado correctamente",
            message="Gracias. Los registros fueron creados correctamente.",
            details=summary,
            confirm_text="Aceptar",
            cancel_text="Cerrar",
            parent=self,
        )
        dialog_ok.exec()

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

        title_size = min(max(int(w / 34), 24), 38)
        back_w = min(max(int(w / 8), 130), 170)
        back_h = min(max(int(h / 16), 42), 50)

        theme_title_size = min(max(int(w / 74), 15), 21)

        crud_size = min(max(int(w / 12), 78), 98)
        crud_font = min(max(int(w / 70), 16), 22)

        panel_title_size = min(max(int(w / 72), 15), 21)
        panel_msg_size = min(max(int(w / 110), 10), 15)
        field_label_size = min(max(int(w / 110), 10), 15)
        input_size = min(max(int(w / 118), 10), 15)
        input_height = min(max(int(h / 18), 38), 46)

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

        panel_min_h = min(max(int(h / 3.2), 240), 330)

        for panel in self.panels:
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