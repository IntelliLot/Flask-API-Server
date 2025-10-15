"""
Configuration settings for the YOLOv8 Parking Detection System
"""

import os
from dataclasses import dataclass
from typing import Tuple

@dataclass
class ModelConfig:
    """Model configuration settings"""
    model_path: str = "runs/detect/carpk_demo/weights/best.pt"
    confidence_threshold: float = 0.25
    device: str = "auto"  # "auto", "cpu", "cuda"
    
@dataclass
class ParkingConfig:
    """Parking detection configuration"""
    parking_positions_file: str = "CarParkPos"
    slot_width: int = 107
    slot_height: int = 48
    occupancy_threshold: float = 0.30  # 30% overlap to consider occupied
    
@dataclass
class VideoConfig:
    """Video processing configuration"""
    default_input_video: str = "carPark.mp4"
    default_input_image: str = "carParkImg.png"
    output_dir: str = "output"
    output_format: str = "mp4v"  # Video codec
    save_frames_interval: int = 30  # Save frame stats every N frames
    
@dataclass
class UIConfig:
    """User interface configuration"""
    # Colors (BGR format)
    occupied_color: Tuple[int, int, int] = (0, 255, 0)    # Green
    empty_color: Tuple[int, int, int] = (0, 0, 255)       # Red
    vehicle_color: Tuple[int, int, int] = (255, 0, 255)   # Magenta
    text_color: Tuple[int, int, int] = (255, 255, 255)    # White
    panel_color: Tuple[int, int, int] = (0, 0, 0)         # Black
    
    # Font settings
    font_face: int = 0  # cv2.FONT_HERSHEY_SIMPLEX
    font_scale: float = 0.6
    font_thickness: int = 2
    
    # Panel settings
    stats_panel_position: Tuple[int, int] = (10, 10)
    stats_panel_size: Tuple[int, int] = (450, 150)
    legend_panel_height: int = 100

@dataclass
class AppConfig:
    """Main application configuration."""
    # Global settings
    debug: bool = False
    verbose: bool = False
    verbose_logging: bool = False
    output_dir: str = "output"
    save_debug_images: bool = False
    
    def __post_init__(self):
        """Initialize nested configurations."""
        self.model = ModelConfig()
        self.parking = ParkingConfig()
        self.video = VideoConfig()
        self.ui = UIConfig()

# Global configuration instance
CONFIG = AppConfig()

# Environment-based configuration overrides
def load_config_from_env():
    """Load configuration from environment variables"""
    if os.getenv("PARKING_DEBUG"):
        CONFIG.debug = True
        CONFIG.verbose_logging = True
    
    if os.getenv("PARKING_MODEL_PATH"):
        CONFIG.model.model_path = os.getenv("PARKING_MODEL_PATH")
    
    if os.getenv("PARKING_CONFIDENCE"):
        CONFIG.model.confidence_threshold = float(os.getenv("PARKING_CONFIDENCE"))
    
    if os.getenv("PARKING_OUTPUT_DIR"):
        CONFIG.video.output_dir = os.getenv("PARKING_OUTPUT_DIR")
        os.makedirs(CONFIG.video.output_dir, exist_ok=True)

# Load environment-based config on import
load_config_from_env()
