#!/usr/bin/env python3
"""
Edge Server for Raspberry Pi - Multi-Camera Support
Captures frames from multiple cameras and sends to cloud server via /updateRaw API
with authentication and node-specific coordinates
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
import threading
from typing import Dict, List, Optional

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


class AuthManager:
    """Manages JWT authentication for the API"""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token = None
        self.token_expiry = 0

    def login(self) -> bool:
        """Login and get JWT token"""
        try:
            url = f"{self.base_url}/auth/login"
            payload = {
                "username": self.username,
                "password": self.password
            }

            logger.info(f"Logging in as {self.username}...")
            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                self.token_expiry = time.time() + data.get('expires_in', 3600)
                logger.info(
                    f"✅ Login successful! Token expires in {data.get('expires_in', 3600)}s")
                return True
            else:
                logger.error(
                    f"❌ Login failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False

    def is_token_valid(self) -> bool:
        """Check if token is still valid (with 5min buffer)"""
        if not self.token:
            return False
        return time.time() < (self.token_expiry - 300)

    def ensure_authenticated(self) -> bool:
        """Ensure we have a valid token"""
        if not self.is_token_valid():
            logger.warning("⚠️ Token expired or missing, re-authenticating...")
            return self.login()
        return True

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        if self.token:
            return {'Authorization': f'Bearer {self.token}'}
        return {}


class CameraWorker:
    """Worker thread for a single camera"""

    def __init__(self, camera_config: Dict, auth_manager: AuthManager,
                 server_config: Dict, local_settings: Dict):
        self.config = camera_config
        self.auth_manager = auth_manager
        self.server_config = server_config
        self.local_settings = local_settings

        # Camera settings
        self.node_id = camera_config['node_id']
        self.camera_id = camera_config['camera_id']
        self.camera_type = camera_config['camera_type']
        self.camera_index = camera_config.get('camera_index', 0)
        self.rtsp_url = camera_config.get('rtsp_url', '')
        self.coordinates = camera_config['coordinates']
        self.interval = camera_config.get('interval', 60)
        self.enabled = camera_config.get('enabled', True)

        # Server settings
        self.api_base_url = server_config['api_base_url']
        self.retry_attempts = server_config.get('retry_attempts', 3)
        self.retry_delay = server_config.get('retry_delay', 5)

        # Local settings
        self.save_local_copy = local_settings.get('save_local_copy', False)
        self.local_save_path = local_settings.get(
            'local_save_path', './captured_frames')

        self.cap = None
        self.running = False
        self.thread = None

        # Create local save directory if needed
        if self.save_local_copy:
            node_path = os.path.join(self.local_save_path, self.node_id)
            Path(node_path).mkdir(parents=True, exist_ok=True)

    def connect_camera(self) -> bool:
        """Connect to USB or RTSP camera"""
        logger.info(
            f"[{self.node_id}] Connecting to {self.camera_type.upper()} camera...")

        try:
            # Release existing connection if any
            if self.cap is not None:
                self.cap.release()

            if self.camera_type == 'usb':
                logger.info(
                    f"[{self.node_id}] Opening USB camera at index {self.camera_index}")
                self.cap = cv2.VideoCapture(self.camera_index)

                # Set resolution for USB camera
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            else:
                logger.info(
                    f"[{self.node_id}] Connecting to RTSP camera at {self.rtsp_url}")
                self.cap = cv2.VideoCapture(self.rtsp_url)

            # Set buffer size to reduce latency
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not self.cap.isOpened():
                logger.error(
                    f"[{self.node_id}] Failed to open {self.camera_type} camera")
                return False

            # Test read a frame
            ret, test_frame = self.cap.read()
            if not ret or test_frame is None:
                logger.error(
                    f"[{self.node_id}] Camera opened but cannot read frames")
                self.cap.release()
                return False

            logger.info(
                f"[{self.node_id}] ✅ Connected - Resolution: {test_frame.shape[1]}x{test_frame.shape[0]}")
            return True

        except Exception as e:
            logger.error(f"[{self.node_id}] Error connecting to camera: {e}")
            return False

    def capture_frame(self) -> Optional[bytes]:
        """Capture a single frame and return as JPEG bytes"""
        try:
            if self.cap is None or not self.cap.isOpened():
                logger.warning(
                    f"[{self.node_id}] Camera not connected, attempting to reconnect...")
                if not self.connect_camera():
                    return None

            # Read frame
            ret, frame = self.cap.read()

            if not ret or frame is None:
                logger.error(f"[{self.node_id}] Failed to capture frame")
                return None

            # Encode as JPEG
            _, buffer = cv2.imencode(
                '.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            image_bytes = buffer.tobytes()

            logger.info(
                f"[{self.node_id}] Frame captured - Size: {len(image_bytes)} bytes")

            # Save locally if configured
            if self.save_local_copy:
                self.save_frame_locally(frame)

            return image_bytes

        except Exception as e:
            logger.error(f"[{self.node_id}] Error capturing frame: {e}")
            return None

    def save_frame_locally(self, frame):
        """Save frame to local storage"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.node_id}_{timestamp}.jpg"
            node_path = os.path.join(self.local_save_path, self.node_id)
            filepath = os.path.join(node_path, filename)

            cv2.imwrite(filepath, frame)
            logger.debug(f"[{self.node_id}] Frame saved locally: {filepath}")

        except Exception as e:
            logger.error(f"[{self.node_id}] Error saving frame locally: {e}")

    def send_to_updateraw(self, image_bytes: bytes) -> bool:
        """Send frame to /parking/updateRaw API"""
        try:
            # Ensure we're authenticated
            if not self.auth_manager.ensure_authenticated():
                logger.error(f"[{self.node_id}] Authentication failed")
                return False

            url = f"{self.api_base_url}/parking/updateRaw"

            # Prepare multipart form data
            files = {
                'image': ('frame.jpg', image_bytes, 'image/jpeg')
            }

            data = {
                'coordinates': json.dumps(self.coordinates),
                'camera_id': self.camera_id,
                'node_id': self.node_id
            }

            headers = self.auth_manager.get_auth_headers()

            # Send with retry logic
            for attempt in range(self.retry_attempts):
                try:
                    logger.info(
                        f"[{self.node_id}] Sending to {url} (attempt {attempt + 1}/{self.retry_attempts})")

                    response = requests.post(
                        url,
                        headers=headers,
                        files=files,
                        data=data,
                        timeout=30
                    )

                    if response.status_code == 201:
                        result = response.json()
                        logger.info(f"[{self.node_id}] ✅ Upload successful!")
                        logger.info(
                            f"[{self.node_id}]    Document ID: {result.get('document_id')}")
                        logger.info(
                            f"[{self.node_id}]    Occupancy: {result.get('occupied_slots')}/{result.get('total_slots')} ({result.get('occupancy_rate')}%)")

                        # Log GCS storage info if available
                        gcs = result.get('gcs_storage', {})
                        if gcs.get('enabled'):
                            logger.info(
                                f"[{self.node_id}]    Cloud Storage: ✅")
                            if gcs.get('raw_image'):
                                logger.debug(
                                    f"[{self.node_id}]    Raw: {gcs['raw_image']['path']}")

                        return True
                    elif response.status_code == 401:
                        logger.warning(
                            f"[{self.node_id}] Token expired, re-authenticating...")
                        self.auth_manager.token = None
                        if self.auth_manager.ensure_authenticated():
                            headers = self.auth_manager.get_auth_headers()
                            continue
                        return False
                    else:
                        logger.warning(
                            f"[{self.node_id}] Server returned {response.status_code}: {response.text}")

                except requests.exceptions.RequestException as e:
                    logger.error(
                        f"[{self.node_id}] Network error on attempt {attempt + 1}: {e}")

                    if attempt < self.retry_attempts - 1:
                        logger.info(
                            f"[{self.node_id}] Retrying in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)

            logger.error(f"[{self.node_id}] ❌ All retry attempts failed")
            return False

        except Exception as e:
            logger.error(f"[{self.node_id}] Error sending to API: {e}")
            return False

    def run_loop(self):
        """Main loop for this camera"""
        logger.info(f"[{self.node_id}] Starting camera worker...")

        # Initial camera connection
        if not self.connect_camera():
            logger.error(
                f"[{self.node_id}] Failed to connect to camera on startup")
            return

        try:
            while self.running:
                cycle_start = time.time()

                # Capture frame
                image_bytes = self.capture_frame()

                if image_bytes is not None:
                    # Send to cloud
                    success = self.send_to_updateraw(image_bytes)

                    if success:
                        logger.info(
                            f"[{self.node_id}] Cycle completed successfully")
                    else:
                        logger.warning(
                            f"[{self.node_id}] Failed to send to cloud")
                else:
                    logger.error(f"[{self.node_id}] Failed to capture frame")

                # Wait for next cycle
                elapsed = time.time() - cycle_start
                wait_time = max(0, self.interval - elapsed)

                if wait_time > 0:
                    logger.info(
                        f"[{self.node_id}] Waiting {wait_time:.1f}s until next capture...")
                    time.sleep(wait_time)

        except Exception as e:
            logger.error(f"[{self.node_id}] Error in main loop: {e}")
        finally:
            self.stop()

    def start(self):
        """Start the camera worker in a separate thread"""
        if not self.enabled:
            logger.info(f"[{self.node_id}] Camera is disabled in config")
            return

        self.running = True
        self.thread = threading.Thread(target=self.run_loop, daemon=True)
        self.thread.start()
        logger.info(f"[{self.node_id}] Worker thread started")

    def stop(self):
        """Stop the camera worker"""
        logger.info(f"[{self.node_id}] Stopping...")
        self.running = False

        if self.cap is not None:
            self.cap.release()
            logger.info(f"[{self.node_id}] Camera released")

        if self.thread is not None:
            self.thread.join(timeout=5)


class EdgeServer:
    """Multi-camera edge server that manages multiple camera workers"""

    def __init__(self, config_path='config.json'):
        """Initialize edge server with configuration"""
        self.config = self.load_config(config_path)

        # Server configuration
        server_config = self.config.get('server', {})
        self.api_base_url = server_config.get('api_base_url')
        self.username = server_config.get('username')
        self.password = server_config.get('password')

        # Validate required fields
        if not all([self.api_base_url, self.username, self.password]):
            raise ValueError(
                "Missing required server configuration (api_base_url, username, password)")

        # Initialize authentication manager
        self.auth_manager = AuthManager(
            self.api_base_url, self.username, self.password)

        # Local settings
        self.local_settings = self.config.get('local_settings', {})

        # Create camera workers
        self.workers: List[CameraWorker] = []
        cameras = self.config.get('cameras', [])

        if not cameras:
            raise ValueError("No cameras configured in config.json")

        for cam_config in cameras:
            worker = CameraWorker(
                cam_config,
                self.auth_manager,
                server_config,
                self.local_settings
            )
            self.workers.append(worker)

        logger.info(f"Initialized {len(self.workers)} camera workers")

    def load_config(self, config_path: str) -> Dict:
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

    def run(self):
        """Main loop - start all camera workers"""
        logger.info("="*70)
        logger.info("🚀 Starting Multi-Camera Edge Server")
        logger.info("="*70)

        # Initial authentication
        if not self.auth_manager.login():
            logger.error("❌ Initial authentication failed. Exiting.")
            return

        logger.info(f"✅ Authenticated as {self.username}")
        logger.info(f"📡 API Base URL: {self.api_base_url}")
        logger.info(f"📹 Total cameras configured: {len(self.workers)}")

        # Start all enabled camera workers
        enabled_count = 0
        for worker in self.workers:
            if worker.enabled:
                logger.info(f"📹 Starting camera: {worker.node_id}")
                logger.info(f"   - Type: {worker.camera_type}")
                logger.info(f"   - Camera ID: {worker.camera_id}")
                logger.info(
                    f"   - Coordinates: {len(worker.coordinates)} parking slots")
                logger.info(f"   - Interval: {worker.interval}s")
                worker.start()
                enabled_count += 1
            else:
                logger.info(f"⏸️  Skipping disabled camera: {worker.node_id}")

        if enabled_count == 0:
            logger.error("❌ No enabled cameras found. Exiting.")
            return

        logger.info("="*70)
        logger.info(f"✅ {enabled_count} camera(s) running")
        logger.info("Press Ctrl+C to stop")
        logger.info("="*70)

        try:
            # Keep main thread alive
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("\n⚠️  Received shutdown signal...")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stop all camera workers"""
        logger.info("="*70)
        logger.info("🛑 Stopping all camera workers...")
        logger.info("="*70)

        for worker in self.workers:
            worker.stop()

        logger.info("✅ All workers stopped")
        logger.info("="*70)


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
