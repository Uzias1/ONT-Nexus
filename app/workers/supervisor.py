from __future__ import annotations

import logging
import threading
import time
from typing import Any

from app.application.dto.execution_test_request import ExecutionTestRequest
from app.application.event_bus.bus import EventBus
from app.infrastructure.config.settings import Settings
from app.infrastructure.logging.logger import get_logger, log_both, log_console
from app.infrastructure.network.ping_service import PingService
from app.workers.port_worker import PortWorker
from app.workers.slot_connection_monitor import SlotConnectionMonitor
from app.workers.worker_context import WorkerContext
from app.infrastructure.network.arp_scanner import ArpScanner
from contextlib import contextmanager
from app.shared.constants import build_default_execution_request

from app.application.event_bus.events import (
    TestIndicatorChangedEvent,
    WorkerGlobalVisualModeEvent,
    WorkerStateChangedEvent,
)

class Supervisor:
    """
    Coordinador central de la estación de pruebas.
    """

    def __init__(self, settings: Settings, event_bus: EventBus) -> None:
        self._settings = settings
        self._event_bus = event_bus
        self._logger = get_logger(self.__class__.__name__)

        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._management_thread: threading.Thread | None = None
        self._running = False

        self._worker_contexts: dict[str, WorkerContext] = {}
        self._active_port_workers: dict[str, PortWorker] = {}
        self._slot_monitors: dict[str, SlotConnectionMonitor] = {}
        self._auto_execution_started: dict[str, bool] = {}
        self._disconnect_cleanup_done: dict[str, bool] = {}

        self._heartbeat_interval_s = settings.monitor.heartbeat_interval_s
        self._wifi_scan_lock = threading.Lock()

        self._ping_service = PingService(timeout_ms=settings.monitor.ping_timeout_ms)
        self._arp_scanner = ArpScanner()

    @staticmethod
    def _resolve_initial_phase_from_request(request: ExecutionTestRequest) -> str:
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
    # ==========================================================
    # Ciclo de vida
    # ==========================================================
    def start(self) -> None:
        with self._lock:
            if self._running:
                log_console(self._logger, logging.INFO, "Supervisor ya estaba en ejecución.")
                return

            self._stop_event.clear()
            self._initialize_worker_contexts()
            self._initialize_slot_monitors()

            self._management_thread = threading.Thread(
                target=self._run_management_loop,
                name="SupervisorThread",
                daemon=True,
            )
            self._management_thread.start()

            self._start_slot_monitors()

            self._running = True
            log_both(self._logger, logging.INFO, "Supervisor iniciado correctamente.")

    def stop(self) -> None:
        with self._lock:
            if not self._running:
                log_console(self._logger, logging.INFO, "Supervisor ya estaba detenido.")
                return

            self._stop_event.set()
            self._stop_slot_monitors()

            for worker_id in list(self._active_port_workers.keys()):
                self.stop_port_worker(worker_id, release=False)

            if self._management_thread is not None:
                self._management_thread.join(
                    timeout=self._settings.workers.worker_join_timeout_s
                )

            self._running = False
            log_both(self._logger, logging.INFO, "Supervisor detenido correctamente.")

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    # ==========================================================
    # Inicialización
    # ==========================================================
    def _initialize_worker_contexts(self) -> None:
        self._worker_contexts.clear()
        self._auto_execution_started.clear()
        self._disconnect_cleanup_done.clear()
        for station in self._settings.station_map:
            context = WorkerContext(
                worker_id=station.worker_id,
                port_index=station.port_index,
                expected_ip=station.expected_ip,
            )
            
            self._worker_contexts[station.worker_id] = context
            self._auto_execution_started[station.worker_id] = False
            self._disconnect_cleanup_done[station.worker_id] = False
            self._publish_worker_state(context)

        log_console(
            self._logger,
            logging.INFO,
            "Contexts inicializados desde station_map: %s instancia(s).",
            len(self._worker_contexts),
        )

    def _initialize_slot_monitors(self) -> None:
        self._slot_monitors.clear()

        for worker_id in self._worker_contexts:
            self._slot_monitors[worker_id] = SlotConnectionMonitor(
                settings=self._settings,
                supervisor=self,
                ping_service=self._ping_service,
                arp_scanner=self._arp_scanner,
                worker_id=worker_id,
            )

        log_console(
            self._logger,
            logging.INFO,
            "Monitores por slot inicializados: %s.",
            len(self._slot_monitors),
        )

    def _start_slot_monitors(self) -> None:
        for monitor in self._slot_monitors.values():
            monitor.start()

    def _stop_slot_monitors(self) -> None:
        for monitor in self._slot_monitors.values():
            monitor.stop()

    # ==========================================================
    # Hilo de gestión
    # ==========================================================
    def _run_management_loop(self) -> None:
        try:
            log_console(self._logger, logging.INFO, "Management loop iniciado.")

            while not self._stop_event.is_set():
                self._cleanup_finished_port_workers()
                time.sleep(self._heartbeat_interval_s)

            log_console(self._logger, logging.INFO, "Management loop finalizado.")
        except Exception:
            log_both(
                self._logger,
                logging.ERROR,
                "Excepción no controlada en el management loop.",
                exc_info=True,
            )
            raise

    # ==========================================================
    # Gestión de PortWorkers
    # ==========================================================
    def start_port_worker(self, request: ExecutionTestRequest) -> bool:
        with self._lock:
            worker_id = request.worker_id

            if worker_id in self._active_port_workers:
                active_worker = self._active_port_workers[worker_id]
                if active_worker.is_running():
                    log_console(
                        self._logger,
                        logging.WARNING,
                        "Ya existe un PortWorker activo para %s.",
                        worker_id,
                    )
                    return False

            port_worker = PortWorker(
                settings=self._settings,
                supervisor=self,
                worker_id=worker_id,
                ping_service=self._ping_service,
                request=request,
            )

            self._active_port_workers[worker_id] = port_worker
            port_worker.start()

            log_both(
                self._logger,
                logging.INFO,
                "PortWorker registrado y arrancado para %s.",
                worker_id,
            )
            return True

    def stop_port_worker(self, worker_id: str, *, release: bool = True) -> bool:
        with self._lock:
            port_worker = self._active_port_workers.get(worker_id)
            if port_worker is None:
                return False

            port_worker.stop()
            self._active_port_workers.pop(worker_id, None)

            if release:
                self.release_worker(worker_id)

            log_console(
                self._logger,
                logging.INFO,
                "PortWorker detenido para %s.",
                worker_id,
            )
            return True

    def has_active_port_worker(self, worker_id: str) -> bool:
        with self._lock:
            port_worker = self._active_port_workers.get(worker_id)
            if port_worker is None:
                return False
            return port_worker.is_running()

    def _cleanup_finished_port_workers(self) -> None:
        with self._lock:
            finished_worker_ids: list[str] = []

            for worker_id, port_worker in self._active_port_workers.items():
                if not port_worker.is_running():
                    finished_worker_ids.append(worker_id)

            for worker_id in finished_worker_ids:
                self._active_port_workers.pop(worker_id, None)
                log_console(
                    self._logger,
                    logging.INFO,
                    "PortWorker finalizado limpiado del registro: %s",
                    worker_id,
                )

    # ==========================================================
    # Consultas de estado
    # ==========================================================
    def get_worker_context(self, worker_id: str) -> WorkerContext | None:
        with self._lock:
            return self._worker_contexts.get(worker_id)

    def get_worker_snapshot(self, worker_id: str) -> dict[str, Any] | None:
        with self._lock:
            context = self._worker_contexts.get(worker_id)
            if context is None:
                return None
            return context.snapshot()

    def get_all_snapshots(self) -> list[dict[str, Any]]:
        with self._lock:
            return [context.snapshot() for context in self._worker_contexts.values()]

    def get_available_worker_ids(self) -> list[str]:
        with self._lock:
            available: list[str] = []

            for worker_id, context in self._worker_contexts.items():
                snapshot = context.snapshot()
                if (
                    snapshot["state"] == "IDLE"
                    and snapshot["phase"] == "WAITING"
                    and worker_id not in self._active_port_workers
                ):
                    available.append(worker_id)

            return available

    # ==========================================================
    # Operaciones sobre workers/contextos
    # ==========================================================
    def assign_worker(
        self,
        *,
        worker_id: str,
        device_ip: str | None = None,
        mac: str | None = None,
        status: str = "USADO",
        phase: str = "WAITING_DEVICE",
    ) -> bool:
        with self._lock:
            context = self._worker_contexts.get(worker_id)
            if context is None:
                log_console(
                    self._logger,
                    logging.WARNING,
                    "No se pudo asignar worker inexistente: %s",
                    worker_id,
                )
                return False

            context.bind_device(device_ip=device_ip, device_mac=mac)
            context.set_state_and_phase(state=status, phase=phase)

            self._publish_worker_state(context)

            log_console(
                self._logger,
                logging.INFO,
                "Worker %s asignado. expected_ip=%s device_ip=%s mac=%s status=%s phase=%s",
                worker_id,
                context.expected_ip,
                device_ip,
                mac,
                status,
                phase,
            )
            return True

    def release_worker(self, worker_id: str) -> bool:
        with self._lock:
            context = self._worker_contexts.get(worker_id)
            if context is None:
                log_console(
                    self._logger,
                    logging.WARNING,
                    "No se pudo liberar worker inexistente: %s",
                    worker_id,
                )
                return False

            self._reset_context(context)
            self._publish_worker_state(self._worker_contexts[worker_id])

            log_console(self._logger, logging.INFO, "Worker %s liberado.", worker_id)
            return True

    def update_worker_network(
        self,
        *,
        worker_id: str,
        device_ip: str | None = None,
        mac: str | None = None,
    ) -> bool:
        with self._lock:
            context = self._worker_contexts.get(worker_id)
            if context is None:
                return False

            if device_ip is None and mac is None:
                context.clear_network_identity()
            else:
                context.bind_device(device_ip=device_ip, device_mac=mac)

            self._publish_worker_state(context)
            return True

    def update_worker_phase(
        self,
        *,
        worker_id: str,
        phase: str,
        status: str | None = None,
    ) -> bool:
        with self._lock:
            context = self._worker_contexts.get(worker_id)
            if context is None:
                return False

            if status is None:
                context.set_phase(phase)
            else:
                context.set_state_and_phase(state=status, phase=phase)

            self._publish_worker_state(context)
            return True

    def set_worker_connected(
        self,
        *,
        worker_id: str,
        connected: bool,
        disconnect_expected: bool | None = None,
        connection_reason: str | None = None,
    ) -> bool:
        with self._lock:
            context = self._worker_contexts.get(worker_id)
            if context is None:
                return False

            if connected:
                context.mark_connected()
                self._disconnect_cleanup_done[worker_id] = False
            else:
                context.mark_disconnected()
                self._auto_execution_started[worker_id] = False

            if disconnect_expected is not None:
                context.set_disconnect_expected(disconnect_expected)

            if connection_reason is not None:
                context.set_metadata("connection_reason", connection_reason)

            self._publish_worker_state(context)

        return True
    
    def set_worker_error(
        self,
        *,
        worker_id: str,
        message: str,
        status: str = "FAIL",
        phase: str = "ERROR",
    ) -> bool:
        with self._lock:
            context = self._worker_contexts.get(worker_id)
            if context is None:
                return False

            context.set_error(message=message, state=status, phase=phase)
            self._publish_worker_state(context)

            log_both(
                self._logger,
                logging.ERROR,
                "Worker %s marcado con error: %s",
                worker_id,
                message,
            )
            return True

    def complete_worker(
        self,
        *,
        worker_id: str,
        status: str = "PASS",
        phase: str = "FINISHED",
    ) -> bool:
        with self._lock:
            context = self._worker_contexts.get(worker_id)
            if context is None:
                return False

            context.mark_finished(state=status, phase=phase)
            self._publish_worker_state(context)

            log_console(
                self._logger,
                logging.INFO,
                "Worker %s completado. status=%s phase=%s",
                worker_id,
                status,
                phase,
            )
            return True
        
    @contextmanager
    def wifi_scan_guard(self, worker_id: str):
        log_both(
            self._logger,
            logging.INFO,
            "Worker %s esperando lock global de WiFi...",
            worker_id,
        )

        with self._wifi_scan_lock:
            log_both(
                self._logger,
                logging.INFO,
                "Worker %s obtuvo lock global de WiFi.",
                worker_id,
            )
            try:
                yield
            finally:
                log_both(
                    self._logger,
                    logging.INFO,
                    "Worker %s liberó lock global de WiFi.",
                    worker_id,
                )
    # ==========================================================
    # Helpers internos
    # ==========================================================
    def mark_disconnect_cleanup_pending(self, worker_id: str) -> None:
        with self._lock:
            self._disconnect_cleanup_done[worker_id] = False

    def mark_disconnect_cleanup_done(self, worker_id: str) -> None:
        with self._lock:
            self._disconnect_cleanup_done[worker_id] = True

    def _reset_worker_after_disconnect_if_safe(self, worker_id: str) -> None:
        context = self._worker_contexts.get(worker_id)
        if context is None:
            return

        active_worker = self._active_port_workers.get(worker_id)
        if active_worker is not None and active_worker.is_running():
            log_console(
                self._logger,
                logging.INFO,
                "Worker %s sigue con PortWorker activo; no se reinicia aún.",
                worker_id,
            )
            return

        self._auto_execution_started[worker_id] = False

        self._reset_context(context)
        self._publish_worker_state(self._worker_contexts[worker_id])

        self.reset_test_indicators(worker_id)

        log_both(
            self._logger,
            logging.INFO,
            "Worker %s reiniciado a estado base tras desconexión física.",
            worker_id,
        )

    def _reset_context(self, context: WorkerContext) -> None:
        port_index = context.port_index
        worker_id = context.worker_id
        expected_ip = context.expected_ip

        new_context = WorkerContext(
            worker_id=worker_id,
            port_index=port_index,
            expected_ip=expected_ip,
        )
        self._worker_contexts[worker_id] = new_context

    def _publish_worker_state(self, context: WorkerContext) -> None:
        snapshot = context.snapshot()

        event = WorkerStateChangedEvent(
            worker_id=snapshot["worker_id"],
            ip=snapshot["expected_ip"],
            status=snapshot["state"],
            mac=snapshot["device_mac"],
            phase=snapshot["phase"],
            extra_payload={
                "port_index": snapshot["port_index"],
                "expected_ip": snapshot["expected_ip"],
                "device_ip": snapshot["device_ip"],
                "connected": snapshot["connected"],
                "disconnect_expected": snapshot["disconnect_expected"],
                "connection_reason": snapshot["metadata"].get("connection_reason"),
                "device_sn": snapshot["device_sn"],
                "vendor": snapshot["vendor"],
                "model": snapshot["model"],
                "error_message": snapshot["error_message"],
                "updated_at": snapshot["updated_at"],
            },
        )

        self._event_bus.publish(event)

    def handle_physical_disconnect(self, worker_id: str) -> None:
        with self._lock:
            # Si ya limpiamos este ciclo de desconexión, no repetir
            if self._disconnect_cleanup_done.get(worker_id, False):
                return

            active_worker = self._active_port_workers.get(worker_id)
            if active_worker is not None and active_worker.is_running():
                log_console(
                    self._logger,
                    logging.INFO,
                    "Worker %s desconectado, pero aún tiene PortWorker activo. No se libera todavía.",
                    worker_id,
                )
                return

            context = self._worker_contexts.get(worker_id)
            if context is None:
                return

            # Si ya está en estado base y desconectado, no limpiar otra vez
            snapshot = context.snapshot()
            if (
                snapshot.get("state") == "IDLE"
                and snapshot.get("phase") == "WAITING"
                and not snapshot.get("connected", False)
            ):
                self._disconnect_cleanup_done[worker_id] = True
                return

            self._auto_execution_started[worker_id] = False

            self._reset_context(context)
            self._publish_worker_state(self._worker_contexts[worker_id])
            self._disconnect_cleanup_done[worker_id] = True

        self.reset_test_indicators(worker_id)

        log_both(
            self._logger,
            logging.INFO,
            "Worker %s reiniciado a estado base tras desconexión física.",
            worker_id,
        )

    def reset_test_indicators(self, worker_id: str) -> None:
        test_names = (
            "PING",
            "FACTORY_RESET",
            "SOFTWARE_UPDATE",
            "USB",
            "FIBER_TX",
            "FIBER_RX",
            "WIFI_2G",
            "WIFI_5G",
        )

        for test_name in test_names:
            visual_state = "OFFLINE" if test_name == "PING" else "IDLE"

            self.publish_test_indicator(
                worker_id=worker_id,
                test_name=test_name,
                visual_state=visual_state,
            )

        self.publish_global_visual_mode(
            worker_id=worker_id,
            mode="EXPECTED_RESET",
            active=False,
        )
        self.publish_global_visual_mode(
            worker_id=worker_id,
            mode="EXPECTED_UPDATE",
            active=False,
        )

    def publish_test_indicator(
        self,
        *,
        worker_id: str,
        test_name: str,
        visual_state: str,
        extra_payload: dict[str, Any] | None = None,
    ) -> None:
        event = TestIndicatorChangedEvent(
            worker_id=worker_id,
            test_name=test_name,
            visual_state=visual_state,
            extra_payload=extra_payload,
        )
        self._event_bus.publish(event)

    def publish_global_visual_mode(
        self,
        *,
        worker_id: str,
        mode: str,
        active: bool,
        extra_payload: dict[str, Any] | None = None,
    ) -> None:
        event = WorkerGlobalVisualModeEvent(
            worker_id=worker_id,
            mode=mode,
            active=active,
            extra_payload=extra_payload,
        )
        self._event_bus.publish(event)

    def try_auto_start_execution(self, worker_id: str) -> bool:
        with self._lock:
            if not self._settings.auto_execution.enabled:
                return False

            if not self._settings.auto_execution.trigger_on_connect:
                return False

            context = self._worker_contexts.get(worker_id)
            if context is None:
                return False

            snapshot = context.snapshot()

            if not snapshot.get("connected", False):
                return False

            if snapshot.get("state") != "IDLE" or snapshot.get("phase") != "WAITING":
                return False

            if worker_id in self._active_port_workers and self._active_port_workers[worker_id].is_running():
                return False

            if self._auto_execution_started.get(worker_id, False):
                return False

            request_data = build_default_execution_request(worker_id)
            request = ExecutionTestRequest.from_dict(request_data)

            assigned = self.assign_worker(
                worker_id=worker_id,
                device_ip=snapshot.get("expected_ip"),
                mac=snapshot.get("device_mac"),
                status="USADO",
                phase=self._resolve_initial_phase_from_request(request),
            )
            if not assigned:
                return False

            if request.device_sn is not None:
                context.bind_device(device_sn=request.device_sn)
            if request.vendor is not None:
                context.bind_device(vendor=request.vendor)
            if request.model is not None:
                context.bind_device(model=request.model)

            context.set_metadata("execution_tests", request.tests)
            context.set_metadata("enabled_tests", request.enabled_tests())
            context.set_metadata("request_payload", request.to_dict())

            started = self.start_port_worker(request)
            if not started:
                self.release_worker(worker_id)
                return False

            self._auto_execution_started[worker_id] = True

            log_both(
                self._logger,
                logging.INFO,
                "Autoejecución iniciada para %s. Pruebas: %s",
                worker_id,
                ", ".join(request.enabled_tests()),
            )
            return True