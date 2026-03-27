from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from selenium.webdriver.common.by import By

from app.infrastructure.config.settings import Settings
from app.infrastructure.logging.logger import get_logger, log_both, log_console
from app.infrastructure.selenium.driver_factory import DriverFactory
from app.infrastructure.selenium.selenium_session import SeleniumSession


@dataclass(slots=True, frozen=True)
class DetectedDevice:
    vendor: str
    model: str | None = None
    detection_method: str = "login_page"
    details: dict[str, Any] = field(default_factory=dict)


class DeviceDetectionService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._logger = get_logger(self.__class__.__name__)

    def detect(self, *, ip: str, worker_id: str) -> DetectedDevice:
        driver_factory = DriverFactory(self._settings.selenium)
        driver = driver_factory.create()
        session = SeleniumSession(driver=driver, default_wait_s=5)

        try:
            detected = self._detect_from_login_page(session=session, ip=ip, worker_id=worker_id)
            log_both(
                self._logger,
                logging.INFO,
                "Equipo detectado para %s en %s: vendor=%s model=%s method=%s",
                worker_id,
                ip,
                detected.vendor,
                detected.model,
                detected.detection_method,
            )
            return detected
        finally:
            session.quit()

    def _detect_from_login_page(
        self,
        *,
        session: SeleniumSession,
        ip: str,
        worker_id: str,
    ) -> DetectedDevice:
        driver = session.driver

        candidate_urls = [
            f"http://{ip}",
            f"http://{ip}/html/login_inter.html",
        ]

        for url in candidate_urls:
            try:
                log_console(
                    self._logger,
                    logging.INFO,
                    "Detectando equipo para %s en %s",
                    worker_id,
                    url,
                )
                session.open(url)
                time.sleep(1.0)

                current_url = (driver.current_url or "").lower()
                page_source = (driver.page_source or "").lower()

                if self._looks_like_fiberhome(driver, current_url, page_source):
                    return DetectedDevice(
                        vendor="FIBERHOME",
                        model=None,
                        detection_method="login_page_fiberhome",
                        details={
                            "url": url,
                            "current_url": current_url,
                        },
                    )

                # TODO: agregar heurísticas Huawei
                # if self._looks_like_huawei(...):
                #     return DetectedDevice(vendor="HUAWEI", ...)

                # TODO: agregar heurísticas ZTE
                # if self._looks_like_zte(...):
                #     return DetectedDevice(vendor="ZTE", ...)

            except Exception as exc:
                log_both(
                    self._logger,
                    logging.WARNING,
                    "Intento de detección fallido para %s en %s: %s",
                    worker_id,
                    url,
                    exc,
                )

        raise ValueError(f"No se pudo detectar el vendor del equipo en {ip}")

    @staticmethod
    def _looks_like_fiberhome(driver, current_url: str, page_source: str) -> bool:
        if "/html/login_inter.html" in current_url:
            return True

        fiber_ids = (
            "user_name",
            "loginpp",
            "password",
            "login_btn",
            "login",
            "LoginId",
        )

        for element_id in fiber_ids:
            try:
                if driver.find_elements(By.ID, element_id):
                    return True
            except Exception:
                pass

        fiber_markers = (
            "login_inter.html",
            "somebody has already logged in",
            "already logged",
        )

        return any(marker in page_source for marker in fiber_markers)