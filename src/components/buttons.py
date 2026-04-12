from PyQt5.QtWidgets import QPushButton
import os
import sys

class ModernButton(QPushButton):
    """Modern styled button"""
    def __init__(self, text, primary=False, parent=None):
        super().__init__(text, parent)
        if primary:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #3D85C6, stop:1 #295F8A);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 13px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                stop:0 #4A90E2, stop:1 #3D85C6);
                }
                QPushButton:pressed {
                    background: #1C456B;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: #333333;
                    color: #EEEEEE;
                    border: 1px solid #444444;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: #444444;
                    border: 1px solid #555555;
                }
                QPushButton:pressed {
                    background: #222222;
                }
            """)
