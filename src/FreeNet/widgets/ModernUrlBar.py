from FreeNet.widgets.GlassMorphism import GlassmorphismWidget
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QStackedLayout,
                            QWidget, QLineEdit)
from PyQt6.QtCore import (Qt, pyqtSignal)
from FreeNet.widgets.ModernButtom import ModernProgressBar
from FreeNet.widgets.ModernButtom import ModernButton


class ModernUrlBar(QWidget):
    """Modern URL bar with search suggestions and glass effect"""
    url_entered = pyqtSignal(str)
    reload_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setMaximumHeight(50)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main input container with progress bar inside
        self.input_container = GlassmorphismWidget(opacity=0.1)
        self.input_container.setStyleSheet("""
            GlassmorphismWidget {
                border-radius: 18px;
                background-clip: border;
            }
        """)

        # Create a stacked layout for overlapping elements
        container_layout = QStackedLayout(self.input_container)
        container_layout.setStackingMode(QStackedLayout.StackingMode.StackAll)

        # Background widget for progress bar
        progress_background = QWidget()
        progress_background.setStyleSheet("background: transparent;")
        progress_background.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Progress bar positioned at the bottom of the container
        self.progress_bar = ModernProgressBar()
        self.progress_bar.setParent(progress_background)
        self.progress_bar.hide()  # Initially hidden

        # Input widget that sits on top
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(16, 8, 8, 8)

        # URL input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Search the web or enter a FreeNet address...")
        self.url_input.returnPressed.connect(self.on_return_pressed)
        self.url_input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: white;
                font-size: 14px;
                font-weight: 400;
                padding: 8px 0;
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.6);
            }
        """)
        input_layout.addWidget(self.url_input)

        # Reload button inside the URL bar
        self.reload_button = ModernButton("⟳", primary=False)
        self.reload_button.setFixedSize(36, 36)
        self.reload_button.setToolTip("Reload page")
        self.reload_button.clicked.connect(self.reload_requested.emit)
        input_layout.addWidget(self.reload_button)

        # Add both widgets to the stacked layout
        container_layout.addWidget(progress_background)
        container_layout.addWidget(input_widget)

        layout.addWidget(self.input_container)

        # Connect to resize event to position progress bar correctly
        self.input_container.resizeEvent = self._on_container_resize

    def _on_container_resize(self, event):
        """Position the progress bar at the bottom of the container"""
        if hasattr(self, 'progress_bar'):
            container_rect = self.input_container.rect()
            # Position progress bar at bottom with same width as container
            self.progress_bar.setGeometry(0, container_rect.height() - 4, container_rect.width(), 4)

    def on_return_pressed(self):
        self.url_entered.emit(self.url_input.text())

    def set_url(self, url):
        self.url_input.setText(url)

    def get_url(self) -> str:
        return self.url_input.text()

    def start_loading(self):
        self.progress_bar.show()
        self.progress_bar.start_loading()

    def stop_loading(self):
        self.progress_bar.stop_loading()
        self.progress_bar.hide()
