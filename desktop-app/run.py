#!/usr/bin/env python3
"""
Final working run script for Phase 4
Handles environment setup and launches the application
"""

import sys
import os
from pathlib import Path
from datetime import datetime

def setup_environment():
    """Setup development environment"""
    # Add src to Python path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))
    
    # Set environment variables for development
    os.environ.setdefault("WAW_API_URL", "http://localhost:8000/api")
    os.environ.setdefault("DEBUG", "True")
    
def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        ('PyQt6', 'from PyQt6.QtWidgets import QApplication'),
        ('cv2', 'import cv2'),
        ('numpy', 'import numpy'),
        ('requests', 'import requests'),
        ('cryptography', 'import cryptography'),
        ('keyring', 'import keyring'),
        ('sqlalchemy', 'import sqlalchemy')
    ]
    
    missing_packages = []
    working_packages = []
    
    for package_name, import_test in required_packages:
        try:
            exec(import_test)
            working_packages.append(package_name)
            print(f"✅ {package_name}")
        except ImportError:
            missing_packages.append(package_name)
            print(f"❌ {package_name}")
            
    if missing_packages:
        print("\n⚠️  Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print(f"\n💡 Install them with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
        
    print(f"\n✅ All {len(working_packages)} essential packages working!")
    return True

def main():
    """Main entry point"""
    print("🎯 Wellness at Work Eye Tracker - Phase 4 Final Run")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Setup environment
    setup_environment()
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        print("\n❌ Dependency check failed!")
        print("💡 Please install missing packages and try again")
        return 1
        
    print("\n🚀 Starting application...")
    print("-" * 40)
    
    try:
        # Import and run the application
        from main import main as app_main
        result = app_main()
        
        print("-" * 40)
        print(f"✅ Application completed successfully!")
        return result
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure src/main.py exists and is properly formatted")
        return 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Application interrupted by user")
        return 0
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())