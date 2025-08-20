from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen


class GlassmorphismWidget(QWidget):
    """Base widget with glassmorphism effect"""
    def __init__(self, parent=None, blur_radius=20, opacity=0.15):
        super().__init__(parent)
        self.blur_radius = blur_radius
        self.bg_opacity = opacity
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, a0):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Create rounded rectangle path
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 12.0, 12.0)

        # Glass background
        glass_color = QColor(255, 255, 255, int(255 * self.bg_opacity))
        painter.fillPath(path, glass_color)

        # Border
        border_pen = QPen(QColor(255, 255, 255, 80), 1)
        painter.setPen(border_pen)
        painter.drawPath(path)
