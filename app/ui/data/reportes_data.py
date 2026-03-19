from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, date
from random import Random
from typing import Iterable


@dataclass(frozen=True)
class ReportRecord:
    id: int
    timestamp: datetime
    fabricante: str
    modelo: str
    puerto: int
    ip: str
    estatus: str


@dataclass(frozen=True)
class TestResultRecord:
    id: int
    sn: str
    mac: str
    ping: str
    factory_reset: str
    actualizacion_software: str
    usb: str
    wifi_24: str
    wifi_5: str
    tx: str
    rx: str


def normalize_status(value: str) -> str:
    raw = (value or "").strip().upper()

    if raw in {"VALIDO", "ACTIVO", "OK", "SUCCESS"}:
        return "VALIDO"

    if raw in {"INVALIDO", "INACTIVO", "FAIL", "ERROR"}:
        return "INVALIDO"

    return "INVALIDO"


class ReportesDataSource:
    FABRICANTES_MODELOS = {
        "ZTE": ["F670L", "F6600", "ZXHN F660"],
        "FIBERHOME": ["HG6145F", "AN5506-04", "HG6245D"],
        "HUAWEI": ["HG8145V5", "EG8141A5", "HG8245H"],
    }

    def __init__(self) -> None:
        self._rng = Random(42)
        self._records = self._build_mock_data()
        self._test_records = self._build_test_result_data()

    def get_all_records(self) -> list[ReportRecord]:
        return list(self._records)

    def get_all_test_records(self) -> list[TestResultRecord]:
        return list(self._test_records)

    def get_unique_values(self, records: Iterable[ReportRecord], field_name: str) -> list[str]:
        values = []
        for record in records:
            value = getattr(record, field_name)
            if field_name == "timestamp":
                value = record.timestamp.date().isoformat()
            else:
                value = str(value)
            values.append(value)
        return sorted(set(values))

    def get_unique_test_values(self, records: Iterable[TestResultRecord], field_name: str) -> list[str]:
        values = [str(getattr(record, field_name)).strip() for record in records]
        return sorted({value for value in values if value})

    def filter_records(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        fabricante: str | None = None,
        modelo: str | None = None,
        puerto: str | None = None,
        ip: str | None = None,
        estatus: str | None = None,
        ip_contains: str | None = None,
    ) -> list[ReportRecord]:
        rows = self.get_all_records()

        if start_date is not None:
            rows = [r for r in rows if r.timestamp.date() >= start_date]

        if end_date is not None:
            rows = [r for r in rows if r.timestamp.date() <= end_date]

        if fabricante:
            rows = [r for r in rows if r.fabricante == fabricante]

        if modelo:
            rows = [r for r in rows if r.modelo == modelo]

        if puerto:
            rows = [r for r in rows if str(r.puerto) == str(puerto)]

        if ip:
            rows = [r for r in rows if r.ip == ip]

        if estatus:
            rows = [r for r in rows if normalize_status(r.estatus) == normalize_status(estatus)]

        if ip_contains:
            needle = ip_contains.strip().lower()
            rows = [r for r in rows if needle in r.ip.lower()]

        rows.sort(key=lambda x: x.timestamp, reverse=True)
        return rows

    def filter_test_records(
        self,
        sn: str | None = None,
        mac: str | None = None,
        ping: str | None = None,
        factory_reset: str | None = None,
        actualizacion_software: str | None = None,
        usb: str | None = None,
        wifi_24: str | None = None,
        wifi_5: str | None = None,
        tx: str | None = None,
        rx: str | None = None,
        sn_contains: str | None = None,
        mac_contains: str | None = None,
    ) -> list[TestResultRecord]:
        rows = self.get_all_test_records()

        if sn:
            rows = [r for r in rows if r.sn == sn]

        if mac:
            rows = [r for r in rows if r.mac == mac]

        if ping:
            rows = [r for r in rows if r.ping == ping]

        if factory_reset:
            rows = [r for r in rows if r.factory_reset == factory_reset]

        if actualizacion_software:
            rows = [r for r in rows if r.actualizacion_software == actualizacion_software]

        if usb:
            rows = [r for r in rows if r.usb == usb]

        if wifi_24:
            rows = [r for r in rows if r.wifi_24 == wifi_24]

        if wifi_5:
            rows = [r for r in rows if r.wifi_5 == wifi_5]

        if tx:
            rows = [r for r in rows if r.tx == tx]

        if rx:
            rows = [r for r in rows if r.rx == rx]

        if sn_contains:
            needle = sn_contains.strip().lower()
            rows = [r for r in rows if needle in r.sn.lower()]

        if mac_contains:
            needle = mac_contains.strip().lower()
            rows = [r for r in rows if needle in r.mac.lower()]

        rows.sort(key=lambda x: (x.id, x.sn))
        return rows

    def build_status_summary(self, records: Iterable[ReportRecord]) -> dict[str, int]:
        validos = 0
        invalidos = 0

        for record in records:
            status = normalize_status(record.estatus)
            if status == "VALIDO":
                validos += 1
            else:
                invalidos += 1

        return {"VALIDO": validos, "INVALIDO": invalidos}

    def build_weekly_success_series(self, records: Iterable[ReportRecord]) -> list[dict]:
        today = date.today()
        monday_current = today - timedelta(days=today.weekday())

        mondays = [
            monday_current - timedelta(weeks=3),
            monday_current - timedelta(weeks=2),
            monday_current - timedelta(weeks=1),
            monday_current,
        ]

        series = []

        for idx, monday in enumerate(mondays):
            saturday = monday + timedelta(days=5)
            week_rows = [r for r in records if monday <= r.timestamp.date() <= saturday]

            points = []
            labels = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]

            for day_index in range(6):
                day = monday + timedelta(days=day_index)
                day_rows = [r for r in week_rows if r.timestamp.date() == day]

                total = len(day_rows)
                if total == 0:
                    success_pct = 0.0
                else:
                    valid_count = sum(1 for r in day_rows if normalize_status(r.estatus) == "VALIDO")
                    success_pct = (valid_count / total) * 100.0

                points.append((day_index, round(success_pct, 2)))

            series.append({
                "label": f"Semana {monday.strftime('%d %b')} - {saturday.strftime('%d %b')}",
                "start": monday,
                "end": saturday,
                "points": points,
                "is_current": idx == 3,
                "x_labels": labels,
            })

        return series

    def _build_mock_data(self) -> list[ReportRecord]:
        rows: list[ReportRecord] = []
        today = datetime.now()
        start_day = today.date() - timedelta(days=40)

        record_id = 1

        for day_offset in range(41):
            current_day = start_day + timedelta(days=day_offset)
            if current_day.weekday() == 6:
                continue

            daily_count = self._rng.randint(5, 12)

            for _ in range(daily_count):
                fabricante = self._rng.choice(list(self.FABRICANTES_MODELOS.keys()))
                modelo = self._rng.choice(self.FABRICANTES_MODELOS[fabricante])
                puerto = self._rng.randint(1, 24)
                hour = self._rng.randint(8, 19)
                minute = self._rng.randint(0, 59)
                second = self._rng.randint(0, 59)

                timestamp = datetime(current_day.year, current_day.month, current_day.day, hour, minute, second)
                estatus = "VALIDO" if self._rng.random() < 0.82 else "INVALIDO"
                ip = f"192.168.{self._rng.randint(1, 3)}.{self._rng.randint(2, 254)}"

                rows.append(ReportRecord(record_id, timestamp, fabricante, modelo, puerto, ip, estatus))
                record_id += 1

        rows.sort(key=lambda x: x.timestamp, reverse=True)
        return rows

    def _build_test_result_data(self) -> list[TestResultRecord]:
        rows: list[TestResultRecord] = []

        base_ids = list(range(1, 31))
        repeated_ids = [
            3, 5, 7, 8, 10, 12, 14, 15, 18, 20,
            21, 22, 24, 25, 27, 28, 30, 6, 9, 11,
            13, 16, 17, 19, 23, 26, 29, 4, 2, 1,
        ]
        ids = base_ids + repeated_ids

        status_values = ["Pass", "Fail", "Desactivado"]
        software_values = ["Pass", "Fail", "Desactivado", "No File"]

        for index, record_id in enumerate(ids, start=1):
            sn = f"SN{index:08d}"
            mac = "AC:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}".format(
                (index * 3) % 256,
                (index * 5) % 256,
                (index * 7) % 256,
                (index * 11) % 256,
                (index * 13) % 256,
            )

            rows.append(
                TestResultRecord(
                    id=record_id,
                    sn=sn,
                    mac=mac,
                    ping=status_values[index % 3],
                    factory_reset=status_values[(index + 1) % 3],
                    actualizacion_software=software_values[index % 4],
                    usb=status_values[(index + 2) % 3],
                    wifi_24=status_values[(index + 3) % 3],
                    wifi_5=status_values[(index + 4) % 3],
                    tx=status_values[(index + 5) % 3],
                    rx=status_values[(index + 6) % 3],
                )
            )

        return rows
        rows: list[TestResultRecord] = []

        status_values = ["Pass", "Fail", "Desactivado"]
        software_values = ["Pass", "Fail", "Desactivado", "No File"]
        max_station_id = 24

        for attempt in range(60):
            logical_id = (attempt % max_station_id) + 1
            cycle_index = attempt // max_station_id

            sn = f"SN{logical_id:04d}{attempt + 1:04d}"
            mac = "AC:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}".format(
                (logical_id * 7 + attempt * 3) % 256,
                (logical_id * 11 + attempt * 5) % 256,
                (logical_id * 13 + attempt * 7) % 256,
                (logical_id * 17 + attempt * 9) % 256,
                (logical_id * 19 + attempt * 11) % 256,
            )

            ping = status_values[(attempt + logical_id + 0) % 3]
            factory_reset = status_values[(attempt + logical_id + 1) % 3]
            actualizacion_software = software_values[(attempt + logical_id) % 4]
            usb = status_values[(attempt + logical_id + 2) % 3]
            wifi_24 = status_values[(attempt + logical_id + 3) % 3]
            wifi_5 = status_values[(attempt + logical_id + 4) % 3]
            tx = status_values[(attempt + logical_id + 5) % 3]
            rx = status_values[(attempt + logical_id + cycle_index + 1) % 3]

            rows.append(
                TestResultRecord(
                    id=logical_id,
                    sn=sn,
                    mac=mac,
                    ping=ping,
                    factory_reset=factory_reset,
                    actualizacion_software=actualizacion_software,
                    usb=usb,
                    wifi_24=wifi_24,
                    wifi_5=wifi_5,
                    tx=tx,
                    rx=rx,
                )
            )

        rows.sort(key=lambda x: (x.id, x.sn))
        return rows
