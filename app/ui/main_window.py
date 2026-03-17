from PySide6.QtWidgets import QMainWindow, QStackedWidget

from app.ui.theme_manager import ThemeManager
from app.ui.views.dashboard_view import DashboardView
from app.ui.views.modificar import ModificarView
from app.ui.views.testeo import TesteoView


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Vista principal")
        self.setMinimumSize(950, 620)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.dashboard_view = DashboardView()
        self.modificar_view = ModificarView()
        self.testeo_view = TesteoView()

        self.stack.addWidget(self.dashboard_view)
        self.stack.addWidget(self.modificar_view)
        self.stack.addWidget(self.testeo_view)

        self.stack.setCurrentWidget(self.dashboard_view)

        self._connect_navigation()
        self.apply_theme()

    def _connect_navigation(self) -> None:
        self.dashboard_view.btn_modificar.clicked.connect(self.show_modificar)
        self.dashboard_view.btn_testear.clicked.connect(self.show_testeo)

        self.modificar_view.btn_cancelar.clicked.connect(self.show_dashboard)
        self.modificar_view.btn_aceptar.clicked.connect(self.handle_accept_changes)
        self.modificar_view.btn_restablecer.clicked.connect(self.handle_reset_values)

        self.testeo_view.header.btn_back.clicked.connect(self.show_dashboard)

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
        self.dashboard_view.status_bar.apply_theme()

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