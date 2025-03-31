import os
import sys
import builtins

# Set up Scapy cache path for .exe compatibility
custom_cache_path = os.path.join(os.getcwd(), "scapy_cache")
os.makedirs(custom_cache_path, exist_ok=True)
os.environ["SCAPY_CACHE"] = custom_cache_path
os.environ["SystemRoot"] = "C:\\Windows"

# Share the patch globally so other files can reuse it
builtins.__SCAPY_CACHE_PATCH__ = custom_cache_path

# Ensure current directory is in Python's path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Prevent accidental fallback to protected .cache directory
try:
    from scapy import config
    config.conf.cache_path = custom_cache_path

    default_cache_path = os.path.expanduser("~/.cache/scapy")
    if os.path.exists(default_cache_path):
        try:
            os.rename(default_cache_path, default_cache_path + "_disabled")
        except PermissionError:
            pass
except ImportError:
    pass

# Run the GUI
from core.app import run_app

if __name__ == '__main__':
    run_app()

