import logging
import time
from typing import Optional
from PyQt5.QtGui import QMovie, QImageReader
from PyQt5.QtCore import QObject, pyqtSignal, QSize, Qt
from PyQt5.QtWidgets import QApplication

from components.constants import DEFAULT_FALLBACK_SIZE, DEFAULT_RESET_SIZE
from components.settings_manager import SettingsManager

logger = logging.getLogger("GIF-Overlay.Service")

class MediaService(QObject):
    """Layer 2: Service Layer - Handles GIF logic and state"""
    mediaLoaded = pyqtSignal(QSize)
    transformChanged = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.movie: Optional[QMovie] = None
        self.current_gif_path: Optional[str] = None
        self.original_size: Optional[QSize] = None
        self.original_size_cache = {}

        # Transformation State
        self.rotation_angle = 0
        self.flip_h = False
        self.flip_v = False

    def load_media(self, path: str) -> bool:
        """Tải và xử lý logic GIF"""
        logger.info(f"Loading media: {path}")
        start_time = time.perf_counter()
        
        self.rotation_angle = 0
        self.flip_h = False
        self.flip_v = False

        if self.movie:
            self.movie.stop()
            self.movie = None

        try:
            temp_movie = QMovie(path)
            if not temp_movie.isValid():
                reader = QImageReader(path)
                if reader.format().lower() != b'gif':
                    logger.error(f"Unsupported format: {reader.format()}")
                    return False
                if not temp_movie.isValid():
                    logger.error(f"Corrupted GIF: {path}")
                    return False

            self.movie = temp_movie
            
            # Determine original size
            reader = QImageReader(path)
            detected_size = reader.size() if reader.canRead() else QSize(0, 0)
            if not detected_size.isValid() or detected_size.width() <= 0:
                self.movie.jumpToFrame(0)
                detected_size = self.movie.frameRect().size()
            if not detected_size.isValid() or detected_size.width() <= 0:
                detected_size = self.original_size_cache.get(path, QSize(*DEFAULT_FALLBACK_SIZE))
            
            self.original_size = detected_size
            self.original_size_cache[path] = self.original_size

            # H DPI Compensation
            ratio = QApplication.primaryScreen().devicePixelRatio()
            if ratio > 1.0:
                self.original_size = QSize(
                    int(self.original_size.width() / ratio), 
                    int(self.original_size.height() / ratio)
                )

            self.current_gif_path = path
            SettingsManager.save_last_path(path)
            
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.info(f"Media loaded in {elapsed:.2f}ms")
            
            self.mediaLoaded.emit(self.get_target_size())
            return True
            
        except Exception:
            logger.exception("Failed to load media")
            return False

    def get_target_size(self) -> QSize:
        """Tính toán kích thước hiển thị tối ưu"""
        if not self.original_size:
            return QSize(*DEFAULT_RESET_SIZE)
            
        target_size = self.original_size
        screen = QApplication.primaryScreen().availableGeometry()
        max_w, max_h = int(screen.width() * 0.8), int(screen.height() * 0.8)
        
        if target_size.width() > max_w or target_size.height() > max_h:
            target_size = target_size.scaled(max_w, max_h, Qt.KeepAspectRatio)
        return target_size

    def rotate_right(self):
        self.rotation_angle = (self.rotation_angle + 90) % 360
        self.transformChanged.emit()

    def rotate_left(self):
        self.rotation_angle = (self.rotation_angle - 90) % 360
        self.transformChanged.emit()

    def toggle_flip_h(self):
        self.flip_h = not self.flip_h
        self.transformChanged.emit()

    def toggle_flip_v(self):
        self.flip_v = not self.flip_v
        self.transformChanged.emit()

    def toggle_pause(self):
        if self.movie:
            self.movie.setPaused(not self.movie.state() == QMovie.Paused)
