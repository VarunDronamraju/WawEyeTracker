# UI Widgets package for Wellness at Work Eye Tracker
"""
UI Widgets package initialization
"""

from .blink_counter import BlinkCounterWidget
from .sync_status_widget import SyncStatusWidget
from .eye_tracking_widget import EyeTrackingWidget

__all__ = ['BlinkCounterWidget', 'SyncStatusWidget', 'EyeTrackingWidget']