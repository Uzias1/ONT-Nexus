from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.application.event_bus.bus import EventBus
from app.application.services.station_service import StationService
from app.infrastructure.config.settings import Settings


TEST_LABELS = [
    "PING",
    "FACTORY RESET",
    "SOFTWARE UPDATE",
    "USB",
    "FIBER TX",
    "FIBER RX",
    "WIFI 2.4",
    "WIFI 5.0",
]

PHASE_TO_INDEX = {
    "FACTORY_RESET": 1,
    "SOFTWARE_UPDATE": 2,
    "USB": 3,
    "FIBER_TX": 4,
    "FIBER_RX": 5,
    "WIFI_2G": 6,
    "WIFI_5G": 7,
}


@dataclass(slots=True)
class PortUiState:
    worker_id: str
    connected: bool = False
    status: str = "IDLE"
    phase: str = "WAITING"
    expected_ip: str | None = None
    device_ip: str | None = None
    device_mac: str | None = None
    circle_states: list[str] = field(default_factory=lambda: ["IDLE"] * 8)


class StatusCircle(QWidget):
    def __init__(self, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._label = label
        self._state = "IDLE"
        self.setMinimumSize(105, 95)

    def set_state(self, state: str) -> None:
        self._state = state
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        _ = event

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect()
        diameter = 32
        x = (rect.width() - diameter) // 2
        y = 8

        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.setBrush(self._map_color(self._state))
        painter.drawEllipse(x, y, diameter, diameter)

        text_rect = rect.adjusted(4, 48, -4, -4)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            self._label,
        )

    @staticmethod
    def _map_color(state: str) -> QColor:
        mapping = {
            "IDLE": QColor("#9CA3AF"),
            "RUNNING": QColor("#F59E0B"),
            "PASS": QColor("#22C55E"),
            "FAIL": QColor("#EF4444"),
            "OFFLINE": QColor("#6B7280"),
        }
        return mapping.get(state, QColor("#9CA3AF"))


class PortRowWidget(QWidget):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._title = QLabel(title)
        self._title.setStyleSheet("font-size: 16px; font-weight: 700;")

        self._subtitle = QLabel("Esperando eventos...")
        self._subtitle.setStyleSheet("font-size: 12px; color: #666;")

        self._circles: list[StatusCircle] = [StatusCircle(label) for label in TEST_LABELS]

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        root.addWidget(self._title)
        root.addWidget(self._subtitle)

        circles_layout = QHBoxLayout()
        circles_layout.setSpacing(12)

        for circle in self._circles:
            circles_layout.addWidget(circle)

        root.addLayout(circles_layout)

    def apply_state(self, ui_state: PortUiState) -> None:
        subtitle = (
            f"expected_ip={ui_state.expected_ip or '-'} | "
            f"device_ip={ui_state.device_ip or '-'} | "
            f"mac={ui_state.device_mac or '-'} | "
            f"connected={ui_state.connected} | "
            f"status={ui_state.status} | "
            f"phase={ui_state.phase}"
        )
        self._subtitle.setText(subtitle)

        for circle, state in zip(self._circles, ui_state.circle_states, strict=False):
            circle.set_state(state)


class MainWindow(QMainWindow):
    def __init__(
        self,
        *,
        settings: Settings,
        event_bus: EventBus,
        station_service: StationService,
    ) -> None:
        super().__init__()

        self._settings = settings
        self._event_bus = event_bus
        self._station_service = station_service

        self._ports: dict[str, PortUiState] = {
            "worker-01": PortUiState(worker_id="worker-01"),
            "worker-02": PortUiState(worker_id="worker-02"),
        }

        self.setWindowTitle(settings.app.name)
        self.resize(1250, 420)

        self._build_ui()
        self._setup_timer()

    def _build_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(18)

        title = QLabel("ONT Tester NEXUS")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        root_layout.addWidget(title)

        subtitle = QLabel("Prueba temporal conectada a worker-01 y worker-02")
        subtitle.setStyleSheet("font-size: 13px; color: #666;")
        root_layout.addWidget(subtitle)

        buttons_layout = QHBoxLayout()
        self._btn_start_1 = QPushButton("Iniciar Puerto 1")
        self._btn_start_2 = QPushButton("Iniciar Puerto 2")
        self._btn_refresh = QPushButton("Refresh manual")

        self._btn_start_1.clicked.connect(lambda: self._start_port_execution("worker-01"))
        self._btn_start_2.clicked.connect(lambda: self._start_port_execution("worker-02"))
        self._btn_refresh.clicked.connect(self._refresh_from_snapshot)

        buttons_layout.addWidget(self._btn_start_1)
        buttons_layout.addWidget(self._btn_start_2)
        buttons_layout.addWidget(self._btn_refresh)
        buttons_layout.addStretch()

        root_layout.addLayout(buttons_layout)

        self._port_1_widget = PortRowWidget("PUERTO 01")
        self._port_2_widget = PortRowWidget("PUERTO 02")

        root_layout.addWidget(self._port_1_widget)
        root_layout.addWidget(self._port_2_widget)

        self._refresh_from_snapshot()

    def _setup_timer(self) -> None:
        self._timer = QTimer(self)
        self._timer.setInterval(self._settings.ui.refresh_interval_ms)
        self._timer.timeout.connect(self._consume_events)
        self._timer.start()

    def _start_port_execution(self, worker_id: str) -> None:
        request_data = {
            "worker_id": worker_id,
            "tests": {
                "factory_reset": True,
                "software_update": True,
                "usb": True,
                "fiber_tx": True,
                "fiber_rx": True,
                "wifi_2g": True,
                "wifi_5g": True,
            },
        }
        self._station_service.start_execution(request_data)

    def _refresh_from_snapshot(self) -> None:
        snapshots = self._station_service.get_station_snapshot()

        for snapshot in snapshots:
            worker_id = str(snapshot.get("worker_id"))
            if worker_id not in self._ports:
                continue

            self._apply_snapshot(worker_id, snapshot)

        self._render()

    def _consume_events(self) -> None:
        events = self._event_bus.drain_events()
        if not events:
            return

        for event in events:
            if event.event_name != "worker.state_changed":
                continue

            payload = event.payload
            worker_id = str(payload.get("worker_id"))
            if worker_id not in self._ports:
                continue

            self._apply_snapshot(worker_id, payload)

        self._render()

    def _apply_snapshot(self, worker_id: str, snapshot: dict) -> None:
        port = self._ports[worker_id]

        port.connected = bool(snapshot.get("connected", False))
        port.status = str(snapshot.get("status", "IDLE"))
        port.phase = str(snapshot.get("phase", "WAITING"))
        port.expected_ip = snapshot.get("expected_ip") or snapshot.get("ip")
        port.device_ip = snapshot.get("device_ip")
        port.device_mac = snapshot.get("device_mac") or snapshot.get("mac")

        port.circle_states = self._build_circle_states(
            connected=port.connected,
            status=port.status,
            phase=port.phase,
        )

    def _build_circle_states(self, *, connected: bool, status: str, phase: str) -> list[str]:
        states = ["IDLE"] * 8

        # Indicador de conectividad / ping
        states[0] = "RUNNING" if connected else "OFFLINE"

        if status in {"FAIL", "ERROR"}:
            phase_index = PHASE_TO_INDEX.get(phase)
            if phase_index is not None:
                states[phase_index] = "FAIL"
            return states

        if status == "PASS" and phase == "FINISHED":
            for index in range(1, 8):
                states[index] = "PASS"
            return states

        phase_index = PHASE_TO_INDEX.get(phase)
        if phase_index is not None:
            states[phase_index] = "RUNNING"

        return states

    def _render(self) -> None:
        self._port_1_widget.apply_state(self._ports["worker-01"])
        self._port_2_widget.apply_state(self._ports["worker-02"])