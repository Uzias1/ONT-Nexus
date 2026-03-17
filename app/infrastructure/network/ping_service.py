from __future__ import annotations

import platform
import subprocess

from app.infrastructure.logging.logger import get_logger


class PingService:
    """
    Servicio de conectividad básica por ping.

    Se usa para validar presencia de un equipo en la IP esperada del slot.
    No forma parte del plan de pruebas funcionales; su objetivo es monitoreo.
    """

    def __init__(self, timeout_ms: int = 1000) -> None:
        self._timeout_ms = timeout_ms
        self._logger = get_logger(self.__class__.__name__)

    def ping(self, ip: str) -> bool:
        """
        Devuelve True si la IP responde a ping, False en caso contrario.
        """
        ip = str(ip).strip()
        if not ip:
            return False

        command = self._build_command(ip)

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=self._subprocess_timeout_seconds(),
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            self._logger.debug(
                "Ping timeout para IP %s",
                ip,
                extra={"log_to_console": True, "log_to_file": False},
            )
            return False
        except Exception:
            self._logger.exception(
                "Error no controlado ejecutando ping para IP %s",
                ip,
                extra={"log_to_console": True, "log_to_file": False},
            )
            return False

    def _build_command(self, ip: str) -> list[str]:
        """
        Construye el comando de ping según el sistema operativo.
        """
        system_name = platform.system().lower()

        if system_name == "windows":
            # -n 1     = un paquete
            # -w 1000  = timeout en milisegundos
            return ["ping", "-n", "1", "-w", str(self._timeout_ms), ip]

        # Linux / macOS / otros Unix-like
        # -c 1 = un paquete
        # -W 1 = timeout en segundos (Linux)
        timeout_seconds = max(1, self._timeout_ms // 1000)
        return ["ping", "-c", "1", "-W", str(timeout_seconds), ip]

    def _subprocess_timeout_seconds(self) -> float:
        """
        Timeout del subprocess para evitar bloqueos largos.
        """
        return max(1.5, (self._timeout_ms / 1000) + 0.5)