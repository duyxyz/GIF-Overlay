from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ModernSlider(QWidget):
    """Thanh trượt với nhãn — sử dụng hoàn toàn style hệ thống"""
    valueChanged = pyqtSignal(int)
    sliderReleased = pyqtSignal()
    
    def __init__(self, label_text, min_val, max_val, current_val, suffix="", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # Header layout for label and value
        head_layout = QHBoxLayout()
        self.label = QLabel(label_text)
        
        # Sử dụng QFont thay vì setStyleSheet để giữ độ native
        font = QFont()
        font.setBold(True)
        self.label.setFont(font)
        
        self.value_label = QLabel(f"{current_val}{suffix}")
        self.value_label.setFont(font)
        
        head_layout.addWidget(self.label)
        head_layout.addStretch()
        head_layout.addWidget(self.value_label)
        layout.addLayout(head_layout)
        
        # Slider — 100% native
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(min_val)
        self.slider.setMaximum(max_val)
        self.slider.setValue(current_val)
        layout.addWidget(self.slider)
        
        self.suffix = suffix
        self.label_text = label_text
        
        self.slider.valueChanged.connect(self._on_value_changed)
        self.slider.sliderReleased.connect(self.sliderReleased.emit)
    
    def _on_value_changed(self, value):
        self.value_label.setText(f"{value}{self.suffix}")
        self.valueChanged.emit(value)
    
    def value(self):
        return self.slider.value()
    
    def setValue(self, value):
        self.slider.setValue(value)
