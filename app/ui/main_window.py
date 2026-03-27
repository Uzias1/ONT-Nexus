from dataclasses import dataclass, field
from pathlib import Path
import logging

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QStackedWidget

from app.application.event_bus.bus import EventBus
from app.application.services.station_service import StationService
from app.infrastructure.config.settings import Settings
from app.infrastructure.logging.logger import get_logger, log_both, log_console
from app.ui.theme_manager import ThemeManager
from app.ui.views.dashboard_view import DashboardView
from app.ui.views.modificar import ModificarView
from app.ui.views.testeo import TesteoView
from app.ui.views.reportes import ReportesView
from app.application.dto.execution_test_request import ExecutionTestRequest

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
    port_index: int | None = None
    connected: bool = False
    status: str = "IDLE"
    phase: str = "WAITING"
    expected_ip: str | None = None
    device_ip: str | None = None
    device_mac: str | None = None
    device_sn: str | None = None
    vendor: str | None = None
    model: str | None = None
    global_mode: str | None = None
    circle_states: list[str] = field(default_factory=lambda: ["IDLE"] * 8)

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
        self._logger = get_logger(self.__class__.__name__)

        self._ports: dict[str, PortUiState] = {}

        self.setWindowTitle("Vista principal")
        self.setMinimumSize(950, 620)

        self._set_app_icon()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.dashboard_view = DashboardView()
        self.modificar_view = ModificarView()
        self.testeo_view = TesteoView()
        self.reportes_view = ReportesView()

        self.stack.addWidget(self.dashboard_view)
        self.stack.addWidget(self.modificar_view)
        self.stack.addWidget(self.testeo_view)
        self.stack.addWidget(self.reportes_view)

        self.stack.setCurrentWidget(self.dashboard_view)

        self._connect_navigation()
        self.apply_theme()
        self._setup_timer()
        self._refresh_from_snapshot()

    def _set_app_icon(self) -> None:
        icon_path = Path(__file__).resolve().parent / "assets" / "logo_tester.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _connect_navigation(self) -> None:
        self.dashboard_view.btn_modificar.clicked.connect(self.show_modificar)
        self.dashboard_view.btn_testear.clicked.connect(self._start_execution_from_dashboard)
        self.dashboard_view.btn_reportes.clicked.connect(self.show_reportes)

        self.modificar_view.back_requested.connect(self.show_dashboard)

        self.testeo_view.header.btn_back.clicked.connect(self.show_dashboard)
        self.reportes_view.btn_back.clicked.connect(self.show_dashboard)

        self.modificar_view.theme_changed.connect(self.apply_theme)

    def apply_theme(self) -> None:
        theme = ThemeManager.get_theme()

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme.app_bg};
            }}
            QStackedWidget {{
                background-color: {theme.app_bg};
            }}
        """)

        self.dashboard_view.apply_theme()
        self.modificar_view.apply_theme()
        self.testeo_view.apply_theme()
        self.reportes_view.apply_theme()
        self.dashboard_view.status_bar.apply_theme()

        self._apply_native_titlebar_theme()

    def _apply_native_titlebar_theme(self) -> None:
        try:
            import sys
            if sys.platform != "win32":
                return

            import ctypes
            hwnd = int(self.winId())

            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(1 if ThemeManager.is_dark() else 0)

            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
        except Exception:
            pass

    def show_dashboard(self) -> None:
        self.setWindowTitle("Vista principal")
        self.stack.setCurrentWidget(self.dashboard_view)

    def show_modificar(self) -> None:
        self.setWindowTitle("Modificar parámetros")
        self.stack.setCurrentWidget(self.modificar_view)

    def show_testeo(self) -> None:
        self.setWindowTitle("Testeo")
        self.stack.setCurrentWidget(self.testeo_view)

    def show_reportes(self) -> None:
        self.setWindowTitle("Reportes")
        self.stack.setCurrentWidget(self.reportes_view)

    def _start_execution_from_dashboard(self) -> None:
        selected_tests = self.dashboard_view.get_selected_tests()

        if not any(selected_tests.values()):
            log_console(
                self._logger,
                logging.WARNING,
                "No se puede iniciar ejecución: no hay pruebas habilitadas en el dashboard.",
            )
            return

        snapshots = self._station_service.get_station_snapshot()

        eligible_workers: list[dict] = []
        for snapshot in snapshots:
            connected = bool(snapshot.get("connected", False))
            state = str(snapshot.get("state", ""))
            phase = str(snapshot.get("phase", ""))

            if connected and state == "IDLE" and phase == "WAITING":
                eligible_workers.append(snapshot)

        if not eligible_workers:
            log_console(
                self._logger,
                logging.WARNING,
                "No hay workers conectados y libres para iniciar ejecución.",
            )
            return

        started_workers: list[str] = []

        for snapshot in eligible_workers:
            worker_id = str(snapshot.get("worker_id", "")).strip()
            if not worker_id:
                continue

            request = ExecutionTestRequest(
                worker_id=worker_id,
                vendor=None,
                model=None,
                tests=dict(selected_tests),
                metadata={
                    "source": "dashboard",
                },
            )

            started = self._station_service.start_execution_request(request)
            if started:
                started_workers.append(worker_id)

        if not started_workers:
            log_console(
                self._logger,
                logging.WARNING,
                "No se pudo iniciar ejecución para ningún worker elegible.",
            )
            return

        log_both(
            self._logger,
            logging.INFO,
            "Ejecución iniciada desde dashboard para: %s | tests=%s",
            ", ".join(started_workers),
            selected_tests,
        )

        self.show_testeo()

    def _setup_timer(self) -> None:
        self._timer = QTimer(self)
        self._timer.setInterval(self._settings.ui.refresh_interval_ms)
        self._timer.timeout.connect(self._consume_events)
        self._timer.start()
    
    @staticmethod
    def _test_name_to_index(test_name: str) -> int | None:
        mapping = {
            "PING": 0,
            "FACTORY_RESET": 1,
            "SOFTWARE_UPDATE": 2,
            "USB": 3,
            "FIBER_TX": 4,
            "FIBER_RX": 5,
            "WIFI_2G": 6,
            "WIFI_5G": 7,
        }
        return mapping.get(test_name)
    
    def _refresh_from_snapshot(self) -> None:
        snapshots = self._station_service.get_station_snapshot()

        for snapshot in snapshots:
            worker_id = str(snapshot.get("worker_id", "")).strip()
            if not worker_id:
                continue

            self._apply_snapshot(worker_id, snapshot)

        self._render_testeo_view()

    def _consume_events(self) -> None:
        events = self._event_bus.drain_events()
        if not events:
            return

        for event in events:
            payload = event.payload
            worker_id = str(payload.get("worker_id", "")).strip()
            if not worker_id:
                continue

            if event.event_name == "worker.state_changed":
                self._apply_snapshot(worker_id, payload)

            elif event.event_name == "test.indicator_changed":
                if worker_id not in self._ports:
                    continue

                test_name = str(payload.get("test_name", "")).upper()
                visual_state = str(payload.get("visual_state", "IDLE")).upper()
                result_status = str(payload.get("result_status", "")).upper()

                if visual_state == "COMPLETED":
                    visual_state = "PASS"

                if result_status == "PASS":
                    visual_state = "PASS"
                elif result_status in {"FAIL", "ERROR", "FAILED"}:
                    visual_state = "FAIL"

                index = self._test_name_to_index(test_name)
                if index is not None:
                    current_state = self._ports[worker_id].circle_states[index]

                    if current_state in {"PASS", "FAIL"} and visual_state == "RUNNING":
                        continue

                    self._ports[worker_id].circle_states[index] = visual_state

            elif event.event_name == "worker.global_visual_mode":
                if worker_id not in self._ports:
                    continue

                mode = str(payload.get("mode", "")).upper()
                active = bool(payload.get("active", False))
                self._ports[worker_id].global_mode = mode if active else None

        self._render_testeo_view()
    
    def _apply_snapshot(self, worker_id: str, snapshot: dict) -> None:
        port = self._ports.get(worker_id)
        if port is None:
            port = PortUiState(worker_id=worker_id)
            self._ports[worker_id] = port

        port.port_index = snapshot.get("port_index")
        port.connected = bool(snapshot.get("connected", False))
        port.status = str(snapshot.get("status", "IDLE"))
        port.phase = str(snapshot.get("phase", "WAITING"))
        port.expected_ip = snapshot.get("expected_ip") or snapshot.get("ip")
        port.device_ip = snapshot.get("device_ip")
        port.device_mac = snapshot.get("device_mac") or snapshot.get("mac")
        port.device_sn = snapshot.get("device_sn")
        port.vendor = snapshot.get("vendor")
        port.model = snapshot.get("model")

        if (
            port.status == "IDLE"
            and port.phase == "WAITING"
            and not port.connected
        ):
            port.global_mode = None
            port.circle_states = ["IDLE"] * 8
            port.circle_states[0] = "OFFLINE"
            return

        self._apply_base_states(port)
    
    def _apply_base_states(self, port: PortUiState) -> None:
        port.circle_states[0] = "PASS" if port.connected else "OFFLINE"

        if port.status in {"FAIL", "ERROR", "FAILED"}:
            phase_index = PHASE_TO_INDEX.get(port.phase)
            if phase_index is not None and port.circle_states[phase_index] not in {"PASS", "FAIL"}:
                port.circle_states[phase_index] = "FAIL"
            return

        if port.status in {"RUNNING", "TESTING", "IN_PROGRESS"}:
            phase_index = PHASE_TO_INDEX.get(port.phase)
            if phase_index is not None and port.circle_states[phase_index] == "IDLE":
                port.circle_states[phase_index] = "RUNNING"
            return

        if port.phase in PHASE_TO_INDEX and port.status not in {"PASS", "FINISHED"}:
            phase_index = PHASE_TO_INDEX.get(port.phase)
            if phase_index is not None and port.circle_states[phase_index] == "IDLE":
                port.circle_states[phase_index] = "RUNNING"
    
    def _render_testeo_view(self) -> None:
        success_count = 0

        for worker_id, port in self._ports.items():
            _ = worker_id

            if port.port_index is None:
                continue

            render_states = list(port.circle_states)

            if port.global_mode == "EXPECTED_RESET":
                render_states = ["EXPECTED_RESET"] * 8
            elif port.global_mode == "EXPECTED_UPDATE":
                render_states = ["EXPECTED_UPDATE"] * 8

            self.testeo_view.set_port_circle_states(port.port_index, render_states)

            test_states = render_states[1:]
            if "FAIL" not in test_states and any(state == "PASS" for state in test_states):
                success_count += 1

        self.testeo_view.set_success_count(success_count)