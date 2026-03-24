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
    USERNAME = "root"
    PASSWORD = "admin"

    def __init__(self, session) -> None:
        super().__init__(session)
        self._logger = get_logger(self.__class__.__name__)
        self._host: str | None = None
        self._base_url: str | None = None

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
            raise RuntimeError("FiberHome reportó sesión activa al intentar login().")

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

    def build_requests_session(self) -> requests.Session:
        if not self._base_url:
            raise RuntimeError("No hay base_url configurada.")

        req_session = requests.Session()

        for cookie in self.session.driver.get_cookies():
            req_session.cookies.set(cookie["name"], cookie["value"])

        return req_session

    def ajax_get(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Alineado con tu _ajax_get viejo:
        /cgi-bin/ajax?ajaxmethod=<method>
        """
        if not self._base_url:
            raise RuntimeError("No hay base_url configurada.")

        req_session = self.build_requests_session()
        ajax_url = f"{self._base_url}/cgi-bin/ajax"

        query = dict(params or {})
        query["ajaxmethod"] = method
        query["_"] = str(time.time())

        response = req_session.get(
            ajax_url,
            params=query,
            auth=("root", "admin"),
            timeout=5,
            verify=False,
        )
        response.raise_for_status()

        try:
            data = response.json()
            if isinstance(data, dict):
                return data
        except Exception:
            pass

        return {}

    def extract_wifi_allwan(self) -> dict[str, Any] | None:
        """
        Método preferido.
        Basado en _extract_wifi_allwan() del código viejo.
        """
        try:
            response = self.ajax_get("get_allwan_info_broadBand")

            if not response or response.get("session_valid") != 1:
                return None

            wifi_info: dict[str, Any] = {}
            wifi_obj = response.get("wifi_obj_enable", {})

            ssids_24ghz = []
            ssids_5ghz = []

            for i in range(1, 9):
                ssid_key = f"ssid{i}"
                config_key = f"ConfigActive{i}"

                ssid = wifi_obj.get(ssid_key, "")
                active = wifi_obj.get(config_key, "0")

                if ssid and ssid != "":
                    wifi_entry = {
                        "ssid": ssid,
                        "enabled": active == "1",
                        "index": i,
                    }

                    if i <= 4:
                        ssids_24ghz.append(wifi_entry)
                    else:
                        ssids_5ghz.append(wifi_entry)

            if ssids_24ghz:
                primary_24 = next((s for s in ssids_24ghz if s["enabled"]), ssids_24ghz[0])
                wifi_info["ssid_24ghz"] = primary_24["ssid"]
                wifi_info["enabled_24ghz"] = primary_24["enabled"]

            if ssids_5ghz:
                primary_5 = next((s for s in ssids_5ghz if s["enabled"]), ssids_5ghz[0])
                wifi_info["ssid_5ghz"] = primary_5["ssid"]
                wifi_info["enabled_5ghz"] = primary_5["enabled"]

            wifi_info["wifi_5g_capable"] = response.get("wifi_5g_enable") == 1
            wifi_info["wifi_device_count"] = response.get("wifi_device", 0)
            wifi_info["wifi_port_num"] = response.get("wifi_port_num", 0)
            wifi_info["extraction_method"] = "get_allwan_info_broadBand"

            return wifi_info

        except Exception:
            return None

    def extract_wifi_info_fallback(self) -> dict[str, Any]:
        """
        Basado en _extract_wifi_info() del código viejo.
        Se usa solo si get_allwan_info_broadBand no devolvió SSIDs.
        """
        wifi_info: dict[str, Any] = {}

        # PRIORIDAD 1: get_wifi_info -> 2.4 GHz
        try:
            wifi_24_response = self.ajax_get("get_wifi_info")
            if wifi_24_response.get("session_valid") == 1:
                if wifi_24_response.get("SSID"):
                    wifi_info["ssid_24ghz"] = wifi_24_response["SSID"]
                if wifi_24_response.get("PreSharedKey"):
                    wifi_info["password_24ghz"] = wifi_24_response["PreSharedKey"]
                if wifi_24_response.get("Channel"):
                    wifi_info["channel_24ghz"] = wifi_24_response["Channel"]
                if wifi_24_response.get("Enable"):
                    wifi_info["enabled_24ghz"] = wifi_24_response["Enable"] == "1"
        except Exception:
            pass

        # PRIORIDAD 2: get_5g_wifi_info -> 5 GHz
        try:
            wifi_5g_response = self.ajax_get("get_5g_wifi_info")
            if wifi_5g_response.get("session_valid") == 1:
                if wifi_5g_response.get("SSID"):
                    wifi_info["ssid_5ghz"] = wifi_5g_response["SSID"]
                if wifi_5g_response.get("PreSharedKey"):
                    wifi_info["password_5ghz"] = wifi_5g_response["PreSharedKey"]
                if wifi_5g_response.get("Channel"):
                    wifi_info["channel_5ghz"] = wifi_5g_response["Channel"]
                if wifi_5g_response.get("Enable"):
                    wifi_info["enabled_5ghz"] = wifi_5g_response["Enable"] == "1"
        except Exception:
            pass

        # PRIORIDAD 3: get_wifi_status
        try:
            wifi_status = self.ajax_get("get_wifi_status")
            if wifi_status.get("session_valid") == 1 and wifi_status.get("wifi_status"):
                wifi_networks = wifi_status["wifi_status"]

                for network in wifi_networks:
                    if network.get("Enable") != "1":
                        continue

                    standard = str(network.get("Standard", "")).lower()
                    is_5ghz = "ac" in standard or "ax" in standard or standard == "a"

                    ssid = network.get("SSID", "")
                    psk = network.get("PreSharedKey", "")
                    channel = network.get("channelIsInUse", network.get("Channel", "Auto"))

                    if is_5ghz:
                        if "ssid_5ghz" not in wifi_info and ssid:
                            wifi_info["ssid_5ghz"] = ssid
                        if "password_5ghz" not in wifi_info and psk:
                            wifi_info["password_5ghz"] = psk
                        wifi_info["channel_5ghz"] = channel
                        wifi_info["enabled_5ghz"] = True
                        wifi_info["standard_5ghz"] = network.get("Standard")
                    else:
                        if "ssid_24ghz" not in wifi_info and ssid:
                            wifi_info["ssid_24ghz"] = ssid
                        if "password_24ghz" not in wifi_info and psk:
                            wifi_info["password_24ghz"] = psk
                        wifi_info["channel_24ghz"] = channel
                        wifi_info["enabled_24ghz"] = True
                        wifi_info["standard_24ghz"] = network.get("Standard")
        except Exception:
            pass

        return wifi_info

    def extract_wifi_info_complete(self) -> dict[str, Any]:
        """
        Flujo completo como en el proyecto viejo:
        1) get_allwan_info_broadBand
        2) si no da SSIDs, fallback a extract_wifi_info_fallback
        """
        wifi_info = self.extract_wifi_allwan() or {}

        if not wifi_info.get("ssid_24ghz") or not wifi_info.get("ssid_5ghz"):
            fallback = self.extract_wifi_info_fallback() or {}

            for key, value in fallback.items():
                if key not in wifi_info or not wifi_info.get(key):
                    wifi_info[key] = value

            if fallback and "extraction_method" not in wifi_info:
                wifi_info["extraction_method"] = "fallback_extract_wifi_info"

        return wifi_info

    def extract_base_info(self) -> dict[str, Any] | None:
        base_info = self.ajax_get("get_base_info")
        if not base_info:
            return None

        raw_data = dict(base_info)

        wifi_info: dict[str, Any] = {}
        

        normalized: dict[str, Any] = {
            "raw_data": raw_data,
            "model_name": raw_data.get("ModelName") or raw_data.get("model_name"),
            "manufacturer": raw_data.get("Manufacturer") or raw_data.get("manufacturer"),
            "hardware_version": raw_data.get("HardwareVersion") or raw_data.get("hardware_version"),
            "software_version": raw_data.get("SoftwareVersion") or raw_data.get("software_version"),
            "serial_number_logical": raw_data.get("gponsn") or raw_data.get("SerialNumber"),
            "tx_power_dbm": (
                raw_data.get("tx_power_dbm")
                or raw_data.get("txPower")
                or raw_data.get("TxPower")
                or raw_data.get("txpower")
            ),
            "rx_power_dbm": (
                raw_data.get("rx_power_dbm")
                or raw_data.get("rxPower")
                or raw_data.get("RxPower")
                or raw_data.get("rxpower")
            ),
            "usb_ports": raw_data.get("usb_ports") or raw_data.get("usb_port_num"),
            "usb_status": raw_data.get("usb_status"),

            # WiFi agrupado
            "wifi_info": wifi_info,

            # WiFi expuesto directo también para compatibilidad
            "ssid_24ghz": wifi_info.get("ssid_24ghz"),
            "ssid_5ghz": wifi_info.get("ssid_5ghz"),
            "password_24ghz": wifi_info.get("password_24ghz"),
            "password_5ghz": wifi_info.get("password_5ghz"),
            "channel_24ghz": wifi_info.get("channel_24ghz"),
            "channel_5ghz": wifi_info.get("channel_5ghz"),
            "enabled_24ghz": wifi_info.get("enabled_24ghz"),
            "enabled_5ghz": wifi_info.get("enabled_5ghz"),
        }
        try:
            normalized["wifi_info"] = self.extract_wifi_info_complete()
        except Exception:
            normalized["wifi_info"] = {}
        return normalized

    def extract_ftpclient_info(self) -> dict[str, Any] | None:
        try:
            return self.ajax_get("get_ftpclient_info")
        except Exception:
            return None

    def extract_wifi_passwords_selenium(self) -> dict[str, str]:
        driver = self.session.driver
        passwords: dict[str, str] = {}

        try:
            network_menu = self.find_element_anywhere(By.ID, "first_menu_network", desc="Network", timeout=5)
            if not network_menu:
                return passwords

            network_menu.click()
            time.sleep(1)

            try:
                wlan_security = self.find_element_anywhere(By.ID, "thr_security", desc="WLAN Security", timeout=5)
                if wlan_security:
                    wlan_security.click()
                    time.sleep(2)

                    psk_field = self.find_element_anywhere(By.ID, "PreSharedKey", desc="PreSharedKey", timeout=5)
                    if psk_field:
                        driver.execute_script("arguments[0].removeAttribute('class');", psk_field)
                        time.sleep(0.5)
                        password = psk_field.get_attribute("value")
                        if password:
                            passwords["password_24ghz"] = password
            except Exception:
                pass

            try:
                thr_5gsecurity = self.find_element_anywhere(By.ID, "thr_5Gsecurity", desc="5G Security", timeout=5)
                if thr_5gsecurity:
                    thr_5gsecurity.click()
                    time.sleep(1)

                    psk_5g_field = self.find_element_anywhere(By.ID, "PreSharedKey", desc="PreSharedKey 5G", timeout=3)
                    if psk_5g_field:
                        driver.execute_script("arguments[0].removeAttribute('class');", psk_5g_field)
                        time.sleep(0.5)
                        password_5g = psk_5g_field.get_attribute("value")
                        if password_5g:
                            passwords["password_5ghz"] = password_5g
            except Exception:
                pass

            if "password_5ghz" not in passwords and "password_24ghz" in passwords:
                passwords["password_5ghz"] = passwords["password_24ghz"]

            return passwords

        except Exception:
            return passwords