"""
Parking occupancy detection and management
"""

import logging
from typing import List, Tuple, Dict, Optional
import numpy as np

from ..config.settings import CONFIG
from ..utils.helpers import calculate_box_overlap_with_slot, load_parking_positions

logger = logging.getLogger(__name__)

class ParkingManager:
    """Manages parking slot detection and occupancy tracking"""
    
    def __init__(self, parking_positions_file: Optional[str] = None,
                 parking_positions: Optional[List] = None,
                 slot_width: Optional[int] = None, 
                 slot_height: Optional[int] = None,
                 occupancy_threshold: Optional[float] = None):
        """
        Initialize parking manager
        
        Args:
            parking_positions_file: Path to parking positions file (optional if positions provided)
            parking_positions: List of coordinates in one of two formats:
                - (x, y): Top-left corner only, uses slot_width/height
                - (x1, y1, x2, y2): Rectangle coordinates (top-left and bottom-right)
            slot_width: Default width for (x, y) format slots
            slot_height: Default height for (x, y) format slots
            occupancy_threshold: Overlap threshold to consider slot occupied
        """
        self.positions_file = parking_positions_file
        self.default_slot_width = slot_width or CONFIG.parking.slot_width
        self.default_slot_height = slot_height or CONFIG.parking.slot_height
        self.occupancy_threshold = occupancy_threshold or CONFIG.parking.occupancy_threshold
        
        # Load parking positions from provided list or file
        if parking_positions is not None:
            raw_positions = parking_positions
            logger.info(f"Loaded {len(raw_positions)} parking positions from provided coordinates")
        elif parking_positions_file:
            raw_positions = load_parking_positions(parking_positions_file)
        else:
            # Fallback to default config file
            self.positions_file = CONFIG.parking.parking_positions_file
            raw_positions = load_parking_positions(self.positions_file)
        
        # Process positions and detect format
        self._process_parking_positions(raw_positions)
        
        self.total_slots = len(self.parking_positions)
        
        logger.info(f"Initialized ParkingManager with {self.total_slots} slots")
        logger.info(f"Slot format: {'Rectangle (x1,y1,x2,y2)' if self.use_rectangles else 'Point (x,y) with dimensions'}")
        if not self.use_rectangles:
            logger.info(f"Default slot dimensions: {self.default_slot_width}x{self.default_slot_height}")
        logger.info(f"Occupancy threshold: {self.occupancy_threshold}")
        
        # Statistics tracking
        self.occupancy_history = []
        self.detection_history = []
    
    def _process_parking_positions(self, positions: List) -> None:
        """
        Process parking positions and determine format
        
        Supports two formats:
        1. (x, y) - top-left corner with default width/height
        2. (x1, y1, x2, y2) - rectangle with explicit boundaries
        """
        if not positions:
            raise ValueError("No parking positions provided")
        
        # Convert to list of tuples if needed
        positions = [tuple(p) if isinstance(p, list) else p for p in positions]
        
        # Detect format from first position
        first_pos = positions[0]
        if len(first_pos) == 2:
            # Format: (x, y) - will use default dimensions
            self.use_rectangles = False
            self.parking_positions = positions
            self.slot_dimensions = [(self.default_slot_width, self.default_slot_height)] * len(positions)
            logger.info(f"Detected format: Point (x, y) with fixed dimensions")
        elif len(first_pos) == 4:
            # Format: (x1, y1, x2, y2) - explicit rectangles
            self.use_rectangles = True
            self.parking_positions = [(p[0], p[1]) for p in positions]  # Store as (x, y) for compatibility
            self.slot_dimensions = [(p[2] - p[0], p[3] - p[1]) for p in positions]  # Calculate width, height
            logger.info(f"Detected format: Rectangle (x1, y1, x2, y2)")
            logger.info(f"Slot sizes range: {min(w for w, h in self.slot_dimensions)}x{min(h for w, h in self.slot_dimensions)} to {max(w for w, h in self.slot_dimensions)}x{max(h for w, h in self.slot_dimensions)}")
        else:
            raise ValueError(f"Invalid position format. Expected (x, y) or (x1, y1, x2, y2), got {len(first_pos)} values")
        
        # Add legacy properties for backward compatibility
        self.slot_width = self.default_slot_width
        self.slot_height = self.default_slot_height
    
    def detect_occupancy(self, vehicle_detections: List[Tuple[int, int, int, int, float, str]]) -> List[bool]:
        """
        Detect which parking slots are occupied based on vehicle detections
        
        Args:
            vehicle_detections: List of vehicle detection tuples
            
        Returns:
            List of boolean values indicating occupancy for each parking slot
        """
        occupancy = [False] * self.total_slots
        slot_overlaps = [0.0] * self.total_slots  # Track max overlap for each slot
        
        for i, parking_slot in enumerate(self.parking_positions):
            max_overlap = 0.0
            best_vehicle = None
            
            # Get slot-specific dimensions
            slot_w, slot_h = self.slot_dimensions[i]
            
            for j, vehicle in enumerate(vehicle_detections):
                vehicle_box = vehicle[:4]  # (x1, y1, x2, y2)
                overlap_ratio = calculate_box_overlap_with_slot(
                    vehicle_box, parking_slot, slot_w, slot_h
                )
                
                if overlap_ratio > max_overlap:
                    max_overlap = overlap_ratio
                    best_vehicle = j
                
                # If overlap exceeds threshold, mark as occupied
                if overlap_ratio > self.occupancy_threshold:
                    occupancy[i] = True
                    break
            
            slot_overlaps[i] = max_overlap
            
            if CONFIG.debug and max_overlap > 0.1:
                logger.debug(f"Slot {i+1}: overlap={max_overlap:.3f}, occupied={occupancy[i]}, size={slot_w}x{slot_h}")
        
        # Update statistics
        occupied_count = sum(occupancy)
        self.occupancy_history.append(occupied_count)
        self.detection_history.append(len(vehicle_detections))
        
        return occupancy
    
    def get_occupancy_statistics(self, occupancy: List[bool]) -> Dict[str, float]:
        """
        Calculate occupancy statistics
        
        Args:
            occupancy: List of slot occupancy status
            
        Returns:
            Dictionary with statistics
        """
        occupied_count = sum(occupancy)
        empty_count = self.total_slots - occupied_count
        occupancy_rate = (occupied_count / self.total_slots) * 100 if self.total_slots > 0 else 0.0
        
        stats = {
            'total_slots': self.total_slots,
            'occupied_slots': occupied_count,
            'empty_slots': empty_count,
            'occupancy_rate': occupancy_rate
        }
        
        # Add historical statistics if available
        if self.occupancy_history:
            stats['average_occupancy'] = sum(self.occupancy_history) / len(self.occupancy_history)
            stats['max_occupancy'] = max(self.occupancy_history)
            stats['min_occupancy'] = min(self.occupancy_history)
        
        if self.detection_history:
            stats['average_detections'] = sum(self.detection_history) / len(self.detection_history)
        
        return stats
    
    def get_slot_details(self, slot_index: int) -> Dict[str, any]:
        """
        Get detailed information about a specific parking slot
        
        Args:
            slot_index: Index of the parking slot
            
        Returns:
            Dictionary with slot details
        """
        if not (0 <= slot_index < self.total_slots):
            raise ValueError(f"Invalid slot index: {slot_index}")
        
        position = self.parking_positions[slot_index]
        
        return {
            'slot_id': slot_index + 1,
            'position': position,
            'bounds': {
                'x': position[0],
                'y': position[1],
                'width': self.slot_width,
                'height': self.slot_height
            },
            'area': self.slot_width * self.slot_height
        }
    
    def find_closest_vehicles(self, vehicle_detections: List[Tuple[int, int, int, int, float, str]], 
                            slot_index: int, max_distance: float = 100.0) -> List[Tuple[int, float]]:
        """
        Find vehicles closest to a specific parking slot
        
        Args:
            vehicle_detections: List of vehicle detections
            slot_index: Index of the parking slot
            max_distance: Maximum distance to consider
            
        Returns:
            List of (vehicle_index, distance) tuples, sorted by distance
        """
        if not (0 <= slot_index < self.total_slots):
            return []
        
        slot_position = self.parking_positions[slot_index]
        slot_center = (
            slot_position[0] + self.slot_width // 2,
            slot_position[1] + self.slot_height // 2
        )
        
        distances = []
        for i, vehicle in enumerate(vehicle_detections):
            x1, y1, x2, y2 = vehicle[:4]
            vehicle_center = ((x1 + x2) // 2, (y1 + y2) // 2)
            
            # Calculate Euclidean distance
            distance = np.sqrt(
                (vehicle_center[0] - slot_center[0]) ** 2 + 
                (vehicle_center[1] - slot_center[1]) ** 2
            )
            
            if distance <= max_distance:
                distances.append((i, distance))
        
        # Sort by distance
        distances.sort(key=lambda x: x[1])
        return distances
    
    def analyze_occupancy_patterns(self, window_size: int = 30) -> Dict[str, any]:
        """
        Analyze occupancy patterns over time
        
        Args:
            window_size: Size of analysis window
            
        Returns:
            Dictionary with pattern analysis
        """
        if len(self.occupancy_history) < window_size:
            return {"status": "insufficient_data", "frames_needed": window_size}
        
        recent_occupancy = self.occupancy_history[-window_size:]
        recent_detections = self.detection_history[-window_size:]
        
        analysis = {
            "window_size": window_size,
            "average_occupancy": sum(recent_occupancy) / len(recent_occupancy),
            "occupancy_std": np.std(recent_occupancy),
            "occupancy_trend": self._calculate_trend(recent_occupancy),
            "detection_stability": np.std(recent_detections),
            "peak_occupancy": max(recent_occupancy),
            "min_occupancy": min(recent_occupancy)
        }
        
        return analysis
    
    def _calculate_trend(self, data: List[float]) -> str:
        """Calculate trend direction from data"""
        if len(data) < 2:
            return "stable"
        
        # Simple linear trend calculation
        x = list(range(len(data)))
        slope = np.polyfit(x, data, 1)[0]
        
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    def reset_statistics(self):
        """Reset all tracking statistics"""
        self.occupancy_history.clear()
        self.detection_history.clear()
        logger.info("Parking statistics reset")
    
    def export_statistics(self) -> Dict[str, any]:
        """Export all statistics for external analysis"""
        return {
            "total_slots": self.total_slots,
            "slot_dimensions": {"width": self.slot_width, "height": self.slot_height},
            "occupancy_threshold": self.occupancy_threshold,
            "occupancy_history": self.occupancy_history.copy(),
            "detection_history": self.detection_history.copy(),
            "total_frames_processed": len(self.occupancy_history)
        }
    
    def __str__(self) -> str:
        return f"ParkingManager(slots={self.total_slots}, threshold={self.occupancy_threshold})"
