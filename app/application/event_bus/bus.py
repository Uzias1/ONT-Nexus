from __future__ import annotations

from queue import Empty, Queue

from app.application.event_bus.events import DomainEvent
from app.infrastructure.logging.logger import get_logger


class EventBus:
    """
    Bus de eventos en memoria basado en una cola thread-safe.

    Los productores publican eventos.
    Los consumidores (por ejemplo la UI) hacen pull de la cola
    mediante drain_events() o get_nowait().
    """

    def __init__(self) -> None:
        self._queue: Queue[DomainEvent] = Queue()
        self._logger = get_logger(self.__class__.__name__)

    def publish(self, event: DomainEvent) -> None:
        """
        Publica un evento en la cola interna del bus.
        """
        self._queue.put(event)
        self._logger.debug(
            "Evento publicado: %s | payload=%s",
            event.event_name,
            event.payload,
            extra={"log_to_console": True, "log_to_file": False},
        )

    def get_nowait(self) -> DomainEvent | None:
        """
        Devuelve un evento inmediatamente si existe.
        Si la cola está vacía, devuelve None.
        """
        try:
            return self._queue.get_nowait()
        except Empty:
            return None

    def drain_events(self, max_items: int | None = None) -> list[DomainEvent]:
        """
        Extrae múltiples eventos de la cola.

        Parámetros:
        - max_items:
            Si es None, vacía toda la cola.
            Si tiene valor, extrae hasta esa cantidad.
        """
        events: list[DomainEvent] = []
        extracted = 0

        while True:
            if max_items is not None and extracted >= max_items:
                break

            try:
                event = self._queue.get_nowait()
            except Empty:
                break

            events.append(event)
            extracted += 1

        return events

    def size(self) -> int:
        """
        Devuelve el tamaño aproximado de la cola.
        """
        return self._queue.qsize()

    def is_empty(self) -> bool:
        """
        Indica si la cola está vacía.
        """
        return self._queue.empty()