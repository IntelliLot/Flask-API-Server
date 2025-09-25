"""
Main YOLOv8 Parking Detection System Application
"""

import cv2
import logging
import time
from datetime import datetime
from typing import Optional, Callable
import os

from .vehicle_detector import VehicleDetector
from .parking_manager import ParkingManager
from .visualizer import ParkingVisualizer
from ..config.settings import CONFIG
from ..utils.helpers import (
    generate_timestamp_filename, 
    create_video_writer, 
    PerformanceTimer,
    log_system_info
)

logger = logging.getLogger(__name__)

class ParkingDetectionSystem:
    """
    Main application class that orchestrates the entire parking detection system
    """
    
    def __init__(self, 
                 model_path: Optional[str] = None,
                 parking_positions_file: Optional[str] = None):
        """
        Initialize the parking detection system
        
        Args:
            model_path: Path to YOLOv8 model (optional)
            parking_positions_file: Path to parking positions file (optional)
        """
        logger.info("🚀 Initializing YOLOv8 Parking Detection System")
        
        if CONFIG.verbose_logging:
            log_system_info()
        
        # Initialize components
        self.vehicle_detector = VehicleDetector(model_path)
        self.parking_manager = ParkingManager(parking_positions_file)
        self.visualizer = ParkingVisualizer()
        
        # Video processing state
        self.video_capture = None
        self.video_writer = None
        self.total_frames = 0
        self.processed_frames = 0
        
        # Performance tracking
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0.0
        
        logger.info("✅ System initialization complete")
    
    def load_video(self, video_path: str) -> bool:
        """
        Load video file for processing
        
        Args:
            video_path: Path to video file
            
        Returns:
            True if video loaded successfully
        """
        try:
            if self.video_capture:
                self.video_capture.release()
            
            self.video_capture = cv2.VideoCapture(video_path)
            
            if not self.video_capture.isOpened():
                logger.error(f"❌ Failed to open video: {video_path}")
                return False
            
            # Get video properties
            self.fps = int(self.video_capture.get(cv2.CAP_PROP_FPS))
            self.width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            
            logger.info(f"📹 Video loaded: {video_path}")
            logger.info(f"   Properties: {self.width}x{self.height}, {self.fps}fps, {self.total_frames} frames")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading video: {e}")
            return False
    
    def load_camera(self, camera_index: int = 0) -> bool:
        """
        Initialize camera for live feed processing
        
        Args:
            camera_index: Camera device index (default: 0 for primary camera)
            
        Returns:
            True if camera initialized successfully
        """
        try:
            if self.video_capture:
                self.video_capture.release()
            
            self.video_capture = cv2.VideoCapture(camera_index)
            
            if not self.video_capture.isOpened():
                logger.error(f"❌ Failed to open camera with index: {camera_index}")
                return False
            
            # Set camera properties for optimal performance
            self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.video_capture.set(cv2.CAP_PROP_FPS, 30)
            
            # Get actual camera properties
            self.fps = int(self.video_capture.get(cv2.CAP_PROP_FPS))
            self.width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.total_frames = -1  # Infinite for camera feed
            
            logger.info(f"📷 Camera initialized: index {camera_index}")
            logger.info(f"   Properties: {self.width}x{self.height}, {self.fps}fps")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing camera: {e}")
            return False
    
    def process_frame(self, frame) -> tuple:
        """
        Process a single frame for parking detection
        
        Args:
            frame: Input video frame
            
        Returns:
            Tuple of (annotated_frame, occupancy_stats, processing_time)
        """
        start_time = time.time()
        
        # Detect vehicles
        vehicle_detections = self.vehicle_detector.detect_vehicles(frame)
        
        # Detect parking occupancy
        occupancy = self.parking_manager.detect_occupancy(vehicle_detections)
        
        # Get statistics
        statistics = self.parking_manager.get_occupancy_statistics(occupancy)
        
        # Create annotated frame
        annotated_frame = self.visualizer.create_annotated_frame(
            frame=frame,
            parking_positions=self.parking_manager.parking_positions,
            occupancy=occupancy,
            vehicle_detections=vehicle_detections,
            statistics=statistics,
            slot_width=self.parking_manager.slot_width,
            slot_height=self.parking_manager.slot_height
        )
        
        processing_time = time.time() - start_time
        
        # Add performance info if in debug mode
        if CONFIG.debug:
            annotated_frame = self.visualizer.add_performance_info(
                annotated_frame, self.current_fps, processing_time
            )
        
        return annotated_frame, statistics, processing_time
    
    def process_video_to_file(self, 
                            input_video_path: str, 
                            output_video_path: Optional[str] = None,
                            progress_callback: Optional[Callable] = None) -> str:
        """
        Process entire video and save to output file
        
        Args:
            input_video_path: Path to input video
            output_video_path: Path for output video (auto-generated if None)
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Path to output video file
        """
        if not self.load_video(input_video_path):
            raise RuntimeError("Failed to load input video")
        
        # Generate output path if not provided
        if output_video_path is None:
            output_video_path = os.path.join(
                CONFIG.video.output_dir,
                generate_timestamp_filename("yolo_parking_detection", "mp4")
            )
        
        logger.info(f"🎬 Processing video to file: {output_video_path}")
        
        # Create video writer
        self.video_writer = create_video_writer(
            output_video_path, self.fps, self.width, self.height, CONFIG.video.output_format
        )
        
        # Processing statistics
        total_occupied = 0
        total_empty = 0
        total_vehicles = 0
        frame_count = 0
        
        try:
            with PerformanceTimer("Video Processing"):
                while True:
                    ret, frame = self.video_capture.read()
                    if not ret:
                        break
                    
                    frame_count += 1
                    self.processed_frames = frame_count
                    
                    # Process frame
                    annotated_frame, statistics, _ = self.process_frame(frame)
                    
                    # Write frame to output
                    self.video_writer.write(annotated_frame)
                    
                    # Update statistics
                    total_occupied += statistics.get('occupied_slots', 0)
                    total_empty += statistics.get('empty_slots', 0)
                    total_vehicles += len(self.vehicle_detector.detect_vehicles(frame))
                    
                    # Progress reporting
                    if frame_count % 50 == 0 or frame_count == self.total_frames:
                        progress = (frame_count / self.total_frames) * 100
                        logger.info(f"  Progress: {progress:.1f}% ({frame_count}/{self.total_frames})")
                        
                        if progress_callback:
                            progress_callback(frame_count, self.total_frames, progress)
                    
                    # Update FPS counter
                    self._update_fps_counter()
        
        finally:
            # Cleanup
            self._cleanup_video_resources()
        
        # Generate final report
        self._generate_processing_report(
            output_video_path, frame_count, total_occupied, total_empty, total_vehicles
        )
        
        return output_video_path
    
    def process_video_realtime(self, 
                             input_video_path: str,
                             display_window_name: str = "YOLOv8 Parking Detection") -> None:
        """
        Process video in real-time with display
        
        Args:
            input_video_path: Path to input video
            display_window_name: Name of display window
        """
        if not self.load_video(input_video_path):
            raise RuntimeError("Failed to load input video")
        
        logger.info("🎬 Starting real-time video processing")
        logger.info("Press 'q' to quit, 's' to save current frame, 'p' to pause")
        
        frame_count = 0
        saved_frames = 0
        paused = False
        
        try:
            while True:
                if not paused:
                    ret, frame = self.video_capture.read()
                    if not ret:
                        # Loop video
                        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    
                    frame_count += 1
                    self.processed_frames = frame_count
                    
                    # Process frame
                    annotated_frame, statistics, _ = self.process_frame(frame)
                
                # Display frame
                cv2.imshow(display_window_name, annotated_frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    logger.info("🛑 Stopping video processing...")
                    break
                elif key == ord('s'):
                    # Save current frame
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = os.path.join(CONFIG.video.output_dir, f"frame_save_{timestamp}.jpg")
                    cv2.imwrite(save_path, annotated_frame)
                    saved_frames += 1
                    logger.info(f"💾 Frame saved: {save_path}")
                elif key == ord('p'):
                    paused = not paused
                    logger.info(f"⏸️ Playback {'paused' if paused else 'resumed'}")
                
                # Print statistics periodically
                if not paused and frame_count % CONFIG.video.save_frames_interval == 0:
                    occupied = statistics.get('occupied_slots', 0)
                    total_slots = statistics.get('total_slots', 0)
                    occupancy_rate = statistics.get('occupancy_rate', 0.0)
                    vehicle_count = len(self.vehicle_detector.detect_vehicles(frame))
                    
                    logger.info(f"Frame {frame_count}: {occupied}/{total_slots} occupied "
                              f"({occupancy_rate:.1f}%), {vehicle_count} vehicles detected")
                
                # Update FPS counter
                self._update_fps_counter()
        
        finally:
            # Cleanup
            cv2.destroyAllWindows()
            self._cleanup_video_resources()
        
        logger.info(f"✅ Real-time processing completed. {saved_frames} frames saved.")
    
    def process_camera_realtime(self, 
                               camera_index: int = 0,
                               display_window_name: str = "YOLOv8 Parking Detection - Live Camera") -> None:
        """
        Process live camera feed in real-time with display
        
        Args:
            camera_index: Camera device index (default: 0 for primary camera)
            display_window_name: Name of display window
        """
        if not self.load_camera(camera_index):
            raise RuntimeError(f"Failed to initialize camera with index: {camera_index}")
        
        logger.info("📷 Starting live camera processing")
        logger.info("Press 'q' to quit, 's' to save current frame, 'p' to pause, 'r' to record")
        
        frame_count = 0
        saved_frames = 0
        paused = False
        recording = False
        video_writer = None
        
        try:
            while True:
                if not paused:
                    ret, frame = self.video_capture.read()
                    if not ret:
                        logger.warning("⚠️ Failed to read from camera")
                        continue
                    
                    frame_count += 1
                    self.processed_frames = frame_count
                    
                    # Process frame
                    annotated_frame, statistics, _ = self.process_frame(frame)
                    
                    # Record if enabled
                    if recording and video_writer is not None:
                        video_writer.write(annotated_frame)
                
                # Display frame
                cv2.imshow(display_window_name, annotated_frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    logger.info("🛑 Stopping camera processing...")
                    break
                elif key == ord('s'):
                    # Save current frame
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = os.path.join(CONFIG.video.output_dir, f"camera_frame_{timestamp}.jpg")
                    cv2.imwrite(save_path, annotated_frame)
                    saved_frames += 1
                    logger.info(f"💾 Frame saved: {save_path}")
                elif key == ord('p'):
                    paused = not paused
                    logger.info(f"⏸️ Camera {'paused' if paused else 'resumed'}")
                elif key == ord('r'):
                    if not recording:
                        # Start recording
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        record_path = os.path.join(CONFIG.video.output_dir, f"camera_recording_{timestamp}.mp4")
                        video_writer = create_video_writer(record_path, self.fps, self.width, self.height, CONFIG.video.output_format)
                        recording = True
                        logger.info(f"🎬 Started recording: {record_path}")
                    else:
                        # Stop recording
                        if video_writer:
                            video_writer.release()
                            video_writer = None
                        recording = False
                        logger.info("⏹️ Stopped recording")
                
                # Print statistics periodically
                if not paused and frame_count % CONFIG.video.save_frames_interval == 0:
                    occupied = statistics.get('occupied_slots', 0)
                    total_slots = statistics.get('total_slots', 0)
                    occupancy_rate = statistics.get('occupancy_rate', 0.0)
                    vehicle_count = len(self.vehicle_detector.detect_vehicles(frame))
                    
                    logger.info(f"Frame {frame_count}: {occupied}/{total_slots} occupied "
                              f"({occupancy_rate:.1f}%), {vehicle_count} vehicles detected")
                
                # Update FPS counter
                self._update_fps_counter()
        
        finally:
            # Cleanup
            if video_writer:
                video_writer.release()
            cv2.destroyAllWindows()
            self._cleanup_video_resources()
        
        logger.info(f"✅ Live camera processing completed. {saved_frames} frames saved.")
    
    def process_single_image(self, image_path: str, output_path: Optional[str] = None) -> str:
        """
        Process a single image
        
        Args:
            image_path: Path to input image
            output_path: Path for output image (auto-generated if None)
            
        Returns:
            Path to output image
        """
        # Load image
        frame = cv2.imread(image_path)
        if frame is None:
            raise RuntimeError(f"Failed to load image: {image_path}")
        
        logger.info(f"🖼️ Processing image: {image_path}")
        logger.info(f"   Dimensions: {frame.shape[1]}x{frame.shape[0]}")
        
        # Process frame
        annotated_frame, statistics, processing_time = self.process_frame(frame)
        
        # Generate output path if not provided
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            output_path = os.path.join(
                CONFIG.video.output_dir,
                f"{base_name}_parking_detection.jpg"
            )
        
        # Save result
        cv2.imwrite(output_path, annotated_frame)
        
        # Log results
        logger.info("="*60)
        logger.info("📊 SINGLE IMAGE PROCESSING COMPLETED")
        logger.info("="*60)
        logger.info(f"✅ Processing time: {processing_time*1000:.1f}ms")
        logger.info(f"🚗 Vehicles detected: {len(self.vehicle_detector.detect_vehicles(frame))}")
        logger.info(f"🅿️ Total parking slots: {statistics.get('total_slots', 0)}")
        logger.info(f"📈 Occupied slots: {statistics.get('occupied_slots', 0)}")
        logger.info(f"📉 Empty slots: {statistics.get('empty_slots', 0)}")
        logger.info(f"📊 Occupancy rate: {statistics.get('occupancy_rate', 0.0):.1f}%")
        logger.info(f"💾 Output saved: {output_path}")
        logger.info("="*60)
        
        return output_path
    
    def _update_fps_counter(self):
        """Update FPS counter"""
        self.fps_counter += 1
        current_time = time.time()
        
        if current_time - self.fps_start_time >= 1.0:
            self.current_fps = self.fps_counter / (current_time - self.fps_start_time)
            self.fps_counter = 0
            self.fps_start_time = current_time
    
    def _cleanup_video_resources(self):
        """Clean up video resources"""
        if hasattr(self, 'video_capture') and self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        
        if hasattr(self, 'video_writer') and self.video_writer:
            self.video_writer.release()
            self.video_writer = None
    
    def _generate_processing_report(self, output_path: str, frame_count: int,
                                   total_occupied: int, total_empty: int, 
                                   total_vehicles: int):
        """Generate final processing report"""
        avg_occupied = total_occupied / frame_count if frame_count > 0 else 0
        avg_empty = total_empty / frame_count if frame_count > 0 else 0
        avg_vehicles = total_vehicles / frame_count if frame_count > 0 else 0
        avg_occupancy_rate = (avg_occupied / (avg_occupied + avg_empty)) * 100 if (avg_occupied + avg_empty) > 0 else 0
        
        logger.info("\n" + "="*60)
        logger.info("📊 VIDEO PROCESSING COMPLETED")
        logger.info("="*60)
        logger.info(f"✅ Total frames processed: {frame_count}")
        logger.info(f"🅿️ Total parking slots: {self.parking_manager.total_slots}")
        logger.info(f"📈 Average occupied slots: {avg_occupied:.1f}")
        logger.info(f"📉 Average empty slots: {avg_empty:.1f}")
        logger.info(f"🚗 Average vehicles detected: {avg_vehicles:.1f}")
        logger.info(f"📊 Average occupancy rate: {avg_occupancy_rate:.1f}%")
        logger.info(f"💾 Output saved: {output_path}")
        logger.info("="*60)
    
    def get_system_status(self) -> dict:
        """Get current system status"""
        return {
            "vehicle_detector": str(self.vehicle_detector),
            "parking_manager": str(self.parking_manager),
            "processed_frames": self.processed_frames,
            "current_fps": self.current_fps,
            "total_frames": self.total_frames
        }
    
    def __del__(self):
        """Cleanup on destruction"""
        self._cleanup_video_resources()
