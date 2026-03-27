from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QSizePolicy

from app.ui.theme_manager import ThemeManager


class BaseStyledButton(QPushButton):
    def __init__(
        self,
        text: str,
        bg: str,
        hover: str,
        pressed: str,
        text_color: str = "white",
        border: str = "transparent",
        parent=None,
    ) -> None:
        super().__init__(text, parent)

        self._bg = bg
        self._hover = hover
        self._pressed = pressed
        self._text_color = text_color
        self._border = border

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(190, 58)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self._apply_style()

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._bg};
                color: {self._text_color};
                border: 1px solid {self._border};
                border-radius: 14px;
                font-size: 16px;
                font-weight: 600;
                padding: 10px 18px;
            }}
            QPushButton:hover {{
                background-color: {self._hover};
            }}
            QPushButton:pressed {{
                background-color: {self._pressed};
            }}
            QPushButton:disabled {{
                background-color: #C8D3DD;
                color: #F4F7FA;
            }}
        """)


class PrimaryButton(BaseStyledButton):
    def __init__(self, text: str, parent=None) -> None:
        theme = ThemeManager.get_theme()
        super().__init__(
            text=text,
            bg=theme.primary,
            hover=theme.primary_hover,
            pressed=theme.primary_pressed,
            text_color="white",
            border=theme.border,
            parent=parent,
        )


class SecondaryButton(BaseStyledButton):
    def __init__(self, text: str, parent=None) -> None:
        theme = ThemeManager.get_theme()
        super().__init__(
            text=text,
            bg=theme.section_bg,
            hover=theme.section_alt_bg,
            pressed=theme.section_alt_bg,
            text_color=theme.text,
            border=theme.border,
            parent=parent,
        )


class SuccessButton(BaseStyledButton):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(
            text=text,
            bg="#7BBE3C",
            hover="#6FAE34",
            pressed="#629C2E",
            text_color="white",
            border="#4D7F1F",
            parent=parent,
        )


class DangerButton(BaseStyledButton):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(
            text=text,
            bg="#E95A52",
            hover="#D94B44",
            pressed="#C93C36",
            text_color="white",
            border="#A73732",
            parent=parent,
        )


class WarningButton(BaseStyledButton):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(
            text=text,
            bg="#F29A2E",
            hover="#E28717",
            pressed="#D47408",
            text_color="#1F2937",
            border="#B96A09",
            parent=parent,
        )


class BackButton(QPushButton):
    def __init__(self, text: str = "Volver", parent=None) -> None:
        super().__init__(text, parent)

        theme = ThemeManager.get_theme()
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(148, 46)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.section_bg};
                color: {theme.text};
                border: 1px solid {theme.border};
                border-radius: 14px;
                font-size: 14px;
                font-weight: 700;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {theme.section_alt_bg};
            }}
            QPushButton:pressed {{
                background-color: {theme.input_bg};
            }}
        """)


class HelpCircleButton(QPushButton):
    def __init__(self, text: str = "?", parent=None) -> None:
        super().__init__(text, parent)

        theme = ThemeManager.get_theme()
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(46, 46)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.primary};
                color: white;
                border: 1px solid {theme.border};
                border-radius: 23px;
                font-size: 20px;
                font-weight: 800;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {theme.primary_hover};
            }}
            QPushButton:pressed {{
                background-color: {theme.primary_pressed};
            }}
        """)
    def __init__(self, text: str = "?", parent=None) -> None:
        super().__init__(text, parent)

        theme = ThemeManager.get_theme()
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(48, 48)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.primary};
                color: white;
                border: 1px solid {theme.border};
                border-radius: 24px;
                font-size: 22px;
                font-weight: 800;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {theme.primary_hover};
            }}
            QPushButton:pressed {{
                background-color: {theme.primary_pressed};
            }}
        """)