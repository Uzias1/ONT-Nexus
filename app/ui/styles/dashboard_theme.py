from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardPalette:
    app_bg: str
    main_card_bg: str
    section_bg: str
    section_alt_bg: str
    border: str
    title: str
    text: str
    muted_text: str
    accent_blue: str
    accent_blue_hover: str
    accent_blue_pressed: str
    accent_yellow: str
    success_green: str
    danger_red: str
    logout_red: str
    reboot_purple: str


LIGHT_DASHBOARD_THEME = DashboardPalette(
    app_bg="#DCE8F2",
    main_card_bg="#E8F0F7",
    section_bg="#D6E4F0",
    section_alt_bg="#CFE0EC",
    border="#8FA8BC",
    title="#243B53",
    text="#243B53",
    muted_text="#486581",
    accent_blue="#4FA3D9",
    accent_blue_hover="#3E94CC",
    accent_blue_pressed="#2F82BB",
    accent_yellow="#F4B942",
    success_green="#BFD4C0",
    danger_red="#E74C3C",
    logout_red="#F08A80",
    reboot_purple="#9B59B6",
)