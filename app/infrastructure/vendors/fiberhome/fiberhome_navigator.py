from __future__ import annotations

import logging
import time
from collections import deque
from typing import Any

import requests
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from app.infrastructure.logging.logger import get_logger, log_console
from app.infrastructure.vendors.base.navigator_base import NavigatorBase


class FiberhomeNavigator(NavigatorBase):
    """
    Navegador Selenium real para FiberHome.

    Basado en la lógica ya probada de tus mixins:
    - login con user_name / loginpp
    - detección de sesión activa
    - logout best effort
    - navegación a reset
    - extracción de base_info vía AJAX usando cookies de Selenium
    """

    USERNAME = "root"
    PASSWORD = "admin"

    def __init__(self, session) -> None:
        super().__init__(session)
        self._logger = get_logger(self.__class__.__name__)
        self._host: str | None = None
        self._base_url: str | None = None

    # ==========================================================
    # Base
    # ==========================================================
    def open_root(self, ip: str) -> None:
        self._host = ip
        self._base_url = f"http://{ip}"
        login_url = f"{self._base_url}/html/login_inter.html"
        log_console(self._logger, logging.INFO, "Abriendo FiberHome en %s", login_url)
        self.session.open(login_url)

    def login(self, username: str | None = None, password: str | None = None) -> None:
        if not self._base_url:
            raise RuntimeError("No se ha llamado open_root() antes de login().")

        username = username or self.USERNAME
        password = password or self.PASSWORD

        driver = self.session.driver
        login_url = f"{self._base_url}/html/login_inter.html"

        # Si ya hay driver con sesión rara, intentar limpiar
        try:
            self.logout_best_effort()
        except Exception:
            pass

        driver.delete_all_cookies()

        if not self._wait_not_busy_login_page(driver, login_url, max_wait=120):
            raise RuntimeError("Login FiberHome bloqueado por sesión activa.")

        driver.get(login_url)

        WebDriverWait(driver, 15).until(
            lambda d: len(d.find_elements(By.ID, "user_name")) > 0
        )

        user_field = driver.find_element(By.ID, "user_name")

        try:
            pass_field = driver.find_element(By.ID, "loginpp")
        except Exception:
            pass_field = driver.find_element(By.ID, "password")

        driver.execute_script("arguments[0].value = arguments[1];", user_field, username)
        driver.execute_script("arguments[0].value = arguments[1];", pass_field, password)

        login_button = None
        for btn_id in ("login_btn", "login", "LoginId"):
            buttons = driver.find_elements(By.ID, btn_id)
            if buttons:
                login_button = buttons[0]
                break

        if login_button is None:
            raise RuntimeError("No se encontró botón de login FiberHome.")

        login_button.click()

        def post_login_ok(drv):
            html = (drv.page_source or "").lower()

            if "already logged" in html or "somebody has already logged in" in html:
                return "BUSY"

            if not drv.find_elements(By.ID, "user_name"):
                return "OK"

            if len(drv.find_elements(By.CSS_SELECTOR, "frame,iframe")) > 0:
                return "OK"

            el = self.find_element_anywhere(By.ID, "first_menu_manage", desc="Management", timeout=1)
            if el:
                return "OK"

            return False

        result = WebDriverWait(driver, 20).until(post_login_ok)
        if result == "BUSY":
            raise RuntimeError("FiberHome reportó sesión activa al intentar login.")

        log_console(self._logger, logging.INFO, "Login FiberHome correcto.")

    def logout_best_effort(self) -> bool:
        driver = self.session.driver

        try:
            driver.switch_to.default_content()
            el = self.find_element_anywhere(By.ID, "logout", desc="Logout", timeout=3)
            if el:
                try:
                    driver.execute_script("arguments[0].click();", el)
                except Exception:
                    el.click()
                time.sleep(1)
                log_console(self._logger, logging.INFO, "Logout FiberHome realizado.")
                return True
        except Exception:
            pass

        return False

    # ==========================================================
    # Helpers de navegación multi-frame
    # ==========================================================
    def find_element_anywhere(
        self,
        by: str,
        selector: str,
        *,
        desc: str = "",
        timeout: int = 10,
        max_depth: int = 8,
    ):
        driver = self.session.driver
        end_time = time.time() + timeout
        last_error = None

        while time.time() < end_time:
            try:
                driver.switch_to.default_content()

                queue = deque([[]])
                visited: set[tuple[int, ...]] = set()

                while queue:
                    path = queue.popleft()
                    tuple_path = tuple(path)
                    if tuple_path in visited:
                        continue
                    visited.add(tuple_path)

                    driver.switch_to.default_content()
                    ok = True
                    for index in path:
                        frames = driver.find_elements(By.CSS_SELECTOR, "frame,iframe")
                        if index >= len(frames):
                            ok = False
                            break
                        driver.switch_to.frame(frames[index])

                    if not ok:
                        continue

                    elements = driver.find_elements(by, selector)
                    if elements:
                        return elements[0]

                    if len(path) < max_depth:
                        frames = driver.find_elements(By.CSS_SELECTOR, "frame,iframe")
                        for index in range(len(frames)):
                            queue.append(path + [index])

            except Exception as exc:
                last_error = exc

            time.sleep(0.25)

        raise TimeoutException(
            f"No se encontró {desc or selector} en {timeout}s. Último error: {last_error}"
        )

    def click_anywhere(
        self,
        selectors: list[tuple[str, str]],
        *,
        desc: str,
        timeout: int = 10,
    ) -> bool:
        driver = self.session.driver
        start = time.time()
        last_error = None

        while time.time() - start < timeout:
            for by, selector in selectors:
                try:
                    el = self.find_element_anywhere(
                        by,
                        selector,
                        desc=desc,
                        timeout=2,
                    )

                    try:
                        driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});",
                            el,
                        )
                    except Exception:
                        pass

                    try:
                        driver.execute_script("arguments[0].click();", el)
                    except Exception as exc_js:
                        last_error = exc_js
                        el.click()

                    return True

                except Exception as exc:
                    last_error = exc

            time.sleep(0.2)

        raise RuntimeError(f"No se pudo encontrar/clickear '{desc}'. Último error: {last_error}")

    def _wait_not_busy_login_page(self, driver, login_url: str, max_wait: int = 120) -> bool:
        start = time.time()

        while time.time() - start < max_wait:
            driver.get(login_url)
            time.sleep(0.8)

            html = (driver.page_source or "").lower()
            if "already logged" not in html and "somebody has already logged in" not in html:
                return True

            log_console(self._logger, logging.INFO, "Router ocupado por sesión activa. Reintentando...")
            time.sleep(5)

        return False

    # ==========================================================
    # Factory Reset
    # ==========================================================
    def go_to_factory_reset(self) -> None:
        driver = self.session.driver

        driver.get(f"{self._base_url}/html/main_inter.html")
        time.sleep(1.5)

        self.click_anywhere(
            [(By.ID, "first_menu_manage")],
            desc="Management",
            timeout=15,
        )

        # Preferimos ID, pero dejamos fallback por texto
        try:
            self.click_anywhere(
                [(By.ID, "span_device_admin")],
                desc="Device Management",
                timeout=8,
            )
        except Exception:
            self.click_anywhere(
                [(By.XPATH, "//a[contains(text(), 'Device Management')]")],
                desc="Device Management",
                timeout=8,
            )

    def trigger_factory_reset(self) -> None:
        driver = self.session.driver

        try:
            restore_button = self.find_element_anywhere(
                By.ID,
                "Restart_button",
                desc="Restart_button",
                timeout=6,
            )
        except Exception:
            restore_button = self.find_element_anywhere(
                By.XPATH,
                "//input[@value='Restore']",
                desc="Restore button",
                timeout=6,
            )

        try:
            driver.execute_script("arguments[0].click();", restore_button)
        except Exception:
            restore_button.click()

        try:
            WebDriverWait(driver, 5).until(lambda d: d.switch_to.alert)
            alert = driver.switch_to.alert
            alert.accept()
        except Exception:
            # algunos modelos no muestran alerta siempre
            pass

        log_console(self._logger, logging.INFO, "Factory Reset enviado en FiberHome.")

    # ==========================================================
    # AJAX / extracción mínima
    # ==========================================================
    def build_requests_session(self) -> requests.Session:
        if not self._base_url:
            raise RuntimeError("No hay base_url configurada.")

        req_session = requests.Session()

        for cookie in self.session.driver.get_cookies():
            req_session.cookies.set(cookie["name"], cookie["value"])

        return req_session

    def ajax_get(self, tag: str) -> dict[str, Any] | None:
        if not self._base_url:
            raise RuntimeError("No hay base_url configurada.")

        req_session = self.build_requests_session()
        url = f"{self._base_url}/cgi-bin/ajax"

        try:
            response = req_session.get(
                url,
                params={"_tag": tag},
                timeout=8,
                verify=False,
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                return data
        except Exception:
            # algunos firmwares responden por POST o con formatos distintos
            pass

        try:
            response = req_session.post(
                url,
                data={"_tag": tag},
                timeout=8,
                verify=False,
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                return data
        except Exception:
            pass

        return None

    def extract_base_info(self) -> dict[str, Any] | None:
        base_info = self.ajax_get("get_base_info")
        if not base_info:
            return None

        session_valid = base_info.get("session_valid")
        try:
            session_valid = int(session_valid)
        except Exception:
            session_valid = session_valid

        if session_valid not in (1, "1", True):
            return None

        return base_info