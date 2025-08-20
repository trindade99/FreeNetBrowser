from PyQt6.QtWidgets import QListView, QLabel, QMenu
from PyQt6.QtCore import Qt, pyqtSignal

class ContextMenuListView(QListView):
    """Custom QListView with context menu support and empty fallback message"""
    edit_requested = pyqtSignal(int, str, str)  # index, title, url
    delete_requested = pyqtSignal(int, str)  # index, url

    def __init__(self, parent=None, empty_text="Looking into the network..."):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Create the fallback label
        self.empty_label = QLabel(empty_text, self)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.6);
                font-size: 14px;
                font-style: italic;
            }
        """)
        self.empty_label.hide()

    def setModel(self, model):
        """Override setModel to connect to model changes."""
        super().setModel(model)
        if model:
            model.rowsInserted.connect(self.update_empty_state)
            model.rowsRemoved.connect(self.update_empty_state)
            model.modelReset.connect(self.update_empty_state)
            self.update_empty_state()

    def resizeEvent(self, event):
        """Ensure the label stays centered."""
        super().resizeEvent(event)
        self.empty_label.resize(self.size())

    def update_empty_state(self):
        """Show label if list is empty."""
        model = self.model()
        if model and model.rowCount() == 0:
            self.empty_label.show()
        else:
            self.empty_label.hide()

    def show_context_menu(self, position):
        index = self.indexAt(position)
        if not index.isValid():
            return

        # Get the item data
        title = self.model().item(index.row(), 0).text()
        url = self.model().item(index.row(), 1).text()

        # Create context menu
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: rgba(40, 40, 60, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: white;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
                margin: 1px;
            }
            QMenu::item:selected {
                background: rgba(74, 158, 255, 0.3);
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255, 255, 255, 0.2);
                margin: 4px 8px;
            }
        """)

        # Add actions
        edit_action = menu.addAction("✏️ Edit")
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ Delete")

        # Execute menu
        action = menu.exec(self.mapToGlobal(position))

        if action == edit_action:
            self.edit_requested.emit(index.row(), title, url)
        elif action == delete_action:
            self.delete_requested.emit(index.row(), url)
