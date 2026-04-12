import os
import sys
import shutil
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMenu, QFileDialog, QMessageBox, QDialog,
    QWidgetAction, QSlider, QHBoxLayout, QWidget, QLabel
)
from PyQt6.QtGui import QMovie, QIcon, QPixmap, QImageReader
from PyQt6.QtCore import Qt, QSize, QTimer

from components.constants import (
    BASE_DIR, CONFIG_FILE, GIF_SAVE_DIR,
    DEFAULT_MEDIA_SIZE, FALLBACK_WINDOW_SIZE
)
from components.dialogs import SavedGifDialog, ResizeOpacityDialog, ModernInputDialog

logger = logging.getLogger(__name__)


class MediaMixin:
    """Quản lý tải, hiển thị và thao tác media (GIF/ảnh tĩnh)"""

    def load_initial_gif(self):
        # 1. Try to load last used GIF from config
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    path = f.read().strip()
                    if os.path.exists(path):
                        self.load_media(path)
                        return
            except Exception as e:
                logger.warning("Error loading last gif: %s", e)
        
        # 2. Fallback to demo GIF in assets
        demo_gif = BASE_DIR / "assets" / "demo1.gif"
        if demo_gif.exists():
            self.load_media(str(demo_gif), reset_default=True)
        else:
            QTimer.singleShot(500, lambda: QMessageBox.information(
                self, "Welcome", "No GIF or Image loaded. Right-click to select one!"
            ))



    def load_media(self, path, reset_default=False):
        if not os.path.exists(path): return

        # Clean up previous media
        if self.movie:
            self.movie.stop()
            self.movie = None
        self.gif_label.clear()
        try:
            # 1. Absolute original size detection using QImageReader
            reader = QImageReader(path)
            detected_size = QSize(0, 0)
            if reader.canRead():
                detected_size = reader.size()
            
            # 2. Try QMovie frameRect if reader fails
            if not detected_size.isValid() or detected_size.width() <= 0:
                temp_test_movie = QMovie(path)
                if temp_test_movie.isValid():
                    temp_test_movie.jumpToFrame(0)
                    detected_size = temp_test_movie.frameRect().size()

            # 3. Final default or cache
            if not detected_size.isValid() or detected_size.width() <= 0:
                detected_size = self.original_size_cache.get(path, DEFAULT_MEDIA_SIZE)
            
            self.original_size = detected_size
            self.original_size_cache[path] = detected_size

            # Load the actual media
            temp_movie = QMovie(path)
            if temp_movie.isValid():
                self.movie = temp_movie
                self.gif_label.setMovie(self.movie)
                self.movie.setScaledSize(self.size()) # Initial sync
                self.movie.start()
                self.movie.jumpToFrame(0)
            else:
                self.current_pixmap = QPixmap(path)
                if self.current_pixmap.isNull():
                    QMessageBox.warning(self, "Error", "Unsupported file format.")
                    return
                self.gif_label.setPixmap(self.current_pixmap)

            if reset_default:
                self.resize(self.original_size if self.original_size else FALLBACK_WINDOW_SIZE)
                self.setWindowOpacity(1.0)
            else:
                saved = self.load_settings()
                if saved:
                    width, height, opacity, _, _, is_locked = saved
                    self.resize(width, height)
                    if self.movie:
                        self.movie.setScaledSize(QSize(width, height))
                    elif self.current_pixmap:
                        self.update_static_image_size(width, height)
                    self.setWindowOpacity(opacity)
                    self.is_locked = is_locked
                else:
                    self.resize(self.original_size)

            self.current_gif_path = path
            with open(CONFIG_FILE, "w", encoding="utf-8") as f: f.write(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load media:\n{str(e)}")

    def update_static_image_size(self, w: int, h: int):
        """Scale and update static pixmap with high quality"""
        if self.current_pixmap:
            scaled_pix = self.current_pixmap.scaled(
                w, h, 
                Qt.AspectRatioMode.IgnoreAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.gif_label.setPixmap(scaled_pix)

    def toggle_pause_gif(self):
        if self.movie: self.movie.setPaused(not self.movie.state() == QMovie.MovieState.Paused)

    def save_gif_to_documents(self):
        if not self.current_gif_path: return
        ext = Path(self.current_gif_path).suffix
        
        dialog = ModernInputDialog(
            "Save Media", 
            "Enter filename for your media:", 
            initial_value=Path(self.current_gif_path).stem, 
            parent=self
        )
        
        if dialog.exec():
            name = dialog.text_value()
            if name.strip():
                dest = GIF_SAVE_DIR / (name + ext)
                shutil.copy2(self.current_gif_path, dest)
                
                msg = QMessageBox(self)
                msg.setWindowFlags(msg.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
                msg.setWindowTitle("Success")
                msg.setText(f"Media saved successfully to:\n{dest}")
                msg.setIcon(QMessageBox.Icon.Information)
                self.apply_dark_title_bar(msg)
                msg.exec()

    def open_file_dialog(self):
        file_filter = "Media Files (*.gif *.png *.jpg *.jpeg *.bmp *.webp);;GIF Files (*.gif);;Image Files (*.png *.jpg *.jpeg *.bmp *.webp)"
        dialog = QFileDialog(self)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        dialog.setWindowTitle("Select Media File")
        dialog.setNameFilter(file_filter)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        self.apply_dark_title_bar(dialog)
        
        if dialog.exec():
            paths = dialog.selectedFiles()
            if paths: self.load_media(paths[0], reset_default=True)

    def open_saved_gif_dialog(self):
        if not GIF_SAVE_DIR.exists(): GIF_SAVE_DIR.mkdir(parents=True)
        dialog = SavedGifDialog(GIF_SAVE_DIR, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            path = dialog.get_selected_path()
            if path: self.load_media(path, reset_default=True)

    def open_resize_opacity_dialog(self):
        ResizeOpacityDialog(self).exec()

    def create_menu(self):
        """Create the context menu with dynamic Lock/Unlock state"""
        menu = QMenu(self)
        
        if self.is_locked:
            act_unlock = menu.addAction("Unlock")
            act_unlock.setIcon(self.load_icon("unlock.png") or QIcon())
            act_unlock.triggered.connect(self.unlock_all)
            return menu

        act_lock = menu.addAction("Lock")
        act_lock.setIcon(self.load_icon("lock.png") or QIcon())
        act_lock.triggered.connect(self.toggle_lock)
        
        menu.addSeparator()

        change_menu = menu.addMenu("Open")
        change_menu.setIcon(self.load_icon("image.png") or QIcon())
        
        act_new = change_menu.addAction("Local File")
        act_new.setIcon(self.load_icon("folder.png") or QIcon())
        act_new.triggered.connect(self.open_file_dialog)
        
        act_saved = change_menu.addAction("Library")
        act_saved.setIcon(self.load_icon("saved.png") or QIcon())
        act_saved.triggered.connect(self.open_saved_gif_dialog)

        act_pause = menu.addAction("Play/Pause")
        act_pause.setIcon(self.load_icon("pause.png") or QIcon())
        act_pause.triggered.connect(self.toggle_pause_gif)

        act_save = menu.addAction("Save")
        act_save.setIcon(self.load_icon("save.png") or QIcon())
        act_save.triggered.connect(self.save_gif_to_documents)

        menu.addSeparator()

        opacity_menu = menu.addMenu("Opacity")
        opacity_menu.setIcon(self.load_icon("settings.png") or QIcon())
        self._add_opacity_slider_to_menu(opacity_menu)
        
        menu.addSeparator()

        close_menu = menu.addMenu("Close")
        close_menu.setIcon(self.load_icon("close.png") or QIcon())
        
        act_quit = close_menu.addAction("Quit")
        act_quit.setIcon(self.load_icon("quit.png") or QIcon())
        act_quit.triggered.connect(self.quit_app)
        
        if self.is_minimized_to_tray:
            act_restore = close_menu.addAction("Restore")
            act_restore.setIcon(self.load_icon("restore.png") or QIcon())
            act_restore.triggered.connect(self.show_normal)
        else:
            act_min = close_menu.addAction("Minimize")
            act_min.setIcon(self.load_icon("minimize.png") or QIcon())
            act_min.triggered.connect(self.minimize_to_tray)

        return menu

    def _add_opacity_slider_to_menu(self, menu: QMenu):
        """Tích hợp thanh kéo độ mờ trực tiếp vào menu"""
        action = QWidgetAction(menu)
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(10)

        label = QLabel("Opacity")
        # Sử dụng font nhỏ hơn cho menu
        font = label.font()
        font.setPointSize(9)
        label.setFont(font)
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(10)
        slider.setMaximum(100)
        slider.setValue(int(self.windowOpacity() * 100))
        slider.setFixedWidth(120)
        
        def update_opacity(val):
            self.setWindowOpacity(val / 100)
            self.save_settings(self.width(), self.height(), self.windowOpacity())

        slider.valueChanged.connect(update_opacity)
        
        layout.addWidget(label)
        layout.addWidget(slider)
        
        action.setDefaultWidget(container)
        menu.addAction(action)

    def show_menu_at_center(self):
        self.create_menu().exec(self.mapToGlobal(self.rect().center()))
