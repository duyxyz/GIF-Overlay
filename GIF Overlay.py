import sys
import os
import shutil
from pathlib import Path
from typing import Optional
from PyQt5.QtWidgets import (
    QApplication, QLabel, QFileDialog, QWidget,
    QVBoxLayout, QMenu, QMessageBox, QInputDialog,
    QDialog, QPushButton, QHBoxLayout,
    QSlider, QGridLayout, QSystemTrayIcon, QAction, QFrame,
    QListWidget, QListWidgetItem, QSplitter
)
from PyQt5.QtGui import QMovie, QIcon, QPalette, QColor, QPainter, QPainterPath, QPixmap
from PyQt5.QtCore import Qt, QSize, QPoint, QRect, pyqtSignal, QTimer

CONFIG_DIR = Path(os.getenv('APPDATA')) / "GIF Overlay"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "last_gif_path.txt"
CONFIG_SETTINGS_FILE = CONFIG_DIR / "settings.txt"
CONFIG_GIF_SETTINGS_DIR = CONFIG_DIR / "gif_configs"
CONFIG_GIF_SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

GIF_SAVE_DIR = Path.home() / "Documents" / "GIF-save"

class ModernSlider(QWidget):
    """Modern slider with label"""
    valueChanged = pyqtSignal(int)
    sliderReleased = pyqtSignal()
    
    def __init__(self, label_text, min_val, max_val, current_val, suffix="", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # Label
        self.label = QLabel(f"{label_text}: {current_val}{suffix}")
        self.label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 12px;
                font-weight: 500;
            }
        """)
        
        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(min_val)
        self.slider.setMaximum(max_val)
        self.slider.setValue(current_val)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: #E0E0E0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #4A90E2;
                border: 2px solid #FFFFFF;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #357ABD;
            }
            QSlider::sub-page:horizontal {
                background: #4A90E2;
                border-radius: 3px;
            }
        """)
        
        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        
        self.suffix = suffix
        self.label_text = label_text
        
        self.slider.valueChanged.connect(self._on_value_changed)
        self.slider.sliderReleased.connect(self.sliderReleased.emit)
    
    def _on_value_changed(self, value):
        self.label.setText(f"{self.label_text}: {value}{self.suffix}")
        self.valueChanged.emit(value)
    
    def value(self):
        return self.slider.value()
    
    def setValue(self, value):
        self.slider.setValue(value)

class ModernButton(QPushButton):
    """Modern styled button"""
    def __init__(self, text, primary=False, parent=None):
        super().__init__(text, parent)
        if primary:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #4A90E2, stop:1 #357ABD);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 13px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #5BA3F5, stop:1 #4A90E2);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #357ABD, stop:1 #2868A6);
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: white;
                    color: #333;
                    border: 1px solid #CCC;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: #F5F5F5;
                    border: 1px solid #999;
                }
                QPushButton:pressed {
                    background: #E0E0E0;
                }
            """)

class SavedGifDialog(QDialog):
    """Modern dialog for selecting saved GIFs with preview"""
    def __init__(self, gif_dir, parent=None):
        super().__init__(parent)
        self.gif_dir = gif_dir
        self.selected_path = None
        self.current_movie = None
        
        self.setWindowTitle("📁 Saved GIFs")
        self.setMinimumSize(700, 500)
        self.setStyleSheet("""
            QDialog {
                background: white;
            }
        """)
        
        self.setup_ui()
        self.load_gifs()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🎬 Select a Saved GIF")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                padding-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background: #E0E0E0;")
        layout.addWidget(line)
        
        # Main content with splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: GIF list
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        list_label = QLabel("Available GIFs:")
        list_label.setStyleSheet("font-weight: 500; color: #555;")
        list_layout.addWidget(list_label)
        
        self.gif_list = QListWidget()
        self.gif_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #CCC;
                border-radius: 6px;
                padding: 5px;
                background: #FAFAFA;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background: #E3F2FD;
                color: #1976D2;
            }
            QListWidget::item:hover {
                background: #F5F5F5;
            }
        """)
        self.gif_list.itemClicked.connect(self.on_gif_selected)
        self.gif_list.itemDoubleClicked.connect(self.on_gif_double_clicked)
        list_layout.addWidget(self.gif_list)
        
        # Right: Preview
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        
        preview_label = QLabel("Preview:")
        preview_label.setStyleSheet("font-weight: 500; color: #555;")
        preview_layout.addWidget(preview_label)
        
        # Preview frame
        preview_frame = QFrame()
        preview_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #CCC;
                border-radius: 8px;
                background: #F9F9F9;
            }
        """)
        preview_frame_layout = QVBoxLayout(preview_frame)
        preview_frame_layout.setContentsMargins(10, 10, 10, 10)
        
        self.preview_label = QLabel("Select a GIF to preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                color: #999;
                font-size: 14px;
                background: transparent;
            }
        """)
        self.preview_label.setMinimumSize(300, 300)
        preview_frame_layout.addWidget(self.preview_label)
        
        # Info label
        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 11px;
                padding: 5px;
            }
        """)
        preview_frame_layout.addWidget(self.info_label)
        
        preview_layout.addWidget(preview_frame)
        
        # Add to splitter
        splitter.addWidget(list_container)
        splitter.addWidget(preview_container)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.delete_btn = ModernButton("🗑️ Delete")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_selected_gif)
        
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        
        cancel_btn = ModernButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        self.select_btn = ModernButton("Select", primary=True)
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.select_btn)
        
        layout.addLayout(btn_layout)
    
    def load_gifs(self):
        """Load GIF files from directory"""
        if not self.gif_dir.exists():
            return
        
        gif_files = sorted(self.gif_dir.glob("*.gif"))
        
        if not gif_files:
            item = QListWidgetItem("No saved GIFs found")
            item.setFlags(Qt.NoItemFlags)
            self.gif_list.addItem(item)
            return
        
        for gif_path in gif_files:
            item = QListWidgetItem(f"🎞️ {gif_path.name}")
            item.setData(Qt.UserRole, str(gif_path))
            self.gif_list.addItem(item)
    
    def on_gif_selected(self, item):
        """Handle GIF selection"""
        gif_path = item.data(Qt.UserRole)
        if not gif_path:
            return
        
        self.selected_path = gif_path
        self.select_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        
        # Stop previous movie
        if self.current_movie:
            self.current_movie.stop()
        
        # Load and preview GIF
        try:
            self.current_movie = QMovie(gif_path)
            if self.current_movie.isValid():
                # Scale to fit preview area
                original_size = self.current_movie.currentPixmap().size()
                scaled_size = original_size.scaled(280, 280, Qt.KeepAspectRatio)
                self.current_movie.setScaledSize(scaled_size)
                
                self.preview_label.setMovie(self.current_movie)
                self.current_movie.start()
                
                # Show info
                file_size = Path(gif_path).stat().st_size / 1024  # KB
                self.info_label.setText(
                    f"Size: {original_size.width()}x{original_size.height()}px | "
                    f"File: {file_size:.1f} KB"
                )
            else:
                self.preview_label.setText("❌ Invalid GIF file")
                self.info_label.setText("")
        except Exception as e:
            self.preview_label.setText(f"❌ Error loading preview:\n{str(e)}")
            self.info_label.setText("")
    
    def on_gif_double_clicked(self, item):
        """Handle double click to select"""
        self.on_gif_selected(item)
        if self.selected_path:
            self.accept()
    
    def delete_selected_gif(self):
        """Delete the selected GIF"""
        if not self.selected_path:
            return
        
        reply = QMessageBox.question(
            self,
            "Delete GIF",
            f"Are you sure you want to delete this GIF?\n\n{Path(self.selected_path).name}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(self.selected_path)
                
                # Remove from list
                current_row = self.gif_list.currentRow()
                self.gif_list.takeItem(current_row)
                
                # Clear preview
                if self.current_movie:
                    self.current_movie.stop()
                self.preview_label.clear()
                self.preview_label.setText("Select a GIF to preview")
                self.info_label.setText("")
                
                self.selected_path = None
                self.select_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
                
                QMessageBox.information(self, "Success", "GIF deleted successfully!")
                
                # Check if list is empty
                if self.gif_list.count() == 0:
                    item = QListWidgetItem("No saved GIFs found")
                    item.setFlags(Qt.NoItemFlags)
                    self.gif_list.addItem(item)
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete GIF:\n{str(e)}")
    
    def get_selected_path(self):
        """Get the selected GIF path"""
        return self.selected_path
    
    def closeEvent(self, event):
        """Clean up when closing"""
        if self.current_movie:
            self.current_movie.stop()
        super().closeEvent(event)

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
        self.gif_label.setStyleSheet("background: transparent;")
        self.layout.addWidget(self.gif_label)

        self.movie: Optional[QMovie] = None
        self.current_gif_path: Optional[str] = None
        self.original_size: Optional[QSize] = None

        self.drag_position = None
        self.is_locked = False

        self.resize(300, 300)

        # Setup tray icon first
        self.setup_tray_icon()

        # Load default demo1.gif or last gif
        self.load_initial_gif()

        self.show()
        if not self.current_gif_path:
            self.show_menu_at_center()

    def setup_tray_icon(self):
        """Setup system tray icon"""
        base_dir = Path(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))))
        
        # Try to load from assets folder first
        icon_path = base_dir / "assets" / "app_icon.ico"
        if not icon_path.exists():
            # Fallback to root directory
            icon_path = base_dir / "app_icon.ico"

        self.tray_icon = QSystemTrayIcon(self)
        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
            # Also set as window icon
            self.setWindowIcon(QIcon(str(icon_path)))
        else:
            default_icon = self.style().standardIcon(QApplication.style().SP_ComputerIcon)
            self.tray_icon.setIcon(default_icon)
            self.setWindowIcon(default_icon)

        tray_menu = QMenu()
        
        # Add icons to tray menu
        show_icon = self.load_icon("show.png")
        show_action = QAction("Show Window", self)
        if show_icon:
            show_action.setIcon(show_icon)
        
        quit_icon = self.load_icon("quit.png")
        quit_action = QAction("Quit", self)
        if quit_icon:
            quit_action.setIcon(quit_icon)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)

        show_action.triggered.connect(self.show_normal)
        quit_action.triggered.connect(QApplication.quit)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def load_initial_gif(self):
        """Load demo1.gif on first run, or last used GIF"""
        # Check if there's a saved GIF path
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    path = f.read().strip()
                    if os.path.exists(path):
                        self.load_gif(path, reset_default=False)
                        return
            except Exception as e:
                print(f"Error loading last gif: {e}")
        
        # Try to load demo1.gif
        base_dir = Path(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))))
        demo_gif = base_dir / "demo1.gif"
        
        if demo_gif.exists():
            self.load_gif(str(demo_gif), reset_default=True)
        else:
            print(f"demo1.gif not found at {demo_gif}")

    def save_settings(self, width: int, height: int, opacity: float):
        """Save window settings for current GIF"""
        try:
            # Save global settings
            with open(CONFIG_SETTINGS_FILE, "w", encoding="utf-8") as f:
                f.write(f"{width}\n{height}\n{opacity}\n")
            
            # Save per-GIF settings
            if self.current_gif_path:
                config_name = self.get_gif_config_name(self.current_gif_path)
                config_path = CONFIG_GIF_SETTINGS_DIR / config_name
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(f"{width}\n{height}\n{opacity}\n")
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_settings(self):
        """Load saved settings for current GIF"""
        # Try to load per-GIF settings first
        if self.current_gif_path:
            config_name = self.get_gif_config_name(self.current_gif_path)
            config_path = CONFIG_GIF_SETTINGS_DIR / config_name
            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        lines = f.read().splitlines()
                        if len(lines) >= 3:
                            w = int(lines[0])
                            h = int(lines[1])
                            o = float(lines[2])
                            return w, h, o
                except Exception as e:
                    print(f"Error loading per-GIF settings: {e}")
        
        # Fallback to global settings
        if CONFIG_SETTINGS_FILE.exists():
            try:
                with open(CONFIG_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    lines = f.read().splitlines()
                    if len(lines) >= 3:
                        w = int(lines[0])
                        h = int(lines[1])
                        o = float(lines[2])
                        return w, h, o
            except Exception as e:
                print(f"Error loading global settings: {e}")
        return None
    
    def get_gif_config_name(self, gif_path):
        """Generate config filename from GIF path"""
        import hashlib
        # Use hash of full path to avoid filename conflicts
        path_hash = hashlib.md5(gif_path.encode()).hexdigest()
        gif_name = Path(gif_path).stem
        # Sanitize filename
        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in gif_name)
        return f"{safe_name}_{path_hash[:8]}.txt"

    def reset_to_default(self):
        """Reset to original GIF size"""
        if self.original_size:
            orig_w = self.original_size.width()
            orig_h = self.original_size.height()
        else:
            orig_w = 300
            orig_h = 300
        self.resize(orig_w, orig_h)
        if self.movie:
            self.movie.setScaledSize(QSize(orig_w, orig_h))
        self.setWindowOpacity(1.0)
        self.save_settings(orig_w, orig_h, 1.0)

    def load_icon(self, icon_name):
        """Load icon from assets folder"""
        base_dir = Path(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))))
        icon_path = base_dir / "assets" / icon_name
        if icon_path.exists():
            return QIcon(str(icon_path))
        return None

    def create_menu(self):
        """Create context menu with modern styling and custom icons"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #CCC;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px 8px 20px;
                margin: 2px 5px;
            }
            QMenu::item:selected {
                background-color: #E3F2FD;
                color: #1976D2;
            }
            QMenu::separator {
                height: 1px;
                background: #E0E0E0;
                margin: 5px 10px;
            }
        """)
        
        if self.is_locked:
            unlock_icon = self.load_icon("unlock.png")
            self.action_unlock = menu.addAction("Unlock")
            if unlock_icon:
                self.action_unlock.setIcon(unlock_icon)
            return menu

        # Change GIF submenu
        change_icon = self.load_icon("image.png")
        change_menu = menu.addMenu("Change GIF")
        if change_icon:
            change_menu.setIcon(change_icon)
        
        open_icon = self.load_icon("folder.png")
        self.action_change_new = change_menu.addAction("Open New GIF...")
        if open_icon:
            self.action_change_new.setIcon(open_icon)
        
        saved_icon = self.load_icon("saved.png")
        self.action_change_saved = change_menu.addAction("Open Saved GIF...")
        if saved_icon:
            self.action_change_saved.setIcon(saved_icon)

        menu.addSeparator()

        settings_icon = self.load_icon("settings.png")
        self.action_change_resize_opacity = menu.addAction("Adjust Size & Opacity...")
        if settings_icon:
            self.action_change_resize_opacity.setIcon(settings_icon)

        menu.addSeparator()

        pause_icon = self.load_icon("pause.png")
        self.action_toggle_pause = menu.addAction("Pause / Play")
        if pause_icon:
            self.action_toggle_pause.setIcon(pause_icon)

        menu.addSeparator()

        save_icon = self.load_icon("save.png")
        self.action_save = menu.addAction("Save GIF...")
        if save_icon:
            self.action_save.setIcon(save_icon)

        # Close submenu
        close_icon = self.load_icon("close.png")
        close_menu = menu.addMenu("Close")
        if close_icon:
            close_menu.setIcon(close_icon)
        
        quit_icon = self.load_icon("quit.png")
        self.action_close_quit = close_menu.addAction("Quit Application")
        if quit_icon:
            self.action_close_quit.setIcon(quit_icon)
        
        minimize_icon = self.load_icon("minimize.png")
        self.action_close_minimize = close_menu.addAction("Minimize to Tray")
        if minimize_icon:
            self.action_close_minimize.setIcon(minimize_icon)

        menu.addSeparator()

        lock_icon = self.load_icon("lock.png")
        self.action_lock = menu.addAction("Lock Window")
        if lock_icon:
            self.action_lock.setIcon(lock_icon)

        return menu

    def handle_menu_action(self, action):
        """Handle menu actions"""
        if self.is_locked:
            if action == self.action_unlock:
                self.is_locked = False
                self.tray_icon.showMessage("GIF Overlay", "Window unlocked.", 
                                         QSystemTrayIcon.Information, 2000)
            return

        if action == self.action_change_new:
            self.open_file_dialog()
        elif action == self.action_change_saved:
            self.open_saved_gif_dialog()
        elif action == self.action_change_resize_opacity:
            self.open_resize_opacity_dialog()
        elif action == self.action_toggle_pause:
            self.toggle_pause_gif()
        elif action == self.action_save:
            self.save_gif_to_documents()
        elif action == self.action_close_quit:
            QApplication.quit()
        elif action == self.action_close_minimize:
            flags = self.windowFlags() | Qt.Tool
            self.setWindowFlags(flags)
            self.show()
            self.raise_()
            self.activateWindow()
            self.tray_icon.showMessage(
                "GIF Overlay",
                "Minimized to system tray (taskbar icon hidden).",
                QSystemTrayIcon.Information,
                2000
            )
        elif action == self.action_lock:
            self.is_locked = True
            self.tray_icon.showMessage("GIF Overlay", "Window locked. Cannot be dragged.", 
                                     QSystemTrayIcon.Information, 2000)

    def contextMenuEvent(self, event):
        """Right-click context menu"""
        menu = self.create_menu()
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action:
            self.handle_menu_action(action)

    def show_menu_at_center(self):
        """Show menu at window center"""
        menu = self.create_menu()
        pos = self.mapToGlobal(self.rect().center())
        action = menu.exec_(pos)
        if action:
            self.handle_menu_action(action)

    def open_file_dialog(self):
        """Open file dialog to select GIF"""
        path, _ = QFileDialog.getOpenFileName(self, "Select GIF File", "", "GIF Files (*.gif)")
        if path:
            self.load_gif(path, reset_default=True)

    def load_gif(self, path, reset_default=False):
        """Load and display GIF"""
        if not os.path.exists(path):
            QMessageBox.warning(self, "Error", f"GIF file not found:\n{path}")
            return
            
        if self.movie:
            self.movie.stop()
            
        try:
            self.movie = QMovie(path)
            if not self.movie.isValid():
                QMessageBox.warning(self, "Error", "Invalid or corrupted GIF file.")
                return
                
            self.gif_label.setMovie(self.movie)
            self.movie.start()
            self.original_size = self.movie.currentPixmap().size()

            if reset_default:
                self.reset_to_default()
            else:
                settings = self.load_settings()
                if settings:
                    w, h, o = settings
                    self.resize(w, h)
                    if self.movie:
                        self.movie.setScaledSize(QSize(w, h))
                    self.setWindowOpacity(o)
                else:
                    self.resize(self.original_size)

            self.current_gif_path = path
            self.save_last_gif(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load GIF:\n{str(e)}")

    def save_last_gif(self, path):
        """Save last used GIF path"""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(path)
        except Exception as e:
            print(f"Error saving last gif path: {e}")

    def open_saved_gif_dialog(self):
        """Open modern dialog to select from saved GIFs"""
        if not GIF_SAVE_DIR.exists():
            QMessageBox.information(self, "Saved GIFs", "No saved GIFs directory found.")
            return
        
        dialog = SavedGifDialog(GIF_SAVE_DIR, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_path = dialog.get_selected_path()
            if selected_path:
                self.load_gif(selected_path, reset_default=True)

    def save_gif_to_documents(self):
        """Save current GIF to documents folder"""
        if not self.current_gif_path or not os.path.exists(self.current_gif_path):
            QMessageBox.warning(self, "Save GIF", "No GIF to save.")
            return
            
        GIF_SAVE_DIR.mkdir(exist_ok=True)
        default_name = os.path.basename(self.current_gif_path)
        default_base = os.path.splitext(default_name)[0]
        
        new_name, ok = QInputDialog.getText(self, "Save GIF", 
                                           "Enter filename (without .gif extension):", 
                                           text=default_base)
        if ok and new_name.strip():
            if not new_name.lower().endswith(".gif"):
                new_name += ".gif"
            dest = GIF_SAVE_DIR / new_name
            try:
                shutil.copy2(self.current_gif_path, dest)
                QMessageBox.information(self, "Save GIF", f"GIF saved to:\n{dest}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save GIF:\n{e}")

    def toggle_pause_gif(self):
        """Toggle GIF pause/play"""
        if not self.movie:
            return
        if self.movie.state() == QMovie.Running:
            self.movie.setPaused(True)
        else:
            self.movie.setPaused(False)

    def open_resize_opacity_dialog(self):
        """Open modern dialog for size and opacity adjustment"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Adjust Size & Opacity")
        dialog.setFixedWidth(450)
        dialog.setStyleSheet("""
            QDialog {
                background: white;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("🎨 Customize Your GIF")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                padding-bottom: 10px;
            }
        """)
        layout.addWidget(title)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background: #E0E0E0;")
        layout.addWidget(line)

        if self.original_size:
            orig_w = self.original_size.width()
            orig_h = self.original_size.height()
        else:
            orig_w = self.width()
            orig_h = self.height()

        # Sliders
        slider_scale = ModernSlider("Scale", 10, 300, 100, "%", dialog)
        slider_w = ModernSlider("Width", 50, 2000, self.width(), "px", dialog)
        slider_h = ModernSlider("Height", 50, 2000, self.height(), "px", dialog)
        slider_o = ModernSlider("Opacity", 10, 100, int(self.windowOpacity()*100), "%", dialog)

        layout.addWidget(slider_scale)
        layout.addWidget(slider_w)
        layout.addWidget(slider_h)
        layout.addWidget(slider_o)

        updating = [False]

        def on_slider_released():
            self.save_settings(self.width(), self.height(), self.windowOpacity())

        def update_width(value):
            if updating[0]:
                return
            updating[0] = True
            self.resize(value, self.height())
            if self.movie:
                self.movie.setScaledSize(QSize(value, self.height()))
            scale_w = int(value / orig_w * 100)
            slider_scale.setValue(scale_w)
            updating[0] = False

        def update_height(value):
            if updating[0]:
                return
            updating[0] = True
            self.resize(self.width(), value)
            if self.movie:
                self.movie.setScaledSize(QSize(self.width(), value))
            scale_h = int(value / orig_h * 100)
            slider_scale.setValue(scale_h)
            updating[0] = False

        def update_scale(value):
            if updating[0]:
                return
            updating[0] = True
            new_w = int(orig_w * value / 100)
            new_h = int(orig_h * value / 100)
            self.resize(new_w, new_h)
            if self.movie:
                self.movie.setScaledSize(QSize(new_w, new_h))
            slider_w.setValue(new_w)
            slider_h.setValue(new_h)
            updating[0] = False

        def update_opacity(value):
            self.setWindowOpacity(value / 100)

        slider_w.valueChanged.connect(update_width)
        slider_h.valueChanged.connect(update_height)
        slider_scale.valueChanged.connect(update_scale)
        slider_o.valueChanged.connect(update_opacity)

        slider_w.sliderReleased.connect(on_slider_released)
        slider_h.sliderReleased.connect(on_slider_released)
        slider_scale.sliderReleased.connect(on_slider_released)
        slider_o.sliderReleased.connect(lambda: self.save_settings(self.width(), self.height(), self.windowOpacity()))

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        btn_reset = ModernButton("Reset to Default")
        def reset_defaults():
            slider_w.setValue(orig_w)
            slider_h.setValue(orig_h)
            slider_scale.setValue(100)
            self.resize(orig_w, orig_h)
            if self.movie:
                self.movie.setScaledSize(QSize(orig_w, orig_h))
            slider_o.setValue(100)
            self.setWindowOpacity(1.0)
            self.save_settings(orig_w, orig_h, 1.0)
        btn_reset.clicked.connect(reset_defaults)
        
        btn_close = ModernButton("Done", primary=True)
        btn_close.clicked.connect(dialog.accept)
        
        btn_layout.addWidget(btn_reset)
        btn_layout.addWidget(btn_close)
        
        layout.addSpacing(10)
        layout.addLayout(btn_layout)

        dialog.exec_()

    def show_normal(self):
        """Show window normally"""
        flags = self.windowFlags()
        flags = flags & (~Qt.Tool)
        self.setWindowFlags(flags)
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self,
            "Close Application",
            "Do you want to quit the application or minimize to system tray?",
            QMessageBox.Close | QMessageBox.Ignore,
            QMessageBox.Ignore
        )
        if reply == QMessageBox.Close:
            event.accept()
        else:
            event.ignore()
            flags = self.windowFlags() | Qt.Tool
            self.setWindowFlags(flags)
            self.show()
            self.tray_icon.showMessage(
                "GIF Overlay",
                "Minimized to system tray (taskbar icon hidden).",
                QSystemTrayIcon.Information,
                2000
            )

    def on_tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                flags = self.windowFlags()
                flags = flags & (~Qt.Tool)
                self.setWindowFlags(flags)
                self.show()
                self.raise_()
                self.activateWindow()

    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if self.is_locked:
            return
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if self.is_locked:
            return
        if event.buttons() & Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    window = GifOnTop()
    sys.exit(app.exec_())