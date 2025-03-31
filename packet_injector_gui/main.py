# Entry point (initializes and runs the app)

import os
import sys

# Force Scapy to use a custom writable cache location
custom_cache_path = os.path.join(os.getcwd(), "scapy_cache")
os.makedirs(custom_cache_path, exist_ok=True)
os.environ["SCAPY_CACHE"] = custom_cache_path
os.environ["SystemRoot"] = "C:\\Windows"

# Ensure current directory is in Python's path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# ✅ Patch Scapy to avoid default .cache access issues in compiled .exe
try:
    from scapy import config
    config.conf.cache_path = custom_cache_path

    default_cache_path = os.path.expanduser("~/.cache/scapy")
    if os.path.exists(default_cache_path):
        try:
            os.rename(default_cache_path, default_cache_path + "_disabled")
        except PermissionError:
            pass  # Ignore if read-only
except ImportError:
    pass  # Scapy not loaded yet — safe for PyInstaller build time

# Launch the main GUI
from core.app import run_app

if __name__ == '__main__':
    run_app()

