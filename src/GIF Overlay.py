import os
import sys
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QLabel, QWidget,
    QVBoxLayout, QMessageBox, QSystemTrayIcon
)
from PyQt6.QtGui import QMovie, QIcon, QPalette, QColor, QPixmap, QCursor
from PyQt6.QtCore import Qt, QSize, QTimer, QPoint
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
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True) # Cần thiết để đổi con trỏ chuột khi hover

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.gif_label = QLabel()
        self.gif_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.gif_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gif_label.setMinimumSize(1, 1)
        self.layout.addWidget(self.gif_label)

        self.movie: Optional[QMovie] = None
        self.current_pixmap: Optional[QPixmap] = None
        self.current_gif_path: Optional[str] = None
        self.original_size: Optional[QSize] = None

        # Interaction States
        self.drag_position = None
        self.is_resizing = False
        self.resize_mode = None # 'R', 'B', 'BR'
        self.RESIZE_MARGIN = 15
        
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
        self.tray_icon.showMessage("GIF Overlay", f"Window is now {status}.", QSystemTrayIcon.MessageIcon.Information, TRAY_MESSAGE_DURATION)
        self.update_tray_menu()

    def unlock_all(self):
        self.is_locked = False
        self.save_settings(self.width(), self.height(), self.windowOpacity())
        self.update_tray_menu()

    def contextMenuEvent(self, event):
        self.create_menu().exec(self.mapToGlobal(event.pos()))

    def closeEvent(self, event):
        if getattr(self, "_force_quit", False):
            event.accept()
            return

        msg = QMessageBox(self)
        msg.setWindowFlags(msg.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        msg.setWindowTitle("GIF Overlay")
        msg.setText("Do you want to quit the application or minimize to tray?")
        quit_btn = msg.addButton("Quit", QMessageBox.ButtonRole.DestructiveRole)
        minimize_btn = msg.addButton("Minimize", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton(QMessageBox.StandardButton.Cancel)
        self.apply_dark_title_bar(msg)
        msg.exec()
        
        if msg.clickedButton() == quit_btn: event.accept()
        elif msg.clickedButton() == minimize_btn: event.ignore(); self.minimize_to_tray()
        else: event.ignore()

    def mousePressEvent(self, event):
        if self.is_locked: return
        
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            w, h = self.width(), self.height()
            margin = self.RESIZE_MARGIN
            
            # Kiểm tra xem có đang nhấn vào vùng cạnh để resize không
            is_right = pos.x() > w - margin
            is_bottom = pos.y() > h - margin
            
            if is_right and is_bottom:
                self.is_resizing = True
                self.resize_mode = Qt.CursorShape.SizeFDiagCursor
            elif is_right:
                self.is_resizing = True
                self.resize_mode = Qt.CursorShape.SizeHorCursor
            elif is_bottom:
                self.is_resizing = True
                self.resize_mode = Qt.CursorShape.SizeVerCursor
            else:
                self.is_resizing = False
                self.resize_mode = None
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            
            event.accept()

    def mouseMoveEvent(self, event):
        if self.is_locked: return

        pos = event.position().toPoint()
        w, h = self.width(), self.height()
        margin = self.RESIZE_MARGIN

        # 1. Update Cursor (khi không nhấn phím nào)
        if not event.buttons():
            is_right = pos.x() > w - margin
            is_bottom = pos.y() > h - margin
            
            if is_right and is_bottom:
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif is_right:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            elif is_bottom:
                self.setCursor(Qt.CursorShape.SizeVerCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        # 2. Handle Resizing
        if self.is_resizing and event.buttons() & Qt.MouseButton.LeftButton:
            global_pos = event.globalPosition().toPoint()
            win_top_left = self.frameGeometry().topLeft()
            
            new_w = w
            new_h = h
            
            if self.resize_mode == Qt.CursorShape.SizeHorCursor:
                new_w = max(50, global_pos.x() - win_top_left.x())
            elif self.resize_mode == Qt.CursorShape.SizeVerCursor:
                new_h = max(50, global_pos.y() - win_top_left.y())
            elif self.resize_mode == Qt.CursorShape.SizeFDiagCursor:
                new_w = max(50, global_pos.x() - win_top_left.x())
                new_h = max(50, global_pos.y() - win_top_left.y())


            
            self.resize(new_w, new_h)
            event.accept()
            
        # 3. Handle Moving
        elif not self.is_resizing and event.buttons() & Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        if self.is_resizing:
            self.is_resizing = False
            self.resize_mode = None
            self.save_settings(self.width(), self.height(), self.windowOpacity())
        self.drag_position = None

    def quit_app(self):
        self._force_quit = True
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Set native style
    app.setStyle('windows11')
    window = GifOnTop()
    sys.exit(app.exec())