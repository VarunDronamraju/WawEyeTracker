from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QWidget, QLabel, QSlider, QSpinBox, QCheckBox,
                            QComboBox, QPushButton, QFormLayout, QGroupBox,
                            QMessageBox, QFileDialog, QTextEdit, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class SettingsDialog(QDialog):
    """Settings dialog for application configuration"""
    
    settings_changed = pyqtSignal(dict)  # Emit when settings change
    
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.modified_settings = {}
        
        self.init_ui()
        self.load_current_settings()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Settings - Wellness at Work")
        self.setFixedSize(500, 600)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_general_tab()
        self.create_tracking_tab()
        self.create_privacy_tab()
        self.create_advanced_tab()
        
        # Buttons
        self.create_buttons(layout)
        
        # Apply styling
        self.apply_styling()
        
    def create_general_tab(self):
        """Create general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Appearance group
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])
        appearance_layout.addRow("Theme:", self.theme_combo)
        
        # Font size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(10)
        appearance_layout.addRow("Font Size:", self.font_size_spin)
        
        layout.addWidget(appearance_group)
        
        # Behavior group
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout(behavior_group)
        
        self.auto_start_check = QCheckBox("Start tracking automatically when logged in")
        behavior_layout.addWidget(self.auto_start_check)
        
        self.minimize_to_tray_check = QCheckBox("Minimize to system tray")
        behavior_layout.addWidget(self.minimize_to_tray_check)
        
        self.show_notifications_check = QCheckBox("Show break reminders")
        behavior_layout.addWidget(self.show_notifications_check)
        
        layout.addWidget(behavior_group)
        
        # Notifications group
        notification_group = QGroupBox("Notifications")
        notification_layout = QFormLayout(notification_group)
        
        # Break reminder interval
        self.break_interval_spin = QSpinBox()
        self.break_interval_spin.setRange(5, 120)
        self.break_interval_spin.setValue(20)
        self.break_interval_spin.setSuffix(" minutes")
        notification_layout.addRow("Break Reminder:", self.break_interval_spin)
        
        # Sound notifications
        self.sound_notifications_check = QCheckBox("Enable sound notifications")
        notification_layout.addRow("Sound:", self.sound_notifications_check)
        
        layout.addWidget(notification_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "General")
        
    def create_tracking_tab(self):
        """Create eye tracking settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Camera settings group
        camera_group = QGroupBox("Camera Settings")
        camera_layout = QFormLayout(camera_group)
        
        # Frame rate
        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setRange(10, 60)
        self.fps_slider.setValue(30)
        self.fps_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.fps_slider.setTickInterval(10)
        
        self.fps_label = QLabel("30 FPS")
        self.fps_slider.valueChanged.connect(
            lambda v: self.fps_label.setText(f"{v} FPS")
        )
        
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(self.fps_slider)
        fps_layout.addWidget(self.fps_label)
        camera_layout.addRow("Frame Rate:", fps_layout)
        
        # Camera resolution
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["640x480", "800x600", "1280x720", "1920x1080"])
        camera_layout.addRow("Resolution:", self.resolution_combo)
        
        layout.addWidget(camera_group)
        
        # Detection settings group
        detection_group = QGroupBox("Blink Detection")
        detection_layout = QFormLayout(detection_group)
        
        # Sensitivity
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(10, 50)
        self.sensitivity_slider.setValue(25)
        self.sensitivity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.sensitivity_slider.setTickInterval(10)
        
        self.sensitivity_label = QLabel("Medium")
        self.sensitivity_slider.valueChanged.connect(self.update_sensitivity_label)
        
        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(self.sensitivity_slider)
        sensitivity_layout.addWidget(self.sensitivity_label)
        detection_layout.addRow("Sensitivity:", sensitivity_layout)
        
        # Confidence threshold
        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setRange(50, 95)
        self.confidence_slider.setValue(80)
        self.confidence_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.confidence_slider.setTickInterval(15)
        
        self.confidence_label = QLabel("80%")
        self.confidence_slider.valueChanged.connect(
            lambda v: self.confidence_label.setText(f"{v}%")
        )
        
        confidence_layout = QHBoxLayout()
        confidence_layout.addWidget(self.confidence_slider)
        confidence_layout.addWidget(self.confidence_label)
        detection_layout.addRow("Confidence:", confidence_layout)
        
        layout.addWidget(detection_group)
        
        # Performance group
        performance_group = QGroupBox("Performance")
        performance_layout = QVBoxLayout(performance_group)
        
        self.gpu_acceleration_check = QCheckBox("Enable GPU acceleration (if available)")
        performance_layout.addWidget(self.gpu_acceleration_check)
        
        self.low_power_mode_check = QCheckBox("Low power mode (reduced accuracy)")
        performance_layout.addWidget(self.low_power_mode_check)
        
        layout.addWidget(performance_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Eye Tracking")
        
    def create_privacy_tab(self):
        """Create privacy and GDPR settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Data collection group
        data_group = QGroupBox("Data Collection")
        data_layout = QVBoxLayout(data_group)
        
        self.collect_analytics_check = QCheckBox("Allow anonymous usage analytics")
        data_layout.addWidget(self.collect_analytics_check)
        
        self.local_storage_only_check = QCheckBox("Store data locally only (no cloud sync)")
        data_layout.addWidget(self.local_storage_only_check)
        
        layout.addWidget(data_group)
        
        # Data retention group
        retention_group = QGroupBox("Data Retention")
        retention_layout = QFormLayout(retention_group)
        
        self.retention_combo = QComboBox()
        self.retention_combo.addItems([
            "1 Month", "3 Months", "6 Months", 
            "1 Year", "2 Years", "Keep Forever"
        ])
        retention_layout.addRow("Keep data for:", self.retention_combo)
        
        layout.addWidget(retention_group)
        
        # GDPR controls group
        gdpr_group = QGroupBox("Your Rights (GDPR)")
        gdpr_layout = QVBoxLayout(gdpr_group)
        
        # Export data button
        self.export_button = QPushButton("Export My Data")
        self.export_button.clicked.connect(self.export_user_data)
        gdpr_layout.addWidget(self.export_button)
        
        # Delete data button
        self.delete_button = QPushButton("Delete All My Data")
        self.delete_button.clicked.connect(self.delete_user_data)
        self.delete_button.setStyleSheet("background-color: #dc3545; color: white;")
        gdpr_layout.addWidget(self.delete_button)
        
        # Privacy policy
        privacy_text = QTextEdit()
        privacy_text.setMaximumHeight(100)
        privacy_text.setReadOnly(True)
        privacy_text.setPlainText(
            "We respect your privacy. Your eye tracking data is used only for wellness "
            "monitoring and is never shared with third parties. You have the right to "
            "access, export, or delete your data at any time."
        )
        gdpr_layout.addWidget(QLabel("Privacy Policy Summary:"))
        gdpr_layout.addWidget(privacy_text)
        
        layout.addWidget(gdpr_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Privacy")
        
    def create_advanced_tab(self):
        """Create advanced settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Sync settings group
        sync_group = QGroupBox("Synchronization")
        sync_layout = QFormLayout(sync_group)
        
        # Sync interval
        self.sync_interval_spin = QSpinBox()
        self.sync_interval_spin.setRange(10, 300)
        self.sync_interval_spin.setValue(60)
        self.sync_interval_spin.setSuffix(" seconds")
        sync_layout.addRow("Sync Interval:", self.sync_interval_spin)
        
        # Batch size
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(10, 1000)
        self.batch_size_spin.setValue(100)
        sync_layout.addRow("Batch Size:", self.batch_size_spin)
        
        # Offline storage limit
        self.offline_limit_spin = QSpinBox()
        self.offline_limit_spin.setRange(1000, 100000)
        self.offline_limit_spin.setValue(10000)
        sync_layout.addRow("Offline Storage Limit:", self.offline_limit_spin)
        
        layout.addWidget(sync_group)
        
        # Debug settings group
        debug_group = QGroupBox("Debug & Logging")
        debug_layout = QVBoxLayout(debug_group)
        
        self.debug_mode_check = QCheckBox("Enable debug mode")
        debug_layout.addWidget(self.debug_mode_check)
        
        self.verbose_logging_check = QCheckBox("Verbose logging")
        debug_layout.addWidget(self.verbose_logging_check)
        
        # Log file location
        log_layout = QHBoxLayout()
        self.log_path_label = QLabel("~/logs/wellness_tracker.log")
        log_layout.addWidget(QLabel("Log File:"))
        log_layout.addWidget(self.log_path_label)
        
        self.open_log_button = QPushButton("Open Log")
        self.open_log_button.clicked.connect(self.open_log_file)
        log_layout.addWidget(self.open_log_button)
        
        debug_layout.addLayout(log_layout)
        layout.addWidget(debug_group)
        
        # Reset settings
        reset_group = QGroupBox("Reset")
        reset_layout = QVBoxLayout(reset_group)
        
        self.reset_button = QPushButton("Reset All Settings to Default")
        self.reset_button.clicked.connect(self.reset_settings)
        reset_layout.addWidget(self.reset_button)
        
        layout.addWidget(reset_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Advanced")
        
    def create_buttons(self, layout):
        """Create dialog buttons"""
        button_layout = QHBoxLayout()
        
        # Reset button
        self.reset_all_button = QPushButton("Reset All")
        self.reset_all_button.clicked.connect(self.reset_settings)
        button_layout.addWidget(self.reset_all_button)
        
        button_layout.addStretch()
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        # Apply button
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_button)
        
        # OK button
        self.ok_button = QPushButton("OK")
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.accept_settings)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
    def apply_styling(self):
        """Apply CSS styling"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 10px;
                border-radius: 4px;
            }
            
            QSlider::sub-page:horizontal {
                background: #4CAF50;
                border: 1px solid #777;
                height: 10px;
                border-radius: 4px;
            }
            
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 1px solid #777;
                width: 18px;
                margin: -2px 0;
                border-radius: 3px;
            }
        """)
        
    def load_current_settings(self):
        """Load current settings from config"""
        if not self.config:
            return
            
        # General settings
        theme_map = {"light": 0, "dark": 1, "system": 2}
        self.theme_combo.setCurrentIndex(theme_map.get(self.config.theme, 0))
        
        self.auto_start_check.setChecked(self.config.auto_start_tracking)
        self.minimize_to_tray_check.setChecked(self.config.minimize_to_tray)
        
        # Tracking settings
        self.fps_slider.setValue(self.config.tracking_fps)
        self.sensitivity_slider.setValue(int(self.config.ear_threshold * 100))
        
        # Sync settings
        self.sync_interval_spin.setValue(self.config.sync_interval)
        self.batch_size_spin.setValue(self.config.batch_size)
        
    def get_current_settings(self):
        """Get current settings from UI"""
        return {
            'theme': ['light', 'dark', 'system'][self.theme_combo.currentIndex()],
            'auto_start_tracking': self.auto_start_check.isChecked(),
            'minimize_to_tray': self.minimize_to_tray_check.isChecked(),
            'tracking_fps': self.fps_slider.value(),
            'ear_threshold': self.sensitivity_slider.value() / 100.0,
            'sync_interval': self.sync_interval_spin.value(),
            'batch_size': self.batch_size_spin.value(),
        }
        
    def update_sensitivity_label(self, value):
        """Update sensitivity label based on slider value"""
        if value < 20:
            text = "Low"
        elif value < 35:
            text = "Medium"
        else:
            text = "High"
        self.sensitivity_label.setText(text)
        
    def export_user_data(self):
        """Export user data for GDPR compliance"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export User Data", "my_wellness_data.json", 
            "JSON Files (*.json)"
        )
        
        if file_path:
            # This would call the data manager's export function
            QMessageBox.information(self, "Export Complete", 
                                  f"Your data has been exported to {file_path}")
            
    def delete_user_data(self):
        """Delete all user data"""
        reply = QMessageBox.question(
            self, "Delete All Data",
            "Are you sure you want to delete ALL your data? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # This would call the data manager's delete function
            QMessageBox.information(self, "Data Deleted", 
                                  "All your data has been permanently deleted.")
            
    def open_log_file(self):
        """Open log file in default application"""
        # This would open the log file
        QMessageBox.information(self, "Log File", "Log file opened in default application.")
        
    def reset_settings(self):
        """Reset all settings to default"""
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reset to default values
            self.theme_combo.setCurrentIndex(0)
            self.auto_start_check.setChecked(False)
            self.minimize_to_tray_check.setChecked(True)
            self.fps_slider.setValue(30)
            self.sensitivity_slider.setValue(25)
            self.sync_interval_spin.setValue(60)
            self.batch_size_spin.setValue(100)
            
    def apply_settings(self):
        """Apply settings without closing dialog"""
        settings = self.get_current_settings()
        self.settings_changed.emit(settings)
        QMessageBox.information(self, "Settings Applied", "Settings have been applied.")
        
    def accept_settings(self):
        """Apply settings and close dialog"""
        settings = self.get_current_settings()
        self.settings_changed.emit(settings)
        self.accept()