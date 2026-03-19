from __future__ import annotations

DEFAULT_EXECUTION_TESTS: dict[str, bool] = {
    "factory_reset": True,
    "software_update": False,
    "usb": True,
    "fiber_tx": False,
    "fiber_rx": False,
    "wifi_2g":  False,
    "wifi_5g":  False,
}

TEST_EXECUTION_ORDER: tuple[str, ...] = (
    "factory_reset",
    "software_update",
    "usb",
    "fiber_tx",
    "fiber_rx",
    "wifi_2g",
    "wifi_5g",
)

def build_default_execution_request(worker_id: str) -> dict[str, object]:
    """
    Request temporal para reemplazar el diccionario de pruebas de la UI
    Mas adelante se recibirá desde la UI
    """
    return {
        "worker_id": worker_id,
        "vendor": "FIBERHOME", # TODO cambiar esto a detección
        "tests": dict(DEFAULT_EXECUTION_TESTS),
    }