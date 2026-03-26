from __future__ import annotations

import logging
import re
import time
from typing import TYPE_CHECKING, Any

from app.application.dto.execution_test_request import ExecutionTestRequest
from app.infrastructure.config.settings import Settings
from app.infrastructure.logging.logger import get_logger, log_both
from app.infrastructure.selenium.driver_factory import DriverFactory
from app.infrastructure.selenium.selenium_session import SeleniumSession
from app.infrastructure.vendors.base.test_runner_base import TestRunnerBase
from app.infrastructure.vendors.fiberhome.fiberhome_adapter import (
    FiberhomeAdapter,
    FiberhomeExecutionResult,
)
from app.infrastructure.vendors.fiberhome.fiberhome_navigator import FiberhomeNavigator
from app.shared.wifi.windows_rssi import evaluate_wifi_rssi_windows
from app.application.services.result_evaluator import TestResultEvaluator
from app.application.services.treshold_provider import TestThresholdProvider

if TYPE_CHECKING:
    from app.workers.supervisor import Supervisor


class FiberhomeTestRunner(TestRunnerBase):
    def __init__(
        self,
        *,
        settings: Settings,
        supervisor: Supervisor,
        worker_id: str,
    ) -> None:
        self._settings = settings
        self._supervisor = supervisor
        self._worker_id = worker_id
        self._logger = get_logger(f"{self.__class__.__name__}.{worker_id}")
        self._adapter = FiberhomeAdapter()

        self._threshold_provider = TestThresholdProvider()
        self._thresholds = self._threshold_provider.get_thresholds(vendor="FIBERHOME")

        self._evaluator = TestResultEvaluator(
            supervisor=self._supervisor,
            worker_id=self._worker_id,
            adapter=self._adapter,
            logger=self._logger,
            thresholds=self._thresholds,
        )

    def run(self, request: ExecutionTestRequest) -> FiberhomeExecutionResult:
        snapshot = self._supervisor.get_worker_snapshot(self._worker_id)
        if snapshot is None:
            raise RuntimeError(f"No existe snapshot para {self._worker_id}")

        target_ip = snapshot.get("expected_ip")
        if not target_ip:
            raise RuntimeError(f"No hay expected_ip configurada para {self._worker_id}")

        driver_factory = DriverFactory(self._settings.selenium)
        driver = driver_factory.create()
        session = SeleniumSession(driver=driver, default_wait_s=10)
        navigator = FiberhomeNavigator(session)
        result = FiberhomeExecutionResult()

        try:
            log_both(
                self._logger,
                logging.INFO,
                "Iniciando FiberHome runner para %s sobre %s",
                self._worker_id,
                target_ip,
            )

            navigator.open_root(str(target_ip))
            navigator.login("root", "admin")

            base_info = navigator.extract_base_info() or {}
            ftp_info = navigator.extract_ftpclient_info() or {}
            wifi_passwords = navigator.extract_wifi_passwords_selenium() or {}

            base_info.setdefault("wifi_info", {})
            if "password_24ghz" in wifi_passwords:
                base_info["wifi_info"]["password_24ghz"] = wifi_passwords["password_24ghz"]
            if "password_5ghz" in wifi_passwords:
                base_info["wifi_info"]["password_5ghz"] = wifi_passwords["password_5ghz"]

            log_both(
                self._logger,
                logging.INFO,
                "base_info wifi_info %s: %s | ssid_24=%s | ssid_5=%s",
                self._worker_id,
                base_info.get("wifi_info", {}),
                (base_info.get("wifi_info") or {}).get("ssid_24ghz") or base_info.get("ssid_24ghz"),
                (base_info.get("wifi_info") or {}).get("ssid_5ghz") or base_info.get("ssid_5ghz"),
            )
            log_both(
                self._logger,
                logging.INFO,
                "ftp_info %s keys=%s session_valid=%s",
                self._worker_id,
                list(ftp_info.keys()),
                ftp_info.get("session_valid"),
            )

            serial_number = (
                base_info.get("serial_number_logical")
                or base_info.get("raw_data", {}).get("gponsn")
                or base_info.get("raw_data", {}).get("SerialNumber")
            )

            result.identity = self._adapter.build_identity(
                serial_number=serial_number,
                mac_address=snapshot.get("device_mac"),
                ip=str(target_ip),
            )

            context = self._supervisor.get_worker_context(self._worker_id)
            if context is not None:
                context.bind_device(
                    device_sn=result.identity.serial_number,
                    device_mac=result.identity.mac_address,
                    vendor="FIBERHOME",
                )
                context.set_metadata("base_info", base_info)
                context.set_metadata("ftp_info", ftp_info)

            if request.is_test_enabled("usb"):
                result.tests["usb"] = self._run_usb(base_info, ftp_info)

            if request.is_test_enabled("fiber_tx"):
                result.tests["fiber_tx"] = self._run_fiber_tx(base_info)

            if request.is_test_enabled("fiber_rx"):
                result.tests["fiber_rx"] = self._run_fiber_rx(base_info)

            wifi_scan_result: dict[str, Any] | None = None

            if request.is_test_enabled("wifi_2g"):
                wifi_scan_result = self._run_wifi_scan(base_info)
                result.tests["wifi_2g"] = self._run_wifi_24(base_info, wifi_scan_result)

            if request.is_test_enabled("wifi_5g"):
                if wifi_scan_result is None:
                    wifi_scan_result = self._run_wifi_scan(base_info)
                result.tests["wifi_5g"] = self._run_wifi_5(base_info, wifi_scan_result)

            return result

        finally:
            session.quit()

    def _run_usb(self, base_info: dict[str, Any], ftp_info: dict[str, Any]):
        self._supervisor.update_worker_phase(
            worker_id=self._worker_id,
            phase="USB",
            status="TESTING",
        )
        self._supervisor.publish_test_indicator(
            worker_id=self._worker_id,
            test_name="USB",
            visual_state="RUNNING",
        )

        result_details: dict[str, Any] = {}

        raw = base_info.get("raw_data") or {}
        usb_ports = (
            base_info.get("usb_ports")
            or raw.get("usb_ports")
            or base_info.get("usb_port_num")
            or raw.get("usb_port_num")
            or 0
        )
        usb_status = base_info.get("usb_status") or raw.get("usb_status")

        try:
            usb_ports = int(usb_ports)
        except (TypeError, ValueError):
            usb_ports = 0

        result_details["hardware_method"] = "AJAX get_base_info"
        result_details["usb_ports_capacity"] = usb_ports
        if usb_status is not None:
            result_details["usb_status_flag"] = usb_status

        if usb_ports <= 0:
            step = self._adapter.build_test_result(
                name="usb",
                status="FAIL",
                details={**result_details, "note": "El equipo no reporta puertos USB en base_info."},
            )
            self._supervisor.publish_test_indicator(
                worker_id=self._worker_id,
                test_name="USB",
                visual_state="FAIL",
            )
            log_both(self._logger, logging.ERROR, "Resultado USB %s: %s", self._worker_id, step.details)
            return step

        devices: list[str] = []
        connected_count = 0

        session_raw = ftp_info.get("session_valid")
        try:
            session_valid = int(session_raw)
        except (TypeError, ValueError):
            session_valid = None

        result_details["ftp_session_valid"] = session_raw

        usb_list_raw = ftp_info.get("UsbList") or ftp_info.get("USBList") or ""
        usb_list_raw = str(usb_list_raw)

        if usb_list_raw:
            devices = [d for d in re.split(r"[,\s]+", usb_list_raw) if d]
            connected_count = len(devices)
            result_details["usb_devices_connected"] = connected_count
            result_details["usb_devices_list"] = devices
            result_details["usb_list_raw"] = usb_list_raw
        else:
            if session_valid not in (1, None):
                result_details["warning_ftp"] = (
                    f"get_ftpclient_info devolvió session_valid={session_raw} y no se recibió UsbList."
                )

        usb_status_norm = (raw.get("usb_status") or base_info.get("usb_status") or "").strip().lower()
        result_details["method"] = "AJAX get_base_info"

        if connected_count >= usb_ports and usb_ports > 0:
            step = self._adapter.build_test_result(
                name="usb",
                status="PASS",
                details={
                    **result_details,
                    "note": f"Capacidad declarada: {usb_ports}; dispositivos detectados: {connected_count} (OK).",
                },
            )
            self._supervisor.publish_test_indicator(
                worker_id=self._worker_id,
                test_name="USB",
                visual_state="PASS",
            )
            log_both(self._logger, logging.INFO, "Resultado USB %s: PASS | %s", self._worker_id, step.details)
            return step

        elif connected_count > 0 and usb_ports > 0:
            step = self._adapter.build_test_result(
                name="usb",
                status="FAIL",
                details={**result_details, "error": "Se detectaron algunos dispositivos USB, pero no coincide con la capacidad."},
            )
            self._supervisor.publish_test_indicator(
                worker_id=self._worker_id,
                test_name="USB",
                visual_state="FAIL",
            )
            log_both(self._logger, logging.ERROR, "Resultado USB %s: FAIL | %s", self._worker_id, step.details)
            return step

        if usb_status_norm == "active":
            step = self._adapter.build_test_result(
                name="usb",
                status="PASS",
                details={**result_details, "usb_status": "Active"},
            )
            self._supervisor.publish_test_indicator(
                worker_id=self._worker_id,
                test_name="USB",
                visual_state="PASS",
            )
            log_both(self._logger, logging.INFO, "Resultado USB %s: PASS | %s", self._worker_id, step.details)
            return step

        step = self._adapter.build_test_result(
            name="usb",
            status="FAIL",
            details={**result_details, "usb_status": "Inactive", "method": "AJAX get_base_info"},
        )
        self._supervisor.publish_test_indicator(
            worker_id=self._worker_id,
            test_name="USB",
            visual_state="FAIL",
        )
        log_both(self._logger, logging.ERROR, "Resultado USB %s: FAIL | %s", self._worker_id, step.details)
        return step

    def _run_fiber_tx(self, base_info: dict[str, Any]):
        self._supervisor.update_worker_phase(
            worker_id=self._worker_id,
            phase="FIBER_TX",
            status="TESTING",
        )
        self._supervisor.publish_test_indicator(
            worker_id=self._worker_id,
            test_name="FIBER_TX",
            visual_state="RUNNING",
        )

        tx_raw = base_info.get("tx_power_dbm")
        details = {
            "method": "AJAX get_base_info",
            "tx_power_dbm": tx_raw,
        }

        return self._evaluator.evaluate_fiber_tx(
            value=tx_raw,
            source_details=details,
        )

    def _run_fiber_rx(self, base_info: dict[str, Any]):
        self._supervisor.update_worker_phase(
            worker_id=self._worker_id,
            phase="FIBER_RX",
            status="TESTING",
        )
        self._supervisor.publish_test_indicator(
            worker_id=self._worker_id,
            test_name="FIBER_RX",
            visual_state="RUNNING",
        )

        rx_raw = base_info.get("rx_power_dbm")
        details = {
            "method": "AJAX get_base_info",
            "rx_power_dbm": rx_raw,
        }

        return self._evaluator.evaluate_fiber_rx(
            value=rx_raw,
            source_details=details,
        )

    def _run_wifi_scan(self, base_info: dict[str, Any]) -> dict[str, Any]:
        wifi_info = base_info.get("wifi_info") or {}

        ssid_24 = (
            wifi_info.get("ssid_24ghz")
            or base_info.get("ssid_24ghz")
        )
        ssid_5 = (
            wifi_info.get("ssid_5ghz")
            or base_info.get("ssid_5ghz")
        )

        if not ssid_24 or not ssid_5:
            return {
                "name": "potencia_wifi",
                "status": "FAIL",
                "details": {
                    "errors": ["No se encontraron SSID 2.4 y/o 5 GHz en base_info"],
                    "ssid_24": ssid_24,
                    "ssid_5": ssid_5,
                },
            }

        retries = max(1, self._settings.wifi.scan_retries)
        retry_delay_s = self._settings.wifi.scan_retry_delay_s
        stabilization_delay_s = self._settings.wifi.stabilization_delay_s

        with self._supervisor.wifi_scan_guard(self._worker_id):
            log_both(
                self._logger,
                logging.INFO,
                "Worker %s estabilizando radios WiFi antes del scan...",
                self._worker_id,
            )
            time.sleep(stabilization_delay_s)

            last_result: dict[str, Any] | None = None

            for attempt in range(1, retries + 1):
                result = evaluate_wifi_rssi_windows(
                    ssid_24=ssid_24,
                    ssid_5=ssid_5,
                )
                last_result = result

                details = result.get("details", {})
                pass_24 = bool(details.get("pass_24"))
                pass_5 = bool(details.get("pass_5"))

                log_both(
                    self._logger,
                    logging.INFO,
                    "Intento WiFi %s/%s para %s: pass_24=%s pass_5=%s errors=%s",
                    attempt,
                    retries,
                    self._worker_id,
                    pass_24,
                    pass_5,
                    details.get("errors", []),
                )

                if pass_24 and pass_5:
                    log_both(
                        self._logger,
                        logging.INFO,
                        "Resultado scan WiFi compartido %s: %s",
                        self._worker_id,
                        result,
                    )
                    return result

                if attempt < retries:
                    time.sleep(retry_delay_s)

            log_both(
                self._logger,
                logging.INFO,
                "Resultado scan WiFi compartido %s: %s",
                self._worker_id,
                last_result,
            )
            return last_result or {
                "name": "potencia_wifi",
                "status": "FAIL",
                "details": {
                    "errors": ["No se obtuvo resultado de scan WiFi."],
                    "ssid_24": ssid_24,
                    "ssid_5": ssid_5,
                },
            }

    def _run_wifi_24(self, base_info: dict[str, Any], wifi_scan_result: dict[str, Any]):
        self._supervisor.update_worker_phase(
            worker_id=self._worker_id,
            phase="WIFI_2G",
            status="TESTING",
        )
        self._supervisor.publish_test_indicator(
            worker_id=self._worker_id,
            test_name="WIFI_2G",
            visual_state="RUNNING",
        )

        wifi_info = base_info.get("wifi_info") or {}
        details = {
            "ssid": wifi_info.get("ssid_24ghz") or base_info.get("ssid_24ghz"),
            "password_unencrypted": (
                wifi_info.get("password_24ghz") or base_info.get("password_24ghz")
            ),
            "signal_percent": wifi_scan_result.get("details", {}).get("best_24_percent"),
            "wifi_scan": wifi_scan_result,
        }

        return self._evaluator.evaluate_wifi_2g(details=details)

    def _run_wifi_5(self, base_info: dict[str, Any], wifi_scan_result: dict[str, Any]):
        self._supervisor.update_worker_phase(
            worker_id=self._worker_id,
            phase="WIFI_5G",
            status="TESTING",
        )
        self._supervisor.publish_test_indicator(
            worker_id=self._worker_id,
            test_name="WIFI_5G",
            visual_state="RUNNING",
        )

        wifi_info = base_info.get("wifi_info") or {}
        details = {
            "ssid": wifi_info.get("ssid_5ghz") or base_info.get("ssid_5ghz"),
            "password_unencrypted": (
                wifi_info.get("password_5ghz") or base_info.get("password_5ghz")
            ),
            "signal_percent": wifi_scan_result.get("details", {}).get("best_5_percent"),
            "wifi_scan": wifi_scan_result,
        }

        return self._evaluator.evaluate_wifi_5g(details=details)