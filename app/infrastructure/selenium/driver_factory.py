from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.chrome.service import Service

from app.infrastructure.config.settings import SeleniumConfig
from app.infrastructure.logging.logger import get_logger, log_console
from app.infrastructure.selenium.browser_options import build_chrome_options
import logging

class DriverFactory:
    def __init__(self, config: SeleniumConfig) -> None:
        self._config = config
        self._logger = get_logger(self.__class__.__name__)

    def create(self) -> WebDriver:
        browser = self._config.browser.strip().lower()

        if browser != "chrome":
            raise ValueError(f"Navegador no soportado aún: {browser}")

        log_console(self._logger, logging.INFO, "Creando WebDriver para navegador: %s", browser)

        options = build_chrome_options(self._config)
        service = Service(executable_path=self._config.chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)

        driver.implicitly_wait(self._config.implicit_wait_s)
        driver.set_page_load_timeout(self._config.page_load_timeout_s)
        driver.set_script_timeout(self._config.script_timeout_s)

        return driver