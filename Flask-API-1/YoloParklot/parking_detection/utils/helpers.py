"""
Utility functions for parking detection system
"""

import cv2
import pickle
import logging
from datetime import datetime
from typing import List, Tuple, Optional
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_parking_positions(file_path: str) -> List[Tuple[int, int]]:
    """
    Load parking positions from pickle file
    
    Args:
        file_path: Path to parking positions pickle file
        
    Returns:
        List of (x, y) coordinates for parking slots
    """
    try:
        with open(file_path, 'rb') as f:
            positions = pickle.load(f)
        logger.info(f"Loaded {len(positions)} parking positions from {file_path}")
        return positions
    except Exception as e:
        logger.error(f"Error loading parking positions: {e}")
        raise

def save_parking_positions(positions: List[Tuple[int, int]], file_path: str) -> None:
    """
    Save parking positions to pickle file
    
    Args:
        positions: List of (x, y) coordinates
        file_path: Output file path
    """
    try:
        with open(file_path, 'wb') as f:
            pickle.dump(positions, f)
        logger.info(f"Saved {len(positions)} parking positions to {file_path}")
    except Exception as e:
        logger.error(f"Error saving parking positions: {e}")
        raise

def generate_timestamp_filename(prefix: str = "", extension: str = "mp4") -> str:
    """
    Generate timestamp-based filename
    
    Args:
        prefix: Filename prefix
        extension: File extension (without dot)
        
    Returns:
        Timestamped filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if prefix:
        return f"{prefix}_{timestamp}.{extension}"
    return f"{timestamp}.{extension}"

def calculate_overlap_ratio(box1: Tuple[int, int, int, int], 
                          box2: Tuple[int, int, int, int]) -> float:
    """
    Calculate intersection over union (IoU) between two boxes
    
    Args:
        box1: (x1, y1, x2, y2) - first box
        box2: (x1, y1, x2, y2) - second box
        
    Returns:
        IoU ratio (0-1)
    """
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    # Calculate intersection
    inter_x1 = max(x1_1, x1_2)
    inter_y1 = max(y1_1, y1_2)
    inter_x2 = min(x2_1, x2_2)
    inter_y2 = min(y2_1, y2_2)
    
    # Check if there's intersection
    if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
        return 0.0
    
    # Calculate areas
    intersection_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
    box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
    union_area = box1_area + box2_area - intersection_area
    
    # Return IoU
    return intersection_area / union_area if union_area > 0 else 0.0

def calculate_box_overlap_with_slot(vehicle_box: Tuple[int, int, int, int],
                                   slot_position: Tuple[int, int],
                                   slot_width: int, slot_height: int) -> float:
    """
    Calculate overlap ratio between vehicle box and parking slot
    
    Args:
        vehicle_box: (x1, y1, x2, y2) - vehicle detection box
        slot_position: (x, y) - parking slot top-left corner
        slot_width: Width of parking slot
        slot_height: Height of parking slot
        
    Returns:
        Overlap ratio (0-1)
    """
    # Convert slot to bounding box
    slot_x, slot_y = slot_position
    slot_box = (slot_x, slot_y, slot_x + slot_width, slot_y + slot_height)
    
    # Calculate intersection with slot area as reference
    veh_x1, veh_y1, veh_x2, veh_y2 = vehicle_box
    
    inter_x1 = max(veh_x1, slot_x)
    inter_y1 = max(veh_y1, slot_y)
    inter_x2 = min(veh_x2, slot_x + slot_width)
    inter_y2 = min(veh_y2, slot_y + slot_height)
    
    if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
        return 0.0
    
    intersection_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    slot_area = slot_width * slot_height
    
    return intersection_area / slot_area if slot_area > 0 else 0.0

def resize_frame_if_needed(frame, max_width: int = 1920, max_height: int = 1080):
    """
    Resize frame if it's too large for display
    
    Args:
        frame: Input frame
        max_width: Maximum width
        max_height: Maximum height
        
    Returns:
        Resized frame and scale factor
    """
    height, width = frame.shape[:2]
    
    if width <= max_width and height <= max_height:
        return frame, 1.0
    
    # Calculate scale factor
    width_scale = max_width / width
    height_scale = max_height / height
    scale = min(width_scale, height_scale)
    
    # Resize frame
    new_width = int(width * scale)
    new_height = int(height * scale)
    resized_frame = cv2.resize(frame, (new_width, new_height))
    
    logger.info(f"Resized frame from {width}x{height} to {new_width}x{new_height} (scale: {scale:.2f})")
    return resized_frame, scale

def create_video_writer(output_path: str, fps: int, width: int, height: int, 
                       fourcc_code: str = 'mp4v') -> cv2.VideoWriter:
    """
    Create video writer with proper codec
    
    Args:
        output_path: Output video file path
        fps: Frames per second
        width: Video width
        height: Video height
        fourcc_code: Video codec code
        
    Returns:
        VideoWriter object
    """
    fourcc = cv2.VideoWriter_fourcc(*fourcc_code)
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    if not writer.isOpened():
        raise RuntimeError(f"Failed to create video writer for {output_path}")
    
    logger.info(f"Created video writer: {output_path} ({width}x{height}, {fps}fps)")
    return writer

def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        directory_path: Path to directory
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path, exist_ok=True)
        logger.info(f"Created directory: {directory_path}")

class PerformanceTimer:
    """Simple performance timing utility"""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            logger.info(f"{self.name} completed in {duration:.2f} seconds")

def log_system_info():
    """Log system information for debugging"""
    import platform
    import cv2 as cv_version
    
    logger.info("=== System Information ===")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Python: {platform.python_version()}")
    logger.info(f"OpenCV: {cv_version.__version__}")
    
    try:
        from ultralytics import __version__ as yolo_version
        logger.info(f"Ultralytics: {yolo_version}")
    except ImportError:
        logger.warning("Ultralytics not available")
    
    logger.info("==========================")
