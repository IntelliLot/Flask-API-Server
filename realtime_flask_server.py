#!/usr/bin/env python3
"""
Flask API Server (Server 2) - YOLO Processing Engine
Server 2: Receives frames from Local Server (Server 1) and processes with YOLO
"""

import os
import sys
import threading
import time
import requests
from datetime import datetime
from flask import Flask, request, jsonify
import json
import logging
from queue import Queue, Empty
from collections import deque
import uuid
import cv2
import numpy as np

# Add YoloParklot to path
sys.path.append('../YoloParklot')
from parking_detection.core.parking_system import ParkingDetectionSystem

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealTimeFlaskConfig:
    """Configuration for Flask API Server (Server 2)"""
    
    # Server Configuration
    HOST = '127.0.0.1'
    PORT = 8000
    DEBUG = False
    
    # Local Server Configuration (Server 1)
    LOCAL_SERVER_URL = 'http://127.0.0.1:5000'
    FRAME_REQUEST_INTERVAL = 1.0
    LOCAL_SERVER_TIMEOUT = 10
    AUTO_FETCH_FRAMES = True
    
    # YOLO Configuration
    YOLO_MODEL_PATH = '../YoloParklot/runs/detect/carpk_demo/weights/best.pt'
    PARKING_POSITIONS_PATH = '../YoloParklot/CarParkPos'
    
    # Processing Configuration
    PROCESSING_QUEUE_SIZE = 20
    RESULT_HISTORY_SIZE = 1000
    MAX_CONCURRENT_PROCESSING = 2
    
    # Output Storage Configuration
    OUTPUT_DIR = 'output'
    RESULTS_FILE = 'output/realtime_results.json'
    PROCESSED_IMAGES_DIR = 'output/processed_frames'
    RAW_FRAMES_DIR = 'output/raw_frames'
    SAVE_PROCESSED_IMAGES = True
    SAVE_RAW_FRAMES = True

class RealTimeFlaskServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.config = RealTimeFlaskConfig()
        
        # Initialize YOLO system
        self.parking_system = None
        self.yolo_initialized = False
        
        # Processing queues and threads
        self.processing_queue = Queue(maxsize=self.config.PROCESSING_QUEUE_SIZE)
        self.processing_threads = []
        self.running = False
        
        # Local server frame fetching
        self.frame_fetcher_thread = None
        
        # Results storage
        self.results_history = deque(maxlen=self.config.RESULT_HISTORY_SIZE)
        self.results_lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'requests_received': 0,
            'frames_processed': 0,
            'processing_errors': 0,
            'queue_overflows': 0,
            'total_processing_time': 0,
            'frames_fetched': 0,
            'fetch_errors': 0,
            'start_time': None,
            'last_processing_time': None
        }
        
        # Create output directories
        self.create_output_directories()
        
        # Setup Flask routes
        self.setup_routes()
    
    def create_output_directories(self):
        """Create all necessary output directories"""
        directories = [
            self.config.OUTPUT_DIR,
            self.config.PROCESSED_IMAGES_DIR,
            self.config.RAW_FRAMES_DIR
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def fetch_frame_from_local_server(self):
        """Fetch a frame from the local server"""
        try:
            # Make request to local server for latest frame
            response = requests.get(
                f"{self.config.LOCAL_SERVER_URL}/latest_frame",
                timeout=self.config.LOCAL_SERVER_TIMEOUT
            )
            
            if response.status_code == 200:
                # Check if response contains image data
                if response.headers.get('content-type', '').startswith('image/'):
                    # Direct image response
                    image_data = response.content
                    frame_info = {
                        'timestamp': datetime.now().isoformat(),
                        'camera_id': 'local_server',
                        'frame_id': str(uuid.uuid4())
                    }
                else:
                    # JSON response with frame data
                    data = response.json()
                    if 'success' in data and data['success']:
                        # Handle different response formats
                        if 'image_data' in data:
                            import base64
                            image_data = base64.b64decode(data['image_data'])
                        elif 'frame_url' in data:
                            # Frame is available at a URL
                            frame_response = requests.get(data['frame_url'], timeout=5)
                            image_data = frame_response.content
                        else:
                            return None
                        
                        frame_info = {
                            'timestamp': data.get('timestamp', datetime.now().isoformat()),
                            'camera_id': data.get('camera_id', 'local_server'),
                            'frame_id': data.get('frame_id', str(uuid.uuid4()))
                        }
                    else:
                        logger.warning(f"Local server returned error: {data.get('error', 'Unknown error')}")
                        return None
                
                # Save raw frame if configured
                if self.config.SAVE_RAW_FRAMES:
                    self.save_raw_frame(image_data, frame_info)
                
                return image_data, frame_info
                
            else:
                logger.warning(f"Local server returned status {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.warning("Timeout fetching frame from local server")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning("Connection error to local server")
            return None
        except Exception as e:
            logger.error(f"Error fetching frame from local server: {e}")
            return None
    
    def save_raw_frame(self, image_data, frame_info):
        """Save raw frame to output directory"""
        try:
            filename = f"raw_{frame_info['frame_id']}_{frame_info['timestamp'][:19].replace(':', '-')}.jpg"
            filepath = os.path.join(self.config.RAW_FRAMES_DIR, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
                
        except Exception as e:
            logger.error(f"Error saving raw frame: {e}")
    
    def frame_fetcher_worker(self):
        """Worker thread that continuously fetches frames from local server"""
        logger.info("🔄 Starting frame fetcher from local server")
        
        while self.running:
            try:
                if not self.config.AUTO_FETCH_FRAMES:
                    time.sleep(1)
                    continue
                
                # Fetch frame from local server
                frame_result = self.fetch_frame_from_local_server()
                
                if frame_result:
                    image_data, frame_info = frame_result
                    
                    # Create processing task
                    task = {
                        'task_id': str(uuid.uuid4()),
                        'image_data': image_data,
                        'timestamp': frame_info['timestamp'],
                        'camera_id': frame_info['camera_id'],
                        'frame_id': frame_info['frame_id'],
                        'received_at': datetime.now(),
                        'source': 'local_server'
                    }
                    
                    # Add to processing queue (non-blocking)
                    try:
                        self.processing_queue.put_nowait(task)
                        self.stats['frames_fetched'] += 1
                        
                    except:
                        self.stats['queue_overflows'] += 1
                        logger.warning(f"Processing queue full, dropping frame {frame_info['frame_id']}")
                        
                else:
                    self.stats['fetch_errors'] += 1
                
                # Wait before next fetch
                time.sleep(self.config.FRAME_REQUEST_INTERVAL)
                
            except Exception as e:
                logger.error(f"Frame fetcher error: {e}")
                self.stats['fetch_errors'] += 1
                time.sleep(5)  # Wait longer on error
        
        logger.info("🛑 Frame fetcher stopped")
    
    def initialize_yolo(self):
        """Initialize YOLO parking system"""
        try:
            logger.info("🤖 Initializing YOLO parking system...")
            
            # Check if model and positions files exist
            if not os.path.exists(self.config.YOLO_MODEL_PATH):
                logger.error(f"YOLO model not found: {self.config.YOLO_MODEL_PATH}")
                return False
            
            if not os.path.exists(self.config.PARKING_POSITIONS_PATH):
                logger.error(f"Parking positions not found: {self.config.PARKING_POSITIONS_PATH}")
                return False
            
            # Initialize parking system
            self.parking_system = ParkingDetectionSystem(
                model_path=self.config.YOLO_MODEL_PATH,
                parking_positions_file=self.config.PARKING_POSITIONS_PATH
            )
            
            self.yolo_initialized = True
            logger.info("✅ YOLO parking system initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize YOLO system: {e}")
            return False
    
    def setup_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'yolo_initialized': self.yolo_initialized,
                'queue_size': self.processing_queue.qsize(),
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/stats', methods=['GET'])
        def get_stats():
            """Get processing statistics"""
            stats = self.stats.copy()
            if stats['start_time']:
                runtime = (datetime.now() - stats['start_time']).total_seconds()
                stats['runtime_seconds'] = runtime
                stats['frames_per_second'] = stats['frames_processed'] / runtime if runtime > 0 else 0
                stats['avg_processing_time'] = (stats['total_processing_time'] / 
                                              max(1, stats['frames_processed']))
            
            return jsonify(stats)
        
        @self.app.route('/upload', methods=['POST'])
        def upload_frame():
            """Process uploaded frame with YOLO"""
            try:
                self.stats['requests_received'] += 1
                
                # Check if YOLO is initialized
                if not self.yolo_initialized:
                    return jsonify({
                        'success': False,
                        'error': 'YOLO system not initialized'
                    }), 500
                
                # Check if image is provided
                if 'image' not in request.files:
                    return jsonify({
                        'success': False,
                        'error': 'No image file provided'
                    }), 400
                
                image_file = request.files['image']
                if image_file.filename == '':
                    return jsonify({
                        'success': False,
                        'error': 'Empty filename'
                    }), 400
                
                # Get metadata
                timestamp = request.form.get('timestamp', datetime.now().isoformat())
                camera_id = request.form.get('camera_id', 'unknown')
                frame_id = request.form.get('frame_id', str(uuid.uuid4()))
                
                # Read image data
                image_data = image_file.read()
                
                # Create processing task
                task = {
                    'task_id': str(uuid.uuid4()),
                    'image_data': image_data,
                    'timestamp': timestamp,
                    'camera_id': camera_id,
                    'frame_id': frame_id,
                    'received_at': datetime.now(),
                    'source': 'upload'
                }
                
                # Add to processing queue (non-blocking)
                try:
                    self.processing_queue.put_nowait(task)
                    logger.debug(f"📤 Queued frame {frame_id} for processing")
                    
                    return jsonify({
                        'success': True,
                        'task_id': task['task_id'],
                        'frame_id': frame_id,
                        'message': 'Frame queued for processing'
                    })
                    
                except:
                    self.stats['queue_overflows'] += 1
                    return jsonify({
                        'success': False,
                        'error': 'Processing queue full'
                    }), 503
                
            except Exception as e:
                logger.error(f"Upload endpoint error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/results', methods=['GET'])
        def get_results():
            """Get recent processing results"""
            try:
                limit = int(request.args.get('limit', 10))
                
                with self.results_lock:
                    results = list(self.results_history)[-limit:]
                
                return jsonify({
                    'success': True,
                    'count': len(results),
                    'results': results
                })
                
            except Exception as e:
                logger.error(f"Results endpoint error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/results/latest', methods=['GET'])
        def get_latest_result():
            """Get latest processing result"""
            try:
                with self.results_lock:
                    if self.results_history:
                        latest = self.results_history[-1]
                        return jsonify({
                            'success': True,
                            'result': latest
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'error': 'No results available'
                        }), 404
                        
            except Exception as e:
                logger.error(f"Latest result endpoint error: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
    
    def process_frame_with_yolo(self, image_data, task_info):
        """Process frame with YOLO parking detection"""
        try:
            start_time = time.time()
            
            # Convert image data to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                raise Exception("Failed to decode image data")
            
            # Process with YOLO
            annotated_frame, statistics, processing_time_yolo = self.parking_system.process_frame(frame)
            
            processing_time = time.time() - start_time
            self.stats['total_processing_time'] += processing_time
            self.stats['last_processing_time'] = processing_time
            
            # Create result record
            result_record = {
                'task_id': task_info['task_id'],
                'frame_id': task_info['frame_id'],
                'camera_id': task_info['camera_id'],
                'timestamp': task_info['timestamp'],
                'processed_at': datetime.now().isoformat(),
                'processing_time_ms': int(processing_time * 1000),
                'parking_data': {
                    'total_slots': statistics.get('total_slots', 0),
                    'occupied_slots': statistics.get('occupied_slots', 0),
                    'empty_slots': statistics.get('empty_slots', 0),
                    'occupancy_rate': statistics.get('occupancy_rate', 0.0)
                },
                'success': True,
                'processed_image': annotated_frame if self.config.SAVE_PROCESSED_IMAGES else None
            }
            
            # Store result
            with self.results_lock:
                self.results_history.append(result_record)
            
            # Save to file (exclude processed_image which is not JSON serializable)
            result_to_save = result_record.copy()
            if 'processed_image' in result_to_save:
                del result_to_save['processed_image']
            self.save_result_to_file(result_to_save)
            
            # Save processed image if configured
            if self.config.SAVE_PROCESSED_IMAGES and annotated_frame is not None:
                self.save_processed_image(annotated_frame, task_info)
            
            self.stats['frames_processed'] += 1
            
            logger.info(f"✅ Processed frame {task_info['frame_id']} - "
                      f"Occupied: {statistics.get('occupied_slots', 0)}/{statistics.get('total_slots', 0)} "
                      f"({statistics.get('occupancy_rate', 0):.1f}%) - "
                      f"Time: {processing_time*1000:.1f}ms")
            
            return result_record
                
        except Exception as e:
            self.stats['processing_errors'] += 1
            error_record = {
                'task_id': task_info['task_id'],
                'frame_id': task_info['frame_id'],
                'camera_id': task_info['camera_id'],
                'timestamp': task_info['timestamp'],
                'processed_at': datetime.now().isoformat(),
                'error': str(e),
                'success': False
            }
            
            with self.results_lock:
                self.results_history.append(error_record)
            
            logger.error(f"❌ Failed to process frame {task_info['frame_id']}: {e}")
            return error_record
    
    def save_result_to_file(self, result):
        """Save result to JSON file"""
        try:
            # Append to results file
            with open(self.config.RESULTS_FILE, 'a') as f:
                f.write(json.dumps(result) + '\n')
        except Exception as e:
            logger.error(f"Error saving result to file: {e}")
    
    def save_processed_image(self, processed_image, task_info):
        """Save processed image with parking annotations"""
        try:
            timestamp_safe = task_info['timestamp'][:19].replace(':', '-')
            
            filename = f"processed_{task_info['frame_id']}_{timestamp_safe}.jpg"
            filepath = os.path.join(self.config.PROCESSED_IMAGES_DIR, filename)
            
            cv2.imwrite(filepath, processed_image)
            
        except Exception as e:
            logger.error(f"Error saving processed image: {e}")
    
    def processing_worker(self, worker_id):
        """Worker thread for processing frames"""
        logger.info(f"🔄 Starting processing worker {worker_id}")
        
        while self.running:
            try:
                # Get task from queue with timeout
                task = self.processing_queue.get(timeout=1.0)
                
                # Process frame with YOLO
                result = self.process_frame_with_yolo(task['image_data'], task)
                
                # Mark task as done
                self.processing_queue.task_done()
                
            except Empty:
                continue  # No tasks in queue
            except Exception as e:
                logger.error(f"Processing worker {worker_id} error: {e}")
                try:
                    self.processing_queue.task_done()
                except:
                    pass
        
        logger.info(f"🛑 Processing worker {worker_id} stopped")
    
    def start_server(self):
        """Start the real-time Flask server"""
        logger.info("🚀 Starting Flask API Server (Server 2)")
        
        # Initialize YOLO system
        if not self.initialize_yolo():
            logger.error("Failed to initialize YOLO system")
            return False
        
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        # Start processing workers
        for i in range(self.config.MAX_CONCURRENT_PROCESSING):
            worker = threading.Thread(target=self.processing_worker, args=(i,), daemon=True)
            worker.start()
            self.processing_threads.append(worker)
        
        # Start frame fetcher from local server
        if self.config.AUTO_FETCH_FRAMES:
            self.frame_fetcher_thread = threading.Thread(target=self.frame_fetcher_worker, daemon=True)
            self.frame_fetcher_thread.start()
            logger.info("🔄 Started frame fetcher from local server")
        
        logger.info(f"✅ Flask API Server running on {self.config.HOST}:{self.config.PORT}")
        logger.info(f"📡 Fetching from: {self.config.LOCAL_SERVER_URL}")
        logger.info(f"🗂️ Output directory: {self.config.OUTPUT_DIR}")
        
        try:
            # Start Flask server
            self.app.run(
                host=self.config.HOST,
                port=self.config.PORT,
                debug=self.config.DEBUG,
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            logger.error(f"Flask server error: {e}")
        finally:
            self.stop()
        
        return True
    
    def stop(self):
        """Stop the real-time server"""
        logger.info("🛑 Stopping real-time Flask server...")
        
        self.running = False
        
        # Wait for processing queue to empty
        try:
            self.processing_queue.join()
        except:
            pass
        
        logger.info("✅ Real-time Flask server stopped")

def main():
    """Main function"""
    print("🤖 Flask API Server (Server 2) - YOLO Processing Engine")
    print("=" * 60)
    print(f"🌐 Server: http://{RealTimeFlaskConfig.HOST}:{RealTimeFlaskConfig.PORT}")
    print(f"📡 Fetching from: {RealTimeFlaskConfig.LOCAL_SERVER_URL}")
    print(f"️ Output: {RealTimeFlaskConfig.OUTPUT_DIR}")
    print("=" * 60)
    
    server = RealTimeFlaskServer()
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        server.stop()

if __name__ == "__main__":
    main()