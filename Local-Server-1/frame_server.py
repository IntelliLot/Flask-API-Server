#!/usr/bin/env python3
"""
Local Frame Server (Server 1)
Simple Flask server that captures frames from camera/video and serves them via REST API
Serves frames to Flask API Server (Server 2) for YOLO processing
"""

import cv2
import time
import logging
import os
import sys
import threading
from datetime import datetime
from flask import Flask, Response, jsonify
from io import BytesIO
import base64
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('frame_server.log')
    ]
)

logger = logging.getLogger(__name__)

class FrameServer:
    """Local server that captures and serves video frames"""
    
    def __init__(self):
        self.config = Config()
        self.app = Flask(__name__)
        self.cap = None
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.running = False
        self.capture_thread = None
        
        # Setup Flask routes
        self.setup_routes()
        
    def setup_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'running',
                'server': 'Local Frame Server',
                'timestamp': datetime.now().isoformat(),
                'video_source': self.config.VIDEO_SOURCE if not self.config.USE_CAMERA else f'Camera {self.config.CAMERA_INDEX}'
            })
        
        @self.app.route('/latest_frame', methods=['GET'])
        def get_latest_frame():
            """Get the latest captured frame as base64 encoded image"""
            try:
                with self.frame_lock:
                    if self.latest_frame is None:
                        return jsonify({'error': 'No frame available'}), 404
                    
                    # Encode frame to base64
                    _, buffer = cv2.imencode('.jpg', self.latest_frame)
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                return jsonify({
                    'frame': frame_base64,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'success'
                })
                
            except Exception as e:
                logger.error(f"Error getting latest frame: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/stats', methods=['GET'])
        def get_stats():
            """Get server statistics"""
            return jsonify({
                'running': self.running,
                'video_source': self.config.VIDEO_SOURCE if not self.config.USE_CAMERA else f'Camera {self.config.CAMERA_INDEX}',
                'has_frame': self.latest_frame is not None,
                'timestamp': datetime.now().isoformat()
            })
    
    def init_video_capture(self):
        """Initialize video capture"""
        try:
            if self.config.USE_CAMERA:
                logger.info(f"Initializing camera {self.config.CAMERA_INDEX}")
                self.cap = cv2.VideoCapture(self.config.CAMERA_INDEX)
            else:
                logger.info(f"Initializing video file: {self.config.VIDEO_SOURCE}")
                if not os.path.exists(self.config.VIDEO_SOURCE):
                    logger.error(f"Video file not found: {self.config.VIDEO_SOURCE}")
                    return False
                self.cap = cv2.VideoCapture(self.config.VIDEO_SOURCE)
            
            if not self.cap.isOpened():
                logger.error("Failed to open video source")
                return False
                
            # Set camera properties for better performance
            if self.config.USE_CAMERA:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            logger.info("Video capture initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing video capture: {e}")
            return False
    
    def capture_frames(self):
        """Continuously capture frames from video source"""
        logger.info("Starting frame capture thread")
        
        while self.running:
            try:
                ret, frame = self.cap.read()
                
                if not ret:
                    if not self.config.USE_CAMERA:
                        # Loop video if using file
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        logger.error("Failed to read frame from camera")
                        time.sleep(1)
                        continue
                
                # Store latest frame
                with self.frame_lock:
                    self.latest_frame = frame.copy()
                
                # Control frame rate
                time.sleep(1.0 / 30.0)  # ~30 FPS
                
            except Exception as e:
                logger.error(f"Error in frame capture: {e}")
                time.sleep(1)
        
        logger.info("Frame capture thread stopped")
    
    def start_server(self, host='127.0.0.1', port=5000):
        """Start the frame server"""
        logger.info(f"Starting Local Frame Server on {host}:{port}")
        
        # Initialize video capture
        if not self.init_video_capture():
            logger.error("Failed to initialize video capture")
            return False
        
        # Start capture thread
        self.running = True
        self.capture_thread = threading.Thread(target=self.capture_frames)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
        try:
            # Start Flask server
            self.app.run(host=host, port=port, debug=False, threaded=True)
            
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.stop_server()
        
        return True
    
    def stop_server(self):
        """Stop the server and cleanup"""
        logger.info("Stopping server...")
        
        self.running = False
        
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2)
        
        if self.cap:
            self.cap.release()
        
        logger.info("Server stopped")

def main():
    """Main function"""
    server = FrameServer()
    
    print("\n" + "="*60)
    print("🎥 LOCAL FRAME SERVER (Server 1) - Starting")
    print("="*60)
    print("📋 Purpose: Capture and serve video frames to Flask API Server")
    print("🌐 Server URL: http://127.0.0.1:5000")
    print("📡 Endpoint: /latest_frame (serves frames to Server 2)")
    print("💊 Health: / (server status)")
    print("📊 Stats: /stats (server statistics)")
    print("="*60)
    
    try:
        server.start_server(host='127.0.0.1', port=5000)
    except KeyboardInterrupt:
        print("\n🛑 Server shutdown requested")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
    
    print("👋 Local Frame Server stopped")

if __name__ == "__main__":
    main()