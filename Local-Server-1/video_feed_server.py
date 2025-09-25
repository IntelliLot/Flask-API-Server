#!/usr/bin/env python3
"""
Video Feed Server (Server I)
Simple server that captures frames from camera and sends them to a remote server.
Focus: Camera access → Frame capture → Transfer to remote server
"""

import cv2
import requests
import time
import logging
import os
from datetime import datetime
from io import BytesIO

class VideoFeedServer:
    def __init__(self, camera_index=0, remote_url="http://localhost:5000/upload", interval=5):
        self.camera_index = camera_index
        self.remote_url = remote_url
        self.capture_interval = interval
        self.cap = None
        
        # Simple logging setup
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('VideoFeedServer')
    
    def initialize_camera(self):
        """Initialize camera access with proper warm-up"""
        self.logger.info(f"Accessing camera {self.camera_index}...")
        
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            self.logger.error(f"Cannot access camera {self.camera_index}")
            return False
        
        # Set basic camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Camera warm-up: read and discard several frames to allow auto-adjustment
        self.logger.info("Warming up camera (allowing auto-exposure adjustment)...")
        for i in range(10):
            ret, frame = self.cap.read()
            if ret:
                self.logger.debug(f"Warm-up frame {i+1}/10 captured")
            time.sleep(0.2)  # 200ms between warm-up frames
        
        # Additional settling time for camera to fully adjust
        time.sleep(2)
        
        self.logger.info("Camera initialized successfully with warm-up period")
        return True
    
    def capture_frame(self):
        """Capture a single frame from camera with black frame detection"""
        if not self.cap or not self.cap.isOpened():
            return None
        
        # Try multiple times to get a non-black frame
        max_attempts = 5
        for attempt in range(max_attempts):
            ret, frame = self.cap.read()
            if not ret:
                self.logger.warning(f"Failed to capture frame (attempt {attempt + 1}/{max_attempts})")
                time.sleep(0.1)
                continue
            
            # Check if frame is mostly black (average pixel value below threshold)
            avg_brightness = frame.mean()
            if avg_brightness < 10:  # Very dark frame threshold
                self.logger.debug(f"Frame too dark (brightness: {avg_brightness:.1f}), retrying...")
                time.sleep(0.2)
                continue
            
            self.logger.debug(f"Good frame captured (brightness: {avg_brightness:.1f})")
            return frame
        
        self.logger.warning("Could not capture a good frame after multiple attempts")
        return None
    
    def frame_to_jpeg_bytes(self, frame):
        """Convert frame to JPEG bytes for transfer"""
        success, encoded_frame = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        
        if not success:
            return None
        
        return encoded_frame.tobytes()
    
    def save_frame_locally(self, frame_bytes, frame_number):
        """Save frame locally for verification"""
        try:
            # Create frames directory if it doesn't exist
            frames_dir = 'captured_frames'
            os.makedirs(frames_dir, exist_ok=True)
            
            # Create filename with timestamp and frame number
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"frame_{frame_number:03d}_{timestamp}.jpg"
            filepath = os.path.join(frames_dir, filename)
            
            # Save the frame
            with open(filepath, 'wb') as f:
                f.write(frame_bytes)
            
            self.logger.info(f"Frame saved locally: {filename} ({len(frame_bytes)} bytes)")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to save frame locally: {e}")
            return None
    
    def send_frame_to_server(self, frame_bytes):
        """Send frame to remote server via HTTP POST"""
        try:
            # Prepare the file for upload
            files = {
                'image': ('frame.jpg', BytesIO(frame_bytes), 'image/jpeg')
            }
            
            # Add timestamp and metadata
            data = {
                'timestamp': datetime.now().isoformat(),
                'camera_id': str(self.camera_index),
                'server_type': 'video_feed_server'
            }
            
            # Send POST request
            response = requests.post(
                self.remote_url,
                files=files,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("Frame sent successfully")
                return True
            else:
                self.logger.warning(f"Server responded with status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send frame: {e}")
            return False
    
    def run(self):
        """Main loop: capture frames and send to server"""
        if not self.initialize_camera():
            return
        
        self.logger.info(f"Starting video feed server...")
        self.logger.info(f"Camera: {self.camera_index}")
        self.logger.info(f"Remote Server: {self.remote_url}")
        self.logger.info(f"Capture Interval: {self.capture_interval} seconds")
        self.logger.info("Press Ctrl+C to stop")
        
        frame_count = 0
        
        try:
            while True:
                # Capture frame from camera
                frame = self.capture_frame()
                if frame is None:
                    self.logger.warning("No frame captured, retrying...")
                    time.sleep(1)
                    continue
                
                frame_count += 1
                self.logger.info(f"Captured frame #{frame_count}")
                
                # Convert frame to bytes
                frame_bytes = self.frame_to_jpeg_bytes(frame)
                if frame_bytes is None:
                    self.logger.warning("Failed to encode frame")
                    continue
                
                # Save frame locally for verification
                saved_path = self.save_frame_locally(frame_bytes, frame_count)
                
                # Send frame to remote server
                success = self.send_frame_to_server(frame_bytes)
                
                if success:
                    self.logger.info(f"Frame #{frame_count} transferred successfully ({len(frame_bytes)} bytes)")
                    if saved_path:
                        self.logger.info(f"✅ Frame also saved locally: {saved_path}")
                else:
                    self.logger.warning(f"Failed to transfer frame #{frame_count}")
                    if saved_path:
                        self.logger.info(f"📁 Frame saved locally for backup: {saved_path}")
                
                # Wait for next capture
                time.sleep(self.capture_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Stopping video feed server...")
        
        finally:
            if self.cap:
                self.cap.release()
                self.logger.info("Camera released")

def main():
    """Main entry point"""
    print("=== VIDEO FEED SERVER (SERVER I) ===")
    print("Simple camera capture and frame transfer service")
    print()
    
    # Configuration
    camera_index = int(os.getenv('CAMERA_INDEX', 0))
    remote_url = os.getenv('REMOTE_SERVER_URL', 'http://localhost:5000/upload')
    interval = int(os.getenv('CAPTURE_INTERVAL', 5))
    
    print(f"Camera: {camera_index}")
    print(f"Remote Server: {remote_url}")
    print(f"Interval: {interval} seconds")
    print()
    
    # Create and run server
    server = VideoFeedServer(camera_index, remote_url, interval)
    server.run()

if __name__ == "__main__":
    main()