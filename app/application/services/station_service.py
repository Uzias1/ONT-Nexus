from __future__ import annotations

import logging
from typing import Any

from app.application.dto.execution_test_request import ExecutionTestRequest
from app.infrastructure.logging.logger import get_logger, log_both, log_console
from app.workers.supervisor import Supervisor


class StationService:
    """
    Servicio de aplicación para operar la estación de pruebas.

    Esta capa actúa como fachada entre la UI / main y el Supervisor.
    Así evitamos que la interfaz conozca detalles internos del backend.
    """

    def __init__(self, supervisor: Supervisor) -> None:
        self._supervisor = supervisor
        self._logger = get_logger(self.__class__.__name__)

    # ==========================================================
    # Ciclo de vida de la estación
    # ==========================================================
    def start_station(self) -> None:
        """
        Inicia la estación de pruebas.
        """
        if self._supervisor.is_running():
            log_console(self._logger, logging.INFO, "La estación ya estaba iniciada.")
            return

        self._supervisor.start()
        log_both(self._logger, logging.INFO, "La estación fue iniciada correctamente.")

    def stop_station(self) -> None:
        """
        Detiene la estación de pruebas.
        """
        if not self._supervisor.is_running():
            log_console(self._logger, logging.INFO, "La estación ya estaba detenida.")
            return

        self._supervisor.stop()
        log_both(self._logger, logging.INFO, "La estación fue detenida correctamente.")

    def is_station_running(self) -> bool:
        """
        Indica si la estación está corriendo.
        """
        return self._supervisor.is_running()

    # ==========================================================
    # Consultas de estado
    # ==========================================================
    def get_station_snapshot(self) -> list[dict[str, Any]]:
        """
        Devuelve el snapshot completo de todas las instancias/workers.
        """
        return self._supervisor.get_all_snapshots()

    def get_available_worker_ids(self) -> list[str]:
        """
        Devuelve la lista de workers disponibles.
        """
        return self._supervisor.get_available_worker_ids()

    def get_worker_snapshot(self, worker_id: str) -> dict[str, Any] | None:
        """
        Devuelve el snapshot de un worker específico.
        """
        context = self._supervisor.get_worker_context(worker_id)
        if context is None:
            return None

        return context.snapshot()

    # ==========================================================
    # Ejecución de pruebas
    # ==========================================================
    def start_execution(self, request_data: dict[str, Any]) -> bool:
        """
        Recibe un diccionario crudo desde la UI, lo normaliza a ExecutionTestRequest
        y prepara la ejecución sobre el worker solicitado.

        Por ahora:
        - valida request
        - valida existencia del worker
        - valida que el worker esté libre
        - valida que haya al menos una prueba habilitada
        - asigna el worker en estado inicial

        Más adelante:
        - creará el PortWorker real
        - disparará las pruebas habilitadas
        """
        try:
            request = ExecutionTestRequest.from_dict(request_data)
        except (TypeError, ValueError) as exc:
            log_console(
                self._logger,
                logging.WARNING,
                "Solicitud de ejecución inválida: %s",
                exc,
            )
            return False

        return self.start_execution_request(request)

    def start_execution_request(self, request: ExecutionTestRequest) -> bool:
        """
        Inicia una ejecución a partir de un DTO ya validado.
        """
        worker_snapshot = self.get_worker_snapshot(request.worker_id)
        if worker_snapshot is None:
            log_console(
                self._logger,
                logging.WARNING,
                "No se encontró el worker solicitado: %s",
                request.worker_id,
            )
            return False

        if not request.has_any_enabled_test():
            log_console(
                self._logger,
                logging.WARNING,
                "La solicitud para %s no contiene pruebas habilitadas.",
                request.worker_id,
            )
            return False

        current_state = str(worker_snapshot.get("state", ""))
        current_phase = str(worker_snapshot.get("phase", ""))
        connected = bool(worker_snapshot.get("connected", False))

        if current_state != "IDLE" or current_phase != "WAITING":
            log_console(
                self._logger,
                logging.WARNING,
                "El worker %s no está libre. state=%s phase=%s",
                request.worker_id,
                current_state,
                current_phase,
            )
            return False

        if not connected:
            log_console(
                self._logger,
                logging.WARNING,
                "El worker %s no está conectado. No se puede iniciar ejecución.",
                request.worker_id,
            )
            return False

        first_phase = self._resolve_initial_phase(request)

        assigned = self._supervisor.assign_worker(
            worker_id=request.worker_id,
            device_ip=worker_snapshot.get("expected_ip"),
            mac=request.device_mac,
            status="USADO",
            phase=first_phase,
        )

        if not assigned:
            log_console(
                self._logger,
                logging.WARNING,
                "No se pudo asignar el worker %s para ejecución.",
                request.worker_id,
            )
            return False

        context = self._supervisor.get_worker_context(request.worker_id)
        if context is not None:
            if request.device_sn is not None:
                context.bind_device(device_sn=request.device_sn)
            if request.vendor is not None:
                context.bind_device(vendor=request.vendor)
            if request.model is not None:
                context.bind_device(model=request.model)

            context.set_metadata("execution_tests", request.tests)
            context.set_metadata("enabled_tests", request.enabled_tests())
            context.set_metadata("request_payload", request.to_dict())

            # Re-publicamos el estado actualizado con metadata/identidad adicional.
            self._supervisor.update_worker_phase(
                worker_id=request.worker_id,
                phase=first_phase,
                status="USADO",
            )

            started = self._supervisor.start_port_worker(request)
            if not started:
                self._supervisor.release_worker(request.worker_id)

                log_console(
                    self._logger,
                    logging.WARNING,
                    "No se pudo arrancar el PortWorker para %s.",
                    request.worker_id,
                )
                return False

            log_both(
                self._logger,
                logging.INFO,
                "Solicitud aceptada para %s. Pruebas habilitadas: %s",
                request.worker_id,
                ", ".join(request.enabled_tests()),
            )

            return True

    # ==========================================================
    # Operaciones sobre instancias/workers
    # ==========================================================
    def release_worker(self, worker_id: str) -> bool:
        """
        Libera un worker y lo regresa a estado base.
        """
        result = self._supervisor.release_worker(worker_id)

        if result:
            log_console(
                self._logger,
                logging.INFO,
                "StationService liberó worker=%s",
                worker_id,
            )
        else:
            log_console(
                self._logger,
                logging.WARNING,
                "StationService no pudo liberar worker=%s",
                worker_id,
            )

        return result

    def update_worker_network(
        self,
        *,
        worker_id: str,
        device_ip: str | None = None,
        mac: str | None = None,
    ) -> bool:
        """
        Actualiza datos de red de un worker.
        """
        return self._supervisor.update_worker_network(
            worker_id=worker_id,
            device_ip=device_ip,
            mac=mac,
        )

    def update_worker_phase(
        self,
        *,
        worker_id: str,
        phase: str,
        status: str | None = None,
    ) -> bool:
        """
        Actualiza la fase actual de una instancia.
        """
        return self._supervisor.update_worker_phase(
            worker_id=worker_id,
            phase=phase,
            status=status,
        )

    def set_worker_connected(
        self,
        *,
        worker_id: str,
        connected: bool,
    ) -> bool:
        """
        Actualiza la conectividad de una instancia.
        """
        return self._supervisor.set_worker_connected(
            worker_id=worker_id,
            connected=connected,
        )

    def set_worker_error(
        self,
        *,
        worker_id: str,
        message: str,
        status: str = "FAIL",
        phase: str = "ERROR",
    ) -> bool:
        """
        Marca error en una instancia.
        """
        return self._supervisor.set_worker_error(
            worker_id=worker_id,
            message=message,
            status=status,
            phase=phase,
        )

    def complete_worker(
        self,
        *,
        worker_id: str,
        status: str = "PASS",
        phase: str = "FINISHED",
    ) -> bool:
        """
        Marca una instancia como completada.
        """
        return self._supervisor.complete_worker(
            worker_id=worker_id,
            status=status,
            phase=phase,
        )

    # ==========================================================
    # Helpers internos
    # ==========================================================
    @staticmethod
    def _resolve_initial_phase(request: ExecutionTestRequest) -> str:
        """
        Determina la primera fase visible a partir del plan de pruebas.

        Por ahora es simplemente la primera prueba habilitada en el orden
        definido por el DTO.
        """
        enabled = request.enabled_tests()
        if not enabled:
            return "WAITING"

        first_test = enabled[0]

        mapping = {
            "factory_reset": "FACTORY_RESET",
            "software_update": "SOFTWARE_UPDATE",
            "usb": "USB",
            "fiber_tx": "FIBER_TX",
            "fiber_rx": "FIBER_RX",
            "wifi_2g": "WIFI_2G",
            "wifi_5g": "WIFI_5G",
        }

        return mapping.get(first_test, "WAITING")