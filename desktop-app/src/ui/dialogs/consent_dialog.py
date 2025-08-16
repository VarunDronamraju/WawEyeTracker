"""
GDPR Consent Dialog - Privacy consent and data protection
Clear consent form with detailed privacy information
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTextEdit, QCheckBox, QScrollArea,
                            QFrame, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from datetime import datetime

class ConsentDialog(QDialog):
    """GDPR consent dialog for data protection compliance"""
    
    consent_given = pyqtSignal(bool)  # Emit when consent is given/withdrawn
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.consent_accepted = False
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Privacy Consent - Wellness at Work")
        self.setFixedSize(600, 700)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Header
        self.create_header(layout)
        
        # Privacy policy content
        self.create_privacy_content(layout)
        
        # Consent checkboxes
        self.create_consent_section(layout)
        
        # Buttons
        self.create_buttons(layout)
        
        # Apply styling
        self.apply_styling()
        
    def create_header(self, layout):
        """Create header section"""
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        
        # Title
        title = QLabel("Privacy and Data Protection")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Your privacy is important to us")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet("color: #666; margin-bottom: 10px;")
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header_frame)
        
    def create_privacy_content(self, layout):
        """Create scrollable privacy policy content"""
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(350)
        
        # Content widget
        content_widget = QFrame()
        content_layout = QVBoxLayout(content_widget)
        
        # Privacy policy text
        privacy_text = self.get_privacy_policy_text()
        
        privacy_display = QTextEdit()
        privacy_display.setPlainText(privacy_text)
        privacy_display.setReadOnly(True)
        privacy_display.setFont(QFont("Arial", 10))
        content_layout.addWidget(privacy_display)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
    def create_consent_section(self, layout):
        """Create consent checkboxes section"""
        consent_frame = QFrame()
        consent_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        consent_layout = QVBoxLayout(consent_frame)
        
        # Required consent
        consent_layout.addWidget(QLabel("Required Consents:"))
        
        self.data_processing_check = QCheckBox(
            "I consent to the processing of my eye tracking data for wellness monitoring purposes"
        )
        self.data_processing_check.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        consent_layout.addWidget(self.data_processing_check)
        
        self.data_storage_check = QCheckBox(
            "I consent to the secure storage of my data both locally and in the cloud"
        )
        self.data_storage_check.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        consent_layout.addWidget(self.data_storage_check)
        
        # Optional consent
        consent_layout.addWidget(QLabel("\nOptional Consents:"))
        
        self.analytics_check = QCheckBox(
            "I consent to anonymous usage analytics to improve the application (Optional)"
        )
        consent_layout.addWidget(self.analytics_check)
        
        self.notifications_check = QCheckBox(
            "I consent to receive wellness reminders and notifications (Optional)"
        )
        consent_layout.addWidget(self.notifications_check)
        
        # Rights information
        rights_text = QLabel(
            "\nYour Rights:\n"
            "• Right to access your data\n"
            "• Right to export your data\n"
            "• Right to delete your data\n"
            "• Right to withdraw consent at any time\n"
            "• Right to data portability"
        )
        rights_text.setFont(QFont("Arial", 9))
        rights_text.setStyleSheet("color: #555; background-color: #f8f9fa; padding: 10px; border-radius: 4px;")
        consent_layout.addWidget(rights_text)
        
        layout.addWidget(consent_frame)
        
    def create_buttons(self, layout):
        """Create action buttons"""
        button_layout = QHBoxLayout()
        
        # Decline button
        self.decline_button = QPushButton("Decline")
        self.decline_button.clicked.connect(self.decline_consent)
        self.decline_button.setStyleSheet("""
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
        button_layout.addWidget(self.decline_button)
        
        button_layout.addStretch()
        
        # Accept button
        self.accept_button = QPushButton("Accept")
        self.accept_button.clicked.connect(self.accept_consent)
        self.accept_button.setEnabled(False)  # Disabled until required consents checked
        self.accept_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.accept_button)
        
        layout.addLayout(button_layout)
        
        # Connect checkbox signals to update button state
        self.data_processing_check.toggled.connect(self.update_accept_button)
        self.data_storage_check.toggled.connect(self.update_accept_button)
        
    def apply_styling(self):
        """Apply CSS styling"""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
            }
            
            QCheckBox {
                spacing: 8px;
                margin: 5px 0;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            
            QCheckBox::indicator:unchecked {
                border: 2px solid #6c757d;
                border-radius: 3px;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                border: 2px solid #28a745;
                border-radius: 3px;
                background-color: #28a745;
                image: url(:/icons/checkmark.png);
            }
            
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
        """)
        
    def get_privacy_policy_text(self):
        """Get privacy policy text"""
        return """
WELLNESS AT WORK - PRIVACY POLICY

1. DATA COLLECTION
We collect only the following data necessary for wellness monitoring:
• Eye blink patterns and frequency
• Session timestamps and duration
• Device information (operating system, app version)
• User account information (email address)

2. DATA USAGE
Your data is used exclusively for:
• Monitoring your eye health and blink patterns
• Providing wellness insights and break reminders
• Improving application functionality (with your consent)

3. DATA STORAGE
• Data is encrypted both locally and during transmission
• Cloud storage uses industry-standard security measures
• Local data is stored in an encrypted database on your device
• You can choose to store data locally only

4. DATA SHARING
We NEVER share your personal data with third parties. Your data remains private and is used only for the purposes you have consented to.

5. DATA RETENTION
• Data is retained according to your preferences (default: 1 year)
• You can delete your data at any time
• Data is automatically deleted when you delete your account

6. YOUR RIGHTS (GDPR)
You have the right to:
• Access all data we have about you
• Export your data in a portable format
• Delete all your data permanently
• Withdraw consent at any time
• Update or correct your data

7. SECURITY MEASURES
• End-to-end encryption for data transmission
• AES-256 encryption for local data storage
• Secure authentication with JWT tokens
• Regular security audits and updates

8. CONTACT INFORMATION
For privacy concerns or to exercise your rights:
Email: privacy@wellnessatwork.com
Address: [Company Address]

Last updated: """ + datetime.now().strftime("%B %d, %Y") + """

By using this application, you acknowledge that you have read and understood this privacy policy.
        """
        
    def update_accept_button(self):
        """Update accept button state based on required consents"""
        required_consents = [
            self.data_processing_check.isChecked(),
            self.data_storage_check.isChecked()
        ]
        
        self.accept_button.setEnabled(all(required_consents))
        
    def accept_consent(self):
        """Handle consent acceptance"""
        if not self.data_processing_check.isChecked() or not self.data_storage_check.isChecked():
            QMessageBox.warning(
                self, "Consent Required",
                "Please check all required consent boxes to continue."
            )
            return
            
        self.consent_accepted = True
        
        # Store consent preferences
        consent_data = {
            'data_processing': self.data_processing_check.isChecked(),
            'data_storage': self.data_storage_check.isChecked(),
            'analytics': self.analytics_check.isChecked(),
            'notifications': self.notifications_check.isChecked(),
            'timestamp': datetime.now().isoformat()
        }
        
        self.consent_given.emit(True)
        
        QMessageBox.information(
            self, "Consent Recorded",
            "Thank you for providing your consent. You can change these preferences at any time in Settings."
        )
        
        self.accept()
        
    def decline_consent(self):
        """Handle consent decline"""
        reply = QMessageBox.question(
            self, "Decline Consent",
            "Without consent to process your data, the application cannot function. "
            "Are you sure you want to decline?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.consent_accepted = False
            self.consent_given.emit(False)
            self.reject()
