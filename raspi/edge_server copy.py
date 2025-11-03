#!/usr/bin/env python3
"""
Edge Server for Raspberry Pi
Captures frames from RTSP camera and sends to cloud server every minute
"""

import cv2
import requests
import time
import logging
import json
import os
from datetime import datetime
from pathlib import Path
import sys
import numpy as np

# Try to import Raspberry Pi camera libraries
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False

try:
    from picamera import PiCamera
    from picamera.array import PiRGBArray
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('edge_server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class EdgeServer:
    """Edge server that captures and sends camera frames to cloud"""

    def __init__(self, config_path='config.json'):
        """Initialize edge server with configuration"""
        self.config = self.load_config(config_path)

        # Camera configuration - supports USB, RTSP, and Pi Camera
        self.camera_type = self.config.get(
            'camera_type', 'usb')  # 'usb', 'rtsp', or 'picamera'
        # USB camera index (0, 1, 2, etc.)
        self.camera_index = self.config.get('camera_index', 0)
        # RTSP URL if using RTSP camera
        self.rtsp_url = self.config.get('rtsp_url', '')

        # Server configuration
        self.api_endpoint = self.config.get('api_endpoint')
        self.interval = self.config.get('interval', 60)  # Default 60 seconds
        self.device_id = self.config.get('device_id', 'edge_device_1')
        self.retry_attempts = self.config.get('retry_attempts', 3)
        self.retry_delay = self.config.get('retry_delay', 5)
        self.save_local_copy = self.config.get('save_local_copy', False)
        self.local_save_path = self.config.get(
            'local_save_path', './captured_frames')

        self.cap = None
        self.picam2 = None  # For picamera2
        self.picam = None   # For legacy picamera
        self.running = False

        # Create local save directory if needed
        if self.save_local_copy:
            Path(self.local_save_path).mkdir(parents=True, exist_ok=True)

        # Log camera configuration
        if self.camera_type == 'usb':
            logger.info(
                f"Configured for USB camera at index {self.camera_index}")
        elif self.camera_type == 'picamera':
            logger.info("Configured for Raspberry Pi Camera Module")
        else:
            logger.info(f"Configured for RTSP camera at {self.rtsp_url}")

    def load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                logger.info(f"Configuration loaded from {config_path}")
                return config
        except FileNotFoundError:
            logger.error(f"Configuration file {config_path} not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing configuration file: {e}")
            raise

    def connect_camera(self):
        """Connect to USB, RTSP, or Pi Camera based on configuration"""
        logger.info(f"Connecting to {self.camera_type.upper()} camera...")

        try:
            # Release existing connections
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            if self.picam2 is not None:
                self.picam2.stop()
                self.picam2.close()
                self.picam2 = None
            if self.picam is not None:
                self.picam.close()
                self.picam = None

            if self.camera_type == 'picamera':
                # Try picamera2 first (modern, for Bullseye+)
                if PICAMERA2_AVAILABLE:
                    logger.info("Using picamera2 library")
                    self.picam2 = Picamera2()

                    # Configure camera
                    config = self.picam2.create_still_configuration(
                        main={"size": (1280, 720)}
                    )
                    self.picam2.configure(config)
                    self.picam2.start()
                    time.sleep(2)  # Camera warm-up

                    # Test capture
                    test_frame = self.picam2.capture_array()
                    if test_frame is None:
                        raise Exception(
                            "Failed to capture test frame with picamera2")

                    logger.info(f"Pi Camera connected via picamera2")
                    logger.info(
                        f"Resolution: {test_frame.shape[1]}x{test_frame.shape[0]}")
                    return True

                # Fall back to legacy picamera
                elif PICAMERA_AVAILABLE:
                    logger.info("Using legacy picamera library")
                    self.picam = PiCamera()
                    self.picam.resolution = (1280, 720)
                    self.picam.framerate = 30
                    time.sleep(2)  # Camera warm-up

                    logger.info("Pi Camera connected via legacy picamera")
                    return True

                else:
                    logger.error(
                        "Pi Camera libraries not available. Install picamera2 or picamera")
                    logger.error(
                        "  For Raspberry Pi OS Bullseye+: sudo apt install python3-picamera2")
                    logger.error("  For older OS: pip install picamera")
                    return False

            elif self.camera_type == 'usb':
                # Connect to USB camera
                logger.info(f"Opening USB camera at index {self.camera_index}")
                self.cap = cv2.VideoCapture(self.camera_index)

                # Set resolution for USB camera (optional, adjust as needed)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

            else:
                # Connect to RTSP stream
                logger.info(f"Connecting to RTSP camera at {self.rtsp_url}")
                self.cap = cv2.VideoCapture(self.rtsp_url)

            # For USB/RTSP: set buffer and test
            if self.cap is not None:
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                if not self.cap.isOpened():
                    logger.error(f"Failed to open {self.camera_type} camera")
                    return False

                # Test read a frame to ensure camera is working
                ret, test_frame = self.cap.read()
                if not ret or test_frame is None:
                    logger.error("Camera opened but cannot read frames")
                    self.cap.release()
                    return False

                logger.info(
                    f"Successfully connected to {self.camera_type.upper()} camera")
                logger.info(
                    f"Camera resolution: {test_frame.shape[1]}x{test_frame.shape[0]}")
                return True

        except Exception as e:
            logger.error(f"Error connecting to camera: {e}")
            return False

    def capture_frame(self):
        """Capture a single frame from the camera"""
        try:
            # Handle Pi Camera
            if self.camera_type == 'picamera':
                if self.picam2 is not None:
                    # picamera2 (modern)
                    frame = self.picam2.capture_array()
                    if frame is None:
                        logger.error("Failed to capture frame with picamera2")
                        return None
                    # Convert RGB to BGR for OpenCV compatibility
                    if len(frame.shape) == 3 and frame.shape[2] == 3:
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    logger.info(
                        f"Frame captured via picamera2 - Shape: {frame.shape}")
                    return frame

                elif self.picam is not None:
                    # legacy picamera
                    raw_capture = PiRGBArray(self.picam, size=(1280, 720))
                    self.picam.capture(raw_capture, format='bgr')
                    frame = raw_capture.array
                    raw_capture.truncate(0)
                    if frame is None:
                        logger.error(
                            "Failed to capture frame with legacy picamera")
                        return None
                    logger.info(
                        f"Frame captured via picamera - Shape: {frame.shape}")
                    return frame

                else:
                    logger.warning(
                        "Pi Camera not connected, attempting reconnect...")
                    if not self.connect_camera():
                        return None
                    # Retry after reconnect
                    return self.capture_frame()

            # Handle USB/RTSP cameras
            if self.cap is None or not self.cap.isOpened():
                logger.warning(
                    "Camera not connected, attempting to reconnect...")
                if not self.connect_camera():
                    return None

            # Read frame
            ret, frame = self.cap.read()

            if not ret or frame is None:
                logger.error("Failed to capture frame")
                return None

            logger.info(f"Frame captured successfully - Shape: {frame.shape}")
            return frame

        except Exception as e:
            logger.error(f"Error capturing frame: {e}")
            return None

    def save_frame_locally(self, frame):
        """Save frame to local storage"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.device_id}_{timestamp}.jpg"
            filepath = os.path.join(self.local_save_path, filename)

            cv2.imwrite(filepath, frame)
            logger.info(f"Frame saved locally: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error saving frame locally: {e}")
            return None

    def send_frame_to_cloud(self, frame):
        """Send captured frame to cloud server"""
        try:
            # Encode frame as JPEG
            _, buffer = cv2.imencode(
                '.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])

            # Prepare the file for upload
            files = {
                'image': ('frame.jpg', buffer.tobytes(), 'image/jpeg')
            }

            # Prepare additional data
            data = {
                'device_id': self.device_id,
                'timestamp': datetime.now().isoformat()
            }

            # Send POST request with retry logic
            for attempt in range(self.retry_attempts):
                try:
                    logger.info(
                        f"Sending frame to {self.api_endpoint} (attempt {attempt + 1}/{self.retry_attempts})")

                    response = requests.post(
                        self.api_endpoint,
                        files=files,
                        data=data,
                        timeout=30
                    )

                    if response.status_code == 200:
                        logger.info(
                            f"Frame sent successfully - Response: {response.text}")
                        return True
                    else:
                        logger.warning(
                            f"Server returned status code {response.status_code}: {response.text}")

                except requests.exceptions.RequestException as e:
                    logger.error(
                        f"Network error on attempt {attempt + 1}: {e}")

                    if attempt < self.retry_attempts - 1:
                        logger.info(
                            f"Retrying in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)
                    else:
                        logger.error("All retry attempts failed")
                        return False

            return False

        except Exception as e:
            logger.error(f"Error sending frame to cloud: {e}")
            return False

    def run(self):
        """Main loop - capture and send frames at specified interval"""
        logger.info("Starting edge server...")
        self.running = True

        # Initial camera connection
        if not self.connect_camera():
            logger.error("Failed to connect to camera on startup")
            return

        try:
            while self.running:
                cycle_start = time.time()

                # Capture frame
                frame = self.capture_frame()

                if frame is not None:
                    # Save locally if configured
                    if self.save_local_copy:
                        self.save_frame_locally(frame)

                    # Send to cloud
                    success = self.send_frame_to_cloud(frame)

                    if success:
                        logger.info(
                            "Frame processing cycle completed successfully")
                    else:
                        logger.warning(
                            "Frame captured but failed to send to cloud")
                else:
                    logger.error(
                        "Failed to capture frame, will retry in next cycle")

                # Calculate time to wait for next cycle
                elapsed = time.time() - cycle_start
                wait_time = max(0, self.interval - elapsed)

                if wait_time > 0:
                    logger.info(
                        f"Waiting {wait_time:.2f} seconds until next capture...")
                    time.sleep(wait_time)
                else:
                    logger.warning(
                        f"Cycle took {elapsed:.2f}s, longer than interval {self.interval}s")

        except KeyboardInterrupt:
            logger.info("Received shutdown signal...")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.stop()

    def stop(self):
        """Clean up resources"""
        logger.info("Stopping edge server...")
        self.running = False

        if self.cap is not None:
            self.cap.release()
            logger.info("Camera released")

        if self.picam2 is not None:
            self.picam2.stop()
            self.picam2.close()
            logger.info("Pi Camera (picamera2) released")

        if self.picam is not None:
            self.picam.close()
            logger.info("Pi Camera (legacy) released")

        logger.info("Edge server stopped")


def main():
    """Entry point"""
    config_file = 'config.json'

    # Check if config file exists
    if not os.path.exists(config_file):
        logger.error(f"Configuration file '{config_file}' not found!")
        logger.error("Please create a config.json file with your settings")
        sys.exit(1)

    try:
        server = EdgeServer(config_file)
        server.run()
    except Exception as e:
        logger.error(f"Failed to start edge server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
