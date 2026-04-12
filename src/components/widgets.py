from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal

class ModernSlider(QWidget):
    """Modern slider with label for dark mode"""
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
        self.label.setStyleSheet("font-weight: bold; color: #BBBBBB; font-size: 13px;")
        
        self.value_label = QLabel(f"{current_val}{suffix}")
        self.value_label.setStyleSheet("color: #3D85C6; font-weight: bold; font-size: 13px;")
        
        head_layout.addWidget(self.label)
        head_layout.addStretch()
        head_layout.addWidget(self.value_label)
        layout.addLayout(head_layout)
        
        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(min_val)
        self.slider.setMaximum(max_val)
        self.slider.setValue(current_val)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #444444;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #3D85C6;
                border: 1px solid #295F8A;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #4A90E2;
            }
            QSlider::sub-page:horizontal {
                background: #3D85C6;
                border-radius: 3px;
            }
        """)
        
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
