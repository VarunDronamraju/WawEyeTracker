from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTextBrowser, QCheckBox, QScrollArea,
                            QWidget, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
import time

class GDPRConsentDialog(QDialog):
    """GDPR consent dialog with full compliance information"""
    
    consent_given = pyqtSignal(bool)
    
    def __init__(self, parent=None, is_update=False):
        super().__init__(parent)
        self.setWindowTitle("Privacy & Data Protection")
        self.setModal(True)
        self.resize(600, 700)
        self.is_update = is_update
        
        # Consent tracking
        self.consents = {
            'essential': False,
            'analytics': False,
            'marketing': False
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup GDPR consent dialog UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Privacy & Data Protection")
        header_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)
        
        # Subtitle
        subtitle_text = "We respect your privacy and are committed to protecting your personal data."
        if self.is_update:
            subtitle_text = "Our privacy policy has been updated. Please review the changes below."
        
        subtitle_label = QLabel(subtitle_text)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)
        
        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Privacy policy text
        self.create_privacy_content(scroll_layout)
        
        # Consent checkboxes
        self.create_consent_controls(scroll_layout)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        if not self.is_update:
            self.decline_button = QPushButton("Decline")
            self.decline_button.clicked.connect(self.decline_consent)
            self.decline_button.setStyleSheet("background-color: #F44336;")
            button_layout.addWidget(self.decline_button)
        
        button_layout.addStretch()
        
        self.accept_button = QPushButton("Accept" if not self.is_update else "Update Preferences")
        self.accept_button.clicked.connect(self.accept_consent)
        self.accept_button.setStyleSheet("background-color: #4CAF50;")
        self.accept_button.setEnabled(False)  # Enabled when essential consent given
        button_layout.addWidget(self.accept_button)
        
        layout.addLayout(button_layout)
    
    def create_privacy_content(self, layout):
        """Create privacy policy content"""
        # What data we collect
        data_group = QGroupBox("What Data We Collect")
        data_layout = QVBoxLayout(data_group)
        
        data_text = QTextBrowser()
        data_text.setMaximumHeight(150)
        data_text.setHtml("""
        <h4>Eye Tracking Data:</h4>
        <ul>
            <li>Blink count per minute</li>
            <li>Blink timing and confidence scores</li>
            <li>Eye strain indicators</li>
            <li>Session duration and timestamps</li>
        </ul>
        
        <h4>Technical Data:</h4>
        <ul>
            <li>Device ID (anonymized)</li>
            <li>Application version</li>
            <li>Operating system information</li>
            <li>Performance metrics</li>
        </ul>
        
        <p><strong>We DO NOT collect:</strong> Personal identification, camera images, 
        or any data that can identify you personally.</p>
        """)
        data_layout.addWidget(data_text)
        layout.addWidget(data_group)
        
        # How we use data
        usage_group = QGroupBox("How We Use Your Data")
        usage_layout = QVBoxLayout(usage_group)
        
        usage_text = QTextBrowser()
        usage_text.setMaximumHeight(120)
        usage_text.setHtml("""
        <ul>
            <li><strong>Essential:</strong> Provide eye tracking functionality and health insights</li>
            <li><strong>Analytics:</strong> Improve application performance and features</li>
            <li><strong>Research:</strong> Advance workplace wellness research (anonymized)</li>
        </ul>
        
        <p>Your data is encrypted and stored securely. You can export or delete your data at any time.</p>
        """)
        usage_layout.addWidget(usage_text)
        layout.addWidget(usage_group)
        
        # Your rights
        rights_group = QGroupBox("Your Rights Under GDPR")
        rights_layout = QVBoxLayout(rights_group)
        
        rights_text = QTextBrowser()
        rights_text.setMaximumHeight(120)
        rights_text.setHtml("""
        <ul>
            <li><strong>Right to Access:</strong> Export all your data in JSON format</li>
            <li><strong>Right to Deletion:</strong> Permanently delete all your data</li>
            <li><strong>Right to Rectification:</strong> Correct any inaccurate data</li>
            <li><strong>Right to Data Portability:</strong> Transfer your data to another service</li>
            <li><strong>Right to Withdraw Consent:</strong> Change your preferences at any time</li>
        </ul>
        """)
        rights_layout.addWidget(rights_text)
        layout.addWidget(rights_group)
    
    def create_consent_controls(self, layout):
        """Create consent checkbox controls"""
        consent_group = QGroupBox("Consent Preferences")
        consent_layout = QVBoxLayout(consent_group)
        
        # Essential consent (required)
        self.essential_checkbox = QCheckBox(
            "Essential Data Processing (Required)\n"
            "Allow processing of eye tracking data to provide core functionality. "
            "This is necessary for the application to work."
        )
        self.essential_checkbox.setStyleSheet("font-weight: bold;")
        self.essential_checkbox.toggled.connect(self.update_consent)
        consent_layout.addWidget(self.essential_checkbox)
        
        # Analytics consent (optional)
        self.analytics_checkbox = QCheckBox(
            "Analytics & Performance (Optional)\n"
            "Allow us to analyze usage patterns to improve the application. "
            "This data is anonymized and used only for development purposes."
        )
        self.analytics_checkbox.toggled.connect(self.update_consent)
        consent_layout.addWidget(self.analytics_checkbox)
        
        # Research consent (optional)
        self.research_checkbox = QCheckBox(
            "Wellness Research (Optional)\n"
            "Contribute anonymized data to workplace wellness research. "
            "This helps advance understanding of digital eye strain and workplace health."
        )
        self.research_checkbox.toggled.connect(self.update_consent)
        consent_layout.addWidget(self.research_checkbox)
        
        layout.addWidget(consent_group)
        
        # Data retention information
        retention_label = QLabel(
            "Data Retention: Your data will be kept for 30 days (configurable in settings) "
            "or until you request deletion. Anonymized research data may be retained longer "
            "but cannot be linked back to you."
        )
        retention_label.setWordWrap(True)
        retention_label.setStyleSheet("color: #666666; font-size: 9pt;")
        layout.addWidget(retention_label)
        
        # Contact information
        contact_label = QLabel(
            "Questions about privacy? Contact us at privacy@wellnessatwork.com"
        )
        contact_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        contact_label.setStyleSheet("color: #666666; font-size: 9pt;")
        layout.addWidget(contact_label)
    
    def update_consent(self):
        """Update consent status and button state"""
        self.consents['essential'] = self.essential_checkbox.isChecked()
        self.consents['analytics'] = self.analytics_checkbox.isChecked()
        self.consents['marketing'] = self.research_checkbox.isChecked()
        
        # Enable accept button only if essential consent is given
        self.accept_button.setEnabled(self.consents['essential'])
    
    def accept_consent(self):
        """Accept consent and close dialog"""
        if not self.consents['essential']:
            return
        
        # Record consent timestamp
        consent_data = {
            **self.consents,
            'timestamp': time.time(),
            'version': '1.0',
            'ip_address': None,  # We don't store IP addresses
            'user_agent': 'WellnessAtWork/1.0'
        }
        
        # TODO: Store consent in data manager
        
        self.consent_given.emit(True)
        self.accept()
    
    def decline_consent(self):
        """Decline consent and close application"""
        self.consent_given.emit(False)
        self.reject()
    
    def get_consent_data(self):
        """Get current consent data"""
        return {
            **self.consents,
            'timestamp': time.time(),
            'version': '1.0'
        }