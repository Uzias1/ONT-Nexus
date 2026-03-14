from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


# ==========================================================
# Rutas base
# ==========================================================
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_APP_SETTINGS_PATH = PROJECT_ROOT / "data" / "config" / "app_settings.yaml"


# ==========================================================
# Modelos de configuración
# ==========================================================
@dataclass(slots=True)
class AppConfig:
    name: str
    version: str
    environment: str


@dataclass(slots=True)
class MonitorConfig:
    heartbeat_interval_s: float
    poll_interval_s: float
    disconnect_threshold: int


@dataclass(slots=True)
class WorkerConfig:
    max_workers: int
    worker_join_timeout_s: float


@dataclass(slots=True)
class UiConfig:
    enabled: bool
    refresh_interval_ms: int


@dataclass(slots=True)
class LoggingConfig:
    level: str
    logs_dir: str


@dataclass(slots=True)
class DatabaseConfig:
    enabled: bool
    path: str
    init_on_startup: bool


@dataclass(slots=True)
class Settings:
    app: AppConfig
    monitor: MonitorConfig
    workers: WorkerConfig
    ui: UiConfig
    logging: LoggingConfig
    database: DatabaseConfig


# ==========================================================
# Helpers internos
# ==========================================================
def _read_yaml_file(file_path: Path) -> dict[str, Any]:
    if not file_path.exists():
        raise FileNotFoundError(f"No existe el archivo de configuración: {file_path}")

    with file_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if not isinstance(data, dict):
        raise ValueError("El archivo de configuración debe contener un objeto YAML válido.")

    return data


def _build_settings(data: dict[str, Any]) -> Settings:
    app_data = data.get("app", {})
    monitor_data = data.get("monitor", {})
    workers_data = data.get("workers", {})
    ui_data = data.get("ui", {})
    logging_data = data.get("logging", {})
    database_data = data.get("database", {})

    return Settings(
        app=AppConfig(
            name=app_data.get("name", "ONT Tester NEXUS"),
            version=app_data.get("version", "0.1.0"),
            environment=app_data.get("environment", "development"),
        ),
        monitor=MonitorConfig(
            heartbeat_interval_s=float(monitor_data.get("heartbeat_interval_s", 2.0)),
            poll_interval_s=float(monitor_data.get("poll_interval_s", 2.0)),
            disconnect_threshold=int(monitor_data.get("disconnect_threshold", 3)),
        ),
        workers=WorkerConfig(
            max_workers=int(workers_data.get("max_workers", 24)),
            worker_join_timeout_s=float(workers_data.get("worker_join_timeout_s", 5.0)),
        ),
        ui=UiConfig(
            enabled=bool(ui_data.get("enabled", True)),
            refresh_interval_ms=int(ui_data.get("refresh_interval_ms", 500)),
        ),
        logging=LoggingConfig(
            level=str(logging_data.get("level", "INFO")),
            logs_dir=str(logging_data.get("logs_dir", "data/logs")),
        ),
        database=DatabaseConfig(
            enabled=bool(database_data.get("enabled", True)),
            path=str(database_data.get("path", "data/runtime/nexus.db")),
            init_on_startup=bool(database_data.get("init_on_startup", True)),
        ),
    )


# ==========================================================
# API pública
# ==========================================================
def load_settings(file_path: str | Path | None = None) -> Settings:
    config_path = Path(file_path) if file_path else DEFAULT_APP_SETTINGS_PATH
    raw_data = _read_yaml_file(config_path)
    return _build_settings(raw_data)