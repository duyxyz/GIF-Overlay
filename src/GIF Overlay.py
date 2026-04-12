import os
import sys
import logging
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget,
    QVBoxLayout, QMessageBox, QSystemTrayIcon
)
from PyQt5.QtGui import QMovie, QIcon, QPalette, QColor, QPixmap
from PyQt5.QtCore import Qt, QSize, QTimer
import ctypes

from components.constants import TRAY_MESSAGE_DURATION
from components.settings_manager import SettingsMixin
from components.tray_manager import TrayMixin
from components.media_handler import MediaMixin

logger = logging.getLogger(__name__)


class GifOnTop(SettingsMixin, TrayMixin, MediaMixin, QWidget):
    """Cửa sổ chính hiển thị GIF/ảnh nổi trên màn hình"""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.gif_label = QLabel()
        self.gif_label.setAttribute(Qt.WA_TranslucentBackground)
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif_label.setStyleSheet("background: transparent;")
        self.gif_label.setMinimumSize(1, 1)
        self.layout.addWidget(self.gif_label)

        self.movie: Optional[QMovie] = None
        self.current_pixmap: Optional[QPixmap] = None
        self.current_gif_path: Optional[str] = None
        self.original_size: Optional[QSize] = None

        self.drag_position = None
        self.is_locked = False
        self.is_minimized_to_tray = False
        self.lock_aspect_ratio = True
        self.original_size_cache = {}

        self.setup_tray_icon()
        self.load_initial_gif()
        self.show()
        
        if not self.current_gif_path:
            QTimer.singleShot(100, self.show_menu_at_center)

    def apply_dark_title_bar(self, target_widget=None):
        """Enable Windows Immersive Dark Mode for the title bar"""
        if sys.platform != "win32": return
        try:
            widget = target_widget or self
            hwnd = int(widget.winId())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)
        except Exception:
            logger.debug("Dark title bar not supported on this Windows version")

    def load_icon(self, icon_name):
        """Load icon from assets folder"""
        base_dir = Path(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))))
        icon_path = base_dir / "assets" / icon_name
        return QIcon(str(icon_path)) if icon_path.exists() else None

    def resizeEvent(self, event):
        """Handle media scaling when window resizes"""
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        if self.movie:
            self.movie.setScaledSize(QSize(w, h))
        elif self.current_pixmap:
            self.update_static_image_size(w, h)

    def toggle_lock(self, _=None):
        """Toggle position and resize lock"""
        self.is_locked = not self.is_locked
        self.save_settings(self.width(), self.height(), self.windowOpacity())
        
        status = "Locked" if self.is_locked else "Unlocked"
        self.tray_icon.showMessage("GIF Overlay", f"Window is now {status}.", QSystemTrayIcon.Information, TRAY_MESSAGE_DURATION)
        self.update_tray_menu()

    def unlock_all(self):
        self.is_locked = False
        self.save_settings(self.width(), self.height(), self.windowOpacity())
        self.update_tray_menu()

    def contextMenuEvent(self, event):
        self.create_menu().exec_(self.mapToGlobal(event.pos()))

    def closeEvent(self, event):
        msg = QMessageBox(self)
        msg.setWindowFlags(msg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        msg.setWindowTitle("GIF Overlay")
        msg.setText("Do you want to quit the application or minimize to tray?")
        quit_btn = msg.addButton("Quit", QMessageBox.DestructiveRole)
        minimize_btn = msg.addButton("Minimize", QMessageBox.AcceptRole)
        msg.addButton(QMessageBox.Cancel)
        self.apply_dark_title_bar(msg)
        msg.exec_()
        
        if msg.clickedButton() == quit_btn: event.accept()
        elif msg.clickedButton() == minimize_btn: event.ignore(); self.minimize_to_tray()
        else: event.ignore()

    def mousePressEvent(self, event):
        if not self.is_locked and event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if not self.is_locked and event.buttons() & Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()


if __name__ == "__main__":
    # High DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    # Global Dark Palette for better Tray Menu support
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(30, 30, 30))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(45, 45, 45))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    app.setStyle('Fusion')
    window = GifOnTop()
    sys.exit(app.exec_())