import sys
import os

if hasattr(sys, "_MEIPASS"):
    # Optional: set an environment variable so RNS can find its resources
    os.environ['RNS_BASE_PATH'] = sys._MEIPASS
