from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING

from app.infrastructure.config.settings import Settings
from app.infrastructure.logging.logger import get_logger, log_both, log_console
from app.infrastructure.network.arp_scanner import ArpScanner
from app.infrastructure.network.ping_service import PingService

if TYPE_CHECKING:
    from app.workers.supervisor import Supervisor


class SlotConnectionMonitor:
    """
    Monitor dedicado a un solo slot/worker.
    """

    def __init__(
        self,
        *,
        settings: Settings,
        supervisor: Supervisor,
        ping_service: PingService,
        arp_scanner: ArpScanner,
        worker_id: str,
    ) -> None:
        self._settings = settings
        self._supervisor = supervisor
        self._ping_service = ping_service
        self._arp_scanner = arp_scanner
        self._worker_id = worker_id
        self._logger = get_logger(f"{self.__class__.__name__}.{worker_id}")

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._running = False
        self._lock = threading.RLock()

        self._poll_interval_s = settings.monitor.poll_interval_s
        self._disconnect_threshold = max(1, settings.monitor.disconnect_threshold)
        self._failure_count = 0

    def start(self) -> None:
        with self._lock:
            if self._running:
                return

            self._stop_event.clear()
            self._failure_count = 0
            self._thread = threading.Thread(
                target=self._run_loop,
                name=f"SlotMonitorThread-{self._worker_id}",
                daemon=True,
            )
            self._thread.start()
            self._running = True

            log_both(
                self._logger,
                logging.INFO,
                "SlotConnectionMonitor iniciado. worker=%s poll=%ss threshold=%s",
                self._worker_id,
                self._poll_interval_s,
                self._disconnect_threshold,
            )

    def stop(self) -> None:
        with self._lock:
            if not self._running:
                return

            self._stop_event.set()

            if self._thread is not None:
                self._thread.join(timeout=self._settings.workers.worker_join_timeout_s)

            self._running = False
            self._failure_count = 0

            log_both(
                self._logger,
                logging.INFO,
                "SlotConnectionMonitor detenido. worker=%s",
                self._worker_id,
            )

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def _run_loop(self) -> None:
        try:
            log_console(self._logger, logging.INFO, "Loop de monitoreo por slot iniciado.")

            while not self._stop_event.is_set():
                self._monitor_once()
                time.sleep(self._poll_interval_s)

            log_console(self._logger, logging.INFO, "Loop de monitoreo por slot finalizado.")
        except Exception:
            log_both(
                self._logger,
                logging.ERROR,
                "Excepción no controlada en SlotConnectionMonitor %s.",
                self._worker_id,
                exc_info=True,
            )
            raise

    def _monitor_once(self) -> None:
        snapshot = self._supervisor.get_worker_snapshot(self._worker_id)
        if snapshot is None:
            return

        expected_ip = snapshot.get("expected_ip")
        if not expected_ip:
            return

        connected_before = bool(snapshot.get("connected", False))
        disconnect_expected = bool(snapshot.get("disconnect_expected", False))

        connected_now = self._ping_service.ping(str(expected_ip))

        if connected_now:
            self._handle_connected(
                expected_ip=str(expected_ip),
                connected_before=connected_before,
            )
        else:
            self._handle_failed_ping(
                connected_before=connected_before,
                disconnect_expected=disconnect_expected,
            )

    def _handle_connected(self, *, expected_ip: str, connected_before: bool) -> None:
        self._failure_count = 0

        detected_mac = self._arp_scanner.get_mac(expected_ip)

        self._supervisor.update_worker_network(
            worker_id=self._worker_id,
            device_ip=expected_ip,
            mac=detected_mac,
        )

        # - Si ya estaba conectado, no debemos limpiar disconnect_expected,
        #   porque podríamos estar justo antes del reboot esperado.
        # - Solo lo limpiamos cuando realmente hubo reconexión
        #   (connected_before == False y ahora volvió a responder).
        if connected_before:
            self._supervisor.set_worker_connected(
                worker_id=self._worker_id,
                connected=True,
                disconnect_expected=None,
                connection_reason="ping_ok",
            )
        else:
            self._supervisor.set_worker_connected(
                worker_id=self._worker_id,
                connected=True,
                disconnect_expected=False,
                connection_reason="reconnected",
            )

            log_console(
                self._logger,
                logging.INFO,
                "Equipo detectado en %s (%s). MAC=%s",
                self._worker_id,
                expected_ip,
                detected_mac or "-",
            )

    def _handle_failed_ping(
        self,
        *,
        connected_before: bool,
        disconnect_expected: bool,
    ) -> None:
        self._failure_count += 1

        log_console(
            self._logger,
            logging.DEBUG,
            "Fallo de ping en %s. consecutive_failures=%s/%s",
            self._worker_id,
            self._failure_count,
            self._disconnect_threshold,
        )

        if self._failure_count < self._disconnect_threshold:
            return

        self._supervisor.update_worker_network(
            worker_id=self._worker_id,
            device_ip=None,
            mac=None,
        )
        self._supervisor.set_worker_connected(
            worker_id=self._worker_id,
            connected=False,
            disconnect_expected=disconnect_expected,
            connection_reason="expected_disconnect" if disconnect_expected else "lost_ping",
        )

        if connected_before:
            if disconnect_expected:
                log_console(
                    self._logger,
                    logging.INFO,
                    "Desconexión esperada confirmada en %s.",
                    self._worker_id,
                )
            else:
                log_console(
                    self._logger,
                    logging.WARNING,
                    "Desconexión real confirmada en %s.",
                    self._worker_id,
                )