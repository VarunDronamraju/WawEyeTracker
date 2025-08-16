"""
Configuration Management
Basic configuration for Phase 4 testing
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Config:
    """Application configuration"""
    
    # API Configuration
    api_base_url: str = "http://localhost:8000/api"
    api_timeout: int = 30
    
    # Eye Tracking Configuration
    tracking_fps: int = 30
    ear_threshold: float = 0.25
    
    # Data Configuration
    batch_size: int = 100
    sync_interval: int = 60
    
    def __post_init__(self):
        """Initialize configuration from environment"""
        self.api_base_url = os.getenv("WAW_API_URL", self.api_base_url)
        self.api_timeout = int(os.getenv("WAW_API_TIMEOUT", self.api_timeout))
        
    def get_data_dir(self) -> Path:
        """Get data directory path"""
        if os.name == 'nt':  # Windows
            data_dir = Path(os.getenv('LOCALAPPDATA', '')) / 'WellnessAtWork'
        else:  # macOS/Linux
            data_dir = Path.home() / '.local' / 'share' / 'wellnessatwork'
            
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
