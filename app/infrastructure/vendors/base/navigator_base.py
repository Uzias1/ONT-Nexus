from __future__ import annotations

from abc import ABC, abstractmethod

from app.infrastructure.selenium.selenium_session import SeleniumSession


class NavigatorBase(ABC):
    """
    Base común para navegadores Selenium por vendor.
    """

    def __init__(self, session: SeleniumSession) -> None:
        self.session = session

    @abstractmethod
    def open_root(self, ip: str) -> None:
        """
        Abre la página principal del equipo.
        """
        raise NotImplementedError

    @abstractmethod
    def login(self, username: str, password: str) -> None:
        """
        Realiza login en la interfaz web del equipo.
        """
        raise NotImplementedError