from __future__ import annotations

import logging

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.infrastructure.logging.logger import get_logger, log_console


class SeleniumSession:
    def __init__(self, driver: WebDriver, default_wait_s: int = 10) -> None:
        self._driver = driver
        self._default_wait_s = default_wait_s
        self._logger = get_logger(self.__class__.__name__)

    @property
    def driver(self) -> WebDriver:
        return self._driver

    def open(self, url: str) -> None:
        log_console(self._logger, logging.INFO, "Abriendo URL: %s", url)
        self._driver.get(url)

    def refresh(self) -> None:
        self._driver.refresh()

    def quit(self) -> None:
        try:
            self._driver.quit()
            log_console(self._logger, logging.INFO, "Sesión Selenium cerrada correctamente.")
        except Exception:
            self._logger.exception(
                "Error cerrando sesión Selenium.",
                extra={"log_to_console": True, "log_to_file": False},
            )

    def wait_for_element(
        self,
        by: str,
        value: str,
        timeout_s: int | None = None,
    ):
        timeout = timeout_s or self._default_wait_s
        wait = WebDriverWait(self._driver, timeout)
        return wait.until(EC.presence_of_element_located((by, value)))

    def wait_for_clickable(
        self,
        by: str,
        value: str,
        timeout_s: int | None = None,
    ):
        timeout = timeout_s or self._default_wait_s
        wait = WebDriverWait(self._driver, timeout)
        return wait.until(EC.element_to_be_clickable((by, value)))

    def click(
        self,
        by: str,
        value: str,
        timeout_s: int | None = None,
    ) -> None:
        element = self.wait_for_clickable(by, value, timeout_s)
        element.click()

    def type_text(
        self,
        by: str,
        value: str,
        text: str,
        timeout_s: int | None = None,
        clear_first: bool = True,
    ) -> None:
        element = self.wait_for_element(by, value, timeout_s)
        if clear_first:
            element.clear()
        element.send_keys(text)

    def get_text(
        self,
        by: str,
        value: str,
        timeout_s: int | None = None,
    ) -> str:
        element = self.wait_for_element(by, value, timeout_s)
        return element.text

    def element_exists(
        self,
        by: str,
        value: str,
        timeout_s: int = 2,
    ) -> bool:
        try:
            self.wait_for_element(by, value, timeout_s)
            return True
        except TimeoutException:
            return False

    @staticmethod
    def by_xpath() -> str:
        return By.XPATH

    @staticmethod
    def by_id() -> str:
        return By.ID

    @staticmethod
    def by_name() -> str:
        return By.NAME

    @staticmethod
    def by_css() -> str:
        return By.CSS_SELECTOR