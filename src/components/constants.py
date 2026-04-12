import os
from pathlib import Path
from PyQt5.QtCore import QStandardPaths

# Determine the base directory (where the script or exe lives)
import sys

# For PyInstaller and regular execution
BASE_DIR = Path(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.argv[0]))))

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_DIR = DATA_DIR / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = CONFIG_DIR / "last_gif_path.txt"
CONFIG_SETTINGS_FILE = CONFIG_DIR / "settings.txt"
CONFIG_GIF_SETTINGS_DIR = CONFIG_DIR / "gif_configs"
CONFIG_GIF_SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

GIF_SAVE_DIR = DATA_DIR / "GIF-save"
GIF_SAVE_DIR.mkdir(parents=True, exist_ok=True)
