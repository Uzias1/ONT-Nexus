from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.infrastructure.network.arp_scanner import ArpScanner


@dataclass(slots=True)
class DeviceIdentity:
    serial_number: str | None = None
    mac_address: str | None = None


@dataclass(slots=True)
class TestStepResult:
    name: str
    status: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FiberhomeExecutionResult:
    identity: DeviceIdentity = field(default_factory=DeviceIdentity)
    tests: dict[str, TestStepResult] = field(default_factory=dict)


class FiberhomeAdapter:
    """
    Adaptador mínimo para FiberHome.

    Su responsabilidad es:
    - Normalizar identidad mínima del equipo
    - Construir resultados mínimos por prueba
    - Evitar acoplar el runner a estructuras viejas como test_results
    """

    def __init__(self) -> None:
        self._arp_scanner = ArpScanner()

    def build_identity(
        self,
        *,
        serial_number: str | None = None,
        mac_address: str | None = None,
        ip: str | None = None,
    ) -> DeviceIdentity:
        mac = mac_address
        if not mac and ip:
            mac = self._arp_scanner.get_mac(ip)

        return DeviceIdentity(
            serial_number=serial_number,
            mac_address=mac,
        )

    def build_test_result(
        self,
        *,
        name: str,
        status: str,
        details: dict[str, Any] | None = None,
    ) -> TestStepResult:
        return TestStepResult(
            name=name,
            status=status,
            details=details or {},
        )