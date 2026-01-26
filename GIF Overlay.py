import os
import sys
import shutil
import hashlib
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QApplication, QLabel, QFileDialog, QWidget,
    QVBoxLayout, QMenu, QMessageBox, QInputDialog,
    QSystemTrayIcon, QAction
)
from PyQt5.QtGui import QMovie, QIcon, QPalette, QColor, QPixmap
from PyQt5.QtCore import Qt, QSize, QTimer
import ctypes

# Import local components
from components.constants import (
    CONFIG_FILE, CONFIG_SETTINGS_FILE, CONFIG_GIF_SETTINGS_DIR, 
    GIF_SAVE_DIR
)
from components.dialogs import SavedGifDialog, ResizeOpacityDialog, ModernInputDialog

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
        self.layout.addWidget(self.gif_label)

        self.movie: Optional[QMovie] = None
        self.current_pixmap: Optional[QPixmap] = None
        self.current_gif_path: Optional[str] = None
        self.original_size: Optional[QSize] = None

        self.drag_position = None
        self.is_locked = False
        self.is_minimized_to_tray = False
        self.lock_aspect_ratio = True

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
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (Windows 11, recent Win 10)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1)), 4)
        except: pass

    def load_icon(self, icon_name):
        """Load icon from assets folder"""
        base_dir = Path(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))))
        icon_path = base_dir / "assets" / icon_name
        return QIcon(str(icon_path)) if icon_path.exists() else None

    def setup_tray_icon(self):
        """Setup system tray icon with dark menu"""
        base_dir = Path(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))))
        icon_path = base_dir / "assets" / "app_icon.ico"
        if not icon_path.exists():
            icon_path = base_dir / "app_icon.ico"

        self.tray_icon = QSystemTrayIcon(self)
        icon = QIcon(str(icon_path)) if icon_path.exists() else self.style().standardIcon(QApplication.style().SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        self.setWindowIcon(icon)

        self.tray_menu = QMenu()
        self.tray_menu.setStyleSheet("""
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
        """)
        
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
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    path = f.read().strip()
                    if os.path.exists(path):
                        self.load_media(path)
                        return
            except Exception as e:
                print(f"Error loading last gif: {e}")
        
        base_dir = Path(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))))
        demo_gif = base_dir / "demo1.gif"
        if demo_gif.exists():
            self.load_media(str(demo_gif), reset_default=True)
        else:
            QTimer.singleShot(500, lambda: QMessageBox.information(
                self, "Welcome", "No GIF or Image loaded. Right-click to select one!"
            ))

    def save_settings(self, width: int, height: int, opacity: float):
        try:
            x, y = self.x(), self.y()
            # Save lock status instead of click_through
            lock_status = 1 if self.is_locked else 0
            settings_str = f"{width}\n{height}\n{opacity}\n{x}\n{y}\n{lock_status}\n"
            with open(CONFIG_SETTINGS_FILE, "w", encoding="utf-8") as f:
                f.write(settings_str)
            if self.current_gif_path:
                config_path = CONFIG_GIF_SETTINGS_DIR / self.get_gif_config_name(self.current_gif_path)
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(settings_str)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_settings(self):
        settings_data = None
        if self.current_gif_path:
            config_path = CONFIG_GIF_SETTINGS_DIR / self.get_gif_config_name(self.current_gif_path)
            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        settings_data = f.read().splitlines()
                except: pass
        
        if not settings_data and CONFIG_SETTINGS_FILE.exists():
            try:
                with open(CONFIG_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings_data = f.read().splitlines()
            except: pass
                
        if settings_data and len(settings_data) >= 3:
            try:
                w, h = int(settings_data[0]), int(settings_data[1])
                o = float(settings_data[2])
                x = int(settings_data[3]) if len(settings_data) >= 4 else None
                y = int(settings_data[4]) if len(settings_data) >= 5 else None
                ct = (int(settings_data[5]) == 1) if len(settings_data) >= 6 else False
                return w, h, o, x, y, ct
            except: pass
        return None
    
    def get_gif_config_name(self, gif_path):
        path_hash = hashlib.md5(gif_path.encode()).hexdigest()
        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in Path(gif_path).stem)
        return f"{safe_name}_{path_hash[:8]}.txt"

    def load_media(self, path, reset_default=False):
        if not os.path.exists(path): return
        
        # Clean up previous media
        if self.movie:
            self.movie.stop()
            self.movie = None
        self.gif_label.clear()
        self.current_pixmap = None

        try:
            # Try to load as a GIF/Animation first
            temp_movie = QMovie(path)
            if temp_movie.isValid():
                self.movie = temp_movie
                self.gif_label.setMovie(self.movie)
                self.movie.start()
                self.movie.jumpToFrame(0)
                self.original_size = self.movie.currentPixmap().size()
            else:
                # Try to load as a static image
                self.current_pixmap = QPixmap(path)
                if self.current_pixmap.isNull():
                    QMessageBox.warning(self, "Error", "Unsupported file format.")
                    return
                self.gif_label.setPixmap(self.current_pixmap)
                self.original_size = self.current_pixmap.size()

            if reset_default:
                self.resize(self.original_size if self.original_size else QSize(300, 300))
                self.setWindowOpacity(1.0)
            else:
                s = self.load_settings()
                if s:
                    w, h, o, x, y, ct = s
                    self.resize(w, h)
                    if x is not None: self.move(x, y)
                    if self.movie:
                        self.movie.setScaledSize(QSize(w, h))
                    elif self.current_pixmap:
                        self.update_static_image_size(w, h)
                    self.setWindowOpacity(o)
                    self.is_locked = ct # Use saved status for locking
                    # Remove click-through flag setting
                else:
                    self.resize(self.original_size)

            self.current_gif_path = path
            with open(CONFIG_FILE, "w", encoding="utf-8") as f: f.write(path)
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
        self.tray_icon.showMessage("GIF Overlay", f"Window is now {status}.", QSystemTrayIcon.Information, 1000)
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

    def create_menu(self):
        """Create the context menu with dynamic Lock/Unlock state"""
        menu = QMenu(self)
        menu.setStyleSheet("""
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
        """)
        
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

        act_settings = menu.addAction("Adjust Size & Opacity...")
        act_settings.setIcon(self.load_icon("settings.png") or QIcon())
        act_settings.triggered.connect(self.open_resize_opacity_dialog)

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
            if paths: self.load_media(paths[0], reset_default=True)

    def open_saved_gif_dialog(self):
        if not GIF_SAVE_DIR.exists(): GIF_SAVE_DIR.mkdir(parents=True)
        dialog = SavedGifDialog(GIF_SAVE_DIR, self)
        if dialog.exec_() == SavedGifDialog.Accepted:
            path = dialog.get_selected_path()
            if path: self.load_media(path, reset_default=True)

    def open_resize_opacity_dialog(self):
        ResizeOpacityDialog(self).exec_()

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
        self.tray_icon.showMessage("GIF Overlay", "Minimized to tray.", QSystemTrayIcon.Information, 1500)
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
            self.save_settings(self.width(), self.height(), self.windowOpacity())
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