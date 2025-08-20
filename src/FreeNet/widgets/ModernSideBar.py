from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QSizePolicy,
                            QWidget, QDialog, QLabel,
                            QMessageBox, QAbstractItemView)
from PyQt6.QtCore import (QTimer, pyqtSignal, Qt)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
# Import your existing modules
import RNS
from FreeNet.widgets.ModernUrlBar import ModernUrlBar
from FreeNet.widgets.ContextMenuListView import ContextMenuListView
from FreeNet.UserDefaultsHandler import get_favorites_list
from FreeNet.widgets.EditItemDialog import EditItemDialog
from FreeNet.UserDefaultsHandler import delete_favorite
from FreeNet.UserDefaultsHandler import save_favorite
from FreeNet.widgets.ModernButtom import ModernButton
from FreeNet.DnsHandler import get_known_hosts_list, delete_known_host_by_hostname


class ModernSidebar(QWidget):
    favorite_selected = pyqtSignal(str)
    host_selected = pyqtSignal(str)
    url_entered = pyqtSignal(str)
    reload_requested = pyqtSignal()
    add_favorite_requested = pyqtSignal()
    show_config_requested = pyqtSignal()
    go_back_requested = pyqtSignal()
    go_forward_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_refresh_timer()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # Header with title
        header = QLabel("FreeNet")
        header.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: 700;
                padding: 8px 0;
            }
        """)
        layout.addWidget(header)

        # URL bar (now includes reload button)
        self.url_bar = ModernUrlBar()
        self.url_bar.url_entered.connect(self.url_entered)
        self.url_bar.reload_requested.connect(self.reload_requested)
        layout.addWidget(self.url_bar)

        # Navigation buttons row
        nav_buttons_layout = QHBoxLayout()
        nav_buttons_layout.setSpacing(4)

        self.back_button = ModernButton("◀", primary=False)
        self.back_button.setFixedSize(36, 36)
        self.back_button.setToolTip("Go back")
        self.back_button.clicked.connect(self.go_back)
        nav_buttons_layout.addWidget(self.back_button)

        self.forward_button = ModernButton("▶", primary=False)
        self.forward_button.setFixedSize(36, 36)
        self.forward_button.setToolTip("Go forward")
        self.forward_button.clicked.connect(self.go_forward)
        nav_buttons_layout.addWidget(self.forward_button)

        self.favorite_button = ModernButton("★", primary=False)
        self.favorite_button.setFixedSize(40, 40)
        self.favorite_button.setToolTip("Add to favorites")
        self.favorite_button.clicked.connect(self.add_favorite_requested.emit)
        nav_buttons_layout.addWidget(self.favorite_button)

        self.config_button = ModernButton("⚙", primary=False)
        self.config_button.setFixedSize(40, 40)
        self.config_button.setToolTip("Settings")
        self.config_button.clicked.connect(self.show_config_requested.emit)
        nav_buttons_layout.addWidget(self.config_button)

        nav_buttons_layout.addStretch()
        layout.addLayout(nav_buttons_layout)

        # Favorites section
        self.favorites_label = QLabel("⭐ Favorites")
        self.favorites_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px; padding: 8px 0;")
        layout.addWidget(self.favorites_label)

        self.favorites_view = ContextMenuListView(empty_text="No favorites yet")
        self.favorites_view.setStyleSheet("""
            QListView {
                background: rgba(255, 255, 255, 0.05);
                color: white;
                font-size: 13px;
                border-radius: 8px;
                padding: 4px;
            }
            QListView::item {
                padding: 8px;
                border-radius: 6px;
                margin: 1px;
            }
            QListView::item:selected {
                background: rgba(74, 158, 255, 0.3);
            }
            QListView::item:hover {
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        self.favorites_model = QStandardItemModel(0, 2, self)
        self.favorites_view.setModel(self.favorites_model)
        self.favorites_view.setModelColumn(0)
        self.favorites_view.clicked.connect(self.on_favorite_clicked)

        # Connect context menu signals for favorites
        self.favorites_view.edit_requested.connect(self.edit_favorite)
        self.favorites_view.delete_requested.connect(self.delete_favorite_item)

        layout.addWidget(self.favorites_view, stretch=2)

        # Known hosts section
        self.hosts_label = QLabel("🌐 Mussolini Search")
        self.hosts_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px; padding: 8px 0;")
        layout.addWidget(self.hosts_label)

        self.hosts_view = ContextMenuListView()
        self.hosts_view.setStyleSheet("""
            QListView {
                background: rgba(255, 255, 255, 0.05);
                color: white;
                font-size: 13px;
                border-radius: 8px;
                padding: 4px;
            }
            QListView::item {
                padding: 8px;
                border-radius: 6px;
                margin: 1px;
            }
            QListView::item:selected {
                background: rgba(74, 158, 255, 0.3);
            }
            QListView::item:hover {
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        self.hosts_model = QStandardItemModel(0, 2, self)
        self.hosts_view.setModel(self.hosts_model)
        self.hosts_view.setModelColumn(0)
        self.hosts_view.clicked.connect(self.on_host_clicked)

        # Connect context menu signals for hosts
        self.hosts_view.edit_requested.connect(self.edit_host)
        self.hosts_view.delete_requested.connect(self.delete_host_item)

        layout.addWidget(self.hosts_view, stretch=3)
        self.favorites_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.hosts_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.favorites_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # remove focus rectangle
        self.favorites_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # disable inline editing

        self.hosts_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.hosts_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        layout.addStretch()

        # Initial load
        self.load_favorites()
        self.load_hosts()


    def setup_refresh_timer(self):
        """Setup timer to refresh lists periodically"""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_lists)
        self.refresh_timer.start(5000)  # 5 seconds

    def refresh_lists(self):
        """Refresh both favorites and hosts lists"""
        self.load_favorites()
        self.load_hosts()

    def load_favorites(self):
        """Load favorites from storage"""
        self.favorites_model.clear()
        try:
            favorites = get_favorites_list()
            for fav in favorites:
                if isinstance(fav, dict):
                    title = fav.get('title', 'Unknown')
                    url = fav.get('subtitle', '')
                else:
                    title = str(fav)
                    url = str(fav)

                text_item = QStandardItem(title)
                value_item = QStandardItem(url)
                self.favorites_model.appendRow([text_item, value_item])
        except Exception as e:
            RNS.log(f"Error loading favorites: {e}")

    def load_hosts(self):
        """Load known hosts from storage"""
        self.hosts_model.clear()
        try:
            hosts = get_known_hosts_list()
            for host in hosts:
                if isinstance(host, dict):
                    title = host.get('title', 'Unknown Host')
                    subtitle = host.get('subtitle', '')
                else:
                    title = str(host)
                    subtitle = str(host)

                text_item = QStandardItem(title)
                value_item = QStandardItem(subtitle)
                self.hosts_model.appendRow([text_item, value_item])
        except Exception as e:
            RNS.log(f"Error loading hosts: {e}")

    def on_favorite_clicked(self, index):
        """Handle favorite selection"""
        if index.isValid():
            value = self.favorites_model.item(index.row(), 1).text()
            self.favorite_selected.emit(value)

    def on_host_clicked(self, index):
        """Handle host selection"""
        if index.isValid():
            value = self.hosts_model.item(index.row(), 1).text()
            self.host_selected.emit(value)

    def edit_favorite(self, index, title, url):
        """Edit a favorite item"""
        dialog = EditItemDialog("Edit Favorite", title, url, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_title = dialog.get_title()
            new_url = dialog.get_url()

            if not new_title or not new_url:
                QMessageBox.warning(self, "Warning", "Both title and URL are required")
                return

            try:
                # Delete old favorite and add new one
                delete_favorite(url)
                save_favorite(new_url, new_title)
                self.load_favorites()  # Refresh the list
                QMessageBox.information(self, "Success", "Favorite updated successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update favorite: {str(e)}")

    def delete_favorite_item(self, index, url):
        """Delete a favorite item"""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this favorite?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_favorite(url)
                self.load_favorites()  # Refresh the list
                QMessageBox.information(self, "Success", "Favorite deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete favorite: {str(e)}")

    def edit_host(self, index, title, hostname):
        """Edit a host item"""
        dialog = EditItemDialog("Edit Network Host", title, hostname, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_title = dialog.get_title()
            new_hostname = dialog.get_url()  # Using get_url for hostname

            if not new_title or not new_hostname:
                QMessageBox.warning(self, "Warning", "Both title and hostname are required")
                return

            try:
                # Note: You may need to implement update functionality in DnsHandler
                # For now, we'll show a message about manual editing
                QMessageBox.information(
                    self,
                    "Manual Edit Required",
                    f"Host editing is not fully implemented.\n"
                    f"Original: {title} ({hostname})\n"
                    f"New: {new_title} ({new_hostname})\n\n"
                    f"Please edit the host configuration files manually."
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update host: {str(e)}")

    def go_back(self):
        """Signal to go back in history"""
        self.go_back_requested.emit()

    def go_forward(self):
        """Signal to go forward in history"""
        self.go_forward_requested.emit()

    def update_navigation_buttons(self, can_go_back, can_go_forward):
        """Update the enabled state of navigation buttons"""
        self.back_button.setEnabled(can_go_back)
        self.forward_button.setEnabled(can_go_forward)

        # Update button styling based on enabled state
        if can_go_back:
            self.back_button.setStyleSheet(self.back_button.styleSheet())
        else:
            self.back_button.setStyleSheet("""
                ModernButton {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 18px;
                    color: rgba(255, 255, 255, 0.3);
                    font-size: 13px;
                    font-weight: 500;
                    padding: 8px 12px;
                }
            """)

        if can_go_forward:
            self.forward_button.setStyleSheet(self.forward_button.styleSheet())
        else:
            self.forward_button.setStyleSheet("""
                ModernButton {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 18px;
                    color: rgba(255, 255, 255, 0.3);
                    font-size: 13px;
                    font-weight: 500;
                    padding: 8px 12px;
                }
            """)

    def delete_host_item(self, index, hostname):
        """Delete a host item"""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the host '{hostname}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                delete_known_host_by_hostname(hostname)
                self.load_hosts()  # Refresh the list
                QMessageBox.information(self, "Success", "Host deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete host: {str(e)}")
