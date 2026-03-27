from __future__ import annotations

import logging
import re
import time
from typing import TYPE_CHECKING, Any
from selenium.common.exceptions import TimeoutException, WebDriverException

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
from app.application.services.software_update_evaluator import SoftwareUpdateEvaluator
from app.application.services.software_update_provider import SoftwareUpdateProvider
from app.infrastructure.network.ping_service import PingService

if TYPE_CHECKING:
    from app.workers.supervisor import Supervisor


class FiberhomeTestRunner(TestRunnerBase):
    def __init__(
        self,
        *,
        settings: Settings,
        supervisor: Supervisor,
        worker_id: str,
        ping_service: PingService,
    ) -> None:
        self._settings = settings
        self._supervisor = supervisor
        self._worker_id = worker_id
        self._logger = get_logger(f"{self.__class__.__name__}.{worker_id}")
        self._adapter = FiberhomeAdapter()
        self._software_update_provider = SoftwareUpdateProvider(settings)
        self._software_update_evaluator = SoftwareUpdateEvaluator()

        self._threshold_provider = TestThresholdProvider()
        self._thresholds = self._threshold_provider.get_thresholds(vendor="FIBERHOME")
        self._ping_service = ping_service

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
            base_info = self._merge_wifi_passwords(base_info, wifi_passwords)

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
            
            if request.is_test_enabled("software_update"):
                software_update_step, base_info = self._run_software_update(
                    navigator=navigator,
                    request=request,
                    base_info=base_info,
                    target_ip=str(target_ip),
                )
                result.tests["software_update"] = software_update_step

                ftp_info = navigator.extract_ftpclient_info() or {}
                wifi_passwords = navigator.extract_wifi_passwords_selenium() or {}
                base_info = self._merge_wifi_passwords(base_info, wifi_passwords)

                if context is not None:
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
            log_both(self._logger, logging.ERROR, "Resultado USB %s: FAIL | %s", self._worker_id, step.details)
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
        usb_list_raw = str(usb_list_raw).strip()

        if usb_list_raw:
            devices = [d for d in re.split(r"[,\s]+", usb_list_raw) if d]
            connected_count = len(devices)

        result_details["usb_devices_connected"] = connected_count
        result_details["usb_devices_list"] = devices
        result_details["usb_list_raw"] = usb_list_raw
        result_details["method"] = "AJAX get_base_info"

        if not usb_list_raw and session_valid not in (1, None):
            result_details["warning_ftp"] = (
                f"get_ftpclient_info devolvió session_valid={session_raw} y no se recibió UsbList."
            )

        if connected_count >= usb_ports:
            step = self._adapter.build_test_result(
                name="usb",
                status="PASS",
                details={
                    **result_details,
                    "note": (
                        f"Capacidad declarada: {usb_ports}; "
                        f"dispositivos detectados: {connected_count} (OK)."
                    ),
                },
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
            details={
                **result_details,
                "reason": (
                    f"La cantidad de dispositivos USB detectados ({connected_count}) "
                    f"es menor que la capacidad declarada del equipo ({usb_ports})."
                ),
            },
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
    
    def _merge_wifi_passwords(
        self,
        base_info: dict[str, Any],
        wifi_passwords: dict[str, Any] | None,
    ) -> dict[str, Any]:
        merged = dict(base_info or {})
        merged.setdefault("wifi_info", {})

        passwords = dict(wifi_passwords or {})

        if "password_24ghz" in passwords:
            merged["wifi_info"]["password_24ghz"] = passwords["password_24ghz"]

        if "password_5ghz" in passwords:
            merged["wifi_info"]["password_5ghz"] = passwords["password_5ghz"]

        return merged

    def _publish_software_update_stage(
        self,
        *,
        stage: str,
        progress_percent: int,
        message: str,
        visual_state: str = "RUNNING",
        extra_payload: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "stage": stage,
            "progress_percent": progress_percent,
            "message": message,
        }
        if extra_payload:
            payload.update(extra_payload)

        self._supervisor.publish_test_indicator(
            worker_id=self._worker_id,
            test_name="SOFTWARE_UPDATE",
            visual_state=visual_state,
            extra_payload=payload,
        )

    def _run_software_update(
        self,
        *,
        navigator: FiberhomeNavigator,
        request: ExecutionTestRequest,
        base_info: dict[str, Any],
        target_ip: str,
    ):
        self._supervisor.update_worker_phase(
            worker_id=self._worker_id,
            phase="SOFTWARE_UPDATE",
            status="TESTING",
        )

        self._publish_software_update_stage(
            stage="PREPARING",
            progress_percent=5,
            message="Preparando actualización de software.",
        )

        current_version = (
            base_info.get("software_version")
            or (base_info.get("raw_data") or {}).get("SoftwareVersion")
            or ""
        )
        model_name = (
            base_info.get("model_name")
            or (base_info.get("raw_data") or {}).get("ModelName")
            or ""
        )

        try:
            self._publish_software_update_stage(
                stage="RESOLVING_FIRMWARE",
                progress_percent=10,
                message="Resolviendo firmware a partir del modelo del equipo.",
                extra_payload={
                    "model_code": request.model,
                    "model_name": model_name,
                    "current_version": current_version,
                },
            )

            firmware = self._software_update_provider.resolve_firmware(
                vendor="fiberhome",
                model_code=request.model,
                model_name=model_name,
            )

            decision = self._software_update_evaluator.evaluate(
                current_version=current_version,
                target_version=firmware.target_version,
            )

            if not decision.required:
                step = self._adapter.build_test_result(
                    name="software_update",
                    status="PASS",
                    details={
                        "update_required": False,
                        "current_version": decision.current_version,
                        "target_version": decision.target_version,
                        "reason": decision.reason,
                        "firmware_path": str(firmware.firmware_path),
                        "model_name": model_name,
                        "model_key": firmware.model_key,
                    },
                )
                self._publish_software_update_stage(
                    stage="COMPLETED_NO_UPDATE",
                    progress_percent=100,
                    message="El equipo ya está actualizado.",
                    visual_state="PASS",
                    extra_payload=step.details,
                )
                log_both(
                    self._logger,
                    logging.INFO,
                    "Resultado SOFTWARE_UPDATE %s: PASS | %s",
                    self._worker_id,
                    step.details,
                )
                return step, base_info

            self._supervisor.publish_global_visual_mode(
                worker_id=self._worker_id,
                mode="EXPECTED_UPDATE",
                active=True,
                extra_payload={
                    "current_version": decision.current_version,
                    "target_version": decision.target_version,
                    "firmware_path": str(firmware.firmware_path),
                },
            )

            self._publish_software_update_stage(
                stage="LOGIN_SUPERUSER",
                progress_percent=20,
                message="Iniciando sesión con superusuario.",
                extra_payload={
                    "firmware_path": str(firmware.firmware_path),
                    "target_version": firmware.target_version,
                    "model_key": firmware.model_key,
                },
            )

            superuser_username, superuser_password = self._software_update_provider.resolve_superuser_credentials(
                vendor="fiberhome"
            )

            login_ok = False
            last_login_error: Exception | None = None

            for attempt in range(1, self._settings.software_update.max_login_retries + 1):
                try:
                    navigator.login(superuser_username, superuser_password)
                    login_ok = True
                    break
                except Exception as exc:
                    last_login_error = exc
                    log_both(
                        self._logger,
                        logging.WARNING,
                        "Intento login superusuario %s/%s fallido para %s: %s",
                        attempt,
                        self._settings.software_update.max_login_retries,
                        self._worker_id,
                        exc,
                    )
                    time.sleep(self._settings.software_update.login_retry_delay_s)

            if not login_ok:
                step = self._adapter.build_test_result(
                    name="software_update",
                    status="FAIL",
                    details={
                        "update_required": True,
                        "current_version": decision.current_version,
                        "target_version": decision.target_version,
                        "firmware_path": str(firmware.firmware_path),
                        "model_name": model_name,
                        "model_key": firmware.model_key,
                        "reason": "No se pudo iniciar sesión con superusuario.",
                        "last_error": str(last_login_error) if last_login_error else None,
                    },
                )
                self._publish_software_update_stage(
                    stage="FAIL_LOGIN_SUPERUSER",
                    progress_percent=100,
                    message="No se pudo iniciar sesión con superusuario.",
                    visual_state="FAIL",
                    extra_payload=step.details,
                )
                log_both(
                    self._logger,
                    logging.ERROR,
                    "Resultado SOFTWARE_UPDATE %s: FAIL | %s",
                    self._worker_id,
                    step.details,
                )
                return step, base_info

            self._publish_software_update_stage(
                stage="UPLOADING_FIRMWARE",
                progress_percent=45,
                message="Subiendo firmware al equipo.",
                extra_payload={
                    "firmware_path": str(firmware.firmware_path),
                    "firmware_filename": firmware.filename,
                },
            )

            navigator.upload_firmware_via_form(str(firmware.firmware_path))
            time.sleep(self._settings.software_update.post_upload_delay_s)

            self._publish_software_update_stage(
                stage="WAITING_REBOOT_START",
                progress_percent=65,
                message="Esperando que el equipo inicie el reinicio.",
            )

            reboot_started = navigator.wait_for_router_reboot_start(
                max_wait_down=self._settings.software_update.reboot_wait_down_s,
            )

            if not reboot_started:
                step = self._adapter.build_test_result(
                    name="software_update",
                    status="FAIL",
                    details={
                        "update_required": True,
                        "current_version": decision.current_version,
                        "target_version": decision.target_version,
                        "firmware_path": str(firmware.firmware_path),
                        "firmware_filename": firmware.filename,
                        "reason": "No se confirmó que el equipo iniciara el reinicio tras subir el firmware.",
                    },
                )
                self._publish_software_update_stage(
                    stage="FAIL_REBOOT_NOT_STARTED",
                    progress_percent=100,
                    message="No se detectó caída del equipo después de iniciar la actualización.",
                    visual_state="FAIL",
                    extra_payload=step.details,
                )
                log_both(
                    self._logger,
                    logging.ERROR,
                    "Resultado SOFTWARE_UPDATE %s: FAIL | %s",
                    self._worker_id,
                    step.details,
                )
                return step, base_info

            self._publish_software_update_stage(
                stage="WAITING_PING_RETURN",
                progress_percent=75,
                message="Esperando que el equipo vuelva a responder por ping.",
            )

            ping_back = self._wait_until_ping_back(
                target_ip=target_ip,
                timeout_s=self._settings.software_update.ping_return_timeout_s,
            )

            if not ping_back:
                step = self._adapter.build_test_result(
                    name="software_update",
                    status="FAIL",
                    details={
                        "update_required": True,
                        "current_version": decision.current_version,
                        "target_version": decision.target_version,
                        "firmware_path": str(firmware.firmware_path),
                        "firmware_filename": firmware.filename,
                        "reason": "El equipo no volvió a responder por ping dentro del tiempo esperado.",
                    },
                )
                self._publish_software_update_stage(
                    stage="FAIL_PING_RETURN_TIMEOUT",
                    progress_percent=100,
                    message="El equipo no volvió a responder por ping tras la actualización.",
                    visual_state="FAIL",
                    extra_payload=step.details,
                )
                log_both(
                    self._logger,
                    logging.ERROR,
                    "Resultado SOFTWARE_UPDATE %s: FAIL | %s",
                    self._worker_id,
                    step.details,
                )
                return step, base_info

            self._publish_software_update_stage(
                stage="POST_REBOOT_STABILIZATION",
                progress_percent=82,
                message="Esperando estabilización del equipo después de recuperar conectividad.",
                extra_payload={
                    "post_reboot_stabilization_s": self._settings.software_update.post_reboot_stabilization_s,
                },
            )

            time.sleep(self._settings.software_update.post_reboot_stabilization_s)

            self._publish_software_update_stage(
                stage="RELOGIN_AFTER_UPDATE",
                progress_percent=85,
                message="Reingresando con credenciales normales para validar la nueva versión.",
            )

            refreshed_version, refreshed_base_info = self._safe_extract_software_version(
                navigator=navigator,
                target_ip=target_ip,
                retries=5,
                delay_s=8.0,
            )

            update_applied = self._software_update_evaluator.is_target_applied(
                current_version=refreshed_version,
                target_version=firmware.target_version,
            )

            if update_applied:
                step = self._build_software_update_pass_result(
                    decision=decision,
                    firmware=firmware,
                    model_name=model_name,
                    refreshed_version=refreshed_version,
                )
                self._publish_software_update_stage(
                    stage="COMPLETED",
                    progress_percent=100,
                    message="Actualización de software completada correctamente.",
                    visual_state="PASS",
                    extra_payload=step.details,
                )
                log_both(
                    self._logger,
                    logging.INFO,
                    "Resultado SOFTWARE_UPDATE %s: PASS | %s",
                    self._worker_id,
                    step.details,
                )
                return step, refreshed_base_info

            step = self._adapter.build_test_result(
                name="software_update",
                status="FAIL",
                details={
                    "update_required": True,
                    "completed": False,
                    "previous_version": decision.current_version,
                    "current_version": refreshed_version,
                    "target_version": firmware.target_version,
                    "firmware_path": str(firmware.firmware_path),
                    "firmware_filename": firmware.filename,
                    "model_name": model_name,
                    "model_key": firmware.model_key,
                    "reason": "El equipo volvió, pero la versión no coincide con la versión objetivo.",
                },
            )
            self._publish_software_update_stage(
                stage="FAIL_VERSION_VALIDATION",
                progress_percent=100,
                message="El equipo volvió, pero la versión final no coincide con la esperada.",
                visual_state="FAIL",
                extra_payload=step.details,
            )
            log_both(
                self._logger,
                logging.ERROR,
                "Resultado SOFTWARE_UPDATE %s: FAIL | %s",
                self._worker_id,
                step.details,
            )
            return step, refreshed_base_info

        except Exception as exc:
            log_both(
                self._logger,
                logging.WARNING,
                "Excepción durante software update para %s. Se intentará validación final de respaldo: %s",
                self._worker_id,
                exc,
            )

            try:
                fallback_version, fallback_base_info = self._safe_extract_software_version(
                    navigator=navigator,
                    target_ip=target_ip,
                    retries=3,
                    delay_s=10.0,
                )

                if "firmware" in locals() and self._software_update_evaluator.is_target_applied(
                    current_version=fallback_version,
                    target_version=firmware.target_version,
                ):
                    step = self._build_software_update_pass_result(
                        decision=decision,
                        firmware=firmware,
                        model_name=model_name,
                        refreshed_version=fallback_version,
                    )
                    step.details["warning"] = "La verificación inicial falló, pero la validación de respaldo confirmó la versión objetivo."

                    self._publish_software_update_stage(
                        stage="COMPLETED_WITH_FALLBACK_VERIFICATION",
                        progress_percent=100,
                        message="La actualización se confirmó mediante validación de respaldo.",
                        visual_state="PASS",
                        extra_payload=step.details,
                    )
                    log_both(
                        self._logger,
                        logging.INFO,
                        "Resultado SOFTWARE_UPDATE %s: PASS | %s",
                        self._worker_id,
                        step.details,
                    )
                    return step, fallback_base_info

            except Exception as fallback_exc:
                log_both(
                    self._logger,
                    logging.WARNING,
                    "Validación de respaldo también falló para %s: %s",
                    self._worker_id,
                    fallback_exc,
                )

            step = self._adapter.build_test_result(
                name="software_update",
                status="FAIL",
                details={
                    "update_required": True,
                    "current_version": current_version,
                    "model_name": model_name,
                    "reason": "Excepción no controlada durante la actualización de software.",
                    "error": str(exc),
                },
            )
            self._publish_software_update_stage(
                stage="FAIL_EXCEPTION",
                progress_percent=100,
                message="Ocurrió una excepción durante la actualización de software.",
                visual_state="FAIL",
                extra_payload=step.details,
            )
            log_both(
                self._logger,
                logging.ERROR,
                "Resultado SOFTWARE_UPDATE %s: FAIL | %s",
                self._worker_id,
                step.details,
            )
            return step, base_info
        finally:
            self._supervisor.publish_global_visual_mode(
                worker_id=self._worker_id,
                mode="EXPECTED_UPDATE",
                active=False,
            )

    def _wait_until_ping_back(
        self,
        *,
        target_ip: str,
        timeout_s: int,
        poll_interval_s: float = 2.0,
    ) -> bool:
        deadline = time.time() + timeout_s

        while time.time() < deadline:
            if self._ping_service.ping(target_ip):
                return True
            time.sleep(poll_interval_s)

        return False

    def _is_host_reachable(self, target_ip: str) -> bool:
        return self._ping_service.ping(target_ip)
    
    def _safe_extract_software_version(
        self,
        *,
        navigator: FiberhomeNavigator,
        target_ip: str,
        retries: int = 5,
        delay_s: float = 8.0,
    ) -> tuple[str, dict[str, Any]]:
        last_error: Exception | None = None

        for attempt in range(1, retries + 1):
            try:
                log_both(
                    self._logger,
                    logging.INFO,
                    "Verificación post-update %s/%s para %s.",
                    attempt,
                    retries,
                    self._worker_id,
                )

                navigator.open_root(target_ip)
                navigator.login("root", "admin")

                refreshed_base_info = navigator.extract_base_info() or {}
                refreshed_version = (
                    refreshed_base_info.get("software_version")
                    or (refreshed_base_info.get("raw_data") or {}).get("SoftwareVersion")
                    or ""
                )

                if refreshed_version:
                    return refreshed_version, refreshed_base_info

            except (TimeoutException, WebDriverException, Exception) as exc:
                last_error = exc
                log_both(
                    self._logger,
                    logging.WARNING,
                    "Intento de verificación post-update %s/%s fallido para %s: %s",
                    attempt,
                    retries,
                    self._worker_id,
                    exc,
                )

            if attempt < retries:
                time.sleep(delay_s)

        if last_error:
            raise last_error

        return "", {}

    def _build_software_update_pass_result(
        self,
        *,
        decision,
        firmware,
        model_name: str,
        refreshed_version: str,
    ):
        return self._adapter.build_test_result(
            name="software_update",
            status="PASS",
            details={
                "update_required": True,
                "completed": True,
                "previous_version": decision.current_version,
                "current_version": refreshed_version,
                "target_version": firmware.target_version,
                "firmware_path": str(firmware.firmware_path),
                "firmware_filename": firmware.filename,
                "model_name": model_name,
                "model_key": firmware.model_key,
            },
        )