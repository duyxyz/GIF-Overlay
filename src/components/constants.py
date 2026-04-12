import os
from pathlib import Path
import sys
from PyQt6.QtCore import QSize

# Determine the base directory
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

# --- UI Constants ---
DEFAULT_MEDIA_SIZE = QSize(400, 400)
FALLBACK_WINDOW_SIZE = QSize(300, 300)
TRAY_MESSAGE_DURATION = 1500

# Removed all manual stylesheets to allow true native rendering
