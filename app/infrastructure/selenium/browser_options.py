from __future__ import annotations

from selenium.webdriver import ChromeOptions

from app.infrastructure.config.settings import SeleniumConfig


def build_chrome_options(config: SeleniumConfig) -> ChromeOptions:
    options = ChromeOptions()

    # Usar el del sistema
    if config.chrome_binary_path:
        options.binary_location = config.chrome_binary_path

    if config.headless:
        options.add_argument("--headless=new")

    options.add_argument(f"--window-size={config.window_width},{config.window_height}")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-insecure-localhost")
    options.add_argument("--log-level=3")

    # Extra opciones
    options.page_load_strategy = "eager"  # <- No esperar recursos innecesarios, solo con el DOM principal

    # Deshabilitar gestor de contraseñas y alertas de seguridad
    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "safebrowsing.enabled": False,
        "profile.default_content_setting_values.notifications": 2
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    return options