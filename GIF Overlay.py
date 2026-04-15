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
import logging
import time

# Cấu hình logging theo chuẩn Skill
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
)
logger = logging.getLogger("GIF-Overlay")

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
        movie = self.movie()
        if not movie:
            return super().paintEvent(event)
            
        pix = movie.currentPixmap()
        if not pix:
            return
            
        # Fast path: No transformations
        if self.angle == 0 and not self.flip_h and not self.flip_v:
            # If no rotation/flip, let the default label painting handle it if possible
            # but since we want Precise control over scaling quality, we still use QPainter
            # or just call super().paintEvent if movie was set correctly.
            # However, TransformableLabel is mixed. Let's optimize the Painter setup.
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(self.rect(), pix)
            painter.end()
            return

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

        self.is_locked = False
        self.lock_aspect_ratio = True
        self.is_updating_menu = False # Flag for slider syncing
        self.icon_cache = {} # Cache for tinted icons
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
        
        # Pre-create context menu to avoid lag on right click
        self.init_menu()
        
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
        """Load icon from assets folder and tint it for visibility (cached)"""
        start_time = time.perf_counter()
        if icon_name in self.icon_cache:
            return self.icon_cache[icon_name]
            
        icon_path = BASE_DIR / "assets" / icon_name
        if not icon_path.exists():
            logger.warning(f"Icon not found: {icon_path}")
            return QIcon()
            
        pixmap = QPixmap(str(icon_path))
        
        # Tint white icons to dark grey for visibility on light menus
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor("#2D2D2D")) 
        painter.end()
        
        icon = QIcon(pixmap)
        self.icon_cache[icon_name] = icon
        
        elapsed = (time.perf_counter() - start_time) * 1000
        logger.debug(f"Loaded and tinted icon '{icon_name}' in {elapsed:.2f}ms")
        return icon

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
        """Tải và hiển thị file GIF với log hiệu năng (Skill Standards)"""
        logger.info(f"Loading media: {path}")
        start_time = time.perf_counter()
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
            # Determine media type (GIF only)
            temp_movie = QMovie(path)
            if not temp_movie.isValid():
                # Try reading header if QMovie fails initially
                reader = QImageReader(path)
                if reader.format().lower() != b'gif':
                    logger.error(f"Unsupported format tried to load: {reader.format()}")
                    QMessageBox.warning(self, "Error", "Only GIF files are supported.")
                    return
                # If it's a GIF but QMovie complained, it might be corrupted or specific issue
                if not temp_movie.isValid():
                    logger.error(f"Corrupted GIF: {path}")
                    QMessageBox.warning(self, "Error", "Invalid or corrupted GIF file.")
                    return

            self.movie = temp_movie
            
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

            # Cập nhật đường dẫn hiện tại và lưu lại
            self.current_gif_path = path
            SettingsManager.save_last_path(path)
            
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.info(f"Media loaded in {elapsed:.2f}ms")
            
        except Exception as e:
            logger.exception("Failed to load media")
            QMessageBox.critical(self, "Error", f"Failed to load media:\n{str(e)}")

    def resizeEvent(self, event):
        """Handle media scaling when window resizes"""
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        
        # If rotated 90/270, the media dimensions are swapped relative to window
        media_w, media_h = (h, w) if self.rotation_angle % 180 != 0 else (w, h)
        
        if self.movie:
            self.movie.setScaledSize(QSize(media_w, media_h))
        self.update_label_transform()

    def toggle_lock(self, _=None):
        """Toggle position and resize lock"""
        self.is_locked = not self.is_locked
        self.save_settings(self.width(), self.height(), self.windowOpacity())

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

    def init_menu(self):
        """Khởi tạo menu cố định để tránh lag (Skill: Performance Profiling)"""
        start_time = time.perf_counter()
        self._main_menu = QMenu(self)
        self._settings_menu = QMenu("Settings", self)
        self._settings_menu.setIcon(self.load_icon("settings.png") or QIcon())
        
        # Persistent Actions
        self.act_lock = QAction("Lock Window", self)
        self.act_lock.setIcon(self.load_icon("lock.png") or QIcon())
        self.act_lock.triggered.connect(self.toggle_lock)
        
        self.act_unlock = QAction("Unlock Window", self)
        self.act_unlock.setIcon(self.load_icon("unlock.png") or QIcon())
        self.act_unlock.triggered.connect(self.unlock_all)
        
        self.act_open = QAction("Change GIF...", self)
        self.act_open.setIcon(self.load_icon("image.png") or QIcon())
        self.act_open.triggered.connect(self.open_file_dialog)
        
        self.act_pause = QAction("Pause / Play", self)
        self.act_pause.setIcon(self.load_icon("pause.png") or QIcon())
        self.act_pause.triggered.connect(self.toggle_pause_gif)
        
        self.act_quit = QAction("Quit Application", self)
        self.act_quit.setIcon(self.load_icon("quit.png") or QIcon())
        self.act_quit.triggered.connect(QApplication.quit)
        
        # Slider Actions (The heavy ones)
        self.m_scale_act = MenuSliderAction("Scale", *SLIDER_SCALE_RANGE, 100, "%", self)
        self.m_scale_act.valueChanged.connect(self.update_scale_from_menu)
        
        self.m_width_act = MenuSliderAction("Width", *SLIDER_SIZE_RANGE, 300, "px", self)
        self.m_width_act.valueChanged.connect(self.update_width_from_menu)
        
        self.m_height_act = MenuSliderAction("Height", *SLIDER_SIZE_RANGE, 300, "px", self)
        self.m_height_act.valueChanged.connect(self.update_height_from_menu)
        
        self.m_opacity_act = MenuSliderAction("Opacity", *SLIDER_OPACITY_RANGE, 100, "%", self)
        self.m_opacity_act.valueChanged.connect(self.update_opacity_from_menu)
        
        self.m_lock_aspect = MenuCheckboxAction("Lock Aspect Ratio", self.lock_aspect_ratio, self)
        self.m_lock_aspect.toggled.connect(self.toggle_aspect_ratio)
        
        self.btn_rot = MenuDoubleButtonAction("Rotate Left", "Rotate Right", self)
        self.btn_rot.clicked1.connect(self.rotate_left)
        self.btn_rot.clicked2.connect(self.rotate_right)
        
        self.btn_flip = MenuDoubleButtonAction("Flip Horizontal", "Flip Vertical", self)
        self.btn_flip.clicked1.connect(self.toggle_flip_h)
        self.btn_flip.clicked2.connect(self.toggle_flip_v)
        
        # Assemble Settings Submenu once
        self._settings_menu.addAction(self.m_scale_act)
        self._settings_menu.addAction(self.m_width_act)
        self._settings_menu.addAction(self.m_height_act)
        self._settings_menu.addAction(self.m_opacity_act)
        self._settings_menu.addAction(MenuSeparatorAction(self))
        self._settings_menu.addAction(self.btn_rot)
        self._settings_menu.addAction(MenuSeparatorAction(self))
        self._settings_menu.addAction(self.btn_flip)
        self._settings_menu.addAction(MenuSeparatorAction(self))
        self._settings_menu.addAction(self.m_lock_aspect)
        self._settings_menu.addAction(MenuSeparatorAction(self))
        
        self.act_reset = MenuButtonAction("Reset to Default", self)
        self.act_reset.clicked.connect(lambda: self.load_media(self.current_gif_path))
        self._settings_menu.addAction(self.act_reset)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        logger.info(f"Menu initialized in {elapsed:.2f}ms")

    def create_menu(self):
        """Update and return the persistent menu"""
        self._main_menu.clear()
        
        if self.is_locked:
            self._main_menu.addAction(self.act_unlock)
        else:
            self._main_menu.addAction(self.act_lock)
            self._main_menu.addSeparator()
            self._main_menu.addAction(self.act_open)
            
            # Sync slider values before showing
            self.is_updating_menu = True
            if self.original_size and self.original_size.width() > 0:
                self.m_scale_act.setValue(int(self.width() / self.original_size.width() * 100))
            self.m_width_act.setValue(self.width())
            self.m_height_act.setValue(self.height())
            self.m_opacity_act.setValue(int(self.windowOpacity() * 100))
            self.m_lock_aspect.setChecked(self.lock_aspect_ratio)
            self.is_updating_menu = False
            
            self._main_menu.addMenu(self._settings_menu)
            self._main_menu.addAction(self.act_pause)
            
        self._main_menu.addSeparator()
        self._main_menu.addAction(self.act_quit)
        return self._main_menu

    def unlock_all(self):
        self.is_locked = False
        self.save_settings(self.width(), self.height(), self.windowOpacity())

    def open_file_dialog(self):
        filter = "GIF Files (*.gif)"
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
        menu = self.create_menu()
        menu.exec_(self.mapToGlobal(event.pos()))

    def show_menu_at_center(self):
        menu = self.create_menu()
        menu.exec_(self.mapToGlobal(self.rect().center()))

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