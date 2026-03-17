from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_APP_SETTINGS_PATH = PROJECT_ROOT / "data" / "config" / "app_settings.yaml"
DEFAULT_STATION_MAP_PATH = PROJECT_ROOT / "data" / "config" / "station_map.yaml"


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
class StationEntryConfig:
    worker_id: str
    port_index: int
    expected_ip: str


@dataclass(slots=True)
class Settings:
    app: AppConfig
    monitor: MonitorConfig
    workers: WorkerConfig
    ui: UiConfig
    logging: LoggingConfig
    database: DatabaseConfig
    station_map: list[StationEntryConfig] = field(default_factory=list)


def _read_yaml_file(file_path: Path) -> dict[str, Any]:
    if not file_path.exists():
        raise FileNotFoundError(f"No existe el archivo de configuración: {file_path}")

    with file_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    if not isinstance(data, dict):
        raise ValueError("El archivo de configuración debe contener un objeto YAML válido.")

    return data


def _build_station_map(data: dict[str, Any]) -> list[StationEntryConfig]:
    raw_stations = data.get("stations", [])
    if not isinstance(raw_stations, list):
        raise TypeError("El archivo station_map.yaml debe contener una lista en 'stations'.")

    station_map: list[StationEntryConfig] = []

    for item in raw_stations:
        if not isinstance(item, dict):
            raise TypeError("Cada entrada de 'stations' debe ser un diccionario.")

        worker_id = str(item.get("worker_id", "")).strip()
        expected_ip = str(item.get("expected_ip", "")).strip()
        port_index = int(item.get("port_index", 0))

        if not worker_id:
            raise ValueError("Cada estación debe tener 'worker_id'.")
        if not expected_ip:
            raise ValueError(f"La estación '{worker_id}' debe tener 'expected_ip'.")
        if port_index <= 0:
            raise ValueError(f"La estación '{worker_id}' debe tener 'port_index' válido.")

        station_map.append(
            StationEntryConfig(
                worker_id=worker_id,
                port_index=port_index,
                expected_ip=expected_ip,
            )
        )

    return station_map


def _build_settings(
    app_data: dict[str, Any],
    station_map_data: dict[str, Any],
) -> Settings:
    app_section = app_data.get("app", {})
    monitor_section = app_data.get("monitor", {})
    workers_section = app_data.get("workers", {})
    ui_section = app_data.get("ui", {})
    logging_section = app_data.get("logging", {})
    database_section = app_data.get("database", {})

    station_map = _build_station_map(station_map_data)

    return Settings(
        app=AppConfig(
            name=app_section.get("name", "ONT Tester NEXUS"),
            version=app_section.get("version", "0.1.0"),
            environment=app_section.get("environment", "development"),
        ),
        monitor=MonitorConfig(
            heartbeat_interval_s=float(monitor_section.get("heartbeat_interval_s", 2.0)),
            poll_interval_s=float(monitor_section.get("poll_interval_s", 2.0)),
            disconnect_threshold=int(monitor_section.get("disconnect_threshold", 3)),
        ),
        workers=WorkerConfig(
            max_workers=int(workers_section.get("max_workers", 24)),
            worker_join_timeout_s=float(workers_section.get("worker_join_timeout_s", 5.0)),
        ),
        ui=UiConfig(
            enabled=bool(ui_section.get("enabled", True)),
            refresh_interval_ms=int(ui_section.get("refresh_interval_ms", 500)),
        ),
        logging=LoggingConfig(
            level=str(logging_section.get("level", "INFO")),
            logs_dir=str(logging_section.get("logs_dir", "data/logs")),
        ),
        database=DatabaseConfig(
            enabled=bool(database_section.get("enabled", True)),
            path=str(database_section.get("path", "data/runtime/nexus.db")),
            init_on_startup=bool(database_section.get("init_on_startup", True)),
        ),
        station_map=station_map,
    )


def load_settings(
    app_settings_path: str | Path | None = None,
    station_map_path: str | Path | None = None,
) -> Settings:
    app_config_path = Path(app_settings_path) if app_settings_path else DEFAULT_APP_SETTINGS_PATH
    station_config_path = Path(station_map_path) if station_map_path else DEFAULT_STATION_MAP_PATH

    app_data = _read_yaml_file(app_config_path)
    station_map_data = _read_yaml_file(station_config_path)

    return _build_settings(app_data, station_map_data)