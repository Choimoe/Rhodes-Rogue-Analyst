import sys
import os

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    APP_ROOT = os.path.dirname(sys.executable)
    RESOURCE_ROOT = sys._MEIPASS
else:
    APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    RESOURCE_ROOT = APP_ROOT


def get_resource_path(relative_path: str) -> str:
    return os.path.join(RESOURCE_ROOT, relative_path)


def get_persistent_path(relative_path: str) -> str:
    return os.path.join(APP_ROOT, relative_path)
