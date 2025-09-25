#!/usr/bin/env python3
"""
Configuration for Local Frame Server
"""

import os
from pathlib import Path

# Load .env file if it exists
def load_env():
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Load environment variables
load_env()

class Config:
    """Configuration class for the frame server"""
    
    def __init__(self):
        # Video source configuration
        self.USE_CAMERA = os.getenv('USE_CAMERA', 'false').lower() == 'true'
        self.CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', '0'))
        
        # Video file path (if not using camera)
        self.VIDEO_SOURCE = os.getenv('VIDEO_SOURCE', 'sample_video.mp4')
        
        # Make video source path absolute if relative
        if not os.path.isabs(self.VIDEO_SOURCE):
            self.VIDEO_SOURCE = os.path.join(os.path.dirname(__file__), self.VIDEO_SOURCE)
        
        # Frame capture settings
        self.FRAME_WIDTH = int(os.getenv('FRAME_WIDTH', '640'))
        self.FRAME_HEIGHT = int(os.getenv('FRAME_HEIGHT', '480'))
        self.FRAME_RATE = int(os.getenv('FRAME_RATE', '30'))
        
        # Server settings
        self.HOST = os.getenv('SERVER_HOST', '127.0.0.1')
        self.PORT = int(os.getenv('SERVER_PORT', '5000'))
        
        # Logging
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        
        # Frame storage
        self.SAVE_FRAMES = os.getenv('SAVE_FRAMES', 'true').lower() == 'true'
        self.FRAME_SAVE_PATH = os.getenv('FRAME_SAVE_PATH', 'captured_frames')
        
        # Create directories if needed
        if self.SAVE_FRAMES and not os.path.exists(self.FRAME_SAVE_PATH):
            os.makedirs(self.FRAME_SAVE_PATH, exist_ok=True)