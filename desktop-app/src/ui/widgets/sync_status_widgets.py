"""
Sync Status Widget - Shows synchronization status
Displays online/offline status and sync progress
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt6.QtCore import pyqtSignal, QTimer
from PyQt6.QtGui import QFont

class SyncStatusWidget(QWidget):
    """Widget for displaying sync status and controls"""
    
    # Signals
    manual_sync_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        self.is_online = False
        self.sync_in_progress = False
        
        self.init_ui()
        self.setup_update_timer()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Connection status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Arial", 12))
        self.update_status_indicator()
        layout.addWidget(self.status_indicator)
        
        # Status text
        self.status_label = QLabel("Offline")
        self.status_label.setFont(QFont("Arial", 9))
        layout.addWidget(self.status_label)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(15)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Manual sync button
        self.sync_button = QPushButton("Sync")
        self.sync_button.setMaximumWidth(50)
        self.sync_button.setMaximumHeight(25)
        self.sync_button.clicked.connect(self.manual_sync_requested.emit)
        layout.addWidget(self.sync_button)
        
        # Pending items count
        self.pending_label = QLabel("")
        self.pending_label.setFont(QFont("Arial", 8))
        layout.addWidget(self.pending_label)
        
    def setup_update_timer(self):
        """Setup timer for status updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(5000)  # Update every 5 seconds
        
    def update_connection_status(self, online: bool):
        """Update connection status"""
        self.is_online = online
        self.update_status_indicator()
        self.update_status_text()
        
    def update_sync_progress(self, in_progress: bool, progress: int = 0):
        """Update sync progress"""
        self.sync_in_progress = in_progress
        
        if in_progress:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(progress)
            self.sync_button.setEnabled(False)
        else:
            self.progress_bar.setVisible(False)
            self.sync_button.setEnabled(True)
            
        self.update_status_text()
        
    def update_pending_count(self, count: int):
        """Update pending items count"""
        if count > 0:
            self.pending_label.setText(f"({count} pending)")
            self.pending_label.setVisible(True)
        else:
            self.pending_label.setVisible(False)
            
    def update_status_indicator(self):
        """Update visual status indicator"""
        if self.is_online:
            self.status_indicator.setStyleSheet("color: green;")
        else:
            self.status_indicator.setStyleSheet("color: red;")
            
    def update_status_text(self):
        """Update status text"""
        if self.sync_in_progress:
            self.status_label.setText("Syncing...")
        elif self.is_online:
            self.status_label.setText("Online")
        else:
            self.status_label.setText("Offline")
            
    def update_display(self):
        """Update display with current status"""
        # This would be connected to sync manager to get real status
        # For now, just update the display
        pass
        
    def set_sync_manager(self, sync_manager):
        """Connect to sync manager for real-time updates"""
        if sync_manager:
            sync_manager.connection_status_changed.connect(self.update_connection_status)
            sync_manager.sync_started.connect(lambda: self.update_sync_progress(True))
            sync_manager.sync_completed.connect(lambda s, e: self.update_sync_progress(False))
            self.manual_sync_requested.connect(sync_manager.force_sync)