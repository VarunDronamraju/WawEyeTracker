# Wellness at Work Eye Tracker - Desktop Application

A comprehensive PyQt6 desktop application for monitoring eye health and blink patterns in workplace environments with cloud synchronization and GDPR compliance.

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Camera/webcam access
- Internet connection (for cloud sync)

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd desktop-app
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the application:**
```bash
python run.py
```

## 🏗️ Architecture Overview

```
Desktop Application
├── PyQt6 GUI Framework
├── OpenCV Eye Tracking
├── SQLite Local Storage
├── Cloud API Integration
├── GDPR Compliance
└── Cross-Platform Support
```

### Core Components

- **Main Window** (`src/ui/main_window.py`) - Primary interface with real-time tracking
- **Eye Tracker** (`src/core/eye_tracker.py`) - OpenCV-based blink detection
- **Data Manager** (`src/services/data_manager.py`) - Local storage and sync
- **Auth Manager** (`src/services/auth_manager.py`) - JWT authentication
- **API Client** (`src/utils/api_client.py`) - Backend communication

## 🎯 Features

### ✅ Core Functionality
- **Real-time Eye Tracking** - Live blink detection using OpenCV
- **Cloud Synchronization** - Automatic sync with backend API
- **Offline Support** - Queue data when offline, sync when online
- **GDPR Compliance** - Data export, deletion, and consent management
- **Cross-Platform** - Windows and macOS support

### ✅ User Interface
- **Modern PyQt6 GUI** - Clean, intuitive interface
- **Real-time Dashboard** - Live blink counter and statistics
- **System Tray Integration** - Background operation
- **Settings Management** - Comprehensive preferences
- **Authentication** - Secure login with JWT tokens

### ✅ Security & Privacy
- **Local Encryption** - AES-256 for local data
- **Secure Communication** - HTTPS with JWT authentication
- **GDPR Rights** - Data access, export, and deletion
- **Consent Management** - Clear privacy controls

## 🛠️ Development

### Project Structure
```
desktop-app/
├── src/
│   ├── main.py                 # Application entry point
│   ├── ui/
│   │   ├── main_window.py      # Main GUI window
│   │   ├── dialogs/            # Login, settings, consent dialogs
│   │   └── widgets/            # Custom UI components
│   ├── core/
│   │   ├── eye_tracker.py      # Eye tracking engine
│   │   └── blink_detector.py   # Blink detection algorithm
│   ├── services/
│   │   ├── data_manager.py     # Data storage and sync
│   │   ├── auth_manager.py     # Authentication
│   │   └── sync_manager.py     # Online/offline sync
│   └── utils/
│       ├── api_client.py       # Backend communication
│       └── config.py           # Configuration management
├── build_scripts/
│   └── build.py               # PyInstaller build script
├── requirements.txt           # Python dependencies
├── run.py                    # Development run script
└── README.md                 # This file
```

### Running from Source

```bash
# Install development dependencies
pip install -r requirements.txt

# Run in development mode
python run.py

# Or run directly
python src/main.py
```

### Building Executables

```bash
# Build for current platform
python build_scripts/build.py

# Windows output: dist/WellnessAtWorkEyeTracker.exe
# macOS output: dist/WellnessAtWorkEyeTracker.app
```

## 🔧 Configuration

### Environment Variables
```bash
# API Configuration
WAW_API_URL=http://localhost:8000/api
WAW_API_TIMEOUT=30

# Development
DEBUG=True
LOG_LEVEL=INFO

# Eye Tracking
TRACKING_FPS=30
EAR_THRESHOLD=0.25
```

### User Settings
Settings are stored in:
- **Windows**: `%APPDATA%/WellnessAtWork/config.json`
- **macOS**: `~/.config/wellnessatwork/config.json`

## 🧪 Testing

### Manual Testing
```bash
# Test basic functionality
python -m pytest tests/

# Test eye tracking
python tests/test_eye_tracker.py

# Test API integration
python tests/test_api_client.py
```

### UI Testing
```bash
# Test PyQt6 components
python tests/test_ui_components.py
```

## 📦 Dependencies

### Core Dependencies
- **PyQt6** >= 6.5.0 - GUI framework
- **opencv-python** >= 4.8.0 - Computer vision
- **numpy** >= 1.24.0 - Numerical computing
- **requests** >= 2.31.0 - HTTP client
- **cryptography** >= 41.0.0 - Encryption
- **keyring** >= 24.0.0 - Secure storage

### Build Dependencies
- **pyinstaller** >= 5.13.0 - Executable creation
- **auto-py-to-exe** >= 2.40.0 - GUI for PyInstaller

## 🚀 Deployment

### Windows Distribution
1. Build executable: `python build_scripts/build.py`
2. Create installer with NSIS
3. Code sign with certificate
4. Distribute via MSIX or direct download

### macOS Distribution
1. Build app bundle: `python build_scripts/build.py`
2. Code sign with Developer ID
3. Notarize with Apple
4. Distribute via TestFlight or direct download

## 🔒 Security Considerations

### Data Protection
- All sensitive data encrypted at rest
- HTTPS communication with certificate pinning
- JWT tokens stored securely in OS keychain
- No plaintext passwords stored locally

### Privacy Compliance
- Explicit user consent before data collection
- Clear privacy policy and user rights
- Data export in portable formats
- Complete data deletion capabilities

## 🐛 Troubleshooting

### Common Issues

**Camera not detected:**
```bash
# Check camera permissions
# Windows: Settings > Privacy > Camera
# macOS: System Preferences > Security & Privacy > Camera
```

**API connection failed:**
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check firewall settings
# Ensure port 8000 is accessible
```

**Import errors:**
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Check Python version
python --version  # Should be 3.11+
```

### Performance Optimization
- Reduce frame rate if CPU usage is high
- Enable low power mode for longer battery life
- Adjust detection sensitivity for better accuracy

## 📈 Performance Metrics

### Target Performance
- **Startup Time**: < 3 seconds
- **Memory Usage**: < 150MB
- **CPU Usage**: < 10% during tracking
- **Frame Rate**: 15-30 FPS
- **Battery Impact**: < 5% additional drain

### Monitoring
Performance metrics are displayed in the Eye Tracking tab:
- Real-time FPS counter
- CPU and memory usage
- Detection accuracy percentage
- Network sync status

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install development dependencies
4. Make changes and test thoroughly
5. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use type hints where possible
- Document all public methods
- Add unit tests for new features

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- **Email**: support@wellnessatwork.com
- **Documentation**: [docs.wellnessatwork.com](https://docs.wellnessatwork.com)
- **Issues**: [GitHub Issues](https://github.com/wellnessatwork/eye-tracker/issues)

---

**Built with ❤️ for workplace wellness monitoring**
```