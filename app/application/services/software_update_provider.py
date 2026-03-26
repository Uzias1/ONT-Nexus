from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.infrastructure.config.settings import PROJECT_ROOT, Settings


@dataclass(frozen=True, slots=True)
class FirmwareCandidate:
    vendor: str
    model_key: str
    firmware_path: Path
    filename: str
    target_version: str
    source_directory: Path


class SoftwareUpdateProvider:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def resolve_firmware(
        self,
        *,
        vendor: str,
        model_code: str | None = None,
        model_name: str | None = None,
    ) -> FirmwareCandidate:
        vendor_key = vendor.strip().lower()
        vendor_cfg = self._get_vendor_config(vendor_key)

        model_key = self._resolve_model_key(
            vendor_cfg=vendor_cfg,
            model_code=model_code,
            model_name=model_name,
        )

        models_map = vendor_cfg.get("models", {})
        rel_dir = models_map.get(model_key)
        if not rel_dir:
            raise FileNotFoundError(
                f"No existe directorio de firmware configurado para vendor={vendor_key} model={model_key}."
            )

        bins_root = self._resolve_bins_root()
        model_dir = (bins_root / rel_dir).resolve()

        if not model_dir.exists():
            raise FileNotFoundError(f"No existe directorio de bins: {model_dir}")

        bin_files = [p for p in model_dir.glob("*.bin") if p.is_file()]
        if not bin_files:
            raise FileNotFoundError(f"No existe archivo .bin dentro de: {model_dir}")

        firmware_path = max(bin_files, key=lambda p: p.stat().st_mtime)
        target_version = self._extract_target_version(firmware_path.name)

        return FirmwareCandidate(
            vendor=vendor_key,
            model_key=model_key,
            firmware_path=firmware_path,
            filename=firmware_path.name,
            target_version=target_version,
            source_directory=model_dir,
        )

    def resolve_superuser_credentials(self, *, vendor: str) -> tuple[str, str]:
        vendor_key = vendor.strip().lower()
        vendor_cfg = self._get_vendor_config(vendor_key)

        username = str(vendor_cfg.get("superuser_username", "")).strip()
        password = str(vendor_cfg.get("superuser_password", "")).strip()

        if not username or not password:
            raise ValueError(
                f"No hay credenciales de superusuario configuradas para vendor={vendor_key}."
            )

        return username, password

    def _resolve_bins_root(self) -> Path:
        raw_root = str(self._settings.paths.bins_root).strip()
        if not raw_root:
            raise ValueError("settings.paths.bins_root está vacío.")

        root = Path(raw_root)
        if not root.is_absolute():
            root = (PROJECT_ROOT / root).resolve()

        return root

    def _get_vendor_config(self, vendor_key: str) -> dict[str, Any]:
        vendors = self._settings.software_update.vendors or {}
        vendor_cfg = vendors.get(vendor_key)

        if not isinstance(vendor_cfg, dict):
            raise ValueError(f"No existe configuración de software_update para vendor={vendor_key}.")

        return vendor_cfg

    def _resolve_model_key(
        self,
        *,
        vendor_cfg: dict[str, Any],
        model_code: str | None,
        model_name: str | None,
    ) -> str:
        aliases = vendor_cfg.get("aliases", {}) or {}

        if model_code:
            normalized_model_code = str(model_code).strip()
            if normalized_model_code:
                return normalized_model_code

        if model_name:
            normalized_model_name = str(model_name).strip()
            if normalized_model_name:
                if normalized_model_name in aliases:
                    return str(aliases[normalized_model_name]).strip()

                upper_name = normalized_model_name.upper()
                if upper_name in aliases:
                    return str(aliases[upper_name]).strip()

        raise ValueError(
            "No se pudo resolver model_key para firmware. "
            f"model_code={model_code!r} model_name={model_name!r}"
        )

    @staticmethod
    def _extract_target_version(filename: str) -> str:
        stem = Path(filename).stem
        if "_" in stem:
            return stem.split("_", 1)[1]
        return stem