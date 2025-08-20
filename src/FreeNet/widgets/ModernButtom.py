from PyQt6.QtWidgets import (QWidget, QPushButton)
from PyQt6.QtCore import (QPropertyAnimation, QEasingCurve, QVariantAnimation)
from PyQt6.QtGui import (QPainter, QBrush, QColor,
                        QLinearGradient, QCursor)
from PyQt6.QtCore import (Qt)

class ModernButton(QPushButton):
    """Modern button with hover animations and glass effect"""
    def __init__(self, text="", icon=None, primary=False):
        super().__init__(text)
        self.primary = primary
        self.is_hovered = False
        if icon:
            self.setIcon(icon)
        self.setMinimumHeight(36)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Remove focus policy to prevent focus rectangle
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Animation setup
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.apply_styles()

    def apply_styles(self):
        if self.primary:
            style = """
                ModernButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #4A9EFF, stop:1 #2D7BF0);
                    border: none;
                    border-radius: 18px;
                    color: white;
                    font-weight: 600;
                    font-size: 13px;
                    padding: 8px 16px;
                    outline: none;
                }
                ModernButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #5BA8FF, stop:1 #3E8BFF);
                }
                ModernButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #3A8EEF, stop:1 #1D6BE0);
                }
                ModernButton:focus {
                    outline: none;
                    border: none;
                }
            """
        else:
            style = """
                ModernButton {
                    background: rgba(255, 255, 255, 0.1);
                    border: none;
                    border-radius: 18px;
                    color: rgba(255, 255, 255, 0.9);
                    font-size: 13px;
                    font-weight: 500;
                    padding: 8px 12px;
                    outline: none;
                }
                ModernButton:hover {
                    background: rgba(255, 255, 255, 0.15);
                    color: white;
                }
                ModernButton:pressed {
                    background: rgba(255, 255, 255, 0.05);
                }
                ModernButton:focus {
                    outline: none;
                    border: none;
                }
            """
        self.setStyleSheet(style)

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()

class ModernProgressBar(QWidget):
    """Animated progress bar with modern design"""
    def __init__(self):
        super().__init__()
        self.setFixedHeight(3)
        self.progress = 0
        self.is_loading = False

        # Animation properties
        self.position = 0
        self.position_animation = QVariantAnimation()
        self.position_animation.valueChanged.connect(self.set_position)
        self.position_animation.finished.connect(self.restart_animation)

    def set_position(self, pos):
        self.position = pos
        self.update()

    def start_loading(self):
        self.is_loading = True
        self.show()
        self.restart_animation()

    def stop_loading(self):
        self.is_loading = False
        self.hide()
        self.position_animation.stop()

    def restart_animation(self):
        if not self.is_loading:
            return

        self.position_animation.setStartValue(0)
        self.position_animation.setEndValue(self.width() + 100)
        self.position_animation.setDuration(1500)
        self.position_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.position_animation.start()

    def paintEvent(self, a0):
        if not self.is_loading:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        bg_color = QColor(255, 255, 255, 20)
        painter.fillRect(self.rect(), bg_color)

        # Progress indicator
        gradient = QLinearGradient(self.position - 50, 0, self.position + 50, 0)
        gradient.setColorAt(0, QColor(74, 158, 255, 0))
        gradient.setColorAt(0.5, QColor(74, 158, 255, 255))
        gradient.setColorAt(1, QColor(74, 158, 255, 0))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.position - 50, 0, 100, self.height())
