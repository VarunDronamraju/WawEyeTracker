import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QGroupBox, QGridLayout,
                            QLCDNumber, QProgressBar, QSystemTrayIcon, 
                            QMenu, QApplication, QSplitter, QFrame,
                            QStatusBar, QMenuBar, QDialog)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
import time
from datetime import datetime, timedelta
from typing import Optional

from ..core.eye_tracker import EyeTrackingEngine, BlinkEvent, TrackingStats
from .widgets.blink_counter import BlinkCounterWidget
from .widgets.performance_monitor import PerformanceMonitorWidget
from .widgets.sync_status import SyncStatusWidget
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.gdpr_consent import GDPRConsentDialog

class MainWindow(QMainWindow):
    """Main application window with eye tracking interface"""
    
    # Signals
    blink_detected = pyqtSignal(BlinkEvent)
    stats_updated = pyqtSignal(TrackingStats)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wellness at Work - Eye Tracker")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize components
        self.eye_tracker = EyeTrackingEngine()
        self.is_tracking = False
        self.session_start_time = None
        
        # Setup UI
        self.setup_ui()
        self.setup_system_tray()
        self.setup_connections()
        self.apply_theme()
        
        # Initialize timers
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second
        
        # Check GDPR consent
        self.check_gdpr_consent()
    
    def setup_ui(self):
        """Setup the main user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Controls and Status
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Live Data and Charts
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter sizes (30% left, 70% right)
        splitter.setSizes([360, 840])
        
        # Setup menu bar
        self.setup_menu_bar()
        
        # Setup status bar
        self.setup_status_bar()
    
    def create_left_panel(self) -> QWidget:
        """Create left control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("Eye Tracking Control")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Tracking controls
        controls_group = QGroupBox("Tracking Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        self.start_button = QPushButton("Start Tracking")
        self.start_button.setMinimumHeight(40)
        self.start_button.clicked.connect(self.toggle_tracking)
        controls_layout.addWidget(self.start_button)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.pause_tracking)
        controls_layout.addWidget(self.pause_button)
        
        layout.addWidget(controls_group)
        
        # Blink counter widget
        self.blink_counter = BlinkCounterWidget()
        layout.addWidget(self.blink_counter)
        
        # Performance monitor
        self.performance_monitor = PerformanceMonitorWidget()
        layout.addWidget(self.performance_monitor)
        
        # Sync status
        self.sync_status = SyncStatusWidget()
        layout.addWidget(self.sync_status)
        
        # Settings button
        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self.show_settings)
        layout.addWidget(settings_button)
        
        layout.addStretch()
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create right data visualization panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("Live Data Visualization")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Real-time blink chart
        self.setup_blink_chart()
        layout.addWidget(self.chart_view)
        
        # Statistics grid
        stats_group = QGroupBox("Session Statistics")
        stats_layout = QGridLayout(stats_group)
        
        # Session time
        stats_layout.addWidget(QLabel("Session Time:"), 0, 0)
        self.session_time_label = QLabel("00:00:00")
        self.session_time_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        stats_layout.addWidget(self.session_time_label, 0, 1)
        
        # Total blinks
        stats_layout.addWidget(QLabel("Total Blinks:"), 1, 0)
        self.total_blinks_label = QLabel("0")
        self.total_blinks_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        stats_layout.addWidget(self.total_blinks_label, 1, 1)
        
        # Blinks per minute
        stats_layout.addWidget(QLabel("Blinks/Min:"), 2, 0)
        self.bpm_label = QLabel("0.0")
        self.bpm_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        stats_layout.addWidget(self.bpm_label, 2, 1)
        
        # Average latency
        stats_layout.addWidget(QLabel("Avg Latency:"), 3, 0)
        self.latency_label = QLabel("0.0 ms")
        self.latency_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        stats_layout.addWidget(self.latency_label, 3, 1)
        
        layout.addWidget(stats_group)
        
        return panel
    
    def setup_blink_chart(self):
        """Setup real-time blink chart"""
        # Create chart
        self.chart = QChart()
        self.chart.setTitle("Blinks Per Minute (Real-time)")
        
        # Create line series
        self.blink_series = QLineSeries()
        self.blink_series.setName("Blinks/Min")
        
        # Add series to chart
        self.chart.addSeries(self.blink_series)
        
        # Setup axes
        self.chart.createDefaultAxes()
        
        # X-axis (time)
        axis_x = QValueAxis()
        axis_x.setTitleText("Time (minutes)")
        axis_x.setRange(0, 10)
        self.chart.setAxisX(axis_x, self.blink_series)
        
        # Y-axis (blinks per minute)
        axis_y = QValueAxis()
        axis_y.setTitleText("Blinks per Minute")
        axis_y.setRange(0, 30)
        self.chart.setAxisY(axis_y, self.blink_series)
        
        # Create chart view
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(self.chart_view.renderHints())
        
        # Initialize data storage
        self.blink_data_points = []
        self.chart_start_time = None
    
    def setup_menu_bar(self):
        """Setup application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        export_action = QAction('Export Data', self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings menu
        settings_menu = menubar.addMenu('Settings')
        
        preferences_action = QAction('Preferences', self)
        preferences_action.triggered.connect(self.show_settings)
        settings_menu.addAction(preferences_action)
        
        gdpr_action = QAction('Privacy Settings', self)
        gdpr_action.triggered.connect(self.show_gdpr_settings)
        settings_menu.addAction(gdpr_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status labels
        self.tracking_status = QLabel("Ready")
        self.fps_status = QLabel("FPS: 0")
        self.connection_status = QLabel("Offline")
        
        self.status_bar.addWidget(self.tracking_status)
        self.status_bar.addPermanentWidget(self.fps_status)
        self.status_bar.addPermanentWidget(self.connection_status)
    
    def setup_system_tray(self):
        """Setup system tray icon"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            
            # Create tray icon (you'll need to add an icon file)
            # self.tray_icon.setIcon(QIcon("assets/icon.png"))
            
            # Create tray menu
            tray_menu = QMenu()
            
            show_action = tray_menu.addAction("Show")
            show_action.triggered.connect(self.show)
            
            start_action = tray_menu.addAction("Start Tracking")
            start_action.triggered.connect(self.start_tracking)
            
            tray_menu.addSeparator()
            
            quit_action = tray_menu.addAction("Quit")
            quit_action.triggered.connect(QApplication.instance().quit)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            
            # Connect tray icon activation
            self.tray_icon.activated.connect(self.tray_icon_activated)
    
    def setup_connections(self):
        """Setup signal connections"""
        # Eye tracker callbacks
        self.eye_tracker.set_blink_callback(self.on_blink_detected)
        self.eye_tracker.set_stats_callback(self.on_stats_updated)
    
    def apply_theme(self):
        """Apply dark/light theme styling"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin: 5px 0px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
            QLabel {
                color: #ffffff;
            }
            QLCDNumber {
                background-color: #1e1e1e;
                color: #00ff00;
                border: 1px solid #555555;
            }
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)
    
    def check_gdpr_consent(self):
        """Check if GDPR consent has been given"""
        # TODO: Check settings for consent status
        # For now, show consent dialog on first run
        consent_dialog = GDPRConsentDialog(self)
        if consent_dialog.exec() != QDialog.DialogCode.Accepted:
            self.close()
    
    @pyqtSlot()
    def toggle_tracking(self):
        """Toggle eye tracking on/off"""
        if not self.is_tracking:
            self.start_tracking()
        else:
            self.stop_tracking()
    
    def start_tracking(self):
        """Start eye tracking"""
        if self.eye_tracker.start_tracking():
            self.is_tracking = True
            self.session_start_time = time.time()
            self.chart_start_time = time.time()
            
            # Update UI
            self.start_button.setText("Stop Tracking")
            self.start_button.setStyleSheet("background-color: #f44336;")
            self.pause_button.setEnabled(True)
            self.tracking_status.setText("Tracking Active")
            
            # Reset counters
            self.blink_counter.reset()
            self.blink_data_points.clear()
            self.blink_series.clear()
        else:
            self.tracking_status.setText("Failed to start camera")
    
    def stop_tracking(self):
        """Stop eye tracking"""
        self.eye_tracker.stop_tracking()
        self.is_tracking = False
        self.session_start_time = None
        
        # Update UI
        self.start_button.setText("Start Tracking")
        self.start_button.setStyleSheet("background-color: #4CAF50;")
        self.pause_button.setEnabled(False)
        self.tracking_status.setText("Ready")
    
    def pause_tracking(self):
        """Pause/resume tracking"""
        if self.eye_tracker.is_paused:
            self.eye_tracker.resume_tracking()
            self.pause_button.setText("Pause")
            self.tracking_status.setText("Tracking Active")
        else:
            self.eye_tracker.pause_tracking()
            self.pause_button.setText("Resume")
            self.tracking_status.setText("Paused")
    
    def on_blink_detected(self, blink_event: BlinkEvent):
        """Handle blink detection event"""
        self.blink_detected.emit(blink_event)
        self.blink_counter.add_blink(blink_event)
        
        # Add to chart data
        if self.chart_start_time:
            minutes_elapsed = (blink_event.timestamp - self.chart_start_time) / 60.0
            self.blink_data_points.append((minutes_elapsed, blink_event))
            self.update_chart()
    
    def on_stats_updated(self, stats: TrackingStats):
        """Handle stats update"""
        self.stats_updated.emit(stats)
        self.performance_monitor.update_stats(stats)
        
        # Update status bar
        self.fps_status.setText(f"FPS: {stats.average_fps:.1f}")
    
    def update_display(self):
        """Update display elements (called every second)"""
        if self.is_tracking and self.session_start_time:
            # Update session time
            elapsed = time.time() - self.session_start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.session_time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Update statistics
            stats = self.eye_tracker.get_stats()
            self.total_blinks_label.setText(str(stats.blinks_detected))
            
            # Calculate blinks per minute
            if elapsed > 0:
                bpm = (stats.blinks_detected / elapsed) * 60
                self.bpm_label.setText(f"{bpm:.1f}")
            
            self.latency_label.setText(f"{stats.average_latency:.1f} ms")
    
    def update_chart(self):
        """Update the real-time blink chart"""
        if not self.blink_data_points:
            return
        
        # Calculate blinks per minute for chart
        current_time = time.time()
        if not self.chart_start_time:
            return
        
        # Group data into 1-minute intervals
        minute_data = {}
        for time_point, blink_event in self.blink_data_points:
            minute = int(time_point)
            if minute not in minute_data:
                minute_data[minute] = 0
            minute_data[minute] += 1
        
        # Update chart series
        self.blink_series.clear()
        for minute in sorted(minute_data.keys()):
            self.blink_series.append(minute, minute_data[minute])
        
        # Update x-axis range
        if minute_data:
            max_minute = max(minute_data.keys())
            axis_x = self.chart.axes(Qt.Orientation.Horizontal)[0]
            axis_x.setRange(max(0, max_minute - 10), max_minute + 1)
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self)
        dialog.exec()
    
    def show_gdpr_settings(self):
        """Show GDPR settings dialog"""
        dialog = GDPRConsentDialog(self)
        dialog.exec()
    
    def show_about(self):
        """Show about dialog"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(self, "About", 
                         "Wellness at Work Eye Tracker v1.0\n\n"
                         "A privacy-focused eye tracking application for workplace wellness.")
    
    def export_data(self):
        """Export tracking data"""
        # TODO: Implement data export functionality
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Export", "Data export functionality coming soon!")
    
    def tray_icon_activated(self, reason):
        """Handle system tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def closeEvent(self, event):
        """Handle window close event"""
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            if self.is_tracking:
                self.stop_tracking()
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())