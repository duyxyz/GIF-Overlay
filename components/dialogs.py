from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QFrame, QSplitter, 
    QListWidget, QListWidgetItem, QHBoxLayout, QMessageBox,
    QCheckBox, QApplication, QWidget, QLineEdit
)
from PyQt5.QtGui import QMovie, QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize
import sys
import os
from pathlib import Path
import ctypes

from components.buttons import ModernButton
from components.widgets import ModernSlider

class ModernInputDialog(QDialog):
    """Premium-styled input dialog for high-end look"""
    def __init__(self, title, label_text, initial_value="", parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.main_window = parent
        self.setWindowTitle(title)
        if self.main_window:
            self.main_window.apply_dark_title_bar(self)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        self.label = QLabel(label_text)
        self.label.setStyleSheet("color: #DDDDDD; font-size: 13px; font-weight: 500;")
        layout.addWidget(self.label)
        
        self.input = QLineEdit(initial_value)
        self.input.setStyleSheet("""
            QLineEdit {
                background: #252526;
                color: #EEEEEE;
                border: 1px solid #454545;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
                selection-background-color: #3D85C6;
            }
            QLineEdit:focus {
                border: 1px solid #3D85C6;
            }
        """)
        # Select text when focused
        self.input.selectAll()
        layout.addWidget(self.input)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()
        
        self.cancel_btn = ModernButton("Cancel")
        if self.main_window:
            self.cancel_btn.setIcon(self.main_window.load_icon("close.png") or QIcon())
        self.cancel_btn.clicked.connect(self.reject)
        
        self.ok_btn = ModernButton("Save", primary=True)
        if self.main_window:
            self.ok_btn.setIcon(self.main_window.load_icon("save.png") or QIcon())
        self.ok_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.ok_btn)
        layout.addLayout(btn_layout)
        
    def text_value(self):
        return self.input.text()

class SavedGifDialog(QDialog):
    """Native-styled dialog for selecting saved media"""
    def __init__(self, gif_dir, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.gif_dir = gif_dir
        self.selected_path = None
        self.current_movie = None
        self.current_pixmap = None
        self.main_window = parent
        
        self.setWindowTitle("Saved Media")
        if self.main_window:
            self.main_window.apply_dark_title_bar(self)
        self.setMinimumSize(650, 450)
        
        self.setup_ui()
        self.load_gifs()
    
    def setup_ui(self):
        """Setup a clean, native UI with minimal QSS"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Main content with splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: GIF list
        self.gif_list = QListWidget()
        self.gif_list.setIconSize(QSize(20, 20))
        self.gif_list.itemClicked.connect(self.on_gif_selected)
        self.gif_list.itemDoubleClicked.connect(self.on_gif_double_clicked)
        
        # Right: Preview
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(5, 0, 0, 0)
        
        self.preview_label = QLabel("Select media")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(250, 250)
        self.preview_label.setStyleSheet("background: #1A1A1A; border-radius: 4px; color: #555;")
        
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #777777; font-size: 11px; margin-left: 10px;")
        
        preview_layout.addWidget(self.preview_label, 1)
        # Removed info_label from here
        
        splitter.addWidget(self.gif_list)
        splitter.addWidget(preview_container)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        self.delete_btn = ModernButton("Delete")
        if self.main_window:
            self.delete_btn.setIcon(self.main_window.load_icon("delete.png") or QIcon())
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_selected_gif)
        
        self.select_btn = ModernButton("Select", primary=True)
        if self.main_window:
            self.select_btn.setIcon(self.main_window.load_icon("select.png") or QIcon())
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self.accept)
        
        cancel_btn = ModernButton("Cancel")
        if self.main_window:
            cancel_btn.setIcon(self.main_window.load_icon("close.png") or QIcon())
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.info_label)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.select_btn)
        
        layout.addLayout(btn_layout)
    
    def load_gifs(self):
        # Search for GIFs and Images
        extensions = ["*.gif", "*.png", "*.jpg", "*.jpeg", "*.bmp", "*.webp"]
        media_files = []
        for ext in extensions:
            media_files.extend(list(self.gif_dir.glob(ext)))
        
        media_files = sorted(media_files, key=lambda x: x.name.lower())
        
        if not media_files:
            item = QListWidgetItem("No saved media found")
            item.setFlags(Qt.NoItemFlags)
            self.gif_list.addItem(item)
            return
        
        for media_path in media_files:
            item = QListWidgetItem(media_path.name)
            item.setData(Qt.UserRole, str(media_path))
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
            self.current_movie = None
        self.preview_label.clear()
        self.current_pixmap = None
        
        # Load and preview media
        try:
            # Try GIF first
            temp_movie = QMovie(gif_path)
            if temp_movie.isValid():
                self.current_movie = temp_movie
                self.current_movie.jumpToFrame(0)
                pix = self.current_movie.currentPixmap()
                if not pix.isNull():
                    original_size = pix.size()
                    scaled_size = original_size.scaled(280, 280, Qt.KeepAspectRatio)
                    self.current_movie.setScaledSize(scaled_size)
                    self.preview_label.setMovie(self.current_movie)
                    self.current_movie.start()
                    
                    file_size = Path(gif_path).stat().st_size / 1024
                    self.info_label.setText(
                        f"Size: {original_size.width()}x{original_size.height()}px | "
                        f"File: {file_size:.1f} KB"
                    )
            else:
                # Try static image
                self.current_pixmap = QPixmap(gif_path)
                if not self.current_pixmap.isNull():
                    original_size = self.current_pixmap.size()
                    scaled_pix = self.current_pixmap.scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.preview_label.setPixmap(scaled_pix)
                    
                    file_size = Path(gif_path).stat().st_size / 1024
                    self.info_label.setText(
                        f"Size: {original_size.width()}x{original_size.height()}px | "
                        f"File: {file_size:.1f} KB"
                    )
                else:
                    self.preview_label.setText("❌ Unsupported format")
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
                current_row = self.gif_list.currentRow()
                self.gif_list.takeItem(current_row)
                if self.current_movie:
                    self.current_movie.stop()
                    self.current_movie = None
                self.preview_label.clear()
                self.preview_label.setText("Select media to preview")
                self.info_label.setText("")
                self.selected_path = None
                self.current_pixmap = None
                self.select_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
                QMessageBox.information(self, "Success", "Media deleted successfully!")
                if self.gif_list.count() == 0:
                    item = QListWidgetItem("No saved media found")
                    item.setFlags(Qt.NoItemFlags)
                    self.gif_list.addItem(item)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete GIF:\n{str(e)}")
    
    def get_selected_path(self):
        return self.selected_path
    
    def closeEvent(self, event):
        if self.current_movie:
            self.current_movie.stop()
        super().closeEvent(event)

class ResizeOpacityDialog(QDialog):
    """Modern dialog for size and opacity adjustment for dark mode"""
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.p = parent_window
        self.setWindowTitle("Adjust Size & Opacity")
        if self.p:
            self.p.apply_dark_title_bar(self)
        self.setFixedWidth(450)
        self.setStyleSheet("QDialog { background: #1E1E1E; border: 1px solid #333333; }")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title_container = QHBoxLayout()
        icon_label = QLabel()
        icon = self.p.load_icon("settings.png")
        if icon:
            icon_label.setPixmap(icon.pixmap(24, 24))
            
        title = QLabel("Customize Your Media")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #EEEEEE;")
        
        title_container.addWidget(icon_label)
        title_container.addWidget(title)
        title_container.addStretch()
        layout.addLayout(title_container)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background: #333333;")
        layout.addWidget(line)

        if self.p.original_size:
            self.orig_w = self.p.original_size.width()
            self.orig_h = self.p.original_size.height()
        else:
            self.orig_w = self.p.width()
            self.orig_h = self.p.height()

        self.slider_scale = ModernSlider("Scale", 10, 300, 100, "%", self)
        self.slider_w = ModernSlider("Width", 50, 2000, self.p.width(), "px", self)
        self.slider_h = ModernSlider("Height", 50, 2000, self.p.height(), "px", self)
        self.slider_o = ModernSlider("Opacity", 10, 100, int(self.p.windowOpacity()*100), "%", self)

        layout.addWidget(self.slider_scale)
        layout.addWidget(self.slider_w)
        layout.addWidget(self.slider_h)
        layout.addWidget(self.slider_o)

        self.cb_lock = QCheckBox("Lock Aspect Ratio")
        self.cb_lock.setChecked(self.p.lock_aspect_ratio)
        self.cb_lock.setStyleSheet("color: #BBBBBB; margin-left: 10px; font-weight: 500;")
        layout.addWidget(self.cb_lock)

        self.updating = False

        self.slider_w.valueChanged.connect(self.update_width)
        self.slider_h.valueChanged.connect(self.update_height)
        self.slider_scale.valueChanged.connect(self.update_scale)
        self.slider_o.valueChanged.connect(self.update_opacity)

        self.slider_w.sliderReleased.connect(self.on_released)
        self.slider_h.sliderReleased.connect(self.on_released)
        self.slider_scale.sliderReleased.connect(self.on_released)
        self.slider_o.sliderReleased.connect(self.on_released)
        
        self.cb_lock.stateChanged.connect(self.update_lock_state)

        btn_layout = QHBoxLayout()
        btn_reset = ModernButton("Reset to Default")
        if self.p:
            btn_reset.setIcon(self.p.load_icon("settings.png") or QIcon())
        btn_reset.clicked.connect(self.reset_defaults)
        
        btn_close = ModernButton("Done", primary=True)
        if self.p:
            btn_close.setIcon(self.p.load_icon("select.png") or QIcon())
        btn_close.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_reset)
        btn_layout.addWidget(btn_close)
        layout.addSpacing(10)
        layout.addLayout(btn_layout)

    def on_released(self):
        self.p.save_settings(self.p.width(), self.p.height(), self.p.windowOpacity())

    def update_width(self, value):
        if self.updating: return
        self.updating = True
        new_h = self.p.height()
        if self.cb_lock.isChecked() and self.orig_w > 0:
            new_h = int(value * self.orig_h / self.orig_w)
            self.slider_h.setValue(new_h)
        self.p.resize(value, new_h)
        scale = int(value / self.orig_w * 100) if self.orig_w > 0 else 100
        self.slider_scale.setValue(scale)
        self.updating = False

    def update_height(self, value):
        if self.updating: return
        self.updating = True
        new_w = self.p.width()
        if self.cb_lock.isChecked() and self.orig_h > 0:
            new_w = int(value * self.orig_w / self.orig_h)
            self.slider_w.setValue(new_w)
        self.p.resize(new_w, value)
        scale = int(value / self.orig_h * 100) if self.orig_h > 0 else 100
        self.slider_scale.setValue(scale)
        self.updating = False

    def update_scale(self, value):
        if self.updating: return
        self.updating = True
        new_w = int(self.orig_w * value / 100)
        new_h = int(self.orig_h * value / 100)
        self.p.resize(new_w, new_h)
        self.slider_w.setValue(new_w)
        self.slider_h.setValue(new_h)
        self.updating = False

    def update_opacity(self, value):
        self.p.setWindowOpacity(value / 100)

    def update_lock_state(self, state):
        self.p.lock_aspect_ratio = (state == Qt.Checked)

    def reset_defaults(self):
        self.slider_w.setValue(self.orig_w)
        self.slider_h.setValue(self.orig_h)
        self.slider_scale.setValue(100)
        self.slider_o.setValue(100)
        self.p.resize(self.orig_w, self.orig_h)
        self.p.setWindowOpacity(1.0)
        self.p.save_settings(self.orig_w, self.orig_h, 1.0)
