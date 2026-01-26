import os
from pathlib import Path
from PyQt5.QtCore import QStandardPaths

# Helper to get standard paths
def get_app_data_dir():
    path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    if not path:
        path = os.getenv('APPDATA') or os.path.expanduser("~/.gif_overlay")
    return Path(path)

def get_documents_dir():
    path = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
    if not path:
        path = Path.home() / "Documents"
    return Path(path)

CONFIG_DIR = get_app_data_dir()
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "last_gif_path.txt"
CONFIG_SETTINGS_FILE = CONFIG_DIR / "settings.txt"
CONFIG_GIF_SETTINGS_DIR = CONFIG_DIR / "gif_configs"
CONFIG_GIF_SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

GIF_SAVE_DIR = get_documents_dir() / "GIF-save"
