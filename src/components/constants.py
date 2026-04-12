import os
from pathlib import Path

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

# --- UI Constants ---
from PyQt5.QtCore import QSize

DEFAULT_MEDIA_SIZE = QSize(400, 400)
FALLBACK_WINDOW_SIZE = QSize(300, 300)
TRAY_MESSAGE_DURATION = 1500

DARK_MENU_STYLESHEET = """
    QMenu { 
        background: #252526; 
        color: #EEEEEE; 
        border: 1px solid #454545; 
        padding: 4px; 
    }
    QMenu::item { 
        padding: 6px 20px 6px 24px; 
        border-radius: 4px;
        margin: 1px 4px;
    }
    QMenu::item:selected { 
        background: #37373D; 
        color: #FFFFFF; 
    }
    QMenu::icon {
        left: 4px;
    }
    QMenu::separator {
        height: 1px;
        background: #454545;
        margin: 4px 8px;
    }
"""
