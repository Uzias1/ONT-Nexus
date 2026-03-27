from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING

from app.application.dto.execution_test_request import ExecutionTestRequest
from app.infrastructure.config.settings import Settings
from app.infrastructure.logging.logger import get_logger, log_both, log_console
from app.infrastructure.vendors.fiberhome.fiberhome_test_runner import FiberhomeTestRunner
from app.infrastructure.network.ping_service import PingService

if TYPE_CHECKING:
    from app.workers.supervisor import Supervisor


class PortWorker:
    """
    Worker de ejecución para una estación lógica específica.

    Ejecuta el plan de pruebas habilitado en ExecutionTestRequest.
    """

    def __init__(
        self,
        *,
        settings: Settings,
        supervisor: Supervisor,
        worker_id: str,
        ping_service: PingService,
        request: ExecutionTestRequest,
    ) -> None:
        self._settings = settings
        self._supervisor = supervisor
        self._worker_id = worker_id
        self._ping_service = ping_service
        self._request = request
        self._logger = get_logger(f"{self.__class__.__name__}.{worker_id}")

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = False
        self._lock = threading.RLock()

    # ==========================================================
    # Ciclo de vida
    # ==========================================================
    def start(self) -> None:
        with self._lock:
            if self._running:
                log_console(
                    self._logger,
                    logging.INFO,
                    "PortWorker %s ya estaba en ejecución.",
                    self._worker_id,
                )
                return

            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run,
                name=f"PortWorkerThread-{self._worker_id}",
                daemon=True,
            )
            self._thread.start()
            self._running = True

            log_both(
                self._logger,
                logging.INFO,
                "PortWorker %s iniciado correctamente.",
                self._worker_id,
            )

    def stop(self) -> None:
        with self._lock:
            if not self._running:
                return

            self._stop_event.set()

            if self._thread is not None:
                self._thread.join(timeout=self._settings.workers.worker_join_timeout_s)

            self._running = False

            log_console(
                self._logger,
                logging.INFO,
                "PortWorker %s detenido.",
                self._worker_id,
            )

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    # ==========================================================
    # Ejecución principal
    # ==========================================================
    def _run(self) -> None:
        try:
            enabled_tests = self._request.enabled_tests()

            log_both(
                self._logger,
                logging.INFO,
                "Iniciando ejecución en %s. Pruebas: %s",
                self._worker_id,
                ", ".join(enabled_tests) if enabled_tests else "(ninguna)",
            )

            if not enabled_tests:
                self._supervisor.set_worker_error(
                    worker_id=self._worker_id,
                    message="La solicitud no contiene pruebas habilitadas.",
                    status="FAIL",
                    phase="ERROR",
                )
                return

            self._supervisor.update_worker_phase(
                worker_id=self._worker_id,
                phase="STARTING",
                status="TESTING",
            )

            vendor = (self._request.vendor or "").strip().upper()
            if vendor == "FIBERHOME":
                runner = FiberhomeTestRunner(
                    settings=self._settings,
                    supervisor=self._supervisor,
                    worker_id=self._worker_id,
                    ping_service=self._ping_service,
                )
                execution_result = runner.run(self._request)

                context = self._supervisor.get_worker_context(self._worker_id)
                if context is not None:
                    context.set_metadata(
                        "fiberhome_execution_result",
                        {
                            "identity": {
                                "serial_number": execution_result.identity.serial_number,
                                "mac_address": execution_result.identity.mac_address,
                            },
                            "tests": {
                                name: {
                                    "name": step.name,
                                    "status": step.status,
                                    "details": step.details,
                                }
                                for name, step in execution_result.tests.items()
                            },
                        },
                    )
            else:
                raise ValueError(f"Vendor no soportado aún: {vendor or '(vacío)'}")

            self._supervisor.complete_worker(
                worker_id=self._worker_id,
                status="PASS",
                phase="FINISHED",
            )

            log_both(
                self._logger,
                logging.INFO,
                "Ejecución completada correctamente en %s.",
                self._worker_id,
            )

        except Exception as exc:
            self._supervisor.set_worker_error(
                worker_id=self._worker_id,
                message=str(exc),
                status="FAIL",
                phase="ERROR",
            )

            log_both(
                self._logger,
                logging.ERROR,
                "Excepción no controlada en PortWorker %s.",
                self._worker_id,
                exc_info=True,
            )
        finally:
            with self._lock:
                self._running = False

    # ==========================================================
    # Dispatcher de pruebas
    # ==========================================================
    def _execute_test(self, test_name: str) -> None:
        dispatch = {
            "factory_reset": self._run_factory_reset,
            "software_update": self._run_software_update,
            "usb": self._run_usb,
            "fiber_tx": self._run_fiber_tx,
            "fiber_rx": self._run_fiber_rx,
            "wifi_2g": self._run_wifi_2g,
            "wifi_5g": self._run_wifi_5g,
        }

        handler = dispatch.get(test_name)
        if handler is None:
            raise ValueError(f"Prueba no soportada: {test_name}")

        handler()

    # ==========================================================
    # Implementaciones de pruebas (placeholders iniciales)
    # ==========================================================
    def _run_factory_reset(self) -> None:
        self._supervisor.update_worker_phase(
            worker_id=self._worker_id,
            phase="FACTORY_RESET",
            status="TESTING",
        )
        self._simulate_step("FACTORY_RESET")

    def _run_software_update(self) -> None:
        self._supervisor.update_worker_phase(
            worker_id=self._worker_id,
            phase="SOFTWARE_UPDATE",
            status="TESTING",
        )
        self._simulate_step("SOFTWARE_UPDATE")

    def _run_usb(self) -> None:
        self._supervisor.update_worker_phase(
            worker_id=self._worker_id,
            phase="USB",
            status="TESTING",
        )
        self._simulate_step("USB")

    def _run_fiber_tx(self) -> None:
        self._supervisor.update_worker_phase(
            worker_id=self._worker_id,
            phase="FIBER_TX",
            status="TESTING",
        )
        self._simulate_step("FIBER_TX")

    def _run_fiber_rx(self) -> None:
        self._supervisor.update_worker_phase(
            worker_id=self._worker_id,
            phase="FIBER_RX",
            status="TESTING",
        )
        self._simulate_step("FIBER_RX")

    def _run_wifi_2g(self) -> None:
        self._supervisor.update_worker_phase(
            worker_id=self._worker_id,
            phase="WIFI_2G",
            status="TESTING",
        )
        self._simulate_step("WIFI_2G")

    def _run_wifi_5g(self) -> None:
        self._supervisor.update_worker_phase(
            worker_id=self._worker_id,
            phase="WIFI_5G",
            status="TESTING",
        )
        self._simulate_step("WIFI_5G")

    # ==========================================================
    # Helpers
    # ==========================================================
    def _simulate_step(self, phase_name: str) -> None:
        """
        Simulación temporal del paso de prueba.

        Esto permite validar concurrencia, cambios de fase y flujo general
        sin depender todavía de Selenium o de hardware real.
        """
        log_console(
            self._logger,
            logging.INFO,
            "Ejecutando fase %s en %s...",
            phase_name,
            self._worker_id,
        )

        elapsed = 0.0
        step = 0.2
        simulated_duration_s = 1.0

        while elapsed < simulated_duration_s:
            if self._stop_event.is_set():
                raise RuntimeError(f"Ejecución cancelada durante {phase_name}.")
            time.sleep(step)
            elapsed += step