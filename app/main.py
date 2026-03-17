from __future__ import annotations

import logging

from app.application.event_bus.bus import EventBus
from app.infrastructure.config.settings import Settings, load_settings
from app.infrastructure.logging.logger import (
    get_logger,
    log_both,
    log_console,
    setup_logging,
)
from app.ui.app import run_ui


logger = get_logger(__name__)


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


def bootstrap() -> tuple[Settings, EventBus]:
    settings = load_settings()
    setup_logging(settings)

    log_both(logger, logging.INFO, "Iniciando %s v%s", settings.app.name, settings.app.version)
    log_console(logger, logging.INFO, "Entorno: %s", settings.app.environment)
    log_console(logger, logging.INFO, "Máximo de workers: %s", settings.workers.max_workers)
    log_console(logger, logging.INFO, "Heartbeat: %ss", settings.monitor.heartbeat_interval_s)

    initialize_database(settings)

    event_bus = EventBus()
    log_console(logger, logging.INFO, "EventBus inicializado correctamente.")

    return settings, event_bus


def run() -> int:
    settings, event_bus = bootstrap()

    log_console(logger, logging.INFO, "Sistema base cargado correctamente.")
    log_console(logger, logging.INFO, "Inicializando UI...")

    _ = settings
    _ = event_bus

    return run_ui()


if __name__ == "__main__":
    raise SystemExit(run())