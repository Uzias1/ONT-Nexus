from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any


@dataclass(slots=True)
class WorkerContext:
    """
    Estado compartido de una instancia/worker del tester.

    Cada worker representa una estación lógica fija. Por eso guarda también
    la IP esperada del slot, además de la identidad detectada del equipo.
    """

    worker_id: str
    port_index: int | None = None
    expected_ip: str | None = None

    device_ip: str | None = None
    device_mac: str | None = None
    device_sn: str | None = None
    vendor: str | None = None
    model: str | None = None

    state: str = "IDLE"
    phase: str = "WAITING"
    connected: bool = False

    disconnect_expected: bool = False
    cancel_requested: bool = False

    started_at: datetime | None = None
    finished_at: datetime | None = None
    last_seen_at: datetime | None = None
    updated_at: datetime = field(default_factory=datetime.now)

    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    _lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def _touch(self) -> None:
        self.updated_at = datetime.now()

    def bind_device(
        self,
        *,
        expected_ip: str | None = None,
        device_ip: str | None = None,
        device_mac: str | None = None,
        device_sn: str | None = None,
        vendor: str | None = None,
        model: str | None = None,
    ) -> None:
        with self._lock:
            if expected_ip is not None:
                self.expected_ip = expected_ip
            if device_ip is not None:
                self.device_ip = device_ip
            if device_mac is not None:
                self.device_mac = device_mac
            if device_sn is not None:
                self.device_sn = device_sn
            if vendor is not None:
                self.vendor = vendor
            if model is not None:
                self.model = model

            self._touch()

    def mark_started(self, phase: str = "STARTING") -> None:
        with self._lock:
            now = datetime.now()
            self.started_at = now
            self.finished_at = None
            self.state = "RUNNING"
            self.phase = phase
            self.error_message = None
            self._touch()

    def mark_finished(self, state: str = "DONE", phase: str = "FINISHED") -> None:
        with self._lock:
            self.state = state
            self.phase = phase
            self.finished_at = datetime.now()
            self._touch()

    def set_state(self, state: str) -> None:
        with self._lock:
            self.state = state
            self._touch()

    def set_phase(self, phase: str) -> None:
        with self._lock:
            self.phase = phase
            self._touch()

    def set_state_and_phase(self, *, state: str, phase: str) -> None:
        with self._lock:
            self.state = state
            self.phase = phase
            self._touch()

    def mark_connected(self) -> None:
        with self._lock:
            now = datetime.now()
            self.connected = True
            self.last_seen_at = now
            self._touch()

    def mark_seen(self) -> None:
        with self._lock:
            now = datetime.now()
            self.connected = True
            self.last_seen_at = now
            self._touch()

    def mark_disconnected(self) -> None:
        with self._lock:
            self.connected = False
            self._touch()

    def set_disconnect_expected(self, expected: bool) -> None:
        with self._lock:
            self.disconnect_expected = expected
            self._touch()

    def request_cancel(self) -> None:
        with self._lock:
            self.cancel_requested = True
            self._touch()

    def clear_cancel_request(self) -> None:
        with self._lock:
            self.cancel_requested = False
            self._touch()

    def set_error(self, message: str, *, state: str = "FAILED", phase: str = "ERROR") -> None:
        with self._lock:
            self.error_message = message
            self.state = state
            self.phase = phase
            self.finished_at = datetime.now()
            self._touch()

    def clear_error(self) -> None:
        with self._lock:
            self.error_message = None
            self._touch()

    def set_metadata(self, key: str, value: Any) -> None:
        with self._lock:
            self.metadata[key] = value
            self._touch()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self.metadata.get(key, default)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "worker_id": self.worker_id,
                "port_index": self.port_index,
                "expected_ip": self.expected_ip,
                "device_ip": self.device_ip,
                "device_mac": self.device_mac,
                "device_sn": self.device_sn,
                "vendor": self.vendor,
                "model": self.model,
                "state": self.state,
                "phase": self.phase,
                "connected": self.connected,
                "disconnect_expected": self.disconnect_expected,
                "cancel_requested": self.cancel_requested,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "last_seen_at": self.last_seen_at,
                "updated_at": self.updated_at,
                "error_message": self.error_message,
                "metadata": dict(self.metadata),
            }
        
    def clear_network_identity(self) -> None:
        with self._lock:
            self.device_ip = None
            self.device_mac = None
            self._touch()