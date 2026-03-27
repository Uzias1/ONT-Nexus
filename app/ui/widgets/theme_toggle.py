from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QCheckBox


class ThemeToggle(QCheckBox):
    def __init__(self, checked: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.setChecked(checked)
        self.setCursor(Qt.PointingHandCursor)
        self.setText("")

        self._w = 150
        self._h = 72
        self.setFixedSize(self._w, self._h)

    def sizeHint(self) -> QSize:
        return QSize(self._w, self._h)

    def hitButton(self, pos) -> bool:
        return self.rect().contains(pos)

    def set_toggle_size(self, width: int, height: int) -> None:
        self._w = max(96, width)
        self._h = max(48, height)
        self.setFixedSize(self._w, self._h)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        track_rect = QRectF(3, 3, rect.width() - 6, rect.height() - 6)
        radius = track_rect.height() / 2

        border_pen = QPen(QColor(255, 255, 255, 70), 2)
        painter.setPen(border_pen)

        if self.isChecked():
            painter.setBrush(QColor("#111827"))
        else:
            painter.setBrush(QColor("#4DA3E6"))

        painter.drawRoundedRect(track_rect, radius, radius)

        w = track_rect.width()
        h = track_rect.height()

        if self.isChecked():
            painter.setBrush(QColor(255, 255, 255, 35))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRectF(w * 0.56, h * 0.05, h * 0.82, h * 0.82))
            painter.drawEllipse(QRectF(w * 0.66, h * 0.13, h * 0.56, h * 0.56))
            painter.drawEllipse(QRectF(w * 0.75, h * 0.22, h * 0.34, h * 0.34))

            painter.setBrush(QColor("#E5E7EB"))
            painter.drawEllipse(QRectF(w * 0.55, h * 0.10, h * 0.75, h * 0.75))
            painter.setBrush(QColor("#BFC7D5"))
            painter.drawEllipse(QRectF(w * 0.67, h * 0.30, h * 0.12, h * 0.12))
            painter.drawEllipse(QRectF(w * 0.78, h * 0.47, h * 0.18, h * 0.18))
            painter.drawEllipse(QRectF(w * 0.75, h * 0.22, h * 0.09, h * 0.09))

            painter.setBrush(QColor("#FFFFFF"))
            for x, y, s in [
                (w * 0.14, h * 0.28, h * 0.06),
                (w * 0.23, h * 0.56, h * 0.09),
                (w * 0.33, h * 0.38, h * 0.05),
                (w * 0.40, h * 0.22, h * 0.08),
            ]:
                painter.drawEllipse(QRectF(x, y, s, s))
        else:
            painter.setBrush(QColor(255, 255, 255, 45))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRectF(w * 0.03, h * 0.08, h * 0.80, h * 0.80))

            painter.setBrush(QColor("#FACC15"))
            painter.drawEllipse(QRectF(w * 0.05, h * 0.10, h * 0.74, h * 0.74))

            painter.setBrush(QColor(255, 255, 255, 40))
            painter.drawEllipse(QRectF(w * 0.48, h * 0.52, w * 0.38, h * 0.22))
            painter.drawEllipse(QRectF(w * 0.58, h * 0.34, w * 0.30, h * 0.26))
            painter.drawEllipse(QRectF(w * 0.70, h * 0.52, w * 0.20, h * 0.18))

        painter.end()