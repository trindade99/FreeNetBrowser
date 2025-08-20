import sys
import os
from FreeNet.FileHandler import get_app_data_dir, get_runtime_dir, get_resource_path
from FreeNet.HttpHandler import RobustFileHandler
import os
from urllib.parse import unquote
import subprocess
import socket
import time

import http.server
import socketserver
import threading
import socket
from urllib.parse import unquote
from pathlib import Path

from http.server import HTTPServer
import sys
import os
import threading
import http.server
import socketserver
import asyncio
import io
import re
import shutil
import functools
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                            QWidget, QLineEdit, QDialog, QLabel, QDialogButtonBox,
                            QMessageBox)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtCore import (Qt, QUrl)
from PyQt6.QtGui import QIcon
# Import your existing modules
import RNS
from FreeNet.transferRo import download_all_from_server, initConfig, resolve_dns
from FreeNet.Commons import BASE_DIR
from FreeNet.ServerConfigHandler import save_user_config, load_user_config
from FreeNet.widgets.ModernSideBar import ModernSidebar
from FreeNet.UserDefaultsHandler import (is_favorite, save_favorite)
from PyQt6.QtWebEngineCore import QWebEngineProfile
from qasync import asyncSlot

PORT = 0

class FavoriteDialog(QDialog):
    """Dialog for adding favorites"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add to Favorites")
        self.setFixedSize(350, 180)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Title input
        layout.addWidget(QLabel("Enter a title for this favorite:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Page title")
        layout.addWidget(self.title_input)

        # URL input
        layout.addWidget(QLabel("URL:"))
        self.url_input = QLineEdit()
        self.url_input.setReadOnly(True)
        layout.addWidget(self.url_input)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def set_url(self, url):
        self.url_input.setText(url)

    def get_title(self):
        return self.title_input.text().strip() or "Untitled"

    def get_url(self):
        return self.url_input.text().strip()

class ConfigDialog(QDialog):
    """Dialog for advanced configuration"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Settings")
        self.setFixedSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Instructions
        layout.addWidget(QLabel("Configure your own page titles and hostname."))
        layout.addWidget(QLabel("Add your index.html file to the serverPages folder."))

        # Title input
        layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit()
        layout.addWidget(self.title_input)

        # Hostname input
        layout.addWidget(QLabel("Hostname:"))
        self.hostname_input = QLineEdit()
        layout.addWidget(self.hostname_input)

        # Load existing config
        config = load_user_config()
        self.title_input.setText(config.get("title", ""))
        self.hostname_input.setText(config.get("hostname", ""))

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_config(self):
        return {
            "title": self.title_input.text().strip(),
            "hostname": self.hostname_input.text().strip()
        }

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FreeNet Browser")
        self.setWindowFlag(Qt.WindowType.NoTitleBarBackgroundHint)
        # self.setGeometry(100, 100, 1400, 900)
        self.history = []
        self.current_index = -1
        self.history_navigation = False
        self.loading = False
        self.httpd = None

        # Initialize config and start server
        initConfig(self)
        self.start_http_server()

        self.setup_ui()
        self.apply_modern_styling()

    def setup_ui(self):
        """Setup the main UI"""
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = ModernSidebar()
        self.sidebar.setFixedWidth(320)

        # Connect sidebar signals
        self.sidebar.favorite_selected.connect(self.navigate_to_url)
        self.sidebar.host_selected.connect(self.navigate_to_url)
        self.sidebar.url_entered.connect(self.navigate_to_url)
        self.sidebar.reload_requested.connect(self.reload_page)
        self.sidebar.add_favorite_requested.connect(self.add_to_favorites)
        self.sidebar.show_config_requested.connect(self.show_config_dialog)
        self.sidebar.go_forward_requested.connect(self.go_forward)
        self.sidebar.go_back_requested.connect(self.go_back)

        main_layout.addWidget(self.sidebar)

        runtime_cache = os.path.join(get_runtime_dir(), "web_cache")
        os.makedirs(runtime_cache, exist_ok=True)

        # Create a persistent profile
        profile: QWebEngineProfile = QWebEngineProfile.defaultProfile()  # type: ignore
        profile.setPersistentStoragePath(runtime_cache)
        profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )

        # Create the view with the profile
        self.web_view = QWebEngineView()
        self.web_page = QWebEnginePage(profile, self.web_view)  # keep a reference to prevent premature deletion
        self.web_view.setPage(self.web_page)
        self.web_view.setUrl(QUrl("https://duckduckgo.com"))

        # Connect web view signals
        self.web_view.loadStarted.connect(self.sidebar.url_bar.start_loading)
        self.web_view.loadFinished.connect(self.on_page_loaded)
        self.web_view.urlChanged.connect(self.on_url_changed)


        # CSS you want to inject
        css = """
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.3);
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.5);
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        """

        # Function to inject CSS after page loads
        def inject_css():
            js = f"""
                var style = document.createElement('style');
                style.type = 'text/css';
                style.innerHTML = `{css}`;
                document.head.appendChild(style);
            """
            self.web_view.page().runJavaScript(js)

        # Connect the injection to loadFinished
        self.web_view.loadFinished.connect(inject_css)

        main_layout.addWidget(self.web_view)
        self.setCentralWidget(main_widget)

    def apply_modern_styling(self):
        """Apply modern Arc/Zen browser styling"""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                           stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f0f23);
                color: white;
            }
            QWidget {
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.05);
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                height: 0px;
            }
        """)


    def start_http_server(self):
        """Start HTTP server with robust handler"""
        pages_dir = os.path.join(get_app_data_dir(), 'pages')
        os.makedirs(pages_dir, exist_ok=True)

        # Find available port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            self.actual_port = s.getsockname()[1]

        try:
            # Create handler with directory
            handler = functools.partial(RobustFileHandler, directory=pages_dir)

            # Use HTTPServer instead of TCPServer
            self.httpd = http.server.HTTPServer(("127.0.0.1", self.actual_port), handler)

            # Start server thread
            self.server_thread = threading.Thread(
                target=self.safe_serve_forever,
                daemon=True
            )
            self.server_thread.start()


            # Wait and test
            time.sleep(1)
            self.test_server_connection()

            return True

        except Exception as e:
            return False

    def safe_serve_forever(self):
        """Serve forever with error handling"""
        try:
            self.httpd.serve_forever()
        except Exception as e:
            import traceback

    def test_server_connection(self):
        """Test server connection"""
        try:
            import urllib.request

            # Create request with timeout and proper headers
            req = urllib.request.Request(f"http://127.0.0.1:{self.actual_port}/")
            req.add_header('User-Agent', 'FreeNet-Browser/1.0')

            response = urllib.request.urlopen(req, timeout=10)

        except Exception as e:
            print(e)




    def check_freenet_url(self, url):
        """Check if URL is a FreeNet address"""
        return url.startswith("freenet") or url.startswith("freeNet")

    @asyncSlot(str)
    async def navigate_to_url(self, url):
        await self.load_url_async(url)

    async def load_url_async(self, url):
        """Async URL loading with FreeNet support"""
        self.sidebar.url_bar.start_loading()

        is_freenet = self.check_freenet_url(url)

        if not is_freenet:
            # Regular web URL
            if not re.match(r"^https?://", url):
                url = "https://" + url
            self.web_view.setUrl(QUrl(url))
            self.sidebar.url_bar.set_url(url)
        else:
            # FreeNet URL
            try:
                resolved_hostname = resolve_dns(url)
                RNS.log(f"Resolved hostname: {resolved_hostname}")

                files = await download_all_from_server(
                    resolved_hostname, None, os.path.join(get_app_data_dir(), "pages")
                )

                if files:
                    # Find index.html or use first file
                    index_file = next(
                        (f for f in files if os.path.basename(f).lower() == "index.html"),
                        files[0]
                    )
                    self.load_file_from_path(index_file)
                    self.sidebar.url_bar.set_url(url)
                else:
                    QMessageBox.warning(self, "Error", "No files downloaded from FreeNet node")

            except Exception as e:
                QMessageBox.critical(self, "FreeNet Error", f"Failed to load FreeNet page: {str(e)}")
            finally:
                self.sidebar.url_bar.stop_loading()

    def load_file_from_path(self, file_path):
        """Load a local file through the HTTP server"""
        path = Path(file_path)
        if not path.is_file():
            QMessageBox.critical(self, "Error", f"File not found: {path}")
            return

        try:
            relative_path = path.relative_to(os.path.join(get_app_data_dir(), "pages"))
        except ValueError:
            QMessageBox.critical(self, "Error", f"File must be inside app data dir")
            return

        # USE THE ACTUAL PORT, NOT THE ORIGINAL PORT VARIABLE
        file_url = f"http://127.0.0.1:{self.actual_port}/{relative_path.as_posix()}"
        self.web_view.setUrl(QUrl(file_url))

    @asyncSlot()
    async def reload_page(self):
        self.web_view.reload()

    @asyncSlot()
    async def go_back(self):
        self.web_view.back()

    @asyncSlot()
    async def go_forward(self):
        self.web_view.forward()

    @asyncSlot()
    async def add_to_favorites(self):
        current_url = self.web_view.url().toString()
        if is_favorite(current_url):
            QMessageBox.information(self, "Info", "This page is already in favorites")
            return

        dialog = FavoriteDialog(self)
        dialog.set_url(current_url)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title = dialog.get_title()
            url = dialog.get_url()
            try:
                save_favorite(url, title)
                self.sidebar.load_favorites()
                QMessageBox.information(self, "Success", "Added to favorites!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save favorite: {str(e)}")

    def show_config_dialog(self):
        """Show configuration dialog"""
        dialog = ConfigDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()

            if not config["hostname"]:
                QMessageBox.warning(self, "Warning", "Hostname is required")
                return

            try:
                save_user_config(config["title"] or "Untitled", config["hostname"])
                QMessageBox.information(self, "Success", "Configuration saved!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save config: {str(e)}")

    def on_page_loaded(self, success):
        """Handle page load completion"""
        self.sidebar.url_bar.stop_loading()

        if success:
            url = self.web_view.url().toString()

            # Update history (avoid duplicates)
            if not self.history_navigation:
                if self.current_index < len(self.history) - 1:
                    self.history = self.history[:self.current_index + 1]

                if not self.history or self.history[-1] != url:
                    self.history.append(url)
                    self.current_index = len(self.history) - 1
            else:
                self.history_navigation = False

    def on_url_changed(self, qurl):
        """Handle URL changes in the web view"""
        url = qurl.toString()

        # Update URL bar if it's not a local file
        if f"http://127.0.0.1:{self.actual_port}" not in url and not self.check_freenet_url(url):
            clean_url = re.sub(r'^https?://(www\.)?', '', url).rstrip('/')
            self.sidebar.url_bar.set_url(clean_url)

    def closeEvent(self, event):
        if self.httpd:
            try:
                self.httpd.shutdown()
                self.httpd.server_close()
                self.server_thread.join()  # Wait for thread to finish
            except Exception as e:
                RNS.log(f"Error shutting down server: {e}")

def ensure_rns_config(app_base_dir):
    """
    Ensure the RNS config file exists in the app's config directory.
    app_base_dir: the base directory for your app data
    """

    config_file = os.path.join(app_base_dir, 'config')  # actual config file
    if not os.path.exists(config_file):
        template_file = get_resource_path(os.path.join('resources', 'config'))
        if os.path.exists(template_file):
            shutil.copy(template_file, config_file)
            print(f"RNS config missing, copied template to: {config_file}")
        else:
            print("Warning: RNS template config not found in ./resources!")

def debug_log(message, filename="http_debug.log"):
    try:
        log_dir = os.path.join(get_app_data_dir(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, filename), 'a', encoding='utf-8') as f:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"[{timestamp}] {message}\n")
            f.flush()
    except:
        pass

def main():
    """Main application entry point"""
    try:
        path = get_app_data_dir()
        ensure_rns_config(path)
        RNS.Reticulum(path)
        RNS.log("Reticulum initialized: ")
        RNS.log(RNS.Reticulum.get_instance())
    except Exception as e:
        RNS.log(f"Failed to initialize RNS: {e}")

    # Create QApplication with async support
    app = QApplication(sys.argv)
    app.setApplicationName("FreeNet Browser")
    app.setApplicationVersion("1.0")
    icon_path = os.path.join(os.path.dirname(__file__), "resources", "freeNet.ico")
    app.setWindowIcon(QIcon(icon_path))

    # Create main window
    window = MainWindow()
    window.show()

    # Setup async event loop
    try:
        import qasync
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)

        with loop:
            loop.run_forever()
    except ImportError:
        RNS.log("qasync not available, running without async support")
        RNS.log("Install with: pip install qasync")
        sys.exit(app.exec())

if __name__ == "__main__":
    main()
