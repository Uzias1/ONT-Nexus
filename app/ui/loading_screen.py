from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout


class LoadingScreen(QDialog):
    def __init__(
        self,
        *,
        image_path: str | None = None,
        width: int = 420,
        height: int = 260,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self._image_path = image_path

        self.setFixedSize(width, height)
        self.setModal(False)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.CustomizeWindowHint
        )

        self.setStyleSheet(
            """
            QDialog {
                background-color: #121212;
                border: 1px solid #2a2a2a;
                border-radius: 12px;
            }
            QLabel {
                background-color: transparent;
                color: white;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(160)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Iniciando... 0%")
        self.progress_bar.setFixedHeight(22)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                background-color: #1f1f1f;
                border: 1px solid #4b5563;
                border-radius: 10px;
                color: white;
                text-align: center;
                padding: 1px;
                font-size: 11px;
                font-weight: 600;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 9px;
            }
            """
        )

        layout.addStretch(1)
        layout.addWidget(self.image_label)
        layout.addWidget(self.progress_bar)
        layout.addStretch(1)

        self._load_image()
        self._center_on_primary_screen()

    def _load_image(self) -> None:
        if not self._image_path:
            self.image_label.setText("ONT Tester NEXUS")
            self.image_label.setStyleSheet(
                """
                QLabel {
                    color: white;
                    font-size: 28px;
                    font-weight: 700;
                }
                """
            )
            return

        image_file = Path(self._image_path)
        if not image_file.exists():
            self.image_label.setText("ONT Tester NEXUS")
            return

        pixmap = QPixmap(str(image_file))
        if pixmap.isNull():
            self.image_label.setText("ONT Tester NEXUS")
            return

        scaled = pixmap.scaled(
            320,
            160,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def set_progress(self, message: str, value: int) -> None:
        safe_value = max(0, min(100, int(value)))
        self.progress_bar.setValue(safe_value)
        self.progress_bar.setFormat(f"{message} {safe_value}%")

    def _center_on_primary_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return

        geometry = screen.availableGeometry()
        x = geometry.x() + (geometry.width() - self.width()) // 2
        y = geometry.y() + (geometry.height() - self.height()) // 2
        self.move(x, y)