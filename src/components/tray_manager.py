import os
import sys
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMenu, QSystemTrayIcon, QStyle
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt

from components.constants import TRAY_MESSAGE_DURATION

logger = logging.getLogger(__name__)


class TrayMixin:
    """Quản lý System Tray Icon và các thao tác ẩn/hiện cửa sổ"""

    def setup_tray_icon(self):
        """Setup system tray icon with dark menu"""
        base_dir = Path(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))))
        icon_path = base_dir / "assets" / "app_icon.ico"
        if not icon_path.exists():
            icon_path = base_dir / "app_icon.ico"

        self.tray_icon = QSystemTrayIcon(self)
        icon = QIcon(str(icon_path)) if icon_path.exists() else self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        self.setWindowIcon(icon)

        self.tray_menu = QMenu()
        
        self.tray_show_action = QAction("Show", self)
        self.tray_show_action.setIcon(self.load_icon("show.png") or QIcon())
        self.tray_show_action.triggered.connect(self.show_normal)
        
        self.tray_lock_action = QAction("Lock", self)
        self.tray_lock_action.triggered.connect(self.toggle_lock)

        quit_action = QAction("Quit", self)
        quit_action.setIcon(self.load_icon("quit.png") or QIcon())
        quit_action.triggered.connect(self.quit_app)
        
        self.tray_menu.addAction(self.tray_show_action)
        self.tray_menu.addAction(self.tray_lock_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(quit_action)
        
        self.tray_menu.aboutToShow.connect(self.update_tray_menu)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def update_tray_menu(self):
        """Dynamically update tray menu states before showing"""
        should_show = not self.isVisible() or self.is_minimized_to_tray
        self.tray_show_action.setVisible(should_show)
        
        if self.is_locked:
            self.tray_lock_action.setText("Unlock")
            self.tray_lock_action.setIcon(self.load_icon("unlock.png") or QIcon())
        else:
            self.tray_lock_action.setText("Lock")
            self.tray_lock_action.setIcon(self.load_icon("lock.png") or QIcon())

    def minimize_to_tray(self):
        self.is_minimized_to_tray = True
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Tool)
        self.show()
        self.tray_icon.showMessage("GIF Overlay", "Minimized to tray.", QSystemTrayIcon.MessageIcon.Information, TRAY_MESSAGE_DURATION)
        self.update_tray_menu()

    def show_normal(self):
        self.is_minimized_to_tray = False
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.Tool)
        self.show()
        self.raise_()
        self.activateWindow()
        self.update_tray_menu()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible(): self.hide()
            else: self.show_normal()
