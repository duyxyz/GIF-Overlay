from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QHBoxLayout, QWidgetAction, QCheckBox, QPushButton, QFrame
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

class MenuSliderAction(QWidgetAction):
    """Custom action to embed a slider into a QMenu"""
    valueChanged = pyqtSignal(int)

    def __init__(self, label, min_val, max_val, current_val, suffix="", parent=None):
        super().__init__(parent)
        self.label_text = label
        self.min_val = min_val
        self.max_val = max_val
        self.current_val = current_val
        self.suffix = suffix
        self.slider = None
        self.val_lbl = None

    def createWidget(self, parent):
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(15, 6, 15, 6)
        layout.setSpacing(10)
        
        lbl = QLabel(self.label_text)
        lbl.setMinimumWidth(50)
        lbl.setStyleSheet("font-weight: 500;")
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(self.min_val)
        self.slider.setMaximum(self.max_val)
        self.slider.setValue(self.current_val)
        self.slider.setMinimumWidth(120)
        
        self.val_lbl = QLabel(f"{self.current_val}{self.suffix}")
        self.val_lbl.setMinimumWidth(40)
        self.val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        layout.addWidget(lbl)
        layout.addWidget(self.slider)
        layout.addWidget(self.val_lbl)
        
        self.slider.valueChanged.connect(self._handle_value_changed)
        
        return widget

    def _handle_value_changed(self, value):
        if self.val_lbl:
            self.val_lbl.setText(f"{value}{self.suffix}")
        self.valueChanged.emit(value)

    def setValue(self, value):
        if self.slider:
            self.slider.setValue(value)
        else:
            self.current_val = value

class MenuCheckboxAction(QWidgetAction):
    """Custom action to embed a checkbox into a QMenu"""
    toggled = pyqtSignal(bool)

    def __init__(self, label, checked=False, parent=None):
        super().__init__(parent)
        self.label_text = label
        self.checked = checked
        self.checkbox = None

    def createWidget(self, parent):
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(15, 6, 15, 6)
        
        self.checkbox = QCheckBox(self.label_text)
        self.checkbox.setChecked(self.checked)
        self.checkbox.setStyleSheet("font-weight: 500;")
        
        layout.addWidget(self.checkbox)
        self.checkbox.stateChanged.connect(lambda state: self.toggled.emit(state == Qt.Checked))
        
        return widget

    def setChecked(self, checked):
        if self.checkbox:
            self.checkbox.setChecked(checked)
        else:
            self.checked = checked

class MenuButtonAction(QWidgetAction):
    """Custom action to embed a button into a QMenu"""
    clicked = pyqtSignal()

    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.label_text = label

    def createWidget(self, parent):
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(15, 6, 15, 6)
        
        btn = QPushButton(self.label_text)
        btn.setStyleSheet("font-weight: 500; padding: 4px;")
        btn.clicked.connect(lambda: (self.clicked.emit(), parent.close()))
        
        layout.addWidget(btn)
        return widget

class MenuSeparatorAction(QWidgetAction):
    """Custom action to embed a full-width separator line into a QMenu"""
    def __init__(self, parent=None):
        super().__init__(parent)

    def createWidget(self, parent):
        line = QFrame(parent)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Plain)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #E0E0E0; margin: 4px 0px;")
        return line
