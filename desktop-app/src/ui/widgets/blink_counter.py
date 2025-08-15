from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLCDNumber, QProgressBar, QGroupBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from typing import List
import time
from collections import deque

from ...core.eye_tracker import BlinkEvent

class BlinkCounterWidget(QWidget):
    """Widget for displaying blink count and rate"""
    
    blink_rate_changed = pyqtSignal(float)  # blinks per minute
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.blink_events: deque = deque(maxlen=1000)  # Store last 1000 blinks
        self.setup_ui()
        
        # Timer for updating blink rate
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_blink_rate)
        self.update_timer.start(5000)  # Update every 5 seconds
    
    def setup_ui(self):
        """Setup the blink counter UI"""
        layout = QVBoxLayout(self)
        
        # Group box
        group = QGroupBox("Blink Counter")
        group_layout = QVBoxLayout(group)
        
        # Total blinks LCD display
        total_label = QLabel("Total Blinks:")
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        group_layout.addWidget(total_label)
        
        self.total_lcd = QLCDNumber(6)
        self.total_lcd.setDigitCount(6)
        self.total_lcd.display(0)
        self.total_lcd.setMinimumHeight(60)
        group_layout.addWidget(self.total_lcd)
        
        # Blinks per minute
        bpm_label = QLabel("Blinks per Minute:")
        bpm_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        group_layout.addWidget(bpm_label)
        
        self.bpm_lcd = QLCDNumber(4)
        self.bpm_lcd.setDigitCount(4)
        self.bpm_lcd.display(0.0)
        self.bpm_lcd.setMinimumHeight(50)
        group_layout.addWidget(self.bpm_lcd)
        
        # Health indicator
        health_label = QLabel("Eye Health Score:")
        health_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        group_layout.addWidget(health_label)
        
        self.health_progress = QProgressBar()
        self.health_progress.setRange(0, 100)
        self.health_progress.setValue(85)  # Default good health score
        self.health_progress.setMinimumHeight(25)
        group_layout.addWidget(self.health_progress)
        
        # Health status text
        self.health_status = QLabel("Good")
        self.health_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.health_status.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        group_layout.addWidget(self.health_status)
        
        layout.addWidget(group)
    
    def add_blink(self, blink_event: BlinkEvent):
        """Add a new blink event"""
        self.blink_events.append(blink_event)
        
        # Update total count
        self.total_lcd.display(len(self.blink_events))
        
        # Update blink rate immediately
        self.update_blink_rate()
    
    def update_blink_rate(self):
        """Update blinks per minute calculation"""
        if not self.blink_events:
            self.bpm_lcd.display(0.0)
            return
        
        current_time = time.time()
        
        # Count blinks in the last minute
        recent_blinks = [
            event for event in self.blink_events 
            if current_time - event.timestamp <= 60
        ]
        
        blinks_per_minute = len(recent_blinks)
        self.bpm_lcd.display(blinks_per_minute)
        
        # Update health score based on blink rate
        self.update_health_score(blinks_per_minute)
        
        # Emit signal
        self.blink_rate_changed.emit(blinks_per_minute)
    
    def update_health_score(self, blinks_per_minute: float):
        """Update eye health score based on blink rate"""
        # Normal blink rate is 15-20 per minute
        # Score calculation:
        # - Optimal range (15-20): 90-100%
        # - Good range (10-25): 70-89%
        # - Fair range (5-30): 50-69%
        # - Poor range (<5 or >30): <50%
        
        if 15 <= blinks_per_minute <= 20:
            score = 90 + ((20 - abs(blinks_per_minute - 17.5)) / 2.5) * 10
            status = "Excellent"
            color = "#4CAF50"  # Green
        elif 10 <= blinks_per_minute <= 25:
            if blinks_per_minute < 15:
                score = 70 + ((blinks_per_minute - 10) / 5) * 20
            else:
                score = 70 + ((25 - blinks_per_minute) / 5) * 20
            status = "Good"
            color = "#8BC34A"  # Light green
        elif 5 <= blinks_per_minute <= 30:
            if blinks_per_minute < 10:
                score = 50 + ((blinks_per_minute - 5) / 5) * 20
            else:
                score = 50 + ((30 - blinks_per_minute) / 5) * 20
            status = "Fair"
            color = "#FFC107"  # Amber
        else:
            score = max(10, 50 - abs(blinks_per_minute - 17.5) * 2)
            status = "Poor"
            color = "#F44336"  # Red
        
        score = int(min(100, max(0, score)))
        
        self.health_progress.setValue(score)
        self.health_status.setText(status)
        
        # Update progress bar color
        self.health_progress.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 2px;
            }}
        """)
    
    def reset(self):
        """Reset blink counter"""
        self.blink_events.clear()
        self.total_lcd.display(0)
        self.bpm_lcd.display(0.0)
        self.health_progress.setValue(85)
        self.health_status.setText("Good")
    
    def get_total_blinks(self) -> int:
        """Get total blink count"""
        return len(self.blink_events)
    
    def get_current_bpm(self) -> float:
        """Get current blinks per minute"""
        if not self.blink_events:
            return 0.0
        
        current_time = time.time()
        recent_blinks = [
            event for event in self.blink_events 
            if current_time - event.timestamp <= 60
        ]
        return len(recent_blinks)