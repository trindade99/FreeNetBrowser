import os
import sys
import platform

def get_resource_path(relative_path: str) -> str:
    """
    Get the absolute path to a resource.
    Works in dev and bundled (PyInstaller) modes.
    - relative_path: path relative to project root or package root
    """
    if hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in dev
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return os.path.join(base_path, relative_path)


def get_app_data_dir() -> str:
    """
    Returns the directory where FreeNet stores its persistent data:
    Windows: %APPDATA%\freeNet
    macOS: ~/Library/Application Support/freeNet
    Linux: ~/.local/share/freeNet
    This is always writable by the app.
    """
    system = platform.system()

    if system == "Windows":
        base_dir = os.environ.get('APPDATA', os.path.expanduser("~"))
    elif system == "Darwin":
        base_dir = os.path.expanduser('~/Library/Application Support')
    else:  # Linux / Unix
        base_dir = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))

    app_data_dir = os.path.join(base_dir, "freeNet", 'config')
    os.makedirs(app_data_dir, exist_ok=True)
    print(f"Application data directory: {app_data_dir}")
    return app_data_dir


def get_runtime_dir() -> str:
    """
    Returns a directory for runtime data (downloads, HTTP server files, cache).
    Inside user's home directory:
    - Windows: %APPDATA%\freeNet\runtime
    - macOS: ~/Library/Application Support/freeNet/runtime
    - Linux: ~/.local/share/freeNet/runtime
    """
    runtime_dir = os.path.join(get_app_data_dir())
    os.makedirs(runtime_dir, exist_ok=True)
    return runtime_dir
