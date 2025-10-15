"""
Vehicle detection module using YOLOv8
"""

import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Tuple, Optional
import logging

from ..config.settings import CONFIG
from ..utils.helpers import PerformanceTimer

logger = logging.getLogger(__name__)

class VehicleDetector:
    """YOLOv8-based vehicle detection system"""
    
    def __init__(self, model_path: Optional[str] = None, 
                 confidence_threshold: Optional[float] = None,
                 device: Optional[str] = None):
        """
        Initialize the vehicle detector
        
        Args:
            model_path: Path to YOLOv8 model (uses config default if None)
            confidence_threshold: Detection confidence threshold
            device: Device to run inference on ('cpu', 'cuda', or 'auto')
        """
        self.model_path = model_path or CONFIG.model.model_path
        self.confidence_threshold = confidence_threshold or CONFIG.model.confidence_threshold
        self.device = device or CONFIG.model.device
        
        logger.info(f"Initializing VehicleDetector with model: {self.model_path}")
        
        # Load YOLOv8 model
        try:
            self.model = YOLO(self.model_path)
            logger.info(f"✅ YOLOv8 model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load YOLOv8 model: {e}")
            raise
        
        # Vehicle class IDs (COCO dataset)
        self.vehicle_class_ids = {
            0: 'car',
            1: 'bicycle', 
            2: 'motorcycle',
            5: 'bus',
            7: 'truck'
        }
        
        # Primary focus on cars for parking detection
        self.primary_vehicle_classes = [0]  # Car only for better accuracy
        
    def detect_vehicles(self, frame: np.ndarray, 
                       include_all_vehicles: bool = False) -> List[Tuple[int, int, int, int, float, str]]:
        """
        Detect vehicles in the given frame
        
        Args:
            frame: Input image frame
            include_all_vehicles: If True, detect all vehicle types; if False, cars only
            
        Returns:
            List of detections: [(x1, y1, x2, y2, confidence, class_name), ...]
        """
        if CONFIG.debug:
            timer = PerformanceTimer("Vehicle Detection")
            timer.__enter__()
        
        try:
            # Run YOLOv8 inference
            results = self.model(frame, conf=self.confidence_threshold, verbose=False)
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extract box data
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # Filter for vehicles
                        if class_id in self.vehicle_class_ids:
                            class_name = self.vehicle_class_ids[class_id]
                            
                            # Apply vehicle type filtering
                            if include_all_vehicles or class_id in self.primary_vehicle_classes:
                                detections.append((
                                    int(x1), int(y1), int(x2), int(y2), 
                                    confidence, class_name
                                ))
            
            if CONFIG.debug:
                logger.debug(f"Detected {len(detections)} vehicles")
                timer.__exit__(None, None, None)
            
            return detections
            
        except Exception as e:
            logger.error(f"Error during vehicle detection: {e}")
            return []
    
    def get_detection_stats(self, detections: List[Tuple[int, int, int, int, float, str]]) -> dict:
        """
        Get statistics about detections
        
        Args:
            detections: List of vehicle detections
            
        Returns:
            Dictionary with detection statistics
        """
        stats = {
            'total_vehicles': len(detections),
            'vehicle_types': {},
            'average_confidence': 0.0,
            'confidence_range': (0.0, 0.0)
        }
        
        if detections:
            # Count vehicle types
            for detection in detections:
                vehicle_type = detection[5]  # class_name
                stats['vehicle_types'][vehicle_type] = stats['vehicle_types'].get(vehicle_type, 0) + 1
            
            # Calculate confidence statistics
            confidences = [det[4] for det in detections]
            stats['average_confidence'] = sum(confidences) / len(confidences)
            stats['confidence_range'] = (min(confidences), max(confidences))
        
        return stats
    
    def filter_detections_by_area(self, detections: List[Tuple[int, int, int, int, float, str]],
                                 min_area: int = 500, max_area: int = 50000) -> List[Tuple[int, int, int, int, float, str]]:
        """
        Filter detections by bounding box area
        
        Args:
            detections: List of vehicle detections
            min_area: Minimum bounding box area
            max_area: Maximum bounding box area
            
        Returns:
            Filtered list of detections
        """
        filtered = []
        for det in detections:
            x1, y1, x2, y2 = det[:4]
            area = (x2 - x1) * (y2 - y1)
            if min_area <= area <= max_area:
                filtered.append(det)
        
        if CONFIG.debug and len(filtered) != len(detections):
            logger.debug(f"Filtered {len(detections)} -> {len(filtered)} detections by area")
        
        return filtered
    
    def non_maximum_suppression(self, detections: List[Tuple[int, int, int, int, float, str]],
                               iou_threshold: float = 0.5) -> List[Tuple[int, int, int, int, float, str]]:
        """
        Apply non-maximum suppression to remove duplicate detections
        
        Args:
            detections: List of vehicle detections
            iou_threshold: IoU threshold for suppression
            
        Returns:
            Filtered list of detections
        """
        if len(detections) <= 1:
            return detections
        
        # Sort by confidence (descending)
        sorted_detections = sorted(detections, key=lambda x: x[4], reverse=True)
        
        keep = []
        while sorted_detections:
            # Take the detection with highest confidence
            current = sorted_detections.pop(0)
            keep.append(current)
            
            # Remove detections with high IoU
            remaining = []
            for det in sorted_detections:
                from ..utils.helpers import calculate_overlap_ratio
                iou = calculate_overlap_ratio(current[:4], det[:4])
                if iou < iou_threshold:
                    remaining.append(det)
            
            sorted_detections = remaining
        
        if CONFIG.debug and len(keep) != len(detections):
            logger.debug(f"NMS: {len(detections)} -> {len(keep)} detections")
        
        return keep
    
    def __str__(self) -> str:
        return f"VehicleDetector(model={self.model_path}, conf={self.confidence_threshold})"
