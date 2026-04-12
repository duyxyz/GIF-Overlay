from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QFont


class ModernButton(QPushButton):
    """
    Nút bấm native 100% — không sử dụng CSS để giữ trọn vẹn engine vẽ của hệ điều hành.
    """
    def __init__(self, text, primary=False, parent=None):
        super().__init__(text, parent)
        
        if primary:
            self.setDefault(True)
            font = self.font()
            font.setBold(True)
            self.setFont(font)
