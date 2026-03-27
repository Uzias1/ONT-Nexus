from __future__ import annotations

import logging
import platform
import re
import subprocess

from app.infrastructure.logging.logger import get_logger, log_console


class ArpScanner:
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

        except subprocess.TimeoutExpired:
            log_console(
                self._logger,
                logging.WARNING,
                "Timeout consultando ARP para %s.",
                ip,
            )
            return None

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

        return ["arp", "-n", ip]

    def _extract_mac(self, text: str) -> str | None:
        match = self.MAC_REGEX.search(text)
        if not match:
            return None

        return match.group(0).replace("-", ":").upper()