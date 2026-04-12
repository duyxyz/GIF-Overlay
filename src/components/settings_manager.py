import hashlib
import logging
from pathlib import Path

from components.constants import (
    CONFIG_FILE, CONFIG_SETTINGS_FILE, CONFIG_GIF_SETTINGS_DIR
)

logger = logging.getLogger(__name__)


class SettingsMixin:
    """Quản lý lưu/đọc cài đặt người dùng (kích thước, độ mờ, trạng thái khóa)"""

    def save_settings(self, width: int, height: int, opacity: float):
        try:
            lock_status = 1 if self.is_locked else 0
            settings_str = f"{width}\n{height}\n{opacity}\n0\n0\n{lock_status}\n"
            with open(CONFIG_SETTINGS_FILE, "w", encoding="utf-8") as f:
                f.write(settings_str)
            if self.current_gif_path:
                config_path = CONFIG_GIF_SETTINGS_DIR / self.get_gif_config_name(self.current_gif_path)
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(settings_str)
        except Exception as e:
            logger.warning("Error saving settings: %s", e)

    def load_settings(self):
        settings_data = None
        if self.current_gif_path:
            config_path = CONFIG_GIF_SETTINGS_DIR / self.get_gif_config_name(self.current_gif_path)
            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        settings_data = f.read().splitlines()
                except Exception:
                    pass
        
        if not settings_data and CONFIG_SETTINGS_FILE.exists():
            try:
                with open(CONFIG_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings_data = f.read().splitlines()
            except Exception:
                pass
                
        if settings_data and len(settings_data) >= 3:
            try:
                width = int(settings_data[0])
                height = int(settings_data[1])
                opacity = float(settings_data[2])
                is_locked = (int(settings_data[5]) == 1) if len(settings_data) >= 6 else False
                return width, height, opacity, None, None, is_locked
            except (ValueError, IndexError):
                pass
        return None
    
    def get_gif_config_name(self, gif_path):
        path_hash = hashlib.md5(gif_path.encode()).hexdigest()
        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in Path(gif_path).stem)
        return f"{safe_name}_{path_hash[:8]}.txt"
