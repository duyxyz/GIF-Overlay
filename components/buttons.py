from PyQt5.QtWidgets import QPushButton


class ModernButton(QPushButton):
    """Native Windows button — no custom QSS"""
    def __init__(self, text, primary=False, parent=None):
        super().__init__(text, parent)
        # primary flag kept for API compatibility but appearance is native
