from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QCheckBox


class ToggleSwitch(QCheckBox):
    def __init__(self, checked: bool = True, parent=None) -> None:
        super().__init__(parent)
        self.setChecked(checked)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(58, 30)
        self.setText("")

    def sizeHint(self) -> QSize:
        return QSize(58, 30)

    def hitButton(self, pos) -> bool:
        return self.rect().contains(pos)

    def paintEvent(self, event: QPaintEvent) -> None:
        radius = 15
        width = self.width()
        height = self.height()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.isChecked():
            bg_color = QColor("#43B97F")
            circle_x = width - height + 2
        else:
            bg_color = QColor("#000000")
            circle_x = 2

        painter.setPen(Qt.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(QRectF(0, 0, width, height), radius, radius)

        painter.setBrush(QColor("white"))
        painter.drawEllipse(QRectF(circle_x, 2, height - 4, height - 4))

        if self.isChecked():
            painter.setPen(QColor("white"))
            font = painter.font()
            font.setPointSize(13)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(10, 21, "✓")

        painter.end()