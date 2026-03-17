from dataclasses import dataclass


@dataclass(frozen=True)
class ThemeColors:
    app_bg: str
    main_card_bg: str
    section_bg: str
    section_alt_bg: str
    border: str
    title: str
    text: str
    muted_text: str
    primary: str
    primary_hover: str
    primary_pressed: str
    switch_on: str
    switch_off: str
    input_bg: str
    input_text: str
    input_border: str


LIGHT_THEME = ThemeColors(
    app_bg="#DCE8F2",
    main_card_bg="#E8F0F7",
    section_bg="#D6E4F0",
    section_alt_bg="#CFE0EC",
    border="#8FA8BC",
    title="#243B53",
    text="#243B53",
    muted_text="#486581",
    primary="#4FA3D9",
    primary_hover="#3E94CC",
    primary_pressed="#2F82BB",
    switch_on="#42B983",
    switch_off="#111111",
    input_bg="#F8FBFE",
    input_text="#243B53",
    input_border="#8FA8BC",
)

DARK_THEME = ThemeColors(
    app_bg="#0F1720",
    main_card_bg="#17212B",
    section_bg="#1E2B37",
    section_alt_bg="#223241",
    border="#35506A",
    title="#EAF2F9",
    text="#DCE7F3",
    muted_text="#9FB3C8",
    primary="#4FA3D9",
    primary_hover="#3E94CC",
    primary_pressed="#2F82BB",
    switch_on="#42B983",
    switch_off="#0A0F14",
    input_bg="#243443",
    input_text="#EAF2F9",
    input_border="#4B6681",
)