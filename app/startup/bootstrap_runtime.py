from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

from app.application.event_bus.bus import EventBus
from app.application.services.station_service import StationService
from app.infrastructure.config.settings import Settings, load_settings
from app.infrastructure.logging.logger import get_logger, log_both, log_console, setup_logging
from app.workers.supervisor import Supervisor


logger = get_logger(__name__)


@dataclass(slots=True)
class RuntimeBundle:
    settings: Settings
    event_bus: EventBus
    supervisor: Supervisor
    station_service: StationService


def initialize_database(settings: Settings) -> None:
    if not settings.database.enabled:
        log_console(logger, logging.INFO, "Base de datos deshabilitada por configuración.")
        return

    if not settings.database.init_on_startup:
        log_console(logger, logging.INFO, "Inicialización de base de datos omitida por configuración.")
        return

    log_both(
        logger,
        logging.INFO,
        "Inicialización de BD pendiente. Ruta configurada: %s",
        settings.database.path,
    )


def bootstrap_runtime(
    on_progress: Callable[[str, int], None] | None = None,
) -> RuntimeBundle:
    def emit(message: str, value: int) -> None:
        if on_progress is not None:
            on_progress(message, value)

    emit("Cargando configuración...", 10)
    settings = load_settings()

    setup_logging(settings)
    log_both(logger, logging.INFO, "Iniciando %s v%s", settings.app.name, settings.app.version)
    log_console(logger, logging.INFO, "Entorno: %s", settings.app.environment)
    log_console(logger, logging.INFO, "Máximo de workers: %s", settings.workers.max_workers)
    log_console(logger, logging.INFO, "Heartbeat: %ss", settings.monitor.heartbeat_interval_s)

    emit("Inicializando base de datos...", 30)
    initialize_database(settings)

    emit("Inicializando bus de eventos...", 45)
    event_bus = EventBus()
    log_console(logger, logging.INFO, "EventBus inicializado correctamente.")

    emit("Creando supervisor...", 65)
    supervisor = Supervisor(settings=settings, event_bus=event_bus)

    emit("Preparando servicios de estación...", 82)
    station_service = StationService(supervisor=supervisor)

    emit("Arrancando hilos de gestión...", 92)
    station_service.start_station()

    emit("Preparando interfaz...", 100)
    return RuntimeBundle(
        settings=settings,
        event_bus=event_bus,
        supervisor=supervisor,
        station_service=station_service,
    )