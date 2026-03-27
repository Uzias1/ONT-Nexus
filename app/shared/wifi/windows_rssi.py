from __future__ import annotations

import re
import subprocess
import time
from typing import Any


def scan_wifi_windows(
    target_ssid: str | None = None,
    retries: int = 3,
    delay: float = 1.0,
    debug: bool = False,
) -> list[dict[str, Any]]:
    """
    Escanea redes WiFi en Windows usando:
        netsh wlan show networks mode=bssid

    Basado en la lógica existente de common_mixin.
    """

    cmd = ["netsh", "wlan", "show", "networks", "mode=bssid"]
    all_networks: list[dict[str, Any]] = []

    def parse_output(output: str) -> list[dict[str, Any]]:
        networks: list[dict[str, Any]] = []
        current_ssid: str | None = None
        current_bssid_index = 0

        for line in output.splitlines():
            line = line.strip()

            if line.startswith("SSID ") and " : " in line:
                parts = line.split(" : ", 1)
                current_ssid = parts[1].strip()
                current_bssid_index = 0
                continue

            if current_ssid is None:
                continue

            if line.startswith("BSSID "):
                current_bssid_index += 1
                networks.append(
                    {
                        "ssid": current_ssid,
                        "bssid_index": current_bssid_index,
                        "bssid": None,
                        "signal_percent": None,
                        "channel": None,
                        "radio_type": None,
                    }
                )
                continue

            if not networks:
                continue

            net = networks[-1]

            if line.lower().startswith("bssid "):
                parts = line.split(" : ", 1)
                if len(parts) == 2:
                    net["bssid"] = parts[1].strip()

            elif line.lower().startswith("señal") or line.lower().startswith("signal"):
                m = re.search(r"(\d+)%", line)
                if m:
                    net["signal_percent"] = int(m.group(1))

            elif line.lower().startswith("tipo de radio") or line.lower().startswith("radio type"):
                parts = line.split(" : ", 1)
                if len(parts) == 2:
                    net["radio_type"] = parts[1].strip()

            elif line.lower().startswith("canal") or line.lower().startswith("channel"):
                parts = line.split(" : ", 1)
                if len(parts) == 2:
                    try:
                        net["channel"] = int(parts[1].strip())
                    except ValueError:
                        net["channel"] = parts[1].strip()

            elif "%" in line and net.get("signal_percent") is None:
                lower = line.lower()
                if "uso del canal" in lower or "capacidad disponible" in lower:
                    pass
                else:
                    m = re.search(r"(\d+)%", line)
                    if m:
                        net["signal_percent"] = int(m.group(1))

        return networks

    for attempt in range(retries):
        proc = subprocess.run(
            cmd,
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

        try:
            output = proc.stdout.decode("cp850", errors="ignore")
        except Exception:
            output = proc.stdout.decode(errors="ignore")

        nets = parse_output(output)

        if debug:
            print(f"[SCAN WIFI] Intento {attempt + 1}, {len(nets)} redes:")
            for n in nets:
                print(
                    f"  SSID='{n['ssid']}', signal={n['signal_percent']}%, "
                    f"ch={n['channel']}, radio={n['radio_type']}"
                )

        for n in nets:
            if not any(
                m["ssid"] == n["ssid"] and m["bssid"] == n["bssid"]
                for m in all_networks
            ):
                all_networks.append(n)

        if target_ssid:
            t = target_ssid.strip().lower()
            if any(n["ssid"] and n["ssid"].strip().lower() == t for n in all_networks):
                break

        time.sleep(delay)

    if target_ssid:
        t = target_ssid.strip().lower()
        all_networks = [
            n for n in all_networks if n["ssid"] and n["ssid"].strip().lower() == t
        ]

    return all_networks


def evaluate_wifi_rssi_windows(
    ssid_24: str,
    ssid_5: str,
) -> dict[str, Any]:
    """
    Basado en test_wifi_rssi_windows de common_mixin.
    Devuelve un resultado compartido para 2.4 y 5 GHz.
    """

    result = {
        "name": "potencia_wifi",
        "status": "FAIL",
        "details": {
            "ssid_24": ssid_24,
            "ssid_5": ssid_5,
            "best_24_percent": None,
            "best_5_percent": None,
            "pass_24": False,
            "pass_5": False,
            "raw_24": [],
            "raw_5": [],
            "errors": [],
        },
    }

    nets_24 = scan_wifi_windows(ssid_24)
    nets_5 = scan_wifi_windows(ssid_5)

    result["details"]["raw_24"] = nets_24
    result["details"]["raw_5"] = nets_5

    if not nets_24:
        result["details"]["errors"].append(f"No se encontró red 2.4G: {ssid_24}")
    if not nets_5:
        result["details"]["errors"].append(f"No se encontró red 5G: {ssid_5}")

    if not nets_24 and not nets_5:
        return result

    def _best_signal(net_list: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not net_list:
            return None
        return max(
            (n for n in net_list if n.get("signal_percent") is not None),
            key=lambda n: n["signal_percent"],
            default=None,
        )

    best_24 = _best_signal(nets_24)
    best_5 = _best_signal(nets_5)

    if best_24:
        result["details"]["best_24_percent"] = best_24["signal_percent"]
    if best_5:
        result["details"]["best_5_percent"] = best_5["signal_percent"]

    p24 = result["details"]["best_24_percent"]
    p5 = result["details"]["best_5_percent"]

    pass_24 = p24 is not None
    pass_5 = p5 is not None

    result["details"]["pass_24"] = bool(pass_24)
    result["details"]["pass_5"] = bool(pass_5)

    if pass_24 and pass_5:
        result["status"] = "PASS"

    return result