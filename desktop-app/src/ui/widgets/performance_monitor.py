from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QProgressBar, QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import psutil
import time

from ...core.eye_tracker import TrackingStats

class PerformanceMonitorWidget(QWidget):
    """Widget for monitoring application performance"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.last_update = time.time()
    
    def setup_ui(self):
        """Setup performance monitor UI"""
        layout = QVBoxLayout(self)
        
        # Group box
        group = QGroupBox("Performance Monitor")
        group_layout = QGridLayout(group)
        
        # FPS display
        group_layout.addWidget(QLabel("FPS:"), 0, 0)
        self.fps_label = QLabel("0.0")
        self.fps_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group_layout.addWidget(self.fps_label, 0, 1)
        
        # Latency display
        group_layout.addWidget(QLabel("Latency:"), 1, 0)
        self.latency_label = QLabel("0.0 ms")
        self.latency_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group_layout.addWidget(self.latency_label, 1, 1)
        
        # CPU usage
        group_layout.addWidget(QLabel("CPU Usage:"), 2, 0)
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_progress.setMinimumHeight(20)
        group_layout.addWidget(self.cpu_progress, 2, 1)
        
        # Memory usage
        group_layout.addWidget(QLabel("Memory:"), 3, 0)
        self.memory_label = QLabel("0 MB")
        self.memory_label.setFont(QFont("Arial", 9))
        group_layout.addWidget(self.memory_label, 3, 1)
        
        # Frames processed
        group_layout.addWidget(QLabel("Frames:"), 4, 0)
        self.frames_label = QLabel("0")
        self.frames_label.setFont(QFont("Arial", 9))
        group_layout.addWidget(self.frames_label, 4, 1)
        
        layout.addWidget(group)
    
    def update_stats(self, stats: TrackingStats):
        """Update performance statistics"""
        # Update FPS
        self.fps_label.setText(f"{stats.average_fps:.1f}")
        
        # Update latency
        self.latency_label.setText(f"{stats.average_latency:.1f} ms")
        
        # Update latency color based on performance
        if stats.average_latency < 50:
            self.latency_label.setStyleSheet("color: #4CAF50;")  # Green
        elif stats.average_latency < 100:
            self.latency_label.setStyleSheet("color: #FFC107;")  # Amber
        else:
            self.latency_label.setStyleSheet("color: #F44336;")  # Red
        
        # Update frames processed
        self.frames_label.setText(str(stats.frames_processed))
        
        # Update system metrics (throttled to once per second)
        current_time = time.time()
        if current_time - self.last_update >= 1.0:
            self.update_system_stats()
            self.last_update = current_time
    
    def update_system_stats(self):
        """Update system-level statistics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)
            self.cpu_progress.setValue(int(cpu_percent))
            
            # Update CPU progress bar color
            if cpu_percent < 50:
                color = "#4CAF50"  # Green
            elif cpu_percent < 80:
                color = "#FFC107"  # Amber
            else:
                color = "#F44336"  # Red
            
            self.cpu_progress.setStyleSheet(f"""
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 2px;
                }}
            """)
            
            # Memory usage
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_label.setText(f"{memory_mb:.1f} MB")
            
            # Color code memory usage
            if memory_mb < 100:
                self.memory_label.setStyleSheet("color: #4CAF50;")  # Green
            elif memory_mb < 200:
                self.memory_label.setStyleSheet("color: #FFC107;")  # Amber
            else:
                self.memory_label.setStyleSheet("color: #F44336;")  # Red
                
        except Exception as e:
            print(f"Error updating system stats: {e}")