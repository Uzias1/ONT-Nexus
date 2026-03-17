from PySide6.QtWidgets import QMainWindow
from ui.views.dashboard_view import DashboardView


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Vista principal")
        self.setMinimumSize(950, 620)
        self.setCentralWidget(DashboardView())