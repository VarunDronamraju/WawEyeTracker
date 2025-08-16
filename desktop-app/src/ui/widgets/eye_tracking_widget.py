"""
Eye Tracking Widget - Camera feed display and tracking controls
Shows live camera feed with eye detection overlay
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFrame, QSlider, QCheckBox,
                            QGroupBox, QGridLayout, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, pyqtSlot
from PyQt6.QtGui import QPixmap, QFont, QPainter, QPen, QColor
import cv2
import numpy as np

class CameraFeedWidget(QLabel):
    """Widget for displaying camera feed with eye detection overlay"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(640, 480)
        self.setStyleSheet("border: 2px solid #ccc; background-color: #000;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("Camera feed will appear here")
        
        # Detection overlay data
        self.face_rectangles = []
        self.eye_rectangles = []
        self.blink_indicators = []
        
    def update_frame(self, frame: np.ndarray):
        """Update camera feed with new frame"""
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Create QPixmap from frame
            height, width, channel = rgb_frame.shape
            bytes_per_line = 3 * width
            
            # Create QImage
            from PyQt6.QtGui import QImage
            qimage = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Scale to fit widget while maintaining aspect ratio
            pixmap = QPixmap.fromImage(qimage)
            scaled_pixmap = pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"Error updating frame: {e}")
            
    def draw_detection_overlay(self, faces, eyes):
        """Draw detection rectangles on the frame"""
        self.face_rectangles = faces
        self.eye_rectangles = eyes
        self.update()  # Trigger paintEvent
        
    def paintEvent(self, event):
        """Custom paint event to draw detection overlay"""
        super().paintEvent(event)
        
        if not self.pixmap():
            return
            
        painter = QPainter(self)
        
        # Draw face rectangles
        painter.setPen(QPen(QColor(0, 255, 0), 2))  # Green for faces
        for rect in self.face_rectangles:
            painter.drawRect(*rect)
            
        # Draw eye rectangles
        painter.setPen(QPen(QColor(0, 0, 255), 2))  # Blue for eyes
        for rect in self.eye_rectangles:
            painter.drawRect(*rect)
            
        # Draw blink indicators
        painter.setPen(QPen(QColor(255, 0, 0), 3))  # Red for blinks
        for indicator in self.blink_indicators:
            painter.drawEllipse(*indicator)

class EyeTrackingWidget(QWidget):
    """Widget for eye tracking interface and controls"""
    
    # Signals
    tracking_requested = pyqtSignal(bool)  # start/stop tracking
    settings_changed = pyqtSignal(dict)  # tracking settings changed
    
    def __init__(self):
        super().__init__()
        
        # Tracking state
        self.is_tracking = False
        self.fps_counter = 0
        self.last_fps_time = 0
        
        # Performance metrics
        self.frame_count = 0
        self.detection_accuracy = 0.0
        
        self.init_ui()
        self.setup_timers()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Eye Tracking")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(header)
        
        # Main content layout
        content_layout = QHBoxLayout()
        
        # Camera feed (left side)
        self.create_camera_section(content_layout)
        
        # Controls (right side)
        self.create_controls_section(content_layout)
        
        layout.addLayout(content_layout)
        
        # Status bar
        self.create_status_section(layout)
        
    def create_camera_section(self, layout):
        """Create camera feed section"""
        camera_frame = QFrame()
        camera_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        camera_layout = QVBoxLayout(camera_frame)
        
        # Camera feed
        self.camera_feed = CameraFeedWidget()
        camera_layout.addWidget(self.camera_feed)
        
        # Camera controls
        camera_controls = QHBoxLayout()
        
        self.start_button = QPushButton("Start Tracking")
        self.start_button.clicked.connect(self.toggle_tracking)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        camera_controls.addWidget(self.start_button)
        
        self.calibrate_button = QPushButton("Calibrate")
        self.calibrate_button.clicked.connect(self.calibrate_tracking)
        camera_controls.addWidget(self.calibrate_button)
        
        camera_controls.addStretch()
        camera_layout.addLayout(camera_controls)
        
        layout.addWidget(camera_frame, 2)  # 2/3 of the space
        
    def create_controls_section(self, layout):
        """Create controls section"""
        controls_frame = QFrame()
        controls_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        controls_layout = QVBoxLayout(controls_frame)
        
        # Detection settings
        detection_group = QGroupBox("Detection Settings")
        detection_layout = QVBoxLayout(detection_group)
        
        # Sensitivity
        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(QLabel("Sensitivity:"))
        
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(10, 50)
        self.sensitivity_slider.setValue(25)
        self.sensitivity_slider.valueChanged.connect(self.on_sensitivity_changed)
        sensitivity_layout.addWidget(self.sensitivity_slider)
        
        self.sensitivity_label = QLabel("25")
        sensitivity_layout.addWidget(self.sensitivity_label)
        detection_layout.addLayout(sensitivity_layout)
        
        # Show detection overlay
        self.show_overlay_check = QCheckBox("Show detection overlay")
        self.show_overlay_check.setChecked(True)
        detection_layout.addWidget(self.show_overlay_check)
        
        # Show confidence scores
        self.show_confidence_check = QCheckBox("Show confidence scores")
        detection_layout.addWidget(self.show_confidence_check)
        
        controls_layout.addWidget(detection_group)
        
        # Performance metrics
        metrics_group = QGroupBox("Performance")
        metrics_layout = QGridLayout(metrics_group)
        
        # FPS
        metrics_layout.addWidget(QLabel("FPS:"), 0, 0)
        self.fps_label = QLabel("0")
        metrics_layout.addWidget(self.fps_label, 0, 1)
        
        # Detection rate
        metrics_layout.addWidget(QLabel("Detection Rate:"), 1, 0)
        self.detection_rate_label = QLabel("0%")
        metrics_layout.addWidget(self.detection_rate_label, 1, 1)
        
        # CPU usage
        metrics_layout.addWidget(QLabel("CPU Usage:"), 2, 0)
        self.cpu_usage_label = QLabel("0%")
        metrics_layout.addWidget(self.cpu_usage_label, 2, 1)
        
        # Memory usage
        metrics_layout.addWidget(QLabel("Memory:"), 3, 0)
        self.memory_label = QLabel("0 MB")
        metrics_layout.addWidget(self.memory_label, 3, 1)
        
        controls_layout.addWidget(metrics_group)
        
        # Statistics
        stats_group = QGroupBox("Session Statistics")
        stats_layout = QGridLayout(stats_group)
        
        # Total blinks
        stats_layout.addWidget(QLabel("Total Blinks:"), 0, 0)
        self.total_blinks_label = QLabel("0")
        stats_layout.addWidget(self.total_blinks_label, 0, 1)
        
        # Blink rate
        stats_layout.addWidget(QLabel("Blink Rate:"), 1, 0)
        self.blink_rate_label = QLabel("0/min")
        stats_layout.addWidget(self.blink_rate_label, 1, 1)
        
        # Session time
        stats_layout.addWidget(QLabel("Session Time:"), 2, 0)
        self.session_time_label = QLabel("00:00:00")
        stats_layout.addWidget(self.session_time_label, 2, 1)
        
        # Accuracy
        stats_layout.addWidget(QLabel("Accuracy:"), 3, 0)
        self.accuracy_label = QLabel("0%")
        stats_layout.addWidget(self.accuracy_label, 3, 1)
        
        controls_layout.addWidget(stats_group)
        
        controls_layout.addStretch()
        layout.addWidget(controls_frame, 1)  # 1/3 of the space
        
    def create_status_section(self, layout):
        """Create status section"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        status_layout = QHBoxLayout(status_frame)
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Arial", 12))
        self.update_status_indicator()
        status_layout.addWidget(self.status_indicator)
        
        # Status text
        self.status_label = QLabel("Ready to start tracking")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Progress bar for calibration
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(status_frame)
        
    def setup_timers(self):
        """Setup update timers"""
        # Performance update timer
        self.perf_timer = QTimer()
        self.perf_timer.timeout.connect(self.update_performance_metrics)
        self.perf_timer.start(1000)  # Update every second
        
    def toggle_tracking(self):
        """Toggle eye tracking on/off"""
        if self.is_tracking:
            self.stop_tracking()
        else:
            self.start_tracking()
            
    def start_tracking(self):
        """Start eye tracking"""
        self.is_tracking = True
        self.start_button.setText("Stop Tracking")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        
        self.status_label.setText("Tracking active")
        self.update_status_indicator()
        
        self.tracking_requested.emit(True)
        
    def stop_tracking(self):
        """Stop eye tracking"""
        self.is_tracking = False
        self.start_button.setText("Start Tracking")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        self.status_label.setText("Tracking stopped")
        self.update_status_indicator()
        
        # Clear camera feed
        self.camera_feed.clear()
        self.camera_feed.setText("Camera feed will appear here")
        
        self.tracking_requested.emit(False)
        
    def calibrate_tracking(self):
        """Calibrate eye tracking"""
        self.status_label.setText("Calibrating...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        
        # Simulate calibration process
        self.calibration_timer = QTimer()
        self.calibration_progress = 0
        
        def update_calibration():
            self.calibration_progress += 10
            self.progress_bar.setValue(self.calibration_progress)
            
            if self.calibration_progress >= 100:
                self.calibration_timer.stop()
                self.progress_bar.setVisible(False)
                self.status_label.setText("Calibration complete")
                
        self.calibration_timer.timeout.connect(update_calibration)
        self.calibration_timer.start(200)  # Update every 200ms
        
    def on_sensitivity_changed(self, value):
        """Handle sensitivity slider change"""
        self.sensitivity_label.setText(str(value))
        
        # Emit settings change
        settings = {
            'sensitivity': value / 100.0,
            'show_overlay': self.show_overlay_check.isChecked(),
            'show_confidence': self.show_confidence_check.isChecked()
        }
        self.settings_changed.emit(settings)
        
    def update_status_indicator(self):
        """Update status indicator color"""
        if self.is_tracking:
            self.status_indicator.setStyleSheet("color: green;")
        else:
            self.status_indicator.setStyleSheet("color: red;")
            
    def update_performance_metrics(self):
        """Update performance metrics display"""
        import psutil
        import time
        
        # Update FPS
        current_time = time.time()
        if hasattr(self, 'last_fps_time'):
            if current_time - self.last_fps_time >= 1.0:
                fps = self.fps_counter
                self.fps_label.setText(str(fps))
                self.fps_counter = 0
                self.last_fps_time = current_time
        else:
            self.last_fps_time = current_time
            
        # Update CPU usage
        try:
            cpu_percent = psutil.cpu_percent()
            self.cpu_usage_label.setText(f"{cpu_percent:.1f}%")
        except:
            self.cpu_usage_label.setText("N/A")
            
        # Update memory usage
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_label.setText(f"{memory_mb:.1f} MB")
        except:
            self.memory_label.setText("N/A")
            
    @pyqtSlot(np.ndarray)
    def update_camera_feed(self, frame):
        """Update camera feed with new frame"""
        self.camera_feed.update_frame(frame)
        self.fps_counter += 1
        
    def update_statistics(self, total_blinks, blink_rate, session_time, accuracy):
        """Update session statistics"""
        self.total_blinks_label.setText(str(total_blinks))
        self.blink_rate_label.setText(f"{blink_rate}/min")
        self.session_time_label.setText(session_time)
        self.accuracy_label.setText(f"{accuracy:.1f}%")