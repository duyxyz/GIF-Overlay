import os
import sys
import shutil
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QApplication, QLabel, QFileDialog, QWidget,
    QVBoxLayout, QMenu, QMessageBox, QAction
)
from PyQt5.QtGui import QMovie, QIcon, QPalette, QColor, QPixmap, QImageReader, QPainter
from PyQt5.QtCore import Qt, QSize, QTimer
import ctypes

# Import local components
from components.constants import (
    GIF_SAVE_DIR, BASE_DIR, DEFAULT_FALLBACK_SIZE, DEFAULT_RESET_SIZE,
    TRAY_MSG_TIMEOUT, TRAY_MSG_TIMEOUT_LONG, WELCOME_DELAY_MS,
    MENU_OPEN_DELAY_MS, SLIDER_SCALE_RANGE, SLIDER_SIZE_RANGE, SLIDER_OPACITY_RANGE
)
from components.widgets import MenuSliderAction, MenuCheckboxAction, MenuButtonAction, MenuSeparatorAction, MenuDoubleButtonAction
from components.settings_manager import SettingsManager

class TransformableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.flip_h = False
        self.flip_v = False

    def paintEvent(self, event):
        # Determine what to draw
        pix = self.pixmap()
        if not pix and self.movie():
            pix = self.movie().currentPixmap()
        
        if not pix:
            return super().paintEvent(event)
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Move to center
        painter.translate(self.width() / 2, self.height() / 2)
        
        # Apply transforms
        painter.rotate(self.angle)
        sx = -1 if self.flip_h else 1
        sy = -1 if self.flip_v else 1
        painter.scale(sx, sy)
        
        # Determine draw area - if rotated 90/270, we swap W/H
        if self.angle % 180 != 0:
            draw_w, draw_h = self.height(), self.width()
        else:
            draw_w, draw_h = self.width(), self.height()
            
        painter.drawPixmap(int(-draw_w / 2), int(-draw_h / 2), draw_w, draw_h, pix)
        painter.end()

class GifOnTop(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.gif_label = TransformableLabel()
        self.gif_label.setAttribute(Qt.WA_TranslucentBackground)
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif_label.setStyleSheet("background: transparent;")
        self.gif_label.setMinimumSize(1, 1) # CRITICAL: Allows the window to shrink
        self.layout.addWidget(self.gif_label)

        self.movie: Optional[QMovie] = None
        self.current_pixmap: Optional[QPixmap] = None
        self.current_gif_path: Optional[str] = None
        self.original_size: Optional[QSize] = None

        self.drag_position = None
        self.is_locked = False
        self.lock_aspect_ratio = True
        self.is_updating_menu = False # Flag for slider syncing
        self.original_size_cache = {} # Cache for media sizes

        # Orientation state
        self.rotation_angle = 0
        self.flip_h = False
        self.flip_v = False
        
        # Debounce timer for save_settings
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(300)
        self._save_timer.timeout.connect(self._flush_settings)
        self._pending_settings = None

        self._pending_settings = None

        self.load_initial_gif()
        self.show()
        
        if not self.current_gif_path:
            QTimer.singleShot(MENU_OPEN_DELAY_MS, self.show_menu_at_center)

    def apply_dark_title_bar(self, target_widget=None):
        """Enable Windows Immersive Dark Mode for the title bar"""
        if sys.platform != "win32": return
        try:
            widget = target_widget or self
            hwnd = int(widget.winId())
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (Windows 11, recent Win 10)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)
        except Exception:
            pass  # Dark mode không khả dụng trên hệ thống này

    def load_icon(self, icon_name):
        """Load icon from assets folder and tint it for visibility"""
        icon_path = BASE_DIR / "assets" / icon_name
        if not icon_path.exists():
            return QIcon()
            
        pixmap = QPixmap(str(icon_path))
        
        # Tint white icons to dark grey for visibility on light menus
        # This fills the opaque parts of the icon with the specified color
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor("#2D2D2D")) 
        painter.end()
        
        return QIcon(pixmap)

    def setup_tray_icon(self):
        """Setup system tray icon with dark menu"""
        icon_path = BASE_DIR / "assets" / "app_icon.ico"

    def load_initial_gif(self):
        # 1. Mở file từ dòng lệnh (ví dụ: Open With / Double Click trong Windows)
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            self.load_media(sys.argv[1])
            return

        # 2. Khôi phục lại ảnh cuối cùng được mở trong phiên làm việc trước
        last_path = SettingsManager.load_last_path()
        if last_path and os.path.exists(last_path):
            self.load_media(last_path)
            return
        
        # 3. Load ảnh demo mặt định nếu không có dữ liệu
        demo_gif = BASE_DIR / "demo1.gif"
        if demo_gif.exists():
            self.load_media(str(demo_gif))
        else:
            QTimer.singleShot(WELCOME_DELAY_MS, lambda: QMessageBox.information(
                self, "Welcome", "No GIF or Image loaded. Right-click to select one!"
            ))

    def save_settings(self, width: int, height: int, opacity: float):
        """Debounced save — chỉ ghi file sau 300ms không thay đổi"""
        self._pending_settings = (width, height, opacity)
        self._save_timer.start()

    def _flush_settings(self):
        """Thực sự ghi settings ra file"""
        if not self._pending_settings:
            return
        width, height, opacity = self._pending_settings
        self._pending_settings = None
        SettingsManager.save(width, height, opacity, self.is_locked, self.current_gif_path)

    def load_settings(self):
        return SettingsManager.load(self.current_gif_path)

    def load_media(self, path):
        # Reset orientation
        self.rotation_angle = 0
        self.flip_h = False
        self.flip_v = False
        self.update_label_transform()

        # Clean up previous media
        if self.movie:
            self.movie.stop()
            self.movie = None
        self.gif_label.clear()
        try:
            # First determine media type
            temp_movie = QMovie(path)
            if temp_movie.isValid():
                self.movie = temp_movie
                self.current_pixmap = None  # Reset pixmap khi load GIF
                
                # Xác định kích thước gốc cho GIF
                reader = QImageReader(path)
                detected_size = QSize(0, 0)
                if reader.canRead():
                    detected_size = reader.size()
                if not detected_size.isValid() or detected_size.width() <= 0:
                    self.movie.jumpToFrame(0)
                    detected_size = self.movie.frameRect().size()
                if not detected_size.isValid() or detected_size.width() <= 0:
                    detected_size = self.original_size_cache.get(path, QSize(*DEFAULT_FALLBACK_SIZE))
                
                self.original_size = detected_size
            else:
                self.movie = None
                self.current_pixmap = QPixmap(path)
                if self.current_pixmap.isNull():
                    QMessageBox.warning(self, "Error", "Unsupported file format.")
                    return
                # Lấy kích thước gốc trực tiếp từ Pixmap để tránh lỗi EXIF xoay ảnh khác với ImageReader
                self.original_size = self.current_pixmap.size()

            self.original_size_cache[path] = self.original_size

            # Bù trừ High DPI (ngăn Windows tự phóng to ảnh pixel vật lý sang pixel logic)
            ratio = QApplication.primaryScreen().devicePixelRatio()
            if ratio > 1.0:
                self.original_size = QSize(
                    int(self.original_size.width() / ratio), 
                    int(self.original_size.height() / ratio)
                )

            # 4. Xác định kích thước tải và resize cửa sổ TRƯỚC KHI set media
            target_size = self.original_size if self.original_size.width() > 0 else QSize(*DEFAULT_RESET_SIZE)
            
            # Giới hạn kích thước theo màn hình để tránh cửa sổ quá khổ (80% màn hình)
            screen = QApplication.primaryScreen().availableGeometry()
            max_w = int(screen.width() * 0.8)
            max_h = int(screen.height() * 0.8)
            if target_size.width() > max_w or target_size.height() > max_h:
                target_size = target_size.scaled(max_w, max_h, Qt.KeepAspectRatio)

            # Khôi phục trạng thái lock nếu có
            s = self.load_settings()
            if s:
                _, _, _, _, _, ct = s
                self.is_locked = ct

            self.resize(target_size)
            self.setWindowOpacity(1.0)

            # Căn giữa màn hình
            screen = QApplication.primaryScreen().availableGeometry()
            self.move(
                screen.x() + (screen.width() - target_size.width()) // 2,
                screen.y() + (screen.height() - target_size.height()) // 2
            )

            # Gán media vào giao diện
            if self.movie:
                self.movie.setScaledSize(target_size)
                self.gif_label.setMovie(self.movie)
                self.movie.start()
            elif self.current_pixmap:
                scaled_pix = self.current_pixmap.scaled(
                    target_size.width(), target_size.height(),
                    Qt.IgnoreAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.gif_label.setPixmap(scaled_pix)

            # Cập nhật đường dẫn hiện tại và lưu lại
            self.current_gif_path = path
            SettingsManager.save_last_path(path)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load media:\n{str(e)}")

    def resizeEvent(self, event):
        """Handle media scaling when window resizes"""
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        
        # If rotated 90/270, the media dimensions are swapped relative to window
        media_w, media_h = (h, w) if self.rotation_angle % 180 != 0 else (w, h)
        
        if self.movie:
            self.movie.setScaledSize(QSize(media_w, media_h))
        elif self.current_pixmap:
            self.update_static_image_size(media_w, media_h)
        self.update_label_transform()

    def update_label_transform(self):
        """Sync orientation state to the transformable label"""
        if hasattr(self, 'gif_label'):
            self.gif_label.angle = self.rotation_angle
            self.gif_label.flip_h = self.flip_h
            self.gif_label.flip_v = self.flip_v
            self.gif_label.update()

    def rotate_right(self):
        self.rotation_angle = (self.rotation_angle + 90) % 360
        self.resize(self.height(), self.width())
        self.update_label_transform()

    def rotate_left(self):
        self.rotation_angle = (self.rotation_angle - 90) % 360
        self.resize(self.height(), self.width())
        self.update_label_transform()

    def toggle_flip_h(self):
        self.flip_h = not self.flip_h
        self.update_label_transform()

    def toggle_flip_v(self):
        self.flip_v = not self.flip_v
        self.update_label_transform()

    def toggle_lock(self, _=None):
        """Toggle position and resize lock"""
        self.is_locked = not self.is_locked
        self.save_settings(self.width(), self.height(), self.windowOpacity())

    def update_static_image_size(self, w: int, h: int):
        """Scale and update static pixmap with high quality"""
        if self.current_pixmap:
            scaled_pix = self.current_pixmap.scaled(
                w, h, 
                Qt.IgnoreAspectRatio, 
                Qt.SmoothTransformation
            )
            self.gif_label.setPixmap(scaled_pix)

    def update_scale_from_menu(self, value):
        if self.is_updating_menu or not self.original_size: return
        self.is_updating_menu = True
        new_w = int(self.original_size.width() * value / 100)
        new_h = int(self.original_size.height() * value / 100)
        self.resize(new_w, new_h)
        
        # Sync other sliders
        if hasattr(self, 'm_width_act'): self.m_width_act.setValue(new_w)
        if hasattr(self, 'm_height_act'): self.m_height_act.setValue(new_h)
        
        self.save_settings(new_w, new_h, self.windowOpacity())
        self.is_updating_menu = False

    def update_width_from_menu(self, value):
        if self.is_updating_menu: return
        self.is_updating_menu = True
        new_w = value
        new_h = self.height()
        if self.lock_aspect_ratio and self.original_size and self.original_size.width() > 0:
            new_h = int(value * self.original_size.height() / self.original_size.width())
        
        self.resize(new_w, new_h)
        
        # Sync other sliders
        if hasattr(self, 'm_height_act'): self.m_height_act.setValue(new_h)
        if hasattr(self, 'm_scale_act') and self.original_size and self.original_size.width() > 0:
            self.m_scale_act.setValue(int(new_w / self.original_size.width() * 100))
        
        self.save_settings(new_w, new_h, self.windowOpacity())
        self.is_updating_menu = False

    def update_height_from_menu(self, value):
        if self.is_updating_menu: return
        self.is_updating_menu = True
        new_h = value
        new_w = self.width()
        if self.lock_aspect_ratio and self.original_size and self.original_size.height() > 0:
            new_w = int(value * self.original_size.width() / self.original_size.height())
        
        self.resize(new_w, new_h)
        
        # Sync other sliders
        if hasattr(self, 'm_width_act'): self.m_width_act.setValue(new_w)
        if hasattr(self, 'm_scale_act') and self.original_size and self.original_size.height() > 0:
            self.m_scale_act.setValue(int(new_h / self.original_size.height() * 100))
            
        self.save_settings(new_w, new_h, self.windowOpacity())
        self.is_updating_menu = False

    def update_opacity_from_menu(self, value):
        self.setWindowOpacity(value / 100)
        self.save_settings(self.width(), self.height(), self.windowOpacity())

    def toggle_aspect_ratio(self, checked):
        self.lock_aspect_ratio = checked

    def create_menu(self):
        """Create the context menu with dynamic Lock/Unlock state"""
        menu = QMenu(self)
        
        if self.is_locked:
            act_unlock = menu.addAction("Unlock Window")
            act_unlock.setIcon(self.load_icon("unlock.png") or QIcon())
            act_unlock.triggered.connect(self.unlock_all)
            return menu

        act_lock = menu.addAction("Lock Window")
        act_lock.setIcon(self.load_icon("lock.png") or QIcon())
        act_lock.triggered.connect(self.toggle_lock)
        
        menu.addSeparator()

        act_open = menu.addAction("Change GIF...")
        act_open.setIcon(self.load_icon("image.png") or QIcon())
        act_open.triggered.connect(self.open_file_dialog)

        # Replace dialog with submenu sliders
        adj_menu = menu.addMenu("Settings")
        adj_menu.setIcon(self.load_icon("settings.png") or QIcon())
        
        # Scale Slider
        curr_scale = 100
        if self.original_size and self.original_size.width() > 0:
            curr_scale = int(self.width() / self.original_size.width() * 100)
        
        self.m_scale_act = MenuSliderAction("Scale", *SLIDER_SCALE_RANGE, curr_scale, "%", self)
        self.m_scale_act.valueChanged.connect(self.update_scale_from_menu)
        adj_menu.addAction(self.m_scale_act)
        
        # Width Slider
        self.m_width_act = MenuSliderAction("Width", *SLIDER_SIZE_RANGE, self.width(), "px", self)
        self.m_width_act.valueChanged.connect(self.update_width_from_menu)
        adj_menu.addAction(self.m_width_act)
        
        # Height Slider
        self.m_height_act = MenuSliderAction("Height", *SLIDER_SIZE_RANGE, self.height(), "px", self)
        self.m_height_act.valueChanged.connect(self.update_height_from_menu)
        adj_menu.addAction(self.m_height_act)

        # Opacity Slider
        curr_opacity = int(self.windowOpacity() * 100)
        self.m_opacity_act = MenuSliderAction("Opacity", *SLIDER_OPACITY_RANGE, curr_opacity, "%", self)
        self.m_opacity_act.valueChanged.connect(self.update_opacity_from_menu)
        adj_menu.addAction(self.m_opacity_act)
        
        adj_menu.addAction(MenuSeparatorAction(self))

        # Orientation Buttons (Double buttons per row)
        self.btn_rot = MenuDoubleButtonAction("Rotate Left", "Rotate Right", self)
        self.btn_rot.clicked1.connect(self.rotate_left)
        self.btn_rot.clicked2.connect(self.rotate_right)
        adj_menu.addAction(self.btn_rot)
        
        adj_menu.addAction(MenuSeparatorAction(self))
        
        self.btn_flip = MenuDoubleButtonAction("Flip Horizontal", "Flip Vertical", self)
        self.btn_flip.clicked1.connect(self.toggle_flip_h)
        self.btn_flip.clicked2.connect(self.toggle_flip_v)
        adj_menu.addAction(self.btn_flip)

        adj_menu.addAction(MenuSeparatorAction(self))
        
        # Lock Aspect Ratio Action (Tick box style)
        self.m_lock_act = MenuCheckboxAction("Lock Aspect Ratio", self.lock_aspect_ratio, self)
        self.m_lock_act.toggled.connect(self.toggle_aspect_ratio)
        adj_menu.addAction(self.m_lock_act)
        
        adj_menu.addAction(MenuSeparatorAction(self))
        
        # Reset Button (Matching slider style)
        act_reset = MenuButtonAction("Reset to Default", self)
        act_reset.clicked.connect(lambda: self.load_media(self.current_gif_path))
        adj_menu.addAction(act_reset)

        act_pause = menu.addAction("Pause / Play")
        act_pause.setIcon(self.load_icon("pause.png") or QIcon())
        act_pause.triggered.connect(self.toggle_pause_gif)

        menu.addSeparator()
        act_quit = menu.addAction("Quit Application")
        act_quit.setIcon(self.load_icon("quit.png") or QIcon())
        act_quit.triggered.connect(QApplication.quit)

        return menu

    def unlock_all(self):
        self.is_locked = False
        self.save_settings(self.width(), self.height(), self.windowOpacity())

    def open_file_dialog(self):
        filter = "Media Files (*.gif *.png *.jpg *.jpeg *.bmp *.webp);;GIF Files (*.gif);;Image Files (*.png *.jpg *.jpeg *.bmp *.webp)"
        dialog = QFileDialog(self)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        dialog.setWindowTitle("Select Media File")
        dialog.setNameFilter(filter)
        dialog.setFileMode(QFileDialog.ExistingFile)
        self.apply_dark_title_bar(dialog)
        
        if dialog.exec_():
            paths = dialog.selectedFiles()
            if paths: self.load_media(paths[0])

    def toggle_pause_gif(self):
        if self.movie: self.movie.setPaused(not self.movie.state() == QMovie.Paused)

    def contextMenuEvent(self, event):
        self.create_menu().exec_(self.mapToGlobal(event.pos()))

    def show_menu_at_center(self):
        self.create_menu().exec_(self.mapToGlobal(self.rect().center()))

    def closeEvent(self, event):
        # Simply accept the event to close normally like a standard app
        event.accept()

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
    app.setStyle("windowsvista")  # Native Windows renderer, no custom palette
    window = GifOnTop()
    sys.exit(app.exec_())