import sys
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow


def run_ui() -> int:
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    return app.exec()