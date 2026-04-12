from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt


class ModernButton(QPushButton):
    """
    Nút bấm native — sử dụng hoàn toàn Fusion style.
    Không dùng setStyleSheet để tránh vỡ render native của Qt.
    """
    def __init__(self, text, primary=False, parent=None):
        super().__init__(text, parent)
        
        # Đặt font size chuẩn một chút (không dùng CSS để giữ native engine)
        font = self.font()
        font.setPointSize(10)
        default_weight = font.weight()
        if hasattr(font, 'Weight'):
             # PyQt5 style
             try:
                 font.setWeight(font.Weight.Medium if primary else font.Weight.Normal)
             except:
                 pass
        self.setFont(font)
        
        # Bỏ qua viền xanh (focus ring) khi người dùng bấm vào nút
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
