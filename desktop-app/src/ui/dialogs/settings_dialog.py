from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QWidget, QLabel, QPushButton, QCheckBox, QSpinBox,
                            QSlider, QComboBox, QGroupBox, QFormLayout,
                            QMessageBox, QFileDialog, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import json
from typing import Dict, Any

class SettingsDialog(QDialog):
    """Settings dialog for application preferences"""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings - Wellness at Work")
        self.setModal(True)
        self.resize(500, 400)
        
        # Default settings
        self.settings = {
            'tracking': {
                'sensitivity': 75,
                'frame_rate': 20,
                'enable_notifications': True,
                'notification_interval': 30
            },
            'appearance': {
                'theme': 'dark',
                'font_size': 10,
                'show_tray_icon': True,
                'minimize_to_tray': True
            },
            'privacy': {
                'local_storage_only': False,
                'auto_sync': True,
                'data_retention_days': 30
            },
            'performance': {
                'cpu_limit': 15,
                'memory_limit': 100,
                'enable_gpu_acceleration': False
            }
        }
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup settings dialog UI"""
        layout = QVBoxLayout(self)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_tracking_tab()
        self.create_appearance_tab()
        self.create_privacy_tab()
        self.create_performance_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_settings)
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def create_tracking_tab(self):
        """Create tracking settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Detection sensitivity
        sensitivity_group = QGroupBox("Detection Sensitivity")
        sensitivity_layout = QFormLayout(sensitivity_group)
        
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(10, 100)
        self.sensitivity_slider.setValue(75)
        self.sensitivity_label = QLabel("75%")
        self.sensitivity_slider.valueChanged.connect(
            lambda v: self.sensitivity_label.setText(f"{v}%")
        )
        
        sensitivity_layout.addRow("Blink Detection:", self.sensitivity_slider)
        sensitivity_layout.addRow("", self.sensitivity_label)
        layout.addWidget(sensitivity_group)
        
        # Performance settings
        performance_group = QGroupBox("Performance")
        performance_layout = QFormLayout(performance_group)
        
        self.frame_rate_spin = QSpinBox()
        self.frame_rate_spin.setRange(10, 30)
        self.frame_rate_spin.setValue(20)
        self.frame_rate_spin.setSuffix(" FPS")
        performance_layout.addRow("Frame Rate:", self.frame_rate_spin)
        
        layout.addWidget(performance_group)
        
        # Notifications
        notifications_group = QGroupBox("Notifications")
        notifications_layout = QFormLayout(notifications_group)
        
        self.enable_notifications = QCheckBox("Enable break reminders")
        self.enable_notifications.setChecked(True)
        notifications_layout.addRow(self.enable_notifications)
        
        self.notification_interval = QSpinBox()
        self.notification_interval.setRange(10, 120)
        self.notification_interval.setValue(30)
        self.notification_interval.setSuffix(" minutes")
        notifications_layout.addRow("Reminder interval:", self.notification_interval)
        
        layout.addWidget(notifications_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Tracking")
    
    def create_appearance_tab(self):
        """Create appearance settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Theme settings
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "Auto"])
        self.theme_combo.setCurrentText("Dark")
        theme_layout.addRow("Theme:", self.theme_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setValue(10)
        self.font_size_spin.setSuffix(" pt")
        theme_layout.addRow("Font Size:", self.font_size_spin)
        
        layout.addWidget(theme_group)
        
        # System tray settings
        tray_group = QGroupBox("System Tray")
        tray_layout = QFormLayout(tray_group)
        
        self.show_tray_icon = QCheckBox("Show system tray icon")
        self.show_tray_icon.setChecked(True)
        tray_layout.addRow(self.show_tray_icon)
        
        self.minimize_to_tray = QCheckBox("Minimize to tray")
        self.minimize_to_tray.setChecked(True)
        tray_layout.addRow(self.minimize_to_tray)
        
        layout.addWidget(tray_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Appearance")
    
    def create_privacy_tab(self):
        """Create privacy settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Data storage
        storage_group = QGroupBox("Data Storage")
        storage_layout = QFormLayout(storage_group)
        
        self.local_storage_only = QCheckBox("Store data locally only")
        storage_layout.addRow(self.local_storage_only)
        
        self.auto_sync = QCheckBox("Automatically sync with cloud")
        self.auto_sync.setChecked(True)
        storage_layout.addRow(self.auto_sync)
        
        self.data_retention_spin = QSpinBox()
        self.data_retention_spin.setRange(7, 365)
        self.data_retention_spin.setValue(30)
        self.data_retention_spin.setSuffix(" days")
        storage_layout.addRow("Data retention:", self.data_retention_spin)
        
        layout.addWidget(storage_group)
        
        # GDPR controls
        gdpr_group = QGroupBox("GDPR Controls")
        gdpr_layout = QVBoxLayout(gdpr_group)
        
        export_button = QPushButton("Export My Data")
        export_button.clicked.connect(self.export_data)
        gdpr_layout.addWidget(export_button)
        
        delete_button = QPushButton("Delete All Data")
        delete_button.clicked.connect(self.delete_all_data)
        delete_button.setStyleSheet("background-color: #F44336;")
        gdpr_layout.addWidget(delete_button)
        
        layout.addWidget(gdpr_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Privacy")
    
    def create_performance_tab(self):
        """Create performance settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Resource limits
        limits_group = QGroupBox("Resource Limits")
        limits_layout = QFormLayout(limits_group)
        
        self.cpu_limit_spin = QSpinBox()
        self.cpu_limit_spin.setRange(5, 50)
        self.cpu_limit_spin.setValue(15)
        self.cpu_limit_spin.setSuffix(" %")
        limits_layout.addRow("CPU limit:", self.cpu_limit_spin)
        
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(50, 500)
        self.memory_limit_spin.setValue(100)
        self.memory_limit_spin.setSuffix(" MB")
        limits_layout.addRow("Memory limit:", self.memory_limit_spin)
        
        layout.addWidget(limits_group)
        
        # Advanced options
        advanced_group = QGroupBox("Advanced")
        advanced_layout = QFormLayout(advanced_group)
        
        self.enable_gpu = QCheckBox("Enable GPU acceleration")
        advanced_layout.addRow(self.enable_gpu)
        
        layout.addWidget(advanced_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Performance")
    
    def load_settings(self):
        """Load settings from storage"""
        # TODO: Load from data manager
        pass
    
    def save_settings(self):
        """Save settings and close dialog"""
        # Collect all settings
        self.settings['tracking']['sensitivity'] = self.sensitivity_slider.value()
        self.settings['tracking']['frame_rate'] = self.frame_rate_spin.value()
        self.settings['tracking']['enable_notifications'] = self.enable_notifications.isChecked()
        self.settings['tracking']['notification_interval'] = self.notification_interval.value()
        
        self.settings['appearance']['theme'] = self.theme_combo.currentText().lower()
        self.settings['appearance']['font_size'] = self.font_size_spin.value()
        self.settings['appearance']['show_tray_icon'] = self.show_tray_icon.isChecked()
        self.settings['appearance']['minimize_to_tray'] = self.minimize_to_tray.isChecked()
        
        self.settings['privacy']['local_storage_only'] = self.local_storage_only.isChecked()
        self.settings['privacy']['auto_sync'] = self.auto_sync.isChecked()
        self.settings['privacy']['data_retention_days'] = self.data_retention_spin.value()
        
        self.settings['performance']['cpu_limit'] = self.cpu_limit_spin.value()
        self.settings['performance']['memory_limit'] = self.memory_limit_spin.value()
        self.settings['performance']['enable_gpu_acceleration'] = self.enable_gpu.isChecked()
        
        # Emit settings changed signal
        self.settings_changed.emit(self.settings)
        
        # TODO: Save to data manager
        
        self.accept()
    
    def reset_settings(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(self, "Reset Settings", 
                                   "Are you sure you want to reset all settings to defaults?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reset UI controls to defaults
            self.sensitivity_slider.setValue(75)
            self.frame_rate_spin.setValue(20)
            self.enable_notifications.setChecked(True)
            self.notification_interval.setValue(30)
            
            self.theme_combo.setCurrentText("Dark")
            self.font_size_spin.setValue(10)
            self.show_tray_icon.setChecked(True)
            self.minimize_to_tray.setChecked(True)
            
            self.local_storage_only.setChecked(False)
            self.auto_sync.setChecked(True)
            self.data_retention_spin.setValue(30)
            
            self.cpu_limit_spin.setValue(15)
            self.memory_limit_spin.setValue(100)
            self.enable_gpu.setChecked(False)
    
    def export_data(self):
        """Export user data"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Data", "wellness_data.json", "JSON Files (*.json)"
        )
        
        if file_path:
            # TODO: Implement data export
            QMessageBox.information(self, "Export", f"Data exported to {file_path}")
    
    def delete_all_data(self):
        """Delete all user data"""
        reply = QMessageBox.warning(self, "Delete All Data",
                                  "This will permanently delete ALL your data. This action cannot be undone.\n\n"
                                  "Are you sure you want to continue?",
                                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Confirm again
            reply2 = QMessageBox.critical(self, "Final Confirmation",
                                        "FINAL WARNING: This will delete all your wellness tracking data permanently.\n\n"
                                        "Type 'DELETE' to confirm:",
                                        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            
            if reply2 == QMessageBox.StandardButton.Ok:
                # TODO: Implement data deletion
                QMessageBox.information(self, "Data Deleted", "All data has been permanently deleted.")