import sys
import os
import platform
import json
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from ui.main_window import MainWindow
from services.data_manager import DataManager
from services.sync_manager import SyncManager
from utils.api_client import APIClient

class WellnessAtWorkApp:
    """Main application class"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Wellness at Work")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("Wellness at Work")
        
        # Set application icon (if available)
        # self.app.setWindowIcon(QIcon("assets/icon.png"))
        
        # Initialize components
        self.data_manager = None
        self.sync_manager = None
        self.api_client = None
        self.main_window = None
        
        # Device information
        self.device_info = {
            'device_id': self.get_device_id(),
            'os': platform.system(),
            'os_version': platform.release(),
            'architecture': platform.machine(),
            'python_version': platform.python_version()
        }
    
    def get_device_id(self) -> str:
        """Get or create unique device ID"""
        app_data_dir = Path.home() / ".wellness-at-work"
        app_data_dir.mkdir(exist_ok=True)
        
        device_id_file = app_data_dir / "device_id"
        
        if device_id_file.exists():
            return device_id_file.read_text().strip()
        else:
            import uuid
            device_id = str(uuid.uuid4())
            device_id_file.write_text(device_id)
            return device_id
    
    def initialize(self):
        """Initialize application components"""
        try:
            # Initialize data manager (using device ID as temp user ID)
            self.data_manager = DataManager(self.device_info['device_id'])
            
            # Initialize API client
            self.api_client = APIClient()
            
            # Initialize sync manager
            self.sync_manager = SyncManager(self.data_manager, self.api_client)
            
            # Initialize main window
            self.main_window = MainWindow()
            
            # Connect components
            self.setup_connections()
            
            return True
            
        except Exception as e:
            QMessageBox.critical(None, "Initialization Error", 
                               f"Failed to initialize application:\n{str(e)}")
            return False
    
    def setup_connections(self):
        """Setup connections between components"""
        # Connect sync manager to main window
        if hasattr(self.main_window, 'sync_status'):
            self.sync_manager.set_sync_callbacks(
                on_complete=self.main_window.sync_status.set_last_sync_time
            )
    
    def run(self):
        """Run the application"""
        if not self.initialize():
            return 1
        
        # Show main window
        self.main_window.show()
        
        # Start sync service
        self.sync_manager.start_sync_service()
        
        # Run application
        try:
            return self.app.exec()
        finally:
            # Cleanup
            self.cleanup()
    
    def cleanup(self):
        """Cleanup application resources"""
        if self.sync_manager:
            self.sync_manager.stop_sync_service()
        
        if self.main_window and self.main_window.is_tracking:
            self.main_window.stop_tracking()

def main():
    """Main entry point"""
    # Enable high DPI support
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    
    # Create and run application
    app = WellnessAtWorkApp()
    return app.run()

if __name__ == "__main__":
    sys.exit(main())