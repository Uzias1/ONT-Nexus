from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from app.application.dto.execution_test_request import ExecutionTestRequest
from app.infrastructure.config.settings import Settings
from app.infrastructure.logging.logger import get_logger, log_both, log_console
from app.infrastructure.selenium.driver_factory import DriverFactory
from app.infrastructure.selenium.selenium_session import SeleniumSession
from app.infrastructure.vendors.base.test_runner_base import TestRunnerBase
from app.infrastructure.vendors.fiberhome.fiberhome_adapter import (
    FiberhomeAdapter,
    FiberhomeExecutionResult,
)
from app.infrastructure.vendors.fiberhome.fiberhome_navigator import FiberhomeNavigator

if TYPE_CHECKING:
    from app.workers.supervisor import Supervisor


class FiberhomeTestRunner(TestRunnerBase):
    """
    Runner real para FiberHome.

    Objetivo actual:
    - login real
    - extraer SN y MAC mínimos
    - ejecutar factory_reset
    - ejecutar usb (vía base_info)
    """

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

            # ========= Identidad mínima =========
            base_info = navigator.extract_base_info() or {}
            serial_number = (
                base_info.get("gponsn")
                or base_info.get("SerialNumber")
                or base_info.get("serial_number")
            )

            result.identity = self._adapter.build_identity(
                serial_number=serial_number,
                mac_address=snapshot.get("device_mac"),
                ip=str(target_ip),
            )

            # Reflejar identidad mínima al contexto vivo
            context = self._supervisor.get_worker_context(self._worker_id)
            if context is not None:
                context.bind_device(
                    device_sn=result.identity.serial_number,
                    device_mac=result.identity.mac_address,
                    vendor="FIBERHOME",
                )

            # ========= Pruebas habilitadas =========
            if request.is_test_enabled("factory_reset"):
                # Publicar para la UI
                self._supervisor.publish_global_visual_mode(
                    worker_id=self._worker_id,
                    mode="EXCEPTED_RESET",
                    active=True,
                )
                result.tests["factory_reset"] = self._run_factory_reset(navigator)
                self._supervisor.publish_global_visual_mode(
                    worker_id=self._worker_id,
                    mode="EXCEPTED_RESET",
                    active=False,
                )

            if request.is_test_enabled("usb"):
                # Después del reset, normalmente hace falta relogin
                if "factory_reset" in result.tests and result.tests["factory_reset"].status == "PASS":
                    navigator.open_root(str(target_ip))
                    navigator.login("root", "admin")
                # Evento
                self._supervisor.publish_test_indicator(
                    worker_id=self._worker_id,
                    test_name="USB",
                    visual_state="RUNNING",
                )
                result.tests["usb"] = self._run_usb(navigator)

            return result

        finally:
            session.quit()

    # ==========================================================
    # Factory Reset
    # ==========================================================
    def _run_factory_reset(self, navigator: FiberhomeNavigator):
        self._supervisor.update_worker_phase(
            worker_id=self._worker_id,
            phase="FACTORY_RESET",
            status="TESTING",
        )

        self._supervisor.publish_global_visual_mode(
            worker_id=self._worker_id,
            mode="EXPECTED_RESET",
            active=True,
        )

        # El monitor debe considerar que la caída es esperada.
        self._supervisor.set_worker_connected(
            worker_id=self._worker_id,
            connected=True,
            disconnect_expected=True,
            connection_reason="factory_reset_started",
        )

        navigator.go_to_factory_reset()
        navigator.trigger_factory_reset()

        disconnected = self._wait_until_connected_state(False, timeout_s=90)
        reconnected = self._wait_until_connected_state(True, timeout_s=240)

        self._supervisor.publish_global_visual_mode(
            worker_id=self._worker_id,
            mode="EXPECTED_RESET",
            active=False,
        )

        details = {
            "disconnect_detected": disconnected,
            "reconnected": reconnected,
        }

        if not disconnected:
            result = self._adapter.build_test_result(
                name="factory_reset",
                status="FAIL",
                details={**details, "reason": "No se detectó desconexión tras factory reset."},
            )
            log_both(
                self._logger,
                logging.ERROR,
                "Resultado FACTORY_RESET %s: %s",
                self._worker_id,
                result.details,
            )
            return result

        if not reconnected:
            result = self._adapter.build_test_result(
                name="factory_reset",
                status="FAIL",
                details={**details, "reason": "No se detectó reconexión tras factory reset."},
            )
            log_both(
                self._logger,
                logging.ERROR,
                "Resultado FACTORY_RESET %s: %s",
                self._worker_id,
                result.details,
            )
            return result

        self._supervisor.publish_test_indicator(
            worker_id=self._worker_id,
            test_name="FACTORY_RESET",
            visual_state="COMPLETED",
        )

        result = self._adapter.build_test_result(
            name="factory_reset",
            status="PASS",
            details=details,
        )

        log_both(
            self._logger,
            logging.INFO,
            "Resultado FACTORY_RESET %s: PASS | %s",
            self._worker_id,
            details,
        )
        return result

    # ==========================================================
    # USB
    # ==========================================================
    def _run_usb(self, navigator: FiberhomeNavigator):
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

        base_info = navigator.extract_base_info() or {}
        usb_ports = base_info.get("usb_port_num")
        usb_status = base_info.get("usb_status")

        try:
            usb_ports = int(usb_ports) if usb_ports is not None else 0
        except Exception:
            usb_ports = 0

        details = {
            "usb_ports": usb_ports,
            "usb_status": usb_status,
        }

        if usb_ports > 0:
            self._supervisor.publish_test_indicator(
                worker_id=self._worker_id,
                test_name="USB",
                visual_state="COMPLETED",
            )

            result = self._adapter.build_test_result(
                name="usb",
                status="PASS",
                details=details,
            )

            log_both(
                self._logger,
                logging.INFO,
                "Resultado USB %s: PASS | %s",
                self._worker_id,
                details,
            )
            return result

        self._supervisor.publish_test_indicator(
            worker_id=self._worker_id,
            test_name="USB",
            visual_state="FAIL",
        )

        result = self._adapter.build_test_result(
            name="usb",
            status="FAIL",
            details={**details, "reason": "El equipo no reporta puertos USB válidos en base_info."},
        )

        log_both(
            self._logger,
            logging.ERROR,
            "Resultado USB %s: FAIL | %s",
            self._worker_id,
            result.details,
        )
        return result
    
    # ==========================================================
    # Helpers
    # ==========================================================
    def _wait_until_connected_state(self, expected_connected: bool, timeout_s: int) -> bool:
        start = time.time()

        while time.time() - start < timeout_s:
            snapshot = self._supervisor.get_worker_snapshot(self._worker_id)
            if snapshot is not None and bool(snapshot.get("connected", False)) == expected_connected:
                return True
            time.sleep(2)

        return False