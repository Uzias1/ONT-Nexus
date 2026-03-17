from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from app.application.event_bus.bus import EventBus
from app.application.services.station_service import StationService
from app.infrastructure.config.settings import Settings, load_settings
from app.infrastructure.logging.logger import (
    get_logger,
    log_both,
    log_console,
    log_file,
    setup_logging,
)
from app.ui.main_window import MainWindow
from app.workers.supervisor import Supervisor


logger = get_logger(__name__)


def initialize_database(settings: Settings) -> None:
    """
    Punto de inicialización de base de datos.
    Por ahora queda como placeholder.
    """
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


def bootstrap() -> tuple[Settings, EventBus, Supervisor, StationService]:
    """
    Carga configuración e inicializa los componentes base del sistema.
    """
    settings = load_settings()
    setup_logging(settings)

    log_both(logger, logging.INFO, "Iniciando %s v%s", settings.app.name, settings.app.version)
    log_console(logger, logging.INFO, "Entorno: %s", settings.app.environment)
    log_console(logger, logging.INFO, "Máximo de workers: %s", settings.workers.max_workers)
    log_console(logger, logging.INFO, "Heartbeat: %ss", settings.monitor.heartbeat_interval_s)

    initialize_database(settings)

    event_bus = EventBus()
    log_console(logger, logging.INFO, "EventBus inicializado correctamente.")

    supervisor = Supervisor(settings=settings, event_bus=event_bus)
    station_service = StationService(supervisor=supervisor)

    return settings, event_bus, supervisor, station_service


def run() -> int:
    """
    Arranque principal de la aplicación con PySide6.
    """
    settings, event_bus, supervisor, station_service = bootstrap()

    app = QApplication(sys.argv)
    app.setApplicationName(settings.app.name)

    station_service.start_station()

    window = MainWindow(
        settings=settings,
        event_bus=event_bus,
        station_service=station_service,
    )
    window.show()

    exit_code = app.exec()

    station_service.stop_station()
    log_both(logger, logging.INFO, "Aplicación finalizada correctamente.")

    _ = supervisor
    return exit_code


def main() -> int:
    try:
        return run()
    except KeyboardInterrupt:
        log_both(logger, logging.WARNING, "Ejecución interrumpida por el usuario.")
        return 130
    except Exception:
        log_file(logger, logging.ERROR, "Excepción no controlada en el hilo principal.", exc_info=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())