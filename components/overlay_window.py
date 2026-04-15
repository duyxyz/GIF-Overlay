import logging
import sys
import ctypes
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QMenu, QMessageBox, QFileDialog, QAction, QApplication
)
from PyQt5.QtGui import QMovie, QIcon, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt, QSize, QTimer

from components.constants import (
    BASE_DIR, MENU_OPEN_DELAY_MS, SLIDER_SCALE_RANGE, SLIDER_SIZE_RANGE, SLIDER_OPACITY_RANGE
)
from components.widgets import (
    MenuSliderAction, MenuCheckboxAction, MenuButtonAction, MenuSeparatorAction, MenuDoubleButtonAction
)
from components.settings_manager import SettingsManager
from components.media_service import MediaService

logger = logging.getLogger("GIF-Overlay.UI")

class TransformableLabel(QLabel):
    """Widget hiển thị GIF hỗ trợ xoay/lật"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.flip_h = False
        self.flip_v = False

    def paintEvent(self, event):
        movie = self.movie()
        if not movie:
            return super().paintEvent(event)
            
        pix = movie.currentPixmap()
        if not pix:
            return
            
        if self.angle == 0 and not self.flip_h and not self.flip_v:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(self.rect(), pix)
            painter.end()
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)
        sx = -1 if self.flip_h else 1
        sy = -1 if self.flip_v else 1
        painter.scale(sx, sy)
        
        if self.angle % 180 != 0:
            draw_w, draw_h = self.height(), self.width()
        else:
            draw_w, draw_h = self.width(), self.height()
            
        painter.drawPixmap(int(-draw_w / 2), int(-draw_h / 2), draw_w, draw_h, pix)
        painter.end()

class GifOnTop(QWidget):
    """Layer 1: View Layer - Cửa sổ overlay chính"""
    def __init__(self, service: MediaService):
        super().__init__()
        self.service = service
        self.icon_cache = {}
        
        # Kết nối tín hiệu từ Service
        self.service.mediaLoaded.connect(self.on_media_loaded)
        self.service.transformChanged.connect(self.update_ui_transform)
        
        self.init_ui()
        self.init_menu()
        
    def init_ui(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.gif_label = TransformableLabel()
        self.gif_label.setAttribute(Qt.WA_TranslucentBackground)
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif_label.setStyleSheet("background: transparent;")
        self.gif_label.setMinimumSize(1, 1)
        self.layout.addWidget(self.gif_label)

        self.is_locked = False
        self.lock_aspect_ratio = True
        self.is_updating_menu = False
        self.drag_position = None

        # Debounce timer for save_settings
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(300)
        self._save_timer.timeout.connect(self._flush_settings)
        self._pending_settings = None
        self.show()

    def apply_dark_title_bar(self, target_widget=None):
        if sys.platform != "win32": return
        try:
            widget = target_widget or self
            hwnd = int(widget.winId())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)
        except Exception: pass

    def load_icon(self, icon_name):
        if icon_name in self.icon_cache:
            return self.icon_cache[icon_name]
        icon_path = BASE_DIR / "assets" / icon_name
        if not icon_path.exists():
            return QIcon()
        pixmap = QPixmap(str(icon_path))
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor("#2D2D2D")) 
        painter.end()
        icon = QIcon(pixmap)
        self.icon_cache[icon_name] = icon
        return icon

    def on_media_loaded(self, target_size: QSize):
        """Callback khi Service tải xong media"""
        self.gif_label.clear()
        
        # Restore settings
        s = SettingsManager.load(self.service.current_gif_path)
        if s: self.is_locked = s[5]

        self.resize(target_size)
        self.setWindowOpacity(1.0)
        self.apply_dark_title_bar()
        
        # Center on screen
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.x() + (screen.width() - target_size.width()) // 2,
            screen.y() + (screen.height() - target_size.height()) // 2
        )

        if self.service.movie:
            self.service.movie.setScaledSize(target_size)
            self.gif_label.setMovie(self.service.movie)
            self.service.movie.start()

    def update_ui_transform(self):
        """Cập nhật hướng hiển thị"""
        self.gif_label.angle = self.service.rotation_angle
        self.gif_label.flip_h = self.service.flip_h
        self.gif_label.flip_v = self.service.flip_v
        self.gif_label.update()

    def init_menu(self):
        """Khởi tạo menu cố định (Layer 1)"""
        self._main_menu = QMenu(self)
        self._settings_menu = QMenu("Settings", self)
        self._settings_menu.setIcon(self.load_icon("settings.png") or QIcon())
        
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
        self.act_pause.triggered.connect(self.service.toggle_pause)
        
        self.act_quit = QAction("Quit Application", self)
        self.act_quit.setIcon(self.load_icon("quit.png") or QIcon())
        self.act_quit.triggered.connect(QApplication.quit)
        
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
        self.btn_flip.clicked1.connect(self.service.toggle_flip_h)
        self.btn_flip.clicked2.connect(self.service.toggle_flip_v)
        
        self._settings_menu.addAction(self.m_scale_act)
        self._settings_menu.addAction(self.m_width_act)
        self._settings_menu.addAction(self.m_height_act)
        self._settings_menu.addAction(self.m_opacity_act)
        self._settings_menu.addSeparator()
        self._settings_menu.addAction(self.btn_rot)
        self._settings_menu.addSeparator()
        self._settings_menu.addAction(self.btn_flip)
        self._settings_menu.addSeparator()
        self._settings_menu.addAction(self.m_lock_aspect)
        self._settings_menu.addSeparator()
        
        self.act_reset = MenuButtonAction("Reset to Default", self)
        self.act_reset.clicked.connect(lambda: self.service.load_media(self.service.current_gif_path))
        self._settings_menu.addAction(self.act_reset)

    def create_menu(self):
        self._main_menu.clear()
        if self.is_locked:
            self._main_menu.addAction(self.act_unlock)
        else:
            self._main_menu.addAction(self.act_lock)
            self._main_menu.addSeparator()
            self._main_menu.addAction(self.act_open)
            self.is_updating_menu = True
            if self.service.original_size and self.service.original_size.width() > 0:
                self.m_scale_act.setValue(int(self.width() / self.service.original_size.width() * 100))
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

    def save_settings(self, width: int, height: int, opacity: float):
        self._pending_settings = (width, height, opacity)
        self._save_timer.start()

    def _flush_settings(self):
        if not self._pending_settings: return
        w, h, o = self._pending_settings
        self._pending_settings = None
        SettingsManager.save(w, h, o, self.is_locked, self.service.current_gif_path)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w, h = self.width(), self.height()
        media_w, media_h = (h, w) if self.service.rotation_angle % 180 != 0 else (w, h)
        if self.service.movie:
            self.service.movie.setScaledSize(QSize(media_w, media_h))
        self.update_ui_transform()

    def update_scale_from_menu(self, value):
        if self.is_updating_menu or not self.service.original_size: return
        self.is_updating_menu = True
        new_w = int(self.service.original_size.width() * value / 100)
        new_h = int(self.service.original_size.height() * value / 100)
        self.resize(new_w, new_h)
        self.m_width_act.setValue(new_w)
        self.m_height_act.setValue(new_h)
        self.save_settings(new_w, new_h, self.windowOpacity())
        self.is_updating_menu = False

    def update_width_from_menu(self, value):
        if self.is_updating_menu: return
        self.is_updating_menu = True
        new_w, new_h = value, self.height()
        if self.lock_aspect_ratio and self.service.original_size and self.service.original_size.width() > 0:
            new_h = int(value * self.service.original_size.height() / self.service.original_size.width())
        self.resize(new_w, new_h)
        self.m_height_act.setValue(new_h)
        if self.service.original_size and self.service.original_size.width() > 0:
            self.m_scale_act.setValue(int(new_w / self.service.original_size.width() * 100))
        self.save_settings(new_w, new_h, self.windowOpacity())
        self.is_updating_menu = False

    def update_height_from_menu(self, value):
        if self.is_updating_menu: return
        self.is_updating_menu = True
        new_h, new_w = value, self.width()
        if self.lock_aspect_ratio and self.service.original_size and self.service.original_size.height() > 0:
            new_w = int(value * self.service.original_size.width() / self.service.original_size.height())
        self.resize(new_w, new_h)
        self.m_width_act.setValue(new_w)
        if self.service.original_size and self.service.original_size.height() > 0:
            self.m_scale_act.setValue(int(new_h / self.service.original_size.height() * 100))
        self.save_settings(new_w, new_h, self.windowOpacity())
        self.is_updating_menu = False

    def rotate_right(self):
        """Xoay phải và swap kích thước cửa sổ"""
        self.service.rotate_right()
        self.resize(self.height(), self.width())

    def rotate_left(self):
        """Xoay trái và swap kích thước cửa sổ"""
        self.service.rotate_left()
        self.resize(self.height(), self.width())

    def update_opacity_from_menu(self, value):
        self.setWindowOpacity(value / 100)
        self.save_settings(self.width(), self.height(), self.windowOpacity())

    def toggle_aspect_ratio(self, checked):
        self.lock_aspect_ratio = checked

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        self.save_settings(self.width(), self.height(), self.windowOpacity())

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
            if paths: self.service.load_media(paths[0])

    def contextMenuEvent(self, event):
        self.create_menu().exec_(self.mapToGlobal(event.pos()))

    def mousePressEvent(self, event):
        if not self.is_locked and event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if not self.is_locked and event.buttons() & Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
