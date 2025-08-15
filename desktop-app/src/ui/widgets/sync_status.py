from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QProgressBar, QGroupBox, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
import time
from typing import Dict, Any

class SyncStatusWidget(QWidget):
    """Widget for displaying sync status and controls"""
    
    sync_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_sync_time = 0
        self.sync_stats = {
            'connectivity_status': 'offline',
            'pending_blinks': 0,
            'pending_sessions': 0,
            'is_syncing': False
        }
        self.setup_ui()
        
        # Timer for updating display
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    def setup_ui(self):
        """Setup sync status UI"""
        layout = QVBoxLayout(self)
        
        # Group box
        group = QGroupBox("Sync Status")
        group_layout = QVBoxLayout(group)
        
        # Connection status
        conn_layout = QHBoxLayout()
        conn_layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Offline")
        self.status_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.status_indicator = QFrame()
        self.status_indicator.setFixedSize(12, 12)
        self.status_indicator.setStyleSheet("background-color: #F44336; border-radius: 6px;")
        
        conn_layout.addWidget(self.status_label)
        conn_layout.addWidget(self.status_indicator)
        conn_layout.addStretch()
        group_layout.addLayout(conn_layout)
        
        # Last sync time
        sync_layout = QHBoxLayout()
        sync_layout.addWidget(QLabel("Last Sync:"))
        self.last_sync_label = QLabel("Never")
        self.last_sync_label.setFont(QFont("Arial", 9))
        sync_layout.addWidget(self.last_sync_label)
        sync_layout.addStretch()
        group_layout.addLayout(sync_layout)
        
        # Pending data
        pending_layout = QHBoxLayout()
        pending_layout.addWidget(QLabel("Pending:"))
        self.pending_label = QLabel("0 records")
        self.pending_label.setFont(QFont("Arial", 9))
        pending_layout.addWidget(self.pending_label)
        pending_layout.addStretch()
        group_layout.addLayout(pending_layout)
        
        # Sync progress bar
        self.sync_progress = QProgressBar()
        self.sync_progress.setVisible(False)
        self.sync_progress.setMinimumHeight(20)
        group_layout.addWidget(self.sync_progress)
        
        # Sync button
        self.sync_button = QPushButton("Sync Now")
        self.sync_button.clicked.connect(self.request_sync)
        self.sync_button.setMinimumHeight(30)
        group_layout.addWidget(self.sync_button)
        
        layout.addWidget(group)
    
    def update_sync_stats(self, stats: Dict[str, Any]):
        """Update sync statistics"""
        self.sync_stats.update(stats)
        self.update_display()
    
    def update_display(self):
        """Update display with current sync status"""
        # Update connection status
        status = self.sync_stats.get('connectivity_status', 'offline')
        if status == 'online':
            self.status_label.setText("Online")
            self.status_indicator.setStyleSheet("background-color: #4CAF50; border-radius: 6px;")
        elif status == 'degraded':
            self.status_label.setText("Degraded")
            self.status_indicator.setStyleSheet("background-color: #FFC107; border-radius: 6px;")
        else:
            self.status_label.setText("Offline")
            self.status_indicator.setStyleSheet("background-color: #F44336; border-radius: 6px;")
        
        # Update last sync time
        if self.last_sync_time > 0:
            elapsed = time.time() - self.last_sync_time
            if elapsed < 60:
                self.last_sync_label.setText(f"{int(elapsed)}s ago")
            elif elapsed < 3600:
                self.last_sync_label.setText(f"{int(elapsed/60)}m ago")
            else:
                self.last_sync_label.setText(f"{int(elapsed/3600)}h ago")
        else:
            self.last_sync_label.setText("Never")
        
        # Update pending data
        pending_blinks = self.sync_stats.get('pending_blinks', 0)
        pending_sessions = self.sync_stats.get('pending_sessions', 0)
        total_pending = pending_blinks + pending_sessions
        
        if total_pending == 0:
            self.pending_label.setText("All synced")
            self.pending_label.setStyleSheet("color: #4CAF50;")
        else:
            self.pending_label.setText(f"{total_pending} records")
            self.pending_label.setStyleSheet("color: #FFC107;")
        
        # Update sync button and progress
        is_syncing = self.sync_stats.get('is_syncing', False)
        if is_syncing:
            self.sync_button.setText("Syncing...")
            self.sync_button.setEnabled(False)
            self.sync_progress.setVisible(True)
            self.sync_progress.setRange(0, 0)  # Indeterminate progress
        else:
            self.sync_button.setText("Sync Now")
            self.sync_button.setEnabled(status == 'online')
            self.sync_progress.setVisible(False)
    
    def request_sync(self):
        """Request manual sync"""
        self.sync_requested.emit()
    
    def set_last_sync_time(self, timestamp: float):
        """Set last sync timestamp"""
        self.last_sync_time = timestamp
        self.update_display()
    
    def show_sync_progress(self, current: int, total: int):
        """Show sync progress"""
        if total > 0:
            self.sync_progress.setRange(0, total)
            self.sync_progress.setValue(current)
            self.sync_progress.setVisible(True)