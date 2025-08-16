from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QFrame, QStackedWidget,
                            QMenuBar, QStatusBar, QSystemTrayIcon, QMenu,
                            QMessageBox, QLCDNumber, QProgressBar, QSplitter)
from PyQt6.QtCore import QTimer, pyqtSignal, QThread, Qt
from PyQt6.QtGui import QAction, QIcon, QFont

from ui.dialogs.login_dialog import LoginDialog
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.consent_dialog import ConsentDialog
from ui.widgets.blink_counter import BlinkCounterWidget
from ui.widgets.eye_tracking_widget import EyeTrackingWidget
from ui.widgets.sync_status_widget import SyncStatusWidget
from core.eye_tracker import EyeTracker

class MainWindow(QMainWindow):
    # Signals
    blink_detected = pyqtSignal(int)  # blink count
    tracking_started = pyqtSignal()
    tracking_stopped = pyqtSignal()
    
    def __init__(self, data_manager, auth_manager, config):
        super().__init__()
        self.data_manager = data_manager
        self.auth_manager = auth_manager
        self.config = config
        
        # Eye tracking components
        self.eye_tracker = None
        self.tracking_active = False
        
        # Timers
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        
        # Initialize UI
        self.init_ui()
        self.setup_connections()
        
        # Check authentication on startup
        self.check_authentication()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Wellness at Work Eye Tracker")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create sidebar
        self.create_sidebar(splitter)
        
        # Create main content area
        self.create_main_content(splitter)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.create_status_bar()
        
        # Apply styling
        self.apply_styling()
        
    def create_sidebar(self, parent):
        """Create navigation sidebar"""
        sidebar = QFrame()
        sidebar.setMaximumWidth(200)
        sidebar.setFrameStyle(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(sidebar)
        
        # Title
        title = QLabel("Eye Tracker")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("Dashboard", self.show_dashboard),
            ("Eye Tracking", self.show_eye_tracking),
            ("Analytics", self.show_analytics),
            ("Settings", self.show_settings)
        ]
        
        for name, handler in nav_items:
            btn = QPushButton(name)
            btn.clicked.connect(handler)
            layout.addWidget(btn)
            self.nav_buttons[name] = btn
            
        layout.addStretch()
        
        # Status widgets at bottom
        self.sync_status = SyncStatusWidget()
        layout.addWidget(self.sync_status)
        
        parent.addWidget(sidebar)
        
    def create_main_content(self, parent):
        """Create main content area with stacked widgets"""
        self.content_stack = QStackedWidget()
        
        # Dashboard view
        self.dashboard_widget = self.create_dashboard()
        self.content_stack.addWidget(self.dashboard_widget)
        
        # Eye tracking view
        self.eye_tracking_widget = EyeTrackingWidget()
        self.content_stack.addWidget(self.eye_tracking_widget)
        
        # Analytics view (placeholder)
        analytics_widget = QLabel("Analytics View - Coming Soon")
        analytics_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_stack.addWidget(analytics_widget)
        
        # Settings view will be handled by dialog
        
        parent.addWidget(self.content_stack)
        
        # Set default view
        self.content_stack.setCurrentWidget(self.dashboard_widget)
        
    def create_dashboard(self):
        """Create dashboard with real-time metrics"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Welcome message
        welcome = QLabel("Welcome to Wellness at Work Eye Tracker")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(welcome)
        
        # Metrics grid
        metrics_layout = QHBoxLayout()
        
        # Real-time blink counter
        self.blink_counter = BlinkCounterWidget()
        metrics_layout.addWidget(self.blink_counter)
        
        # Session info
        session_frame = QFrame()
        session_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        session_layout = QVBoxLayout(session_frame)
        
        session_layout.addWidget(QLabel("Session Status"))
        self.session_status = QLabel("Not Tracking")
        session_layout.addWidget(self.session_status)
        
        session_layout.addWidget(QLabel("Session Time"))
        self.session_time = QLabel("00:00:00")
        session_layout.addWidget(self.session_time)
        
        metrics_layout.addWidget(session_frame)
        
        layout.addLayout(metrics_layout)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Tracking")
        self.start_button.clicked.connect(self.start_tracking)
        controls_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Tracking")
        self.stop_button.clicked.connect(self.stop_tracking)
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.stop_button)
        
        layout.addLayout(controls_layout)
        layout.addStretch()
        
        return widget
        
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        login_action = QAction('Login', self)
        login_action.triggered.connect(self.show_login)
        file_menu.addAction(login_action)
        
        logout_action = QAction('Logout', self)
        logout_action.triggered.connect(self.logout)
        file_menu.addAction(logout_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        settings_action = QAction('Settings', self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Add permanent widgets
        self.auth_status = QLabel("Not Authenticated")
        self.status_bar.addPermanentWidget(self.auth_status)
        
    def setup_connections(self):
        """Setup signal-slot connections"""
        # Connect eye tracking signals
        self.blink_detected.connect(self.blink_counter.update_count)
        self.tracking_started.connect(self.on_tracking_started)
        self.tracking_stopped.connect(self.on_tracking_stopped)
        
        # Connect update timer
        self.update_timer.start(1000)  # Update every second
        
    def apply_styling(self):
        """Apply CSS styling to the application"""
        style = """
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
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
            background-color: #cccccc;
            color: #666666;
        }
        
        QFrame {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
        }
        
        QLabel {
            color: #333;
        }
        """
        self.setStyleSheet(style)
        
    # Navigation methods
    def show_dashboard(self):
        self.content_stack.setCurrentWidget(self.dashboard_widget)
        
    def show_eye_tracking(self):
        self.content_stack.setCurrentWidget(self.eye_tracking_widget)
        
    def show_analytics(self):
        self.content_stack.setCurrentIndex(2)  # Analytics placeholder
        
    def show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()
        
    # Authentication methods
    def check_authentication(self):
        """Check if user is authenticated"""
        if self.auth_manager.is_authenticated():
            self.on_authenticated()
        else:
            self.show_login()
            
    def show_login(self):
        """Show login dialog"""
        dialog = LoginDialog(self.auth_manager, self)
        if dialog.exec() == LoginDialog.DialogCode.Accepted:
            self.on_authenticated()
            
    def logout(self):
        """Logout user"""
        self.auth_manager.logout()
        self.auth_status.setText("Not Authenticated")
        self.stop_tracking()
        
    def on_authenticated(self):
        """Handle successful authentication"""
        user = self.auth_manager.get_current_user()
        self.auth_status.setText(f"Logged in as: {user.get('email', 'Unknown')}")
        
        # Check GDPR consent
        if not self.auth_manager.has_gdpr_consent():
            self.show_consent_dialog()
            
    def show_consent_dialog(self):
        """Show GDPR consent dialog"""
        dialog = ConsentDialog(self)
        if dialog.exec() == ConsentDialog.DialogCode.Accepted:
            self.auth_manager.set_gdpr_consent(True)
            
    # Eye tracking methods
    def start_tracking(self):
        """Start eye tracking"""
        if not self.auth_manager.is_authenticated():
            QMessageBox.warning(self, "Authentication Required", 
                              "Please log in to start tracking.")
            return
            
        if not self.auth_manager.has_gdpr_consent():
            QMessageBox.warning(self, "Consent Required", 
                              "Please provide GDPR consent to start tracking.")
            return
            
        try:
            # Initialize eye tracker
            if not self.eye_tracker:
                self.eye_tracker = EyeTracker()
                
            # Start tracking
            self.eye_tracker.start_tracking()
            self.tracking_active = True
            
            # Update UI
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.session_status.setText("Tracking Active")
            
            # Emit signal
            self.tracking_started.emit()
            
            self.status_bar.showMessage("Eye tracking started")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start tracking: {str(e)}")
            
    def stop_tracking(self):
        """Stop eye tracking"""
        if self.eye_tracker and self.tracking_active:
            self.eye_tracker.stop_tracking()
            self.tracking_active = False
            
            # Update UI
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.session_status.setText("Not Tracking")
            
            # Emit signal
            self.tracking_stopped.emit()
            
            self.status_bar.showMessage("Eye tracking stopped")
            
    def on_tracking_started(self):
        """Handle tracking started"""
        # Start session in data manager
        self.data_manager.start_session()
        
    def on_tracking_stopped(self):
        """Handle tracking stopped"""
        # End session in data manager
        self.data_manager.end_session()
        
    def update_display(self):
        """Update display with current data"""
        if self.tracking_active and self.eye_tracker:
            # Get latest blink count
            blink_count = self.eye_tracker.get_blink_count()
            self.blink_detected.emit(blink_count)
            
            # Update session time
            session_time = self.data_manager.get_session_duration()
            self.session_time.setText(self.format_duration(session_time))
            
    def format_duration(self, seconds):
        """Format duration in HH:MM:SS format"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About", 
                         "Wellness at Work Eye Tracker v1.0.0\n\n"
                         "A desktop application for monitoring eye health "
                         "and blink patterns in workplace environments.")
        
    def closeEvent(self, event):
        """Handle application close"""
        if self.tracking_active:
            reply = QMessageBox.question(self, "Close Application",
                                       "Eye tracking is active. Stop tracking and exit?",
                                       QMessageBox.StandardButton.Yes | 
                                       QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.stop_tracking()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()