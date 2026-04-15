import hashlib
from pathlib import Path
from components.constants import (
    CONFIG_FILE, CONFIG_SETTINGS_FILE, CONFIG_GIF_SETTINGS_DIR
)


class SettingsManager:
    """Quản lý đọc/ghi settings cho ứng dụng"""

    @staticmethod
    def get_gif_config_name(gif_path: str) -> str:
        path_hash = hashlib.md5(gif_path.encode()).hexdigest()
        safe_name = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in Path(gif_path).stem)
        return f"{safe_name}_{path_hash[:8]}.txt"

    @staticmethod
    def save(width: int, height: int, opacity: float, is_locked: bool, gif_path: str = None):
        """Ghi settings ra file"""
        try:
            lock_status = 1 if is_locked else 0
            settings_str = f"{width}\n{height}\n{opacity}\n0\n0\n{lock_status}\n"
            with open(CONFIG_SETTINGS_FILE, "w", encoding="utf-8") as f:
                f.write(settings_str)
            if gif_path:
                config_path = CONFIG_GIF_SETTINGS_DIR / SettingsManager.get_gif_config_name(gif_path)
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(settings_str)
        except Exception as e:
            print(f"Error saving settings: {e}")

    @staticmethod
    def load(gif_path: str = None):
        """Đọc settings từ file. Trả về (w, h, opacity, None, None, is_locked) hoặc None."""
        settings_data = None
        if gif_path:
            config_path = CONFIG_GIF_SETTINGS_DIR / SettingsManager.get_gif_config_name(gif_path)
            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        settings_data = f.read().splitlines()
                except Exception as e:
                    print(f"Error reading gif config: {e}")

        if not settings_data and CONFIG_SETTINGS_FILE.exists():
            try:
                with open(CONFIG_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings_data = f.read().splitlines()
            except Exception as e:
                print(f"Error reading global settings: {e}")

        if settings_data and len(settings_data) >= 3:
            try:
                w, h = int(settings_data[0]), int(settings_data[1])
                o = float(settings_data[2])
                ct = (int(settings_data[5]) == 1) if len(settings_data) >= 6 else False
                return w, h, o, None, None, ct
            except (ValueError, IndexError) as e:
                print(f"Error parsing settings data: {e}")
        return None

    @staticmethod
    def save_last_path(path: str):
        """Lưu đường dẫn media cuối cùng"""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(path)
        except Exception as e:
            print(f"Error saving last path: {e}")

    @staticmethod
    def load_last_path() -> str:
        """Đọc đường dẫn media cuối cùng"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                print(f"Error loading last path: {e}")
        return None
