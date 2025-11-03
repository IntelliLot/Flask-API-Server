"""
Camera Manager - Handles multiple camera types
Supports: Raspberry Pi Camera, USB Cameras, RTSP/IP Cameras
"""

import cv2
import numpy as np
import logging
from typing import Optional, Tuple
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class CameraInterface(ABC):
    """Abstract base class for camera interfaces"""

    def __init__(self, node_id: str, config: dict):
        self.node_id = node_id
        self.config = config
        self.is_opened = False

    @abstractmethod
    def open(self) -> bool:
        """Open camera connection"""
        pass

    @abstractmethod
    def capture(self) -> Optional[np.ndarray]:
        """Capture a frame"""
        pass

    @abstractmethod
    def release(self):
        """Release camera resources"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if camera is available"""
        pass


class PiCamera(CameraInterface):
    """Raspberry Pi Camera Module interface"""

    def __init__(self, node_id: str, config: dict):
        super().__init__(node_id, config)
        self.camera = None
        self.using_opencv = False

    def open(self) -> bool:
        """Open Pi Camera"""
        try:
            # Try using picamera2 (Raspberry Pi OS Bullseye and later)
            try:
                from picamera2 import Picamera2
                self.camera = Picamera2()

                # Configure camera
                camera_config = self.camera.create_still_configuration(
                    main={
                        "size": tuple(self.config.get('resolution', [1920, 1080])),
                        "format": "RGB888"
                    }
                )
                self.camera.configure(camera_config)
                self.camera.start()

                # Camera warm-up
                import time
                time.sleep(2)

                # Test capture to ensure camera is working
                test_frame = self.camera.capture_array()
                if test_frame is None:
                    raise Exception("Failed to capture test frame")

                self.is_opened = True
                self.using_opencv = False
                logger.info(
                    f"✅ Pi Camera {self.node_id} opened using picamera2")
                logger.info(
                    f"   Resolution: {test_frame.shape[1]}x{test_frame.shape[0]}")
                return True

            except ImportError:
                # Fall back to legacy picamera
                try:
                    from picamera import PiCamera as LegacyPiCamera
                    from picamera.array import PiRGBArray

                    self.camera = LegacyPiCamera()
                    self.camera.resolution = tuple(
                        self.config.get('resolution', [1920, 1080]))
                    self.camera.framerate = self.config.get('framerate', 30)
                    self.camera.rotation = self.config.get('rotation', 0)

                    # Warm up camera
                    import time
                    time.sleep(2)  # Camera warm-up time

                    self.is_opened = True
                    self.using_opencv = False
                    logger.info(
                        f"✅ Pi Camera {self.node_id} opened using legacy picamera")
                    logger.info(
                        f"   Resolution: {self.camera.resolution[0]}x{self.camera.resolution[1]}")
                    return True

                except ImportError:
                    # Last resort: try OpenCV with index 0
                    logger.warning("picamera not available, trying OpenCV...")
                    self.camera = cv2.VideoCapture(0)

                    if not self.camera.isOpened():
                        raise Exception("Could not open camera with OpenCV")

                    # Set resolution
                    resolution = self.config.get('resolution', [1920, 1080])
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

                    # Set buffer to reduce lag
                    self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                    # Warm up camera
                    import time
                    time.sleep(2)

                    # Test read a frame to ensure camera is working
                    ret, test_frame = self.camera.read()
                    if not ret or test_frame is None:
                        logger.error("Camera opened but cannot read frames")
                        self.camera.release()
                        raise Exception("Camera opened but cannot read frames")

                    self.is_opened = True
                    self.using_opencv = True
                    logger.info(
                        f"✅ Pi Camera {self.node_id} opened using OpenCV")
                    logger.info(
                        f"   Resolution: {test_frame.shape[1]}x{test_frame.shape[0]}")
                    return True

        except Exception as e:
            logger.error(f"❌ Failed to open Pi Camera {self.node_id}: {e}")
            return False

    def capture(self) -> Optional[np.ndarray]:
        """Capture frame from Pi Camera"""
        try:
            if not self.is_opened:
                return None

            if self.using_opencv:
                # For OpenCV capture
                if self.camera is None or not self.camera.isOpened():
                    logger.error(f"Camera {self.node_id} not opened")
                    return None

                ret, frame = self.camera.read()

                if not ret or frame is None:
                    logger.warning(
                        f"⚠️  Failed to read frame from {self.node_id}")
                    return None

                return frame
            else:
                # Using picamera2
                if hasattr(self.camera, 'capture_array'):
                    frame = self.camera.capture_array()
                    if frame is None:
                        logger.error(
                            f"Failed to capture frame with picamera2 for {self.node_id}")
                        return None
                    # Convert RGB to BGR for OpenCV compatibility
                    if len(frame.shape) == 3 and frame.shape[2] == 3:
                        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    return frame
                # Using legacy picamera
                else:
                    from picamera.array import PiRGBArray
                    resolution = tuple(self.config.get(
                        'resolution', [1920, 1080]))
                    rawCapture = PiRGBArray(self.camera, size=resolution)
                    self.camera.capture(rawCapture, format="bgr")
                    frame = rawCapture.array
                    rawCapture.truncate(0)  # Clear stream for next capture
                    if frame is None:
                        logger.error(
                            f"Failed to capture frame with legacy picamera for {self.node_id}")
                        return None
                    return frame

        except Exception as e:
            logger.error(
                f"❌ Failed to capture from Pi Camera {self.node_id}: {e}")
            return None

    def release(self):
        """Release Pi Camera"""
        try:
            if self.camera:
                if self.using_opencv:
                    self.camera.release()
                else:
                    if hasattr(self.camera, 'stop'):
                        self.camera.stop()
                    if hasattr(self.camera, 'close'):
                        self.camera.close()
                self.is_opened = False
                logger.info(f"✅ Pi Camera {self.node_id} released")
        except Exception as e:
            logger.error(f"❌ Error releasing Pi Camera {self.node_id}: {e}")

    def is_available(self) -> bool:
        """Check if Pi Camera is available"""
        try:
            # Check if picamera2 is available
            try:
                from picamera2 import Picamera2
                return True
            except ImportError:
                pass

            # Check if legacy picamera is available
            try:
                from picamera import PiCamera
                return True
            except ImportError:
                pass

            # Check if OpenCV can access camera
            cap = cv2.VideoCapture(0)
            available = cap.isOpened()
            cap.release()
            return available

        except Exception:
            return False


class USBCamera(CameraInterface):
    """USB Camera interface using OpenCV"""

    def __init__(self, node_id: str, config: dict):
        super().__init__(node_id, config)
        self.camera = None

    def open(self) -> bool:
        """Open USB Camera"""
        try:
            camera_index = self.config.get('camera_index', 0)
            self.camera = cv2.VideoCapture(camera_index)

            if not self.camera.isOpened():
                raise Exception(
                    f"Could not open camera at index {camera_index}")

            # Set resolution if specified
            resolution = self.config.get('resolution', [1280, 720])
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

            self.is_opened = True
            logger.info(
                f"✅ USB Camera {self.node_id} opened (index: {camera_index})")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to open USB Camera {self.node_id}: {e}")
            return False

    def capture(self) -> Optional[np.ndarray]:
        """Capture frame from USB Camera"""
        try:
            if not self.is_opened or self.camera is None:
                return None

            ret, frame = self.camera.read()
            return frame if ret else None

        except Exception as e:
            logger.error(
                f"❌ Failed to capture from USB Camera {self.node_id}: {e}")
            return None

    def release(self):
        """Release USB Camera"""
        try:
            if self.camera:
                self.camera.release()
                self.is_opened = False
                logger.info(f"✅ USB Camera {self.node_id} released")
        except Exception as e:
            logger.error(f"❌ Error releasing USB Camera {self.node_id}: {e}")

    def is_available(self) -> bool:
        """Check if USB Camera is available"""
        try:
            camera_index = self.config.get('camera_index', 0)
            cap = cv2.VideoCapture(camera_index)
            available = cap.isOpened()
            cap.release()
            return available
        except Exception:
            return False


class RTSPCamera(CameraInterface):
    """RTSP/IP Camera interface"""

    def __init__(self, node_id: str, config: dict):
        super().__init__(node_id, config)
        self.camera = None

    def open(self) -> bool:
        """Open RTSP Camera stream"""
        try:
            rtsp_url = self.config.get('rtsp_url')
            if not rtsp_url:
                raise Exception("RTSP URL not provided")

            self.camera = cv2.VideoCapture(rtsp_url)

            if not self.camera.isOpened():
                raise Exception(f"Could not open RTSP stream: {rtsp_url}")

            self.is_opened = True
            logger.info(f"✅ RTSP Camera {self.node_id} opened")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to open RTSP Camera {self.node_id}: {e}")
            return False

    def capture(self) -> Optional[np.ndarray]:
        """Capture frame from RTSP Camera"""
        try:
            if not self.is_opened or self.camera is None:
                return None

            ret, frame = self.camera.read()
            return frame if ret else None

        except Exception as e:
            logger.error(
                f"❌ Failed to capture from RTSP Camera {self.node_id}: {e}")
            return None

    def release(self):
        """Release RTSP Camera"""
        try:
            if self.camera:
                self.camera.release()
                self.is_opened = False
                logger.info(f"✅ RTSP Camera {self.node_id} released")
        except Exception as e:
            logger.error(f"❌ Error releasing RTSP Camera {self.node_id}: {e}")

    def is_available(self) -> bool:
        """Check if RTSP Camera is available"""
        try:
            rtsp_url = self.config.get('rtsp_url')
            if not rtsp_url:
                return False

            cap = cv2.VideoCapture(rtsp_url)
            available = cap.isOpened()
            cap.release()
            return available
        except Exception:
            return False


class CameraManager:
    """Manages multiple cameras of different types"""

    def __init__(self, cameras_config: list):
        self.cameras = []
        self._initialize_cameras(cameras_config)

    def _initialize_cameras(self, cameras_config: list):
        """Initialize all configured cameras"""
        for cam_config in cameras_config:
            if not cam_config.get('enabled', False):
                logger.info(
                    f"⏭️  Camera {cam_config.get('node_id')} is disabled, skipping...")
                continue

            camera_type = cam_config.get('type', '').lower()
            node_id = cam_config.get('node_id', 'unknown')

            try:
                if camera_type == 'picamera':
                    camera = PiCamera(node_id, cam_config)
                elif camera_type == 'usb':
                    camera = USBCamera(node_id, cam_config)
                elif camera_type == 'rtsp':
                    camera = RTSPCamera(node_id, cam_config)
                else:
                    logger.warning(
                        f"⚠️  Unknown camera type: {camera_type} for {node_id}")
                    continue

                self.cameras.append(camera)
                logger.info(f"📷 Camera registered: {node_id} ({camera_type})")

            except Exception as e:
                logger.error(f"❌ Failed to initialize camera {node_id}: {e}")

    def open_all(self) -> dict:
        """Open all cameras and return status"""
        results = {}
        for camera in self.cameras:
            success = camera.open()
            results[camera.node_id] = success
        return results

    def capture_all(self) -> dict:
        """Capture frames from all cameras"""
        frames = {}
        for camera in self.cameras:
            if camera.is_opened:
                frame = camera.capture()
                if frame is not None:
                    frames[camera.node_id] = frame
                else:
                    logger.warning(
                        f"⚠️  Failed to capture from {camera.node_id}")
        return frames

    def release_all(self):
        """Release all cameras"""
        for camera in self.cameras:
            camera.release()
        logger.info("✅ All cameras released")

    def get_camera(self, node_id: str) -> Optional[CameraInterface]:
        """Get specific camera by node_id"""
        for camera in self.cameras:
            if camera.node_id == node_id:
                return camera
        return None

    def get_active_cameras(self) -> list:
        """Get list of active camera node_ids"""
        return [cam.node_id for cam in self.cameras if cam.is_opened]
