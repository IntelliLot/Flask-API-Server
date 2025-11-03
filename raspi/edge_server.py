#!/usr/bin/env python3
"""
Raspberry Pi Edge Server
Captures images from multiple cameras and uploads to central server
"""

# Try to import system monitor (optional)
try:
    from raspi.system_monitor import SystemMonitor
    SYSTEM_MONITOR_AVAILABLE = True
except ImportError:
    SYSTEM_MONITOR_AVAILABLE = False
    print("⚠️  Warning: psutil not available, system monitoring disabled")
    print("   Install with: sudo apt install python3-psutil")
    print("   Or: pip3 install psutil --break-system-packages")

from raspi.camera_manager import CameraManager
import os
import sys
import json
import time
import logging
import requests
import cv2
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
import threading

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class EdgeServer:
    """Edge server for capturing and uploading parking lot images"""

    def __init__(self, config_path: str = "config.json"):
        """Initialize edge server"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()

        # Initialize components
        self.camera_manager = CameraManager(self.config['cameras'])

        # Initialize system monitor if available
        if SYSTEM_MONITOR_AVAILABLE:
            self.system_monitor = SystemMonitor(
                self.config.get('monitoring', {}))
        else:
            self.system_monitor = None
            self.logger.warning(
                "System monitoring disabled (psutil not available)")

        # Statistics
        self.stats = {
            'total_captures': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'errors': 0,
            'consecutive_errors': 0,
            'start_time': datetime.now()
        }

        # Setup local storage
        if self.config['capture_settings'].get('save_local_copy', False):
            self._setup_local_storage()

        self.running = False
        self.logger.info("🚀 Edge Server initialized")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file"""
        try:
            config_file = Path(__file__).parent / config_path
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f"✅ Configuration loaded from {config_file}")
            return config
        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
            sys.exit(1)

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_level = self.config['system_settings'].get('log_level', 'INFO')
        log_file = self.config['system_settings'].get(
            'log_file', './logs/edge_server.log')

        # Create logs directory
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

        return logging.getLogger(__name__)

    def _setup_local_storage(self):
        """Setup local storage directory"""
        local_path = Path(self.config['capture_settings']['local_save_path'])
        local_path.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"📁 Local storage: {local_path.absolute()}")

    def _save_local_copy(self, frame, node_id: str):
        """Save frame to local storage"""
        try:
            if not self.config['capture_settings'].get('save_local_copy', False):
                return

            local_path = Path(
                self.config['capture_settings']['local_save_path'])
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{node_id}_{timestamp}.jpg"
            filepath = local_path / filename

            cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY,
                                               self.config['capture_settings'].get('quality', 85)])

            # Cleanup old files
            self._cleanup_old_files(local_path)

        except Exception as e:
            self.logger.error(f"❌ Failed to save local copy: {e}")

    def _cleanup_old_files(self, directory: Path):
        """Remove old files if exceeding max limit"""
        try:
            max_files = self.config['capture_settings'].get(
                'max_local_images', 100)
            files = sorted(directory.glob('*.jpg'),
                           key=os.path.getmtime, reverse=True)

            if len(files) > max_files:
                for old_file in files[max_files:]:
                    old_file.unlink()
                    self.logger.debug(f"🗑️  Removed old file: {old_file.name}")

        except Exception as e:
            self.logger.error(f"❌ Failed to cleanup old files: {e}")

    def _encode_image(self, frame) -> Optional[str]:
        """Encode frame to base64 string"""
        try:
            quality = self.config['capture_settings'].get('quality', 85)
            _, buffer = cv2.imencode(
                '.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            return base64.b64encode(buffer).decode('utf-8')
        except Exception as e:
            self.logger.error(f"❌ Failed to encode image: {e}")
            return None

    def _upload_image(self, image_base64: str, node_id: str, metadata: dict) -> bool:
        """Upload image to central server"""
        upload_config = self.config['upload_settings']

        for attempt in range(upload_config['retry_attempts']):
            try:
                # Prepare payload
                payload = {
                    'image': image_base64,
                    'device_id': self.config['device_id'],
                    'camera_id': node_id,  # API requires camera_id
                    'node_id': node_id,     # Also send node_id for tracking
                    # Empty coordinates (edge device doesn't have parking positions)
                    'coordinates': [],
                    'timestamp': datetime.now().isoformat(),
                    'organization_name': self.config.get('organization_name', ''),
                    'location': self.config.get('location', ''),
                    'metadata': metadata
                }

                # Prepare headers
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.config["api_key"]}'
                }

                # Make request
                response = requests.post(
                    self.config['api_endpoint'],
                    json=payload,
                    headers=headers,
                    timeout=upload_config['timeout'],
                    verify=upload_config.get('verify_ssl', True)
                )

                if response.status_code == 200:
                    self.logger.info(f"✅ Upload successful: {node_id}")
                    self.stats['successful_uploads'] += 1
                    self.stats['consecutive_errors'] = 0
                    return True
                else:
                    self.logger.error(
                        f"❌ Upload failed: {response.status_code} - {response.text}")

            except requests.exceptions.Timeout:
                self.logger.warning(
                    f"⚠️  Upload timeout (attempt {attempt + 1}/{upload_config['retry_attempts']})")

            except Exception as e:
                self.logger.error(
                    f"❌ Upload error (attempt {attempt + 1}/{upload_config['retry_attempts']}): {e}")

            # Wait before retry
            if attempt < upload_config['retry_attempts'] - 1:
                time.sleep(upload_config['retry_delay'])

        self.stats['failed_uploads'] += 1
        self.stats['consecutive_errors'] += 1
        return False

    def _capture_and_upload(self):
        """Capture frames from all cameras and upload"""
        try:
            # Capture from all cameras
            frames = self.camera_manager.capture_all()

            if not frames:
                self.logger.warning("⚠️  No frames captured from any camera")
                return

            self.stats['total_captures'] += len(frames)

            # Process each captured frame
            for node_id, frame in frames.items():
                try:
                    # Save local copy
                    self._save_local_copy(frame, node_id)

                    # Encode image
                    image_base64 = self._encode_image(frame)
                    if not image_base64:
                        continue

                    # Prepare metadata
                    metadata = {
                        'resolution': f"{frame.shape[1]}x{frame.shape[0]}",
                        'format': 'JPEG',
                        'quality': self.config['capture_settings'].get('quality', 85),
                        'camera_type': self._get_camera_type(node_id)
                    }

                    # Upload to server
                    self._upload_image(image_base64, node_id, metadata)

                except Exception as e:
                    self.logger.error(
                        f"❌ Error processing frame from {node_id}: {e}")
                    self.stats['errors'] += 1

        except Exception as e:
            self.logger.error(f"❌ Capture and upload error: {e}")
            self.stats['errors'] += 1

    def _get_camera_type(self, node_id: str) -> str:
        """Get camera type from node_id"""
        for cam_config in self.config['cameras']:
            if cam_config.get('node_id') == node_id:
                return cam_config.get('type', 'unknown')
        return 'unknown'

    def _print_status(self):
        """Print current status"""
        uptime = datetime.now() - self.stats['start_time']

        self.logger.info("=" * 60)
        self.logger.info("📊 Edge Server Status")
        self.logger.info("=" * 60)
        self.logger.info(f"⏱️  Uptime: {uptime}")
        self.logger.info(
            f"📷 Active Cameras: {len(self.camera_manager.get_active_cameras())}")
        self.logger.info(f"📸 Total Captures: {self.stats['total_captures']}")
        self.logger.info(
            f"✅ Successful Uploads: {self.stats['successful_uploads']}")
        self.logger.info(f"❌ Failed Uploads: {self.stats['failed_uploads']}")
        self.logger.info(f"⚠️  Errors: {self.stats['errors']}")

        # System stats
        if self.config.get('monitoring', {}).get('enable_system_stats', False) and self.system_monitor:
            sys_stats = self.system_monitor.get_stats()
            self.logger.info(
                f"🖥️  CPU: {sys_stats.get('cpu_percent', 0):.1f}%")
            self.logger.info(
                f"💾 Memory: {sys_stats.get('memory_percent', 0):.1f}%")
            self.logger.info(
                f"💽 Disk: {sys_stats.get('disk_percent', 0):.1f}%")
            if 'temperature' in sys_stats:
                self.logger.info(
                    f"🌡️  Temperature: {sys_stats['temperature']:.1f}°C")

        self.logger.info("=" * 60)

    def _check_system_health(self) -> bool:
        """Check system health and return True if healthy"""
        if not self.config.get('monitoring', {}).get('enable_system_stats', False):
            return True

        if not self.system_monitor:
            return True

        stats = self.system_monitor.get_stats()
        monitoring_config = self.config['monitoring']

        # Check thresholds
        if stats.get('cpu_percent', 0) > monitoring_config.get('cpu_threshold', 80):
            self.logger.warning(
                f"⚠️  CPU usage high: {stats['cpu_percent']:.1f}%")

        if stats.get('memory_percent', 0) > monitoring_config.get('memory_threshold', 85):
            self.logger.warning(
                f"⚠️  Memory usage high: {stats['memory_percent']:.1f}%")

        if stats.get('disk_percent', 0) > monitoring_config.get('disk_threshold', 90):
            self.logger.warning(
                f"⚠️  Disk usage high: {stats['disk_percent']:.1f}%")

        if 'temperature' in stats:
            if stats['temperature'] > monitoring_config.get('temperature_threshold', 70):
                self.logger.warning(
                    f"⚠️  Temperature high: {stats['temperature']:.1f}°C")

        # Check consecutive errors
        max_errors = self.config['system_settings'].get(
            'max_consecutive_errors', 10)
        if self.stats['consecutive_errors'] >= max_errors:
            self.logger.error(
                f"❌ Too many consecutive errors: {self.stats['consecutive_errors']}")
            return False

        return True

    def start(self):
        """Start edge server"""
        self.logger.info("🚀 Starting Edge Server...")
        self.logger.info(f"📡 API Endpoint: {self.config['api_endpoint']}")
        self.logger.info(f"🆔 Device ID: {self.config['device_id']}")
        self.logger.info(
            f"⏱️  Capture Interval: {self.config['capture_settings']['interval']}s")

        # Open all cameras
        results = self.camera_manager.open_all()
        active_cameras = [node_id for node_id,
                          success in results.items() if success]

        if not active_cameras:
            self.logger.error("❌ No cameras available. Exiting.")
            return

        self.logger.info(
            f"✅ {len(active_cameras)} camera(s) ready: {', '.join(active_cameras)}")

        # Start main loop
        self.running = True
        interval = self.config['capture_settings']['interval']
        status_interval = self.config['system_settings'].get(
            'status_report_interval', 300)
        last_status_time = time.time()

        try:
            while self.running:
                start_time = time.time()

                # Check system health
                if not self._check_system_health():
                    if self.config['system_settings'].get('auto_restart_on_error', True):
                        self.logger.info("🔄 Attempting to restart...")
                        self.stats['consecutive_errors'] = 0
                        continue
                    else:
                        self.logger.error("❌ System unhealthy. Stopping.")
                        break

                # Capture and upload
                self._capture_and_upload()

                # Print status periodically
                if time.time() - last_status_time >= status_interval:
                    self._print_status()
                    last_status_time = time.time()

                # Wait for next interval
                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)

                if sleep_time > 0:
                    self.logger.debug(f"⏳ Sleeping for {sleep_time:.1f}s...")
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            self.logger.info("\n⏸️  Interrupted by user")
        except Exception as e:
            self.logger.error(f"❌ Fatal error: {e}", exc_info=True)
        finally:
            self.stop()

    def stop(self):
        """Stop edge server"""
        self.logger.info("🛑 Stopping Edge Server...")
        self.running = False
        self.camera_manager.release_all()
        self._print_status()
        self.logger.info("✅ Edge Server stopped")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Raspberry Pi Edge Server')
    parser.add_argument('--config', default='config.json',
                        help='Configuration file path')
    args = parser.parse_args()

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Start server
    server = EdgeServer(args.config)
    server.start()


if __name__ == '__main__':
    main()
