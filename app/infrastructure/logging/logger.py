from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.infrastructure.config.settings import Settings


_LOGGER_CONFIGURED = False


class DestinationFilter(logging.Filter):
    """
    Filtro para decidir si un registro debe pasar a consola o archivo.

    Usa los atributos extra:
    - log_to_console: bool
    - log_to_file: bool

    Si no vienen informados, usa los valores por defecto definidos al crear el filtro.
    """

    def __init__(self, destination: str, default_enabled: bool) -> None:
        super().__init__()
        self.destination = destination
        self.default_enabled = default_enabled

    def filter(self, record: logging.LogRecord) -> bool:
        attr_name = f"log_to_{self.destination}"
        return bool(getattr(record, attr_name, self.default_enabled))


def setup_logging(settings: Settings) -> None:
    """
    Configura el sistema global de logging.

    Consola y archivo usan filtros independientes para permitir decidir
    el destino de cada mensaje con banderas en `extra`.
    """
    global _LOGGER_CONFIGURED

    if _LOGGER_CONFIGURED:
        return

    logs_dir = Path(settings.logging.logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_file = logs_dir / "nexus.log"
    log_level = getattr(logging, settings.logging.level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(threadName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(DestinationFilter(destination="console", default_enabled=True))

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(DestinationFilter(destination="file", default_enabled=False))

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    _LOGGER_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """
    Devuelve un logger con el nombre solicitado.
    """
    return logging.getLogger(name)


def log_console(
    logger: logging.Logger,
    level: int,
    message: str,
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Envía un mensaje solo a consola.
    """
    extra = kwargs.pop("extra", {})
    extra.update({"log_to_console": True, "log_to_file": False})
    logger.log(level, message, *args, extra=extra, **kwargs)


def log_file(
    logger: logging.Logger,
    level: int,
    message: str,
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Envía un mensaje solo a archivo.
    """
    extra = kwargs.pop("extra", {})
    extra.update({"log_to_console": False, "log_to_file": True})
    logger.log(level, message, *args, extra=extra, **kwargs)


def log_both(
    logger: logging.Logger,
    level: int,
    message: str,
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Envía un mensaje a consola y archivo.
    """
    extra = kwargs.pop("extra", {})
    extra.update({"log_to_console": True, "log_to_file": True})
    logger.log(level, message, *args, extra=extra, **kwargs)