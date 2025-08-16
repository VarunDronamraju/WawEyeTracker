"""
Login Dialog - User authentication interface
Secure login with email/password and remember me option
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QCheckBox, QFrame,
                            QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QPixmap, QIcon

class LoginWorker(QThread):
    """Background login worker to prevent UI blocking"""
    login_completed = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, auth_manager, email, password):
        super().__init__()
        self.auth_manager = auth_manager
        self.email = email
        self.password = password
        
    def run(self):
        """Perform login in background"""
        try:
            success = self.auth_manager.login(self.email, self.password)
            if success:
                self.login_completed.emit(True, "Login successful")
            else:
                self.login_completed.emit(False, "Invalid email or password")
        except Exception as e:
            self.login_completed.emit(False, f"Login error: {str(e)}")

class LoginDialog(QDialog):
    """Login dialog for user authentication"""
    
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.login_worker = None
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Login - Wellness at Work")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header
        self.create_header(layout)
        
        # Login form
        self.create_login_form(layout)
        
        # Buttons
        self.create_buttons(layout)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Apply styling
        self.apply_styling()
        
    def create_header(self, layout):
        """Create header with logo and title"""
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        
        # Title
        title = QLabel("Wellness at Work")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Eye Tracker Login")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet("color: #666;")
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header_frame)
        
    def create_login_form(self, layout):
        """Create login form fields"""
        form_frame = QFrame()
        form_layout = QVBoxLayout(form_frame)
        
        # Email field
        email_layout = QVBoxLayout()
        email_label = QLabel("Email:")
        email_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        email_layout.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email address")
        self.email_input.setMaxLength(255)
        email_layout.addWidget(self.email_input)
        form_layout.addLayout(email_layout)
        
        # Password field
        password_layout = QVBoxLayout()
        password_label = QLabel("Password:")
        password_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        password_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMaxLength(255)
        password_layout.addWidget(self.password_input)
        form_layout.addLayout(password_layout)
        
        # Remember me checkbox
        self.remember_checkbox = QCheckBox("Remember me")
        form_layout.addWidget(self.remember_checkbox)
        
        layout.addWidget(form_frame)
        
    def create_buttons(self, layout):
        """Create action buttons"""
        button_layout = QHBoxLayout()
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self.perform_login)
        button_layout.addWidget(self.login_button)
        
        layout.addLayout(button_layout)
        
    def setup_connections(self):
        """Setup signal connections"""
        # Enter key in password field triggers login
        self.password_input.returnPressed.connect(self.perform_login)
        self.email_input.returnPressed.connect(self.perform_login)
        
    def apply_styling(self):
        """Apply CSS styling"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
                border-radius: 8px;
            }
            
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #dee2e6;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
            }
            
            QLineEdit:focus {
                border-color: #4CAF50;
                outline: none;
            }
            
            QPushButton {
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                min-width: 80px;
            }
            
            QPushButton#login_button {
                background-color: #4CAF50;
                color: white;
            }
            
            QPushButton#login_button:hover {
                background-color: #45a049;
            }
            
            QPushButton#login_button:pressed {
                background-color: #3d8b40;
            }
            
            QPushButton#cancel_button {
                background-color: #6c757d;
                color: white;
            }
            
            QPushButton#cancel_button:hover {
                background-color: #5a6268;
            }
            
            QCheckBox {
                font-size: 12px;
                color: #495057;
            }
            
            QLabel {
                color: #212529;
            }
        """)
        
        # Set object names for styling
        self.login_button.setObjectName("login_button")
        self.cancel_button.setObjectName("cancel_button")
        
    def perform_login(self):
        """Perform login authentication"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        # Validate input
        if not email:
            QMessageBox.warning(self, "Input Error", "Please enter your email address.")
            self.email_input.setFocus()
            return
            
        if not password:
            QMessageBox.warning(self, "Input Error", "Please enter your password.")
            self.password_input.setFocus()
            return
            
        # Validate email format
        if "@" not in email or "." not in email:
            QMessageBox.warning(self, "Input Error", "Please enter a valid email address.")
            self.email_input.setFocus()
            return
            
        # Start login process
        self.set_login_in_progress(True)
        
        # Create and start login worker
        self.login_worker = LoginWorker(self.auth_manager, email, password)
        self.login_worker.login_completed.connect(self.on_login_completed)
        self.login_worker.start()
        
    @pyqtSlot(bool, str)
    def on_login_completed(self, success, message):
        """Handle login completion"""
        self.set_login_in_progress(False)
        
        if success:
            # Save email if remember me is checked
            if self.remember_checkbox.isChecked():
                self.save_remembered_email()
                
            QMessageBox.information(self, "Success", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Login Failed", message)
            self.password_input.clear()
            self.password_input.setFocus()
            
    def set_login_in_progress(self, in_progress):
        """Update UI for login progress"""
        self.login_button.setEnabled(not in_progress)
        self.cancel_button.setEnabled(not in_progress)
        self.email_input.setEnabled(not in_progress)
        self.password_input.setEnabled(not in_progress)
        self.remember_checkbox.setEnabled(not in_progress)
        
        if in_progress:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.login_button.setText("Logging in...")
        else:
            self.progress_bar.setVisible(False)
            self.login_button.setText("Login")
            
    def save_remembered_email(self):
        """Save email for remember me functionality"""
        # In production, use QSettings or keyring
        pass
        
    def load_remembered_email(self):
        """Load saved email if available"""
        # In production, load from QSettings or keyring
        pass
        
    def showEvent(self, event):
        """Handle dialog show event"""
        super().showEvent(event)
        self.load_remembered_email()
        self.email_input.setFocus()