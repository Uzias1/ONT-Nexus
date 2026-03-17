from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dataclasses import dataclass

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.application.event_bus.bus import EventBus
from app.application.event_bus.events import DomainEvent


TESTS = [
    "PING",
    "FACTORY_RESET",
    "SOFTWARE_UPDATE",
    "USB",
    "FIBER_TX",
    "FIBER_RX",
    "WIFI_2G",
    "WIFI_5G",
]


@dataclass
class TestState:
    name: str
    status: str = "IDLE"


class StatusCircle(QWidget):
    def __init__(self, label: str):
        super().__init__()
        self._label = label
        self._color = QColor("#9CA3AF")
        self.setMinimumSize(95, 100)

    def set_status(self, status: str):
        self._color = self.map_color(status)
        self.update()

    def paintEvent(self, event):  # noqa: N802
        _ = event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = self.rect()
        size = 36
        x = (rect.width() - size) // 2
        y = 10

        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.setBrush(self._color)
        painter.drawEllipse(x, y, size, size)

        painter.drawText(
            rect.adjusted(5, 55, -5, -5),
            Qt.AlignmentFlag.AlignCenter,
            self._label,
        )

    @staticmethod
    def map_color(status: str) -> QColor:
        return {
            "IDLE": QColor("#9CA3AF"),
            "RUNNING": QColor("#F59E0B"),
            "PASS": QColor("#22C55E"),
            "FAIL": QColor("#EF4444"),
            "REBOOT": QColor("#B944EF"),
            "UPDATE": QColor("#445EEF"),
        }.get(status, QColor("#9CA3AF"))


class MainWindow(QMainWindow):
    def __init__(self, bus: EventBus):
        super().__init__()

        self.bus = bus
        self.states = {name: TestState(name) for name in TESTS}
        self.circles: dict[str, StatusCircle] = {}

        self.current_index = -1
        self.global_mode: str | None = None

        self.setWindowTitle("ONT Tester - Demo Pruebas")
        self.resize(1050, 620)

        self._build_ui()
        self._setup_timer()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)

        title = QLabel("Simulación de pruebas ONT")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel(
            "FACTORY_RESET y SOFTWARE_UPDATE activan un estado global temporal."
        )
        subtitle.setStyleSheet("font-size: 13px; color: #555;")
        layout.addWidget(subtitle)

        layout.addWidget(self._build_indicators())
        layout.addWidget(self._build_controls())

    def _build_indicators(self):
        box = QGroupBox("Indicadores")
        layout = QHBoxLayout(box)

        for test in TESTS:
            circle = StatusCircle(test)
            self.circles[test] = circle
            layout.addWidget(circle)

        return box

    def _build_controls(self):
        box = QGroupBox("Controles")
        layout = QGridLayout(box)

        row = 0
        for test in TESTS:
            layout.addWidget(QLabel(test), row, 0)

            btn_run = QPushButton("RUN")
            btn_pass = QPushButton("PASS")
            btn_fail = QPushButton("FAIL")

            btn_run.clicked.connect(lambda _, t=test: self._handle_run(t))
            btn_pass.clicked.connect(lambda _, t=test: self._publish_test_status(t, "PASS"))
            btn_fail.clicked.connect(lambda _, t=test: self._publish_test_status(t, "FAIL"))

            layout.addWidget(btn_run, row, 1)
            layout.addWidget(btn_pass, row, 2)
            layout.addWidget(btn_fail, row, 3)

            row += 1

        reset_btn = QPushButton("RESET TODO")
        reset_btn.clicked.connect(self._reset_all)
        layout.addWidget(reset_btn, row, 0, 1, 4)

        return box

    def _setup_timer(self):
        self.timer = QTimer(self)
        self.timer.setInterval(150)
        self.timer.timeout.connect(self._process_events)
        self.timer.start()

    def _handle_run(self, test_name: str):
        index = TESTS.index(test_name)
        self.current_index = max(self.current_index, index)

        if test_name in ("FACTORY_RESET", "SOFTWARE_UPDATE"):
            mode = "REBOOT" if test_name == "FACTORY_RESET" else "UPDATE"
            self._activate_global_mode(mode=mode, test_name=test_name)
            return

        self._publish_test_status(test_name, "RUNNING")

    def _activate_global_mode(self, mode: str, test_name: str):
        self.global_mode = mode

        for test in TESTS:
            self._publish_test_status(test, mode)

        QTimer.singleShot(
            3000,
            lambda tn=test_name: self._finish_global_mode(tn),
        )

    def _finish_global_mode(self, test_name: str):
        self.global_mode = None
        self._restore_progress_until(test_name)

    def _restore_progress_until(self, test_name: str):
        end_index = TESTS.index(test_name)

        for index, test in enumerate(TESTS):
            if index <= end_index:
                self._publish_test_status(test, "RUNNING")
            else:
                self._publish_test_status(test, "IDLE")

    def _publish_test_status(self, test_name: str, status: str):
        event = DomainEvent(
            event_name="test.status_changed",
            payload={
                "test_name": test_name,
                "status": status,
            },
        )
        self.bus.publish(event)

    def _reset_all(self):
        self.current_index = -1
        self.global_mode = None

        for test in TESTS:
            self._publish_test_status(test, "IDLE")

    def _process_events(self):
        events = self.bus.drain_events()

        for event in events:
            if event.event_name != "test.status_changed":
                continue

            test_name = str(event.payload["test_name"])
            status = str(event.payload["status"])

            self.states[test_name].status = status
            self.circles[test_name].set_status(status)


def main():
    app = QApplication(sys.argv)
    bus = EventBus()

    window = MainWindow(bus)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())