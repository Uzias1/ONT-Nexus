from __future__ import annotations

import logging
from typing import Any

from app.application.services.treshold_provider import EvaluationThresholds
from app.infrastructure.logging.logger import log_both


class TestResultEvaluator:
    """
    Evalúa pruebas comunes entre vendors y publica el estado visual del indicador.
    """

    def __init__(
        self,
        *,
        supervisor: Any,
        worker_id: str,
        adapter: Any,
        logger: logging.Logger,
        thresholds: EvaluationThresholds,
    ) -> None:
        self._supervisor = supervisor
        self._worker_id = worker_id
        self._adapter = adapter
        self._logger = logger
        self._thresholds = thresholds

    def evaluate_fiber_tx(
        self,
        *,
        value: Any,
        source_details: dict[str, Any] | None = None,
    ):
        details = dict(source_details or {})
        details["tx_power_dbm"] = value

        numeric_value = self._to_float(value)
        if numeric_value is None:
            step = self._adapter.build_test_result(
                name="fiber_tx",
                status="FAIL",
                details={**details, "reason": "Valor TX ausente o no convertible a número."},
            )
            self._publish(
                test_name="FIBER_TX",
                visual_state="FAIL",
                result_status="FAIL",
                details=step.details,
            )
            log_both(self._logger, logging.ERROR, "Resultado FIBER_TX %s: FAIL | %s", self._worker_id, step.details)
            return step

        if self._thresholds.min_tx <= numeric_value <= self._thresholds.max_tx:
            step = self._adapter.build_test_result(
                name="fiber_tx",
                status="PASS",
                details={
                    **details,
                    "note": (
                        f"TX dentro de rango "
                        f"({self._thresholds.min_tx}..{self._thresholds.max_tx})"
                    ),
                },
            )
            self._publish(
                test_name="FIBER_TX",
                visual_state="PASS",
                result_status="PASS",
                details=step.details,
            )
            log_both(self._logger, logging.INFO, "Resultado FIBER_TX %s: PASS | %s", self._worker_id, step.details)
            return step

        step = self._adapter.build_test_result(
            name="fiber_tx",
            status="FAIL",
            details={
                **details,
                "note": (
                    f"TX fuera de rango "
                    f"({self._thresholds.min_tx}..{self._thresholds.max_tx})"
                ),
            },
        )
        self._publish(
            test_name="FIBER_TX",
            visual_state="FAIL",
            result_status="FAIL",
            details=step.details,
        )
        log_both(self._logger, logging.ERROR, "Resultado FIBER_TX %s: FAIL | %s", self._worker_id, step.details)
        return step

    def evaluate_fiber_rx(
        self,
        *,
        value: Any,
        source_details: dict[str, Any] | None = None,
    ):
        details = dict(source_details or {})
        details["rx_power_dbm"] = value

        numeric_value = self._to_float(value)
        if numeric_value is None:
            step = self._adapter.build_test_result(
                name="fiber_rx",
                status="FAIL",
                details={**details, "reason": "Valor RX ausente o no convertible a número."},
            )
            self._publish(
                test_name="FIBER_RX",
                visual_state="FAIL",
                result_status="FAIL",
                details=step.details,
            )
            log_both(self._logger, logging.ERROR, "Resultado FIBER_RX %s: FAIL | %s", self._worker_id, step.details)
            return step

        if self._thresholds.min_rx <= numeric_value <= self._thresholds.max_rx:
            step = self._adapter.build_test_result(
                name="fiber_rx",
                status="PASS",
                details={
                    **details,
                    "note": (
                        f"RX dentro de rango "
                        f"({self._thresholds.min_rx}..{self._thresholds.max_rx})"
                    ),
                },
            )
            self._publish(
                test_name="FIBER_RX",
                visual_state="PASS",
                result_status="PASS",
                details=step.details,
            )
            log_both(self._logger, logging.INFO, "Resultado FIBER_RX %s: PASS | %s", self._worker_id, step.details)
            return step

        step = self._adapter.build_test_result(
            name="fiber_rx",
            status="FAIL",
            details={
                **details,
                "note": (
                    f"RX fuera de rango "
                    f"({self._thresholds.min_rx}..{self._thresholds.max_rx})"
                ),
            },
        )
        self._publish(
            test_name="FIBER_RX",
            visual_state="FAIL",
            result_status="FAIL",
            details=step.details,
        )
        log_both(self._logger, logging.ERROR, "Resultado FIBER_RX %s: FAIL | %s", self._worker_id, step.details)
        return step

    def evaluate_wifi_2g(
        self,
        *,
        details: dict[str, Any],
    ):
        signal_percent = details.get("signal_percent")

        if signal_percent is None:
            step = self._adapter.build_test_result(
                name="wifi_2g",
                status="FAIL",
                details={
                    **details,
                    "reason": "No se encontró o no se pudo medir la red 2.4 GHz.",
                },
            )
            self._publish(
                test_name="WIFI_2G",
                visual_state="FAIL",
                result_status="FAIL",
                details=step.details,
            )
            log_both(self._logger, logging.ERROR, "Resultado WIFI_2G %s: FAIL | %s", self._worker_id, step.details)
            return step

        if signal_percent >= self._thresholds.min_wifi_24_percent:
            step = self._adapter.build_test_result(
                name="wifi_2g",
                status="PASS",
                details={
                    **details,
                    "method": "netsh_wlan_scan",
                    "note": (
                        f"WiFi 2.4 GHz dentro de umbral "
                        f"(>= {self._thresholds.min_wifi_24_percent}%)."
                    ),
                },
            )
            self._publish(
                test_name="WIFI_2G",
                visual_state="PASS",
                result_status="PASS",
                details=step.details,
            )
            log_both(self._logger, logging.INFO, "Resultado WIFI_2G %s: PASS | %s", self._worker_id, step.details)
            return step

        step = self._adapter.build_test_result(
            name="wifi_2g",
            status="FAIL",
            details={
                **details,
                "method": "netsh_wlan_scan",
                "note": (
                    f"WiFi 2.4 GHz por debajo de umbral "
                    f"(>= {self._thresholds.min_wifi_24_percent}%)."
                ),
            },
        )
        self._publish(
            test_name="WIFI_2G",
            visual_state="FAIL",
            result_status="FAIL",
            details=step.details,
        )
        log_both(self._logger, logging.ERROR, "Resultado WIFI_2G %s: FAIL | %s", self._worker_id, step.details)
        return step

    def evaluate_wifi_5g(
        self,
        *,
        details: dict[str, Any],
    ):
        signal_percent = details.get("signal_percent")

        if signal_percent is None:
            step = self._adapter.build_test_result(
                name="wifi_5g",
                status="FAIL",
                details={
                    **details,
                    "reason": "No se encontró o no se pudo medir la red 5 GHz.",
                },
            )
            self._publish(
                test_name="WIFI_5G",
                visual_state="FAIL",
                result_status="FAIL",
                details=step.details,
            )
            log_both(self._logger, logging.ERROR, "Resultado WIFI_5G %s: FAIL | %s", self._worker_id, step.details)
            return step

        if signal_percent >= self._thresholds.min_wifi_5_percent:
            step = self._adapter.build_test_result(
                name="wifi_5g",
                status="PASS",
                details={
                    **details,
                    "method": "netsh_wlan_scan",
                    "note": (
                        f"WiFi 5 GHz dentro de umbral "
                        f"(>= {self._thresholds.min_wifi_5_percent}%)."
                    ),
                },
            )
            self._publish(
                test_name="WIFI_5G",
                visual_state="PASS",
                result_status="PASS",
                details=step.details,
            )
            log_both(self._logger, logging.INFO, "Resultado WIFI_5G %s: PASS | %s", self._worker_id, step.details)
            return step

        step = self._adapter.build_test_result(
            name="wifi_5g",
            status="FAIL",
            details={
                **details,
                "method": "netsh_wlan_scan",
                "note": (
                    f"WiFi 5 GHz por debajo de umbral "
                    f"(>= {self._thresholds.min_wifi_5_percent}%)."
                ),
            },
        )
        self._publish(
            test_name="WIFI_5G",
            visual_state="FAIL",
            result_status="FAIL",
            details=step.details,
        )
        log_both(self._logger, logging.ERROR, "Resultado WIFI_5G %s: FAIL | %s", self._worker_id, step.details)
        return step

    def _publish(
        self,
        *,
        test_name: str,
        visual_state: str,
        result_status: str,
        details: dict[str, Any],
    ) -> None:
        self._supervisor.publish_test_indicator(
            worker_id=self._worker_id,
            test_name=test_name,
            visual_state=visual_state,
            extra_payload={
                "result_status": result_status,
                "details": details,
            },
        )

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None