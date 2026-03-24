from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from app.shared.constants import TEST_EXECUTION_ORDER

SUPPORTED_TESTS = (
    "factory_reset",
    "software_update",
    "usb",
    "fiber_tx",
    "fiber_rx",
    "wifi_2g",
    "wifi_5g",
)


@dataclass(slots=True)
class ExecutionTestRequest:
    """
    DTO que representa una solicitud de ejecución de pruebas para una instancia/slot.

    La UI ya no manda la IP del equipo. En su lugar, manda el worker_id (o estación lógica)
    sobre el que se debe ejecutar el plan de pruebas.
    """

    worker_id: str
    device_mac: str | None = None
    device_sn: str | None = None
    vendor: str | None = None
    model: str | None = None
    tests: dict[str, bool] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def enabled_tests(self) -> list[str]:
        return [
            test_name
            for test_name in TEST_EXECUTION_ORDER
            if self.tests.get(test_name, False)
        ]

    def is_test_enabled(self, test_name: str) -> bool:
        """
        Indica si una prueba está habilitada.
        """
        return bool(self.tests.get(test_name, False))

    def has_any_enabled_test(self) -> bool:
        """
        Indica si al menos una prueba fue habilitada.
        """
        return any(self.tests.values())

    def to_dict(self) -> dict[str, Any]:
        """
        Devuelve la solicitud como diccionario serializable.
        """
        return {
            "worker_id": self.worker_id,
            "device_mac": self.device_mac,
            "device_sn": self.device_sn,
            "vendor": self.vendor,
            "model": self.model,
            "tests": dict(self.tests),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionTestRequest":
        """
        Construye y normaliza una solicitud a partir de un diccionario.

        Reglas:
        - worker_id es obligatorio
        - tests faltantes se completan en False
        - tests desconocidos se ignoran
        """
        if not isinstance(data, dict):
            raise TypeError("La solicitud de ejecución debe ser un diccionario.")

        worker_id = str(data.get("worker_id", "")).strip()
        if not worker_id:
            raise ValueError("El campo 'worker_id' es obligatorio.")

        raw_tests = data.get("tests", {})
        if raw_tests is None:
            raw_tests = {}

        if not isinstance(raw_tests, dict):
            raise TypeError("El campo 'tests' debe ser un diccionario.")

        normalized_tests: dict[str, bool] = {
            test_name: bool(raw_tests.get(test_name, False))
            for test_name in SUPPORTED_TESTS
        }

        metadata = data.get("metadata", {})
        if metadata is None:
            metadata = {}

        if not isinstance(metadata, dict):
            raise TypeError("El campo 'metadata' debe ser un diccionario.")

        return cls(
            worker_id=worker_id,
            device_mac=_normalize_optional_string(data.get("device_mac")),
            device_sn=_normalize_optional_string(data.get("device_sn")),
            vendor=_normalize_optional_string(data.get("vendor")),
            model=_normalize_optional_string(data.get("model")),
            tests=normalized_tests,
            metadata=dict(metadata),
        )


def _normalize_optional_string(value: Any) -> str | None:
    """
    Convierte un valor opcional a string limpio o None.
    """
    if value is None:
        return None

    normalized = str(value).strip()
    return normalized if normalized else None