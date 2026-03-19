from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QStackedWidget

from app.ui.theme_manager import ThemeManager
from app.ui.views.dashboard_view import DashboardView
from app.ui.views.modificar import ModificarView
from app.ui.views.testeo import TesteoView
from app.ui.views.reportes import ReportesView


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

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

    def _set_app_icon(self) -> None:
        icon_path = Path(__file__).resolve().parent / "assets" / "logo_tester.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _connect_navigation(self) -> None:
        self.dashboard_view.btn_modificar.clicked.connect(self.show_modificar)
        self.dashboard_view.btn_testear.clicked.connect(self.show_testeo)
        self.dashboard_view.btn_reportes.clicked.connect(self.show_reportes)

        self.modificar_view.btn_cancelar.clicked.connect(self.show_dashboard)
        self.modificar_view.btn_aceptar.clicked.connect(self.handle_accept_changes)
        self.modificar_view.btn_restablecer.clicked.connect(self.handle_reset_values)

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

    def handle_accept_changes(self) -> None:
        if self.modificar_view.confirm_changes():
            self.show_dashboard()

    def handle_reset_values(self) -> None:
        if self.modificar_view.confirm_reset():
            self.modificar_view.reset_default_values()

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