from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QDialogButtonBox
)

class EditItemDialog(QDialog):
    """Dialog for editing bookmarks or network items"""
    def __init__(self, title="Edit Item", item_title="", item_url="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 200)
        self.setup_ui(item_title, item_url)

    def setup_ui(self, item_title, item_url):
        layout = QVBoxLayout(self)

        # Title input
        layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        self.title_input.setText(item_title)
        self.title_input.setPlaceholderText("Enter title")
        layout.addWidget(self.title_input)

        # URL/Path input
        layout.addWidget(QLabel("URL/Path:"))
        self.url_input = QLineEdit()
        self.url_input.setText(item_url)
        self.url_input.setPlaceholderText("Enter URL or path")
        layout.addWidget(self.url_input)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_title(self):
        return self.title_input.text().strip()

    def get_url(self):
        return self.url_input.text().strip()
