from __future__ import annotations

import platform
import re
import subprocess

from app.infrastructure.logging.logger import get_logger


class ArpScanner:
    """
    Servicio simple para extraer la MAC asociada a una IP desde la tabla ARP local.

    Normalmente funciona mejor después de que la IP ya respondió a ping.
    """

    MAC_REGEX = re.compile(r"([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})")

    def __init__(self) -> None:
        self._logger = get_logger(self.__class__.__name__)

    def get_mac(self, ip: str) -> str | None:
        ip = str(ip).strip()
        if not ip:
            return None

        command = self._build_command(ip)

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=2.0,
            )

            output = f"{result.stdout}\n{result.stderr}"
            return self._extract_mac(output)

        except Exception:
            self._logger.exception(
                "Error extrayendo MAC por ARP para IP %s",
                ip,
                extra={"log_to_console": True, "log_to_file": False},
            )
            return None

    def _build_command(self, ip: str) -> list[str]:
        system_name = platform.system().lower()

        if system_name == "windows":
            return ["arp", "-a", ip]

        # Linux / macOS / Unix-like
        return ["arp", "-n", ip]

    def _extract_mac(self, text: str) -> str | None:
        match = self.MAC_REGEX.search(text)
        if not match:
            return None

        mac = match.group(0).replace("-", ":").upper()
        return mac