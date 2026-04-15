import os
import sys
import shutil
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QApplication, QLabel, QFileDialog, QWidget,
    QVBoxLayout, QMenu, QMessageBox,
    QSystemTrayIcon, QAction
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
from components.dialogs import SavedGifDialog, ModernInputDialog
from components.widgets import MenuSliderAction, MenuCheckboxAction, MenuButtonAction, MenuSeparatorAction
from components.settings_manager import SettingsManager

class GifOnTop(QWidget):
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
        self.gif_label.setMinimumSize(1, 1) # CRITICAL: Allows the window to shrink
        self.layout.addWidget(self.gif_label)

        self.movie: Optional[QMovie] = None
        self.current_pixmap: Optional[QPixmap] = None
        self.current_gif_path: Optional[str] = None
        self.original_size: Optional[QSize] = None

        self.drag_position = None
        self.is_locked = False
        self.is_minimized_to_tray = False
        self.lock_aspect_ratio = True
        self.is_updating_menu = False # Flag for slider syncing
        self.original_size_cache = {} # Cache for media sizes
        
        # Debounce timer for save_settings
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(300)
        self._save_timer.timeout.connect(self._flush_settings)
        self._pending_settings = None

        self.setup_tray_icon()
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
        if not icon_path.exists():
            icon_path = BASE_DIR / "app_icon.ico"

        self.tray_icon = QSystemTrayIcon(self)
        icon = QIcon(str(icon_path)) if icon_path.exists() else self.style().standardIcon(QApplication.style().SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        self.setWindowIcon(icon)

        self.tray_menu = QMenu()
        
        self.tray_show_action = QAction("Show Window", self)
        self.tray_show_action.setIcon(self.load_icon("show.png") or QIcon())
        self.tray_show_action.triggered.connect(self.show_normal)
        
        self.tray_lock_action = QAction("Lock Window", self)
        self.tray_lock_action.triggered.connect(self.toggle_lock)

        quit_action = QAction("Quit", self)
        quit_action.setIcon(self.load_icon("quit.png") or QIcon())
        quit_action.triggered.connect(QApplication.quit)
        
        self.tray_menu.addAction(self.tray_show_action)
        self.tray_menu.addAction(self.tray_lock_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(quit_action)
        
        self.tray_menu.aboutToShow.connect(self.update_tray_menu)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def update_tray_menu(self):
        """Dynamically update tray menu states before showing"""
        # "Show Window" should only be visible if it's hidden or minimized to tray
        should_show = not self.isVisible() or self.is_minimized_to_tray
        self.tray_show_action.setVisible(should_show)
        
        # Update lock action text and icon
        if self.is_locked:
            self.tray_lock_action.setText("Unlock Window")
            self.tray_lock_action.setIcon(self.load_icon("unlock.png") or QIcon())
        else:
            self.tray_lock_action.setText("Lock Window")
            self.tray_lock_action.setIcon(self.load_icon("lock.png") or QIcon())


    def load_initial_gif(self):
        last_path = SettingsManager.load_last_path()
        if last_path and os.path.exists(last_path):
            self.load_media(last_path)
            return
        
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
        if not os.path.exists(path): return
        
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
        if self.movie:
            self.movie.setScaledSize(QSize(w, h))
        elif self.current_pixmap:
            self.update_static_image_size(w, h)

    def toggle_lock(self, _=None):
        """Toggle position and resize lock"""
        self.is_locked = not self.is_locked
        self.save_settings(self.width(), self.height(), self.windowOpacity())
        
        # Update tray icon message
        status = "Locked" if self.is_locked else "Unlocked"
        self.tray_icon.showMessage("GIF Overlay", f"Window is now {status}.", QSystemTrayIcon.Information, TRAY_MSG_TIMEOUT)
        self.update_tray_menu() # Immediate update

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

        change_menu = menu.addMenu("Change Media")
        change_menu.setIcon(self.load_icon("image.png") or QIcon())
        
        act_new = change_menu.addAction("Open New Media...")
        act_new.setIcon(self.load_icon("folder.png") or QIcon())
        act_new.triggered.connect(self.open_file_dialog)
        
        act_saved = change_menu.addAction("Open Saved Media...")
        act_saved.setIcon(self.load_icon("saved.png") or QIcon())
        act_saved.triggered.connect(self.open_saved_gif_dialog)

        # Replace dialog with submenu sliders
        adj_menu = menu.addMenu("Size & Opacity")
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

        act_save = menu.addAction("Save Media...")
        act_save.setIcon(self.load_icon("save.png") or QIcon())
        act_save.triggered.connect(self.save_gif_to_documents)

        close_menu = menu.addMenu("Close")
        close_menu.setIcon(self.load_icon("close.png") or QIcon())
        
        act_quit = close_menu.addAction("Quit Application")
        act_quit.setIcon(self.load_icon("quit.png") or QIcon())
        act_quit.triggered.connect(QApplication.quit)
        
        if self.is_minimized_to_tray:
            act_restore = close_menu.addAction("Restore to Taskbar")
            act_restore.setIcon(self.load_icon("restore.png") or QIcon())
            act_restore.triggered.connect(self.show_normal)
        else:
            act_min = close_menu.addAction("Minimize to Tray")
            act_min.setIcon(self.load_icon("minimize.png") or QIcon())
            act_min.triggered.connect(self.minimize_to_tray)

        return menu

    def unlock_all(self):
        self.is_locked = False
        self.save_settings(self.width(), self.height(), self.windowOpacity())
        self.update_tray_menu() # Immediate update

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

    def open_saved_gif_dialog(self):
        if not GIF_SAVE_DIR.exists(): GIF_SAVE_DIR.mkdir(parents=True)
        dialog = SavedGifDialog(GIF_SAVE_DIR, self)
        if dialog.exec_() == SavedGifDialog.Accepted:
            path = dialog.get_selected_path()
            if path: self.load_media(path)


    def toggle_pause_gif(self):
        if self.movie: self.movie.setPaused(not self.movie.state() == QMovie.Paused)

    def save_gif_to_documents(self):
        if not self.current_gif_path: return
        ext = Path(self.current_gif_path).suffix
        
        # Use custom ModernInputDialog for premium look and bigger size
        dialog = ModernInputDialog(
            "Save Media", 
            "Enter filename for your media:", 
            initial_value=Path(self.current_gif_path).stem, 
            parent=self
        )
        
        if dialog.exec_():
            name = dialog.text_value()
            if name.strip():
                dest = GIF_SAVE_DIR / (name + ext)
                shutil.copy2(self.current_gif_path, dest)
                
                # Use QMessageBox instance for dark title bar and remove help button
                msg = QMessageBox(self)
                msg.setWindowFlags(msg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
                msg.setWindowTitle("Success")
                msg.setText(f"Media saved successfully to:\n{dest}")
                msg.setIcon(QMessageBox.Information)
                self.apply_dark_title_bar(msg)
                msg.exec_()

    def minimize_to_tray(self):
        self.is_minimized_to_tray = True
        self.setWindowFlags(self.windowFlags() | Qt.Tool)
        self.show()
        self.tray_icon.showMessage("GIF Overlay", "Minimized to tray.", QSystemTrayIcon.Information, TRAY_MSG_TIMEOUT_LONG)
        self.update_tray_menu()

    def show_normal(self):
        self.is_minimized_to_tray = False
        self.setWindowFlags(self.windowFlags() & ~Qt.Tool)
        self.show()
        self.raise_()
        self.activateWindow()
        self.update_tray_menu()

    def contextMenuEvent(self, event):
        self.create_menu().exec_(self.mapToGlobal(event.pos()))

    def show_menu_at_center(self):
        self.create_menu().exec_(self.mapToGlobal(self.rect().center()))

    def closeEvent(self, event):
        msg = QMessageBox(self)
        msg.setWindowFlags(msg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        msg.setWindowTitle("GIF Overlay")
        msg.setText("Do you want to quit the application or minimize to tray?")
        q = msg.addButton("Quit", QMessageBox.DestructiveRole)
        m = msg.addButton("Minimize", QMessageBox.AcceptRole)
        msg.addButton(QMessageBox.Cancel)
        self.apply_dark_title_bar(msg)
        msg.exec_()
        
        if msg.clickedButton() == q: event.accept()
        elif msg.clickedButton() == m: event.ignore(); self.minimize_to_tray()
        else: event.ignore()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible(): self.hide()
            else: self.show_normal()

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