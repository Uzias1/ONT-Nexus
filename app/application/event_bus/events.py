from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class DomainEvent:
    event_name: str
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=datetime.now)


class WorkerStateChangedEvent(DomainEvent):
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


class TestIndicatorChangedEvent(DomainEvent):
    def __init__(
        self,
        *,
        worker_id: str,
        test_name: str,
        visual_state: str,
        extra_payload: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "worker_id": worker_id,
            "test_name": test_name,
            "visual_state": visual_state,
        }

        if extra_payload:
            payload.update(extra_payload)

        super().__init__(
            event_name="test.indicator_changed",
            payload=payload,
        )


class WorkerGlobalVisualModeEvent(DomainEvent):
    def __init__(
        self,
        *,
        worker_id: str,
        mode: str,
        active: bool,
        extra_payload: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "worker_id": worker_id,
            "mode": mode,
            "active": active,
        }

        if extra_payload:
            payload.update(extra_payload)

        super().__init__(
            event_name="worker.global_visual_mode",
            payload=payload,
        )