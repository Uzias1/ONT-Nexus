from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING

from app.infrastructure.config.settings import Settings
from app.infrastructure.logging.logger import get_logger, log_both, log_console
from app.infrastructure.network.ping_service import PingService

if TYPE_CHECKING:
    from app.workers.supervisor import Supervisor


class ConnectionMonitor:
    """
    Monitor de conectividad de slots/workers.

    Recorre periódicamente las IP esperadas configuradas en cada WorkerContext
    y actualiza el estado de conexión mediante el Supervisor.
    """

    def __init__(
        self,
        *,
        settings: Settings,
        supervisor: Supervisor,
        ping_service: PingService,
    ) -> None:
        self._settings = settings
        self._supervisor = supervisor
        self._ping_service = ping_service
        self._logger = get_logger(self.__class__.__name__)

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._running = False
        self._lock = threading.RLock()

        self._poll_interval_s = settings.monitor.poll_interval_s

    # ==========================================================
    # Ciclo de vida
    # ==========================================================
    def start(self) -> None:
        with self._lock:
            if self._running:
                log_console(self._logger, logging.INFO, "ConnectionMonitor ya estaba en ejecución.")
                return

            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run_loop,
                name="ConnectionMonitorThread",
                daemon=True,
            )
            self._thread.start()
            self._running = True

            log_both(self._logger, logging.INFO, "ConnectionMonitor iniciado correctamente.")

    def stop(self) -> None:
        with self._lock:
            if not self._running:
                log_console(self._logger, logging.INFO, "ConnectionMonitor ya estaba detenido.")
                return

            self._stop_event.set()

            if self._thread is not None:
                self._thread.join(timeout=self._settings.workers.worker_join_timeout_s)

            self._running = False
            log_both(self._logger, logging.INFO, "ConnectionMonitor detenido correctamente.")

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    # ==========================================================
    # Loop principal
    # ==========================================================
    def _run_loop(self) -> None:
        try:
            log_console(self._logger, logging.INFO, "Loop de monitoreo iniciado.")

            while not self._stop_event.is_set():
                self._monitor_once()
                time.sleep(self._poll_interval_s)

            log_console(self._logger, logging.INFO, "Loop de monitoreo finalizado.")
        except Exception:
            log_both(
                self._logger,
                logging.ERROR,
                "Excepción no controlada en ConnectionMonitor.",
                exc_info=True,
            )
            raise

    def _monitor_once(self) -> None:
        snapshots = self._supervisor.get_all_snapshots()

        for snapshot in snapshots:
            worker_id = str(snapshot["worker_id"])
            expected_ip = snapshot.get("expected_ip")
            if not expected_ip:
                continue

            connected_before = bool(snapshot.get("connected", False))
            disconnect_expected = bool(snapshot.get("disconnect_expected", False))

            connected_now = self._ping_service.ping(str(expected_ip))

            if connected_now:
                self._handle_connected(
                    worker_id=worker_id,
                    expected_ip=str(expected_ip),
                    connected_before=connected_before,
                )
            else:
                self._handle_disconnected(
                    worker_id=worker_id,
                    connected_before=connected_before,
                    disconnect_expected=disconnect_expected,
                )

    # ==========================================================
    # Transiciones de estado
    # ==========================================================
    def _handle_connected(
        self,
        *,
        worker_id: str,
        expected_ip: str,
        connected_before: bool,
    ) -> None:
        # Actualizamos la IP detectada del equipo al menos al valor esperado.
        self._supervisor.update_worker_network(
            worker_id=worker_id,
            device_ip=expected_ip,
        )
        self._supervisor.set_worker_connected(
            worker_id=worker_id,
            connected=True,
        )

        if not connected_before:
            log_console(
                self._logger,
                logging.INFO,
                "Equipo detectado en %s (%s).",
                worker_id,
                expected_ip,
            )

    def _handle_disconnected(
        self,
        *,
        worker_id: str,
        connected_before: bool,
        disconnect_expected: bool,
    ) -> None:
        self._supervisor.set_worker_connected(
            worker_id=worker_id,
            connected=False,
        )

        if connected_before:
            if disconnect_expected:
                log_console(
                    self._logger,
                    logging.INFO,
                    "Desconexión esperada detectada en %s.",
                    worker_id,
                )
            else:
                log_console(
                    self._logger,
                    logging.WARNING,
                    "Desconexión detectada en %s.",
                    worker_id,
                )