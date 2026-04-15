from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal


class ModernSlider(QWidget):
    """Slider with label — native Windows appearance, no QSS"""
    valueChanged = pyqtSignal(int)
    sliderReleased = pyqtSignal()

    def __init__(self, label_text, min_val, max_val, current_val, suffix="", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)

        head_layout = QHBoxLayout()
        self.label = QLabel(label_text)
        self.value_label = QLabel(f"{current_val}{suffix}")

        head_layout.addWidget(self.label)
        head_layout.addStretch()
        head_layout.addWidget(self.value_label)
        layout.addLayout(head_layout)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(min_val)
        self.slider.setMaximum(max_val)
        self.slider.setValue(current_val)
        layout.addWidget(self.slider)

        self.suffix = suffix
        self.slider.valueChanged.connect(self._on_value_changed)
        self.slider.sliderReleased.connect(self.sliderReleased.emit)

    def _on_value_changed(self, value):
        self.value_label.setText(f"{value}{self.suffix}")
        self.valueChanged.emit(value)

    def value(self):
        return self.slider.value()

    def setValue(self, value):
        self.slider.setValue(value)
