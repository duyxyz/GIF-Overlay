from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QFrame, QSplitter,
    QListWidget, QListWidgetItem, QHBoxLayout, QMessageBox,
    QWidget, QLineEdit
)
from PyQt5.QtGui import QMovie, QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize
import os
from pathlib import Path

from components.buttons import ModernButton



class ModernInputDialog(QDialog):
    """Native input dialog — no custom QSS"""
    def __init__(self, title, label_text, initial_value="", parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.main_window = parent
        self.setWindowTitle(title)
        if self.main_window:
            self.main_window.apply_dark_title_bar(self)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.label = QLabel(label_text)
        layout.addWidget(self.label)

        self.input = QLineEdit(initial_value)
        self.input.selectAll()
        layout.addWidget(self.input)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
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
    """Native dialog for selecting saved media — no custom QSS"""
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        splitter = QSplitter(Qt.Horizontal)

        self.gif_list = QListWidget()
        self.gif_list.setIconSize(QSize(20, 20))
        self.gif_list.itemClicked.connect(self.on_gif_selected)
        self.gif_list.itemDoubleClicked.connect(self.on_gif_double_clicked)

        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(5, 0, 0, 0)

        self.preview_label = QLabel("Select media")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(250, 250)
        self.preview_label.setFrameShape(QFrame.StyledPanel)

        self.info_label = QLabel("")

        preview_layout.addWidget(self.preview_label, 1)

        splitter.addWidget(self.gif_list)
        splitter.addWidget(preview_container)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

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
        gif_path = item.data(Qt.UserRole)
        if not gif_path:
            return

        self.selected_path = gif_path
        self.select_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)

        if self.current_movie:
            self.current_movie.stop()
            self.current_movie = None
        self.preview_label.clear()
        self.current_pixmap = None

        try:
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
                        f"{original_size.width()}x{original_size.height()}px | {file_size:.1f} KB"
                    )
            else:
                self.current_pixmap = QPixmap(gif_path)
                if not self.current_pixmap.isNull():
                    original_size = self.current_pixmap.size()
                    scaled_pix = self.current_pixmap.scaled(280, 280, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.preview_label.setPixmap(scaled_pix)

                    file_size = Path(gif_path).stat().st_size / 1024
                    self.info_label.setText(
                        f"{original_size.width()}x{original_size.height()}px | {file_size:.1f} KB"
                    )
                else:
                    self.preview_label.setText("Unsupported format")
                    self.info_label.setText("")
        except Exception as e:
            self.preview_label.setText(f"Error loading preview:\n{str(e)}")
            self.info_label.setText("")

    def on_gif_double_clicked(self, item):
        self.on_gif_selected(item)
        if self.selected_path:
            self.accept()

    def delete_selected_gif(self):
        if not self.selected_path:
            return

        msg = QMessageBox(self)
        msg.setWindowFlags(msg.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        msg.setWindowTitle("Delete Media")
        msg.setText(f"Are you sure you want to delete this media?\n\n{Path(self.selected_path).name}")
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        if self.main_window:
            self.main_window.apply_dark_title_bar(msg)

        if msg.exec_() == QMessageBox.Yes:
            try:
                os.remove(self.selected_path)
                self.gif_list.takeItem(self.gif_list.currentRow())
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
                QMessageBox.critical(self, "Error", f"Failed to delete media:\n{str(e)}")

    def get_selected_path(self):
        return self.selected_path

    def closeEvent(self, event):
        if self.current_movie:
            self.current_movie.stop()
        super().closeEvent(event)


