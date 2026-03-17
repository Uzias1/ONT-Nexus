from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class DomainEvent:
    """
    Evento base del sistema.
    Se publica en el EventBus y puede ser consumido después por la UI
    u otros componentes que hagan pull de la cola.
    """
    event_name: str
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=datetime.now)

@dataclass(slots=True)
class WorkerStateChangedEvent(DomainEvent):
    """
    Evento especializado para reflejar cambios de estado 'vivo' de una instancia
    de prueba / worker del sistema.
    """

    def __init__(
        self,
        *,
        worker_id: str,
        ip: str | None = None,
        status: str = "LIBRE",
        mac: str | None = None,
        phase: str = "WAITING",
        extra_payload: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "worker_id": worker_id,
            "ip": ip,
            "status": status,
            "mac": mac,
            "phase": phase,
        }

        if extra_payload:
            payload.update(extra_payload)

        super().__init__(
            event_name="worker.state_changed",
            payload=payload,
        )