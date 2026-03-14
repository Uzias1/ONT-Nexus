from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import TypeVar

from app.application.event_bus.events import DomainEvent
from app.infrastructure.logging.logger import get_logger


EventHandler = Callable[[DomainEvent], None]
TEventName = TypeVar("TEventName", bound=str)


class EventBus:
    """
    Bus de eventos simple en memoria.

    Permite suscribir handlers por nombre de evento y publicar eventos
    sin acoplar directamente productores y consumidores.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._logger = get_logger(self.__class__.__name__)

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """
        Registra un handler para un nombre de evento.
        """
        self._subscribers[event_name].append(handler)
        self._logger.debug("Handler suscrito a evento '%s': %s", event_name, handler)

    def publish(self, event: DomainEvent) -> None:
        """
        Publica un evento a todos los handlers suscritos.
        """
        handlers = self._subscribers.get(event.event_name, [])

        self._logger.debug(
            "Publicando evento '%s' a %s handler(s). Payload=%s",
            event.event_name,
            len(handlers),
            event.payload,
        )

        for handler in handlers:
            try:
                handler(event)
            except Exception:
                self._logger.exception(
                    "Error ejecutando handler para evento '%s'. Handler=%s",
                    event.event_name,
                    handler,
                )