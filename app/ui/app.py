from __future__ import annotations

from PySide6.QtWidgets import QApplication


def build_qt_app() -> QApplication:
    """
    Helper simple para crear QApplication.
    """
    return QApplication.instance() or QApplication([])