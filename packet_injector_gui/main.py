# main.py
import os
import sys
import builtins

DEV_MODE = False
IS_FROZEN = getattr(sys, 'frozen', False)  # ✅ Detect if running as .exe

if DEV_MODE and not IS_FROZEN:
    print("⚙️  Running in DEV_MODE — default Scapy behavior.")
else:
    # ✅ Patch Scapy to avoid Windows .cache permission issues
    custom_cache_path = os.path.join(os.getcwd(), "scapy_cache")
    os.makedirs(custom_cache_path, exist_ok=True)
    os.environ["SCAPY_CACHE"] = custom_cache_path
    os.environ["SystemRoot"] = "C:\\Windows"
    builtins.__SCAPY_CACHE_PATCH__ = custom_cache_path

    try:
        from scapy.config import conf
        conf.cache_path = custom_cache_path
    except ImportError:
        pass

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.app import run_app

if __name__ == '__main__':
    run_app()
