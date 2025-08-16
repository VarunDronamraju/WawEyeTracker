"""
Blink Counter Widget - Real-time blink count display
Shows current session blinks with visual feedback
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLCDNumber, QFrame
from PyQt6.QtCore import pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QPalette

class BlinkCounterWidget(QWidget):
    """Widget for displaying real-time blink count"""
    
    # Signals
    blink_threshold_reached = pyqtSignal(int)  # Emit when certain thresholds reached
    
    def __init__(self):
        super().__init__()
        self.current_count = 0
        self.session_start_count = 0
        
        self.init_ui()
        self.setup_animations()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create frame for styling
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel)
        frame.setLineWidth(2)
        layout.addWidget(frame)
        
        frame_layout = QVBoxLayout(frame)
        
        # Title
        title = QLabel("Real-time Blinks")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        frame_layout.addWidget(title)
        
        # LCD Display for blink count
        self.lcd_display = QLCDNumber(4)  # 4 digits
        self.lcd_display.setDigitCount(4)
        self.lcd_display.setSegmentStyle(QLCDNumber.SegmentStyle.Filled)
        self.lcd_display.display(0)
        
        # Set LCD styling
        self.lcd_display.setStyleSheet("""
            QLCDNumber {
                background-color: #000000;
                color: #00FF00;
                border: 2px solid #333333;
                border-radius: 8px;
            }
        """)
        
        frame_layout.addWidget(self.lcd_display)
        
        # Statistics labels
        self.rate_label = QLabel("Rate: 0 blinks/min")
        self.rate_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(self.rate_label)
        
        self.session_label = QLabel("Session: 0 blinks")
        self.session_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(self.session_label)
        
        # Health indicator
        self.health_indicator = QLabel("●")
        self.health_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.health_indicator.setFont(QFont("Arial", 24))
        self.update_health_indicator()
        frame_layout.addWidget(self.health_indicator)
        
    def setup_animations(self):
        """Setup animations for visual feedback"""
        # Blink flash animation
        self.flash_animation = QPropertyAnimation(self.lcd_display, b"geometry")
        self.flash_animation.setDuration(200)
        self.flash_animation.setEasingCurve(QEasingCurve.Type.OutBounce)
        
    def update_count(self, new_count: int):
        """Update the blink count display"""
        if new_count > self.current_count:
            # New blink detected
            self.current_count = new_count
            self.lcd_display.display(self.current_count)
            
            # Update session count
            session_blinks = self.current_count - self.session_start_count
            self.session_label.setText(f"Session: {session_blinks} blinks")
            
            # Calculate and update rate (simplified)
            # In a real implementation, you'd track time properly
            self.update_blink_rate()
            
            # Update health indicator
            self.update_health_indicator()
            
            # Play flash animation
            self.play_blink_animation()
            
            # Check thresholds
            self.check_thresholds(session_blinks)
            
    def update_blink_rate(self):
        """Update blink rate calculation"""
        # Simplified rate calculation
        # In production, use proper time tracking
        import time
        current_time = time.time()
        
        if not hasattr(self, 'last_update_time'):
            self.last_update_time = current_time
            self.rate_window_blinks = []
            
        # Add current blink to rate window
        self.rate_window_blinks.append(current_time)
        
        # Keep only blinks from last minute
        minute_ago = current_time - 60
        self.rate_window_blinks = [t for t in self.rate_window_blinks if t > minute_ago]
        
        # Calculate rate
        rate = len(self.rate_window_blinks)
        self.rate_label.setText(f"Rate: {rate} blinks/min")
        
        self.last_update_time = current_time
        
    def update_health_indicator(self):
        """Update health status indicator based on blink rate"""
        if not hasattr(self, 'rate_window_blinks'):
            return
            
        current_rate = len(getattr(self, 'rate_window_blinks', []))
        
        # Health thresholds (blinks per minute)
        if current_rate < 5:  # Too low
            self.health_indicator.setText("●")
            self.health_indicator.setStyleSheet("color: red; font-size: 24px;")
        elif current_rate > 25:  # Too high
            self.health_indicator.setText("●")
            self.health_indicator.setStyleSheet("color: orange; font-size: 24px;")
        else:  # Normal range
            self.health_indicator.setText("●")
            self.health_indicator.setStyleSheet("color: green; font-size: 24px;")
            
    def play_blink_animation(self):
        """Play visual animation when blink is detected"""
        if self.flash_animation.state() == QPropertyAnimation.State.Running:
            return
            
        # Get current geometry
        current_rect = self.lcd_display.geometry()
        
        # Create slightly larger rect for flash effect
        flash_rect = QRect(
            current_rect.x() - 2,
            current_rect.y() - 2,
            current_rect.width() + 4,
            current_rect.height() + 4
        )
        
        # Setup animation
        self.flash_animation.setStartValue(current_rect)
        self.flash_animation.setEndValue(flash_rect)
        self.flash_animation.finished.connect(lambda: self.lcd_display.setGeometry(current_rect))
        
        # Start animation
        self.flash_animation.start()
        
    def check_thresholds(self, session_blinks: int):
        """Check if blink count has reached certain thresholds"""
        thresholds = [10, 25, 50, 100, 250, 500, 1000]
        
        for threshold in thresholds:
            if (session_blinks >= threshold and 
                session_blinks - 1 < threshold):  # Just crossed threshold
                self.blink_threshold_reached.emit(threshold)
                break
                
    def reset_session(self):
        """Reset session counters"""
        self.session_start_count = self.current_count
        self.session_label.setText("Session: 0 blinks")
        
        # Reset rate tracking
        if hasattr(self, 'rate_window_blinks'):
            self.rate_window_blinks.clear()
            
    def get_session_blinks(self) -> int:
        """Get current session blink count"""
        return max(0, self.current_count - self.session_start_count)