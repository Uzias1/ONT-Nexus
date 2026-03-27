from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SoftwareUpdateDecision:
    required: bool
    current_version: str
    target_version: str
    reason: str


class SoftwareUpdateEvaluator:
    def evaluate(
        self,
        *,
        current_version: str | None,
        target_version: str,
    ) -> SoftwareUpdateDecision:
        current_version = (current_version or "").strip()
        target_version = (target_version or "").strip()

        current_digits = self._only_digits(current_version)
        target_digits = self._only_digits(target_version)

        if not target_digits:
            return SoftwareUpdateDecision(
                required=False,
                current_version=current_version,
                target_version=target_version,
                reason="No se pudo interpretar la versión objetivo del firmware.",
            )

        if current_digits == target_digits:
            return SoftwareUpdateDecision(
                required=False,
                current_version=current_version,
                target_version=target_version,
                reason="El equipo ya tiene la misma versión objetivo.",
            )

        return SoftwareUpdateDecision(
            required=True,
            current_version=current_version,
            target_version=target_version,
            reason="La versión actual es distinta a la versión objetivo.",
        )

    def is_target_applied(
        self,
        *,
        current_version: str | None,
        target_version: str,
    ) -> bool:
        current_digits = self._only_digits(current_version or "")
        target_digits = self._only_digits(target_version or "")
        return bool(target_digits) and current_digits == target_digits

    @staticmethod
    def _only_digits(value: str) -> str:
        return "".join(ch for ch in value if ch.isdigit())