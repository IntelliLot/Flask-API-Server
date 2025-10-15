"""
Visualization and UI rendering for parking detection system
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
import logging

from ..config.settings import CONFIG

logger = logging.getLogger(__name__)

class ParkingVisualizer:
    """Handles all visualization aspects of the parking detection system"""
    
    def __init__(self, config: Optional[any] = None):
        """
        Initialize the visualizer
        
        Args:
            config: UI configuration (uses global config if None)
        """
        self.config = config or CONFIG.ui
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        
        # UI element dimensions (calculated dynamically based on frame size)
        self.frame_width = 0
        self.frame_height = 0
        
    def set_frame_dimensions(self, width: int, height: int):
        """Set frame dimensions for proper UI scaling"""
        self.frame_width = width
        self.frame_height = height
        
    def draw_parking_slots(self, frame: np.ndarray, 
                          parking_positions: List[Tuple[int, int]],
                          occupancy: List[bool],
                          slot_dimensions: List[Tuple[int, int]] = None,
                          slot_width: int = None, slot_height: int = None) -> np.ndarray:
        """
        Draw parking slot rectangles on the frame
        
        Args:
            frame: Input frame
            parking_positions: List of (x, y) parking slot positions
            occupancy: List of occupancy status for each slot
            slot_dimensions: List of (width, height) for each slot (optional, per-slot sizing)
            slot_width: Default width for all slots (used if slot_dimensions not provided)
            slot_height: Default height for all slots (used if slot_dimensions not provided)
            
        Returns:
            Frame with parking slots drawn
        """
        for i, ((x, y), is_occupied) in enumerate(zip(parking_positions, occupancy)):
            # Get slot-specific dimensions
            if slot_dimensions:
                w, h = slot_dimensions[i]
            else:
                w, h = slot_width, slot_height
            
            # Choose color and thickness based on occupancy
            if is_occupied:
                color = self.config.occupied_color
                thickness = 3
            else:
                color = self.config.empty_color
                thickness = 2
            
            # Draw parking slot rectangle
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)
            
            # Add slot number
            text_position = (x + 5, y + 15)
            cv2.putText(frame, str(i + 1), text_position, 
                       self.font, 0.4, self.config.text_color, 1)
        
        return frame
    
    def draw_vehicle_detections(self, frame: np.ndarray, 
                              detections: List[Tuple[int, int, int, int, float, str]]) -> np.ndarray:
        """
        Draw vehicle detection bounding boxes
        
        Args:
            frame: Input frame
            detections: List of vehicle detections
            
        Returns:
            Frame with vehicle detections drawn
        """
        for detection in detections:
            x1, y1, x2, y2, confidence, class_name = detection
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), self.config.vehicle_color, 2)
            
            # Add label with confidence
            label = f"{class_name} {confidence:.2f}"
            label_size = cv2.getTextSize(label, self.font, 0.5, 2)[0]
            
            # Draw label background
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), self.config.vehicle_color, -1)
            
            # Draw label text
            cv2.putText(frame, label, (x1, y1 - 5), 
                       self.font, 0.5, self.config.text_color, 2)
        
        return frame
    
    def draw_statistics_panel(self, frame: np.ndarray, 
                            statistics: Dict[str, any],
                            vehicle_count: int) -> np.ndarray:
        """
        Draw statistics panel on the frame
        
        Args:
            frame: Input frame
            statistics: Parking statistics dictionary
            vehicle_count: Number of detected vehicles
            
        Returns:
            Frame with statistics panel drawn
        """
        panel_x, panel_y = self.config.stats_panel_position
        panel_w, panel_h = self.config.stats_panel_size
        
        # Draw panel background
        cv2.rectangle(frame, (panel_x, panel_y), 
                     (panel_x + panel_w, panel_y + panel_h), 
                     self.config.panel_color, -1)
        cv2.rectangle(frame, (panel_x, panel_y), 
                     (panel_x + panel_w, panel_y + panel_h), 
                     self.config.text_color, 2)
        
        # Prepare statistics text
        stats_lines = [
            "YOLOv8 Parking Detection System",
            f"Total Parking Slots: {statistics.get('total_slots', 0)}",
            f"Occupied Slots: {statistics.get('occupied_slots', 0)}",
            f"Empty Slots: {statistics.get('empty_slots', 0)}",
            f"Occupancy Rate: {statistics.get('occupancy_rate', 0.0):.1f}%",
            f"Vehicles Detected: {vehicle_count}"
        ]
        
        # Draw statistics text
        for i, text in enumerate(stats_lines):
            font_size = 0.7 if i == 0 else 0.6
            font_weight = 2 if i == 0 else 1
            color = (0, 255, 255) if i == 0 else self.config.text_color  # Yellow title
            
            y_position = panel_y + 25 + i * 20
            cv2.putText(frame, text, (panel_x + 10, y_position),
                       self.font, font_size, color, font_weight)
        
        return frame
    
    def draw_legend(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw legend explaining the color coding
        
        Args:
            frame: Input frame
            
        Returns:
            Frame with legend drawn
        """
        if self.frame_height == 0:
            return frame
        
        legend_height = self.config.legend_panel_height
        legend_y = self.frame_height - legend_height - 10
        legend_width = 350
        legend_x = 10
        
        # Draw legend background
        cv2.rectangle(frame, (legend_x, legend_y), 
                     (legend_x + legend_width, legend_y + legend_height), 
                     self.config.panel_color, -1)
        cv2.rectangle(frame, (legend_x, legend_y), 
                     (legend_x + legend_width, legend_y + legend_height), 
                     self.config.text_color, 2)
        
        # Legend title
        cv2.putText(frame, "Legend:", (legend_x + 10, legend_y + 20),
                   self.font, 0.6, self.config.text_color, 2)
        
        # Occupied slot indicator
        occupied_rect_start = (legend_x + 10, legend_y + 30)
        occupied_rect_end = (legend_x + 30, legend_y + 45)
        cv2.rectangle(frame, occupied_rect_start, occupied_rect_end, 
                     self.config.occupied_color, -1)
        cv2.putText(frame, "Occupied Slot", (legend_x + 40, legend_y + 42),
                   self.font, 0.5, self.config.text_color, 1)
        
        # Empty slot indicator
        empty_rect_start = (legend_x + 10, legend_y + 55)
        empty_rect_end = (legend_x + 30, legend_y + 70)
        cv2.rectangle(frame, empty_rect_start, empty_rect_end, 
                     self.config.empty_color, -1)
        cv2.putText(frame, "Empty Slot", (legend_x + 40, legend_y + 67),
                   self.font, 0.5, self.config.text_color, 1)
        
        # Vehicle detection indicator
        vehicle_rect_start = (legend_x + 180, legend_y + 30)
        vehicle_rect_end = (legend_x + 200, legend_y + 45)
        cv2.rectangle(frame, vehicle_rect_start, vehicle_rect_end, 
                     self.config.vehicle_color, 2)
        cv2.putText(frame, "Vehicle Detection", (legend_x + 210, legend_y + 42),
                   self.font, 0.5, self.config.text_color, 1)
        
        return frame
    
    def create_annotated_frame(self, frame: np.ndarray,
                             parking_positions: List[Tuple[int, int]],
                             occupancy: List[bool],
                             vehicle_detections: List[Tuple[int, int, int, int, float, str]],
                             statistics: Dict[str, any],
                             slot_dimensions: List[Tuple[int, int]] = None,
                             slot_width: int = None, slot_height: int = None) -> np.ndarray:
        """
        Create a fully annotated frame with all visualizations
        
        Args:
            frame: Input frame
            parking_positions: List of parking slot positions
            occupancy: List of occupancy status
            vehicle_detections: List of vehicle detections
            statistics: Parking statistics
            slot_dimensions: List of (width, height) for each slot (optional, per-slot sizing)
            slot_width: Default width of parking slots (fallback)
            slot_height: Default height of parking slots (fallback)
            
        Returns:
            Fully annotated frame
        """
        # Set frame dimensions for proper UI scaling
        self.set_frame_dimensions(frame.shape[1], frame.shape[0])
        
        # Create a copy to avoid modifying the original
        annotated_frame = frame.copy()
        
        # Draw parking slots
        annotated_frame = self.draw_parking_slots(
            annotated_frame, parking_positions, occupancy, 
            slot_dimensions=slot_dimensions,
            slot_width=slot_width, slot_height=slot_height
        )
        
        # Draw vehicle detections
        annotated_frame = self.draw_vehicle_detections(
            annotated_frame, vehicle_detections
        )
        
        # Draw statistics panel
        annotated_frame = self.draw_statistics_panel(
            annotated_frame, statistics, len(vehicle_detections)
        )
        
        # Draw legend
        annotated_frame = self.draw_legend(annotated_frame)
        
        return annotated_frame
    
    def add_performance_info(self, frame: np.ndarray, 
                           fps: float, processing_time: float) -> np.ndarray:
        """
        Add performance information to the frame
        
        Args:
            frame: Input frame
            fps: Current FPS
            processing_time: Frame processing time in seconds
            
        Returns:
            Frame with performance info added
        """
        if not CONFIG.debug:
            return frame
        
        # Performance info position (top right)
        info_x = frame.shape[1] - 200
        info_y = 30
        
        # Performance text
        perf_lines = [
            f"FPS: {fps:.1f}",
            f"Process: {processing_time*1000:.1f}ms"
        ]
        
        # Draw background
        bg_height = len(perf_lines) * 25 + 10
        cv2.rectangle(frame, (info_x - 5, info_y - 20), 
                     (frame.shape[1] - 5, info_y + bg_height), 
                     (0, 0, 0), -1)
        
        # Draw performance text
        for i, text in enumerate(perf_lines):
            cv2.putText(frame, text, (info_x, info_y + i * 25),
                       self.font, 0.5, (0, 255, 0), 1)  # Green text
        
        return frame
    
    def create_thumbnail(self, frame: np.ndarray, 
                        max_width: int = 320, max_height: int = 240) -> np.ndarray:
        """
        Create a thumbnail version of the frame
        
        Args:
            frame: Input frame
            max_width: Maximum thumbnail width
            max_height: Maximum thumbnail height
            
        Returns:
            Thumbnail image
        """
        height, width = frame.shape[:2]
        
        # Calculate scale factor
        scale_width = max_width / width
        scale_height = max_height / height
        scale = min(scale_width, scale_height)
        
        # Calculate new dimensions
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        # Resize frame
        thumbnail = cv2.resize(frame, (new_width, new_height))
        
        return thumbnail
