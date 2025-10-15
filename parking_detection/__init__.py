"""
YOLOv8 Parking Detection System

A professional computer vision system for parking space detection and occupancy monitoring
using YOLOv8 object detection and intelligent parking space management.

Features:
- Real-time vehicle detection using YOLOv8
- Parking space occupancy detection
- Video processing and analysis
- Real-time visualization
- Performance monitoring
- Configurable detection parameters

Author: AI Assistant
Version: 2.0.0
"""

from .core import ParkingDetectionSystem, VehicleDetector, ParkingManager, ParkingVisualizer
from .config import CONFIG
from .utils import *

__version__ = "2.0.0"
__author__ = "AI Assistant"

__all__ = [
    'ParkingDetectionSystem',
    'VehicleDetector',
    'ParkingManager',
    'ParkingVisualizer',
    'CONFIG'
]
