from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvaluationThresholds:
    min_tx: float
    max_tx: float
    min_rx: float
    max_rx: float
    min_wifi_24_percent: int
    min_wifi_5_percent: int


class TestThresholdProvider:
    """
    Proveedor central de thresholds de validación.

    Hoy devuelve valores fijos.
    Mañana puede leerlos desde SQLite, API o cualquier otra fuente
    sin obligar a cambiar los runners.
    """

    def get_thresholds(
        self,
        *,
        vendor: str | None = None,
        model: str | None = None,
    ) -> EvaluationThresholds:
        # Por ahora todos los vendors comparten la misma lógica.
        # Más adelante aquí puedes meter lectura por vendor/modelo desde BD.
        return EvaluationThresholds(
            min_tx=0.0,
            max_tx=10.0,
            min_rx=-28.0,
            max_rx=0.0,
            min_wifi_24_percent=60,
            min_wifi_5_percent=60,
        )