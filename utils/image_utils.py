"""
Image utilities for decoding and processing images
"""

import base64
import logging
import cv2
import numpy as np

logger = logging.getLogger(__name__)


def decode_image(image_data):
    """
    Decode image from base64 string or bytes
    
    Args:
        image_data: Base64 string, data URL, or bytes
    
    Returns:
        OpenCV image (numpy array)
    
    Raises:
        ValueError: If image cannot be decoded
    """
    try:
        if isinstance(image_data, str):
            # Remove data URL prefix if present
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
        elif isinstance(image_data, bytes):
            # Direct bytes
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
        else:
            raise ValueError("Unsupported image format. Expected base64 string or bytes")
        
        if image is None:
            raise ValueError("Failed to decode image. Image may be corrupted")
        
        return image
        
    except Exception as e:
        logger.error(f"Error decoding image: {e}")
        raise ValueError(f"Image decoding failed: {str(e)}")


def encode_image_to_base64(image, format='.jpg', quality=90) -> str:
    """
    Encode OpenCV image to base64 string
    
    Args:
        image: OpenCV image (numpy array)
        format: Image format ('.jpg', '.png', etc.)
        quality: JPEG quality (0-100)
    
    Returns:
        Base64 encoded string
    """
    try:
        if format == '.jpg':
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        else:
            encode_param = []
        
        _, buffer = cv2.imencode(format, image, encode_param)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return f"data:image/{format[1:]};base64,{image_base64}"
        
    except Exception as e:
        logger.error(f"Error encoding image: {e}")
        raise ValueError(f"Image encoding failed: {str(e)}")


def validate_coordinates(coordinates) -> bool:
    """
    Validate parking slot coordinates format
    
    Args:
        coordinates: List of coordinate arrays
    
    Returns:
        True if valid, raises ValueError if invalid
    """
    if not isinstance(coordinates, list):
        raise ValueError("Coordinates must be a list")
    
    if len(coordinates) == 0:
        raise ValueError("Coordinates list cannot be empty")
    
    for i, coord in enumerate(coordinates):
        if not isinstance(coord, (list, tuple)):
            raise ValueError(f"Coordinate {i} must be a list or tuple")
        
        if len(coord) != 4:
            raise ValueError(f"Coordinate {i} must have 4 values [x1, y1, x2, y2], got {len(coord)}")
        
        x1, y1, x2, y2 = coord
        
        if x2 <= x1:
            raise ValueError(f"Coordinate {i}: x2 must be greater than x1")
        
        if y2 <= y1:
            raise ValueError(f"Coordinate {i}: y2 must be greater than y1")
    
    return True


def get_image_dimensions(image) -> dict:
    """
    Get image dimensions
    
    Args:
        image: OpenCV image
    
    Returns:
        Dict with width and height
    """
    height, width = image.shape[:2]
    return {'width': width, 'height': height}
