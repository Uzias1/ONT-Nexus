from app.ui.styles.theme import LIGHT_THEME, DARK_THEME, ThemeColors


class ThemeManager:
    _is_dark = False

    @classmethod
    def get_theme(cls) -> ThemeColors:
        return DARK_THEME if cls._is_dark else LIGHT_THEME

    @classmethod
    def is_dark(cls) -> bool:
        return cls._is_dark

    @classmethod
    def set_dark(cls, value: bool) -> None:
        cls._is_dark = value

    @classmethod
    def toggle(cls) -> None:
        cls._is_dark = not cls._is_dark