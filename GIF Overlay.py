import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Import 3-Layer Components
from components.media_service import MediaService
from components.overlay_window import GifOnTop
from components.settings_manager import SettingsManager

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
)
logger = logging.getLogger("GIF-Overlay.Main")

def main():
    # High DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("windowsvista")

    # Layer 2: Logic
    service = MediaService()
    
    # Layer 1: View
    window = GifOnTop(service)
    
    # Initial load logic
    last_path = SettingsManager.load_last_path()
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        service.load_media(sys.argv[1])
    elif last_path and os.path.exists(last_path):
        service.load_media(last_path)
    else:
        # Fallback to demo if it exists
        from components.constants import BASE_DIR
        demo_gif = BASE_DIR / "demo1.gif"
        if demo_gif.exists():
            service.load_media(str(demo_gif))

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()