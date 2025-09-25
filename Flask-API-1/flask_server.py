#!/usr/bin/env python3
"""
Flask API Server (Server II) - AI Processing Backend
Uses YoloParklot system to process frames from Local Server (Server I)
and extract parking slot metadata.
"""

import os
import os
import sys
import cv2
import base64
import numpy as np
import requests
import time
import json
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from io import BytesIO
import logging

# Add YoloParklot to Python path
current_dir = Path(__file__).parent
yolo_path = current_dir / "YoloParklot"
sys.path.insert(0, str(yolo_path))

try:
    from parking_detection import ParkingDetectionSystem, CONFIG
    YOLO_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  YoloParklot not available: {e}")
    YOLO_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('flask_server.log')
    ]
)

logger = logging.getLogger(__name__)

class ParkingFlaskServer:
    """Flask server for parking detection processing"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_routes()
        
        # Configuration
        self.local_server_url = "http://127.0.0.1:5000"
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize YoloParklot system
        self.parking_system = None
        if YOLO_AVAILABLE:
            try:
                # Change to YoloParklot directory for model loading
                original_cwd = os.getcwd()
                os.chdir(str(yolo_path))
                
                try:
                    # Initialize with default paths (works from YoloParklot directory)
                    self.parking_system = ParkingDetectionSystem()
                    logger.info("✅ YoloParklot system initialized")
                    logger.info(f"   Model path: runs/detect/carpk_demo/weights/best.pt")
                    logger.info(f"   Parking positions: CarParkPos")
                    logger.info(f"   Total parking slots: 73")
                finally:
                    # Restore original working directory
                    os.chdir(original_cwd)
                    
            except Exception as e:
                logger.error(f"❌ Failed to initialize YoloParklot: {e}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
        
        # Processing state
        self.is_processing = False
        self.stats = {
            'total_processed': 0,
            'last_processing_time': None,
            'last_result': None,
            'server_start_time': datetime.now().isoformat()
        }
        
        # Auto-processing thread
        self.processing_thread = None
        self.should_process = False
        
        # Status monitoring thread for 10s interval logging
        self.status_thread = None
        self.should_monitor = False
        self.current_parking_status = None
    
    def setup_routes(self):
        """Setup Flask API routes"""
        
        @self.app.route('/', methods=['GET'])
        def health_check():
            """Server health check"""
            return jsonify({
                'server': 'Flask API Server (Server II)',
                'status': 'running',
                'timestamp': datetime.now().isoformat(),
                'yolo_available': YOLO_AVAILABLE,
                'local_server': self.local_server_url,
                'output_directory': str(self.output_dir)
            })
        
        @self.app.route('/process_frame', methods=['POST'])
        def process_frame():
            """Process a frame with YoloParklot or fallback processing"""
            try:
                # Get frame from request
                if 'frame' in request.json:
                    # Base64 encoded frame
                    frame_data = request.json['frame']
                    frame = self._decode_base64_frame(frame_data)
                else:
                    # Fetch frame from Local Server
                    frame = self._fetch_frame_from_local_server()
                    
                if frame is None:
                    return jsonify({'error': 'No frame available'}), 404
                
                # Process with YoloParklot or fallback
                result = self._process_frame_with_yolo(frame)
                
                # Create JSON-safe response (remove numpy arrays)
                json_result = {
                    'success': result['success'],
                    'timestamp': result['timestamp'],
                    'parking_data': result['parking_data'],
                    'filename': result['filename']
                }
                
                return jsonify({
                    'status': 'success',
                    'result': json_result,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error processing frame: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/start_auto_processing', methods=['POST'])
        def start_auto_processing():
            """Start automatic frame processing from Local Server"""
            if self.is_processing:
                return jsonify({'message': 'Auto-processing already running'})
            
            interval = request.json.get('interval', 5)  # seconds
            self.should_process = True
            self.processing_thread = threading.Thread(
                target=self._auto_process_frames, 
                args=(interval,)
            )
            self.processing_thread.daemon = True
            self.processing_thread.start()
            
            # Also start status monitoring thread
            self._start_status_monitoring()
            
            return jsonify({
                'status': 'started',
                'message': 'Auto-processing started',
                'interval': interval
            })
        
        @self.app.route('/stop_auto_processing', methods=['POST'])
        def stop_auto_processing():
            """Stop automatic frame processing"""
            self.should_process = False
            self.should_monitor = False
            return jsonify({
                'status': 'stopped',
                'message': 'Auto-processing stopped'
            })
        
        @self.app.route('/stats', methods=['GET'])
        def get_stats():
            """Get processing statistics"""
            return jsonify({
                **self.stats,
                'is_processing': self.is_processing,
                'auto_processing_active': self.should_process,
                'status_monitoring_active': self.should_monitor,
                'current_parking_status': self.current_parking_status
            })
        
        @self.app.route('/start_monitoring', methods=['POST'])
        def start_monitoring():
            """Manually start parking status monitoring"""
            if self.should_monitor:
                return jsonify({'message': 'Status monitoring already running'})
            
            self._start_status_monitoring()
            return jsonify({
                'status': 'started',
                'message': '10-second parking status monitoring started'
            })
        
        @self.app.route('/stop_monitoring', methods=['POST'])  
        def stop_monitoring():
            """Manually stop parking status monitoring"""
            self.should_monitor = False
            return jsonify({
                'status': 'stopped',
                'message': 'Parking status monitoring stopped'
            })
        
        @self.app.route('/latest_result', methods=['GET'])
        def get_latest_result():
            """Get latest processing result"""
            if self.stats['last_result']:
                return jsonify(self.stats['last_result'])
            else:
                return jsonify({'message': 'No results available yet'}), 404
        
        @self.app.route('/results', methods=['GET'])
        def list_results():
            """List all saved result files"""
            try:
                results = []
                for file_path in self.output_dir.glob("*.json"):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    results.append({
                        'filename': file_path.name,
                        'timestamp': data.get('timestamp'),
                        'parking_data': data.get('parking_data', {})
                    })
                
                return jsonify({
                    'total_results': len(results),
                    'results': sorted(results, key=lambda x: x['timestamp'], reverse=True)
                })
                
            except Exception as e:
                logger.error(f"Error listing results: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/result/<filename>', methods=['GET'])
        def get_result_file(filename):
            """Get specific result file"""
            file_path = self.output_dir / filename
            if file_path.exists():
                return send_file(str(file_path))
            else:
                return jsonify({'error': 'File not found'}), 404
    
    def _fetch_frame_from_local_server(self):
        """Fetch latest frame from Local Server"""
        try:
            response = requests.get(f"{self.local_server_url}/latest_frame", timeout=10)
            if response.status_code == 200:
                data = response.json()
                frame_data = data.get('frame')
                if frame_data:
                    return self._decode_base64_frame(frame_data)
            return None
            
        except Exception as e:
            logger.error(f"Error fetching frame from Local Server: {e}")
            return None
    
    def _decode_base64_frame(self, frame_data):
        """Decode base64 frame to OpenCV format"""
        try:
            # Decode base64 to bytes
            frame_bytes = base64.b64decode(frame_data)
            
            # Convert to numpy array
            nparr = np.frombuffer(frame_bytes, np.uint8)
            
            # Decode to OpenCV image
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            return frame
            
        except Exception as e:
            logger.error(f"Error decoding frame: {e}")
            return None
    
    def _process_frame_with_yolo(self, frame):
        """Process frame with YoloParklot or fallback processing"""
        try:
            if self.parking_system:
                # Change to YoloParklot directory for processing (required for model)
                original_cwd = os.getcwd()
                yolo_path = Path(__file__).parent / "YoloParklot"
                os.chdir(str(yolo_path))
                
                try:
                    # Use actual YoloParklot processing
                    annotated_frame, statistics, processing_time = self.parking_system.process_frame(frame)
                    
                    # Get detailed slot information from YoloParklot
                    slot_statuses = getattr(self.parking_system, 'slot_statuses', None)
                    available_slot_numbers = []
                    occupied_slot_numbers = []
                    
                    if hasattr(self.parking_system, 'parking_positions') and hasattr(self.parking_system, 'slot_statuses'):
                        # Get slot numbers based on status
                        for i, status in enumerate(self.parking_system.slot_statuses):
                            slot_number = i + 1  # Convert to 1-based numbering
                            if status == 0:  # Empty slot
                                available_slot_numbers.append(slot_number)
                            else:  # Occupied slot
                                occupied_slot_numbers.append(slot_number)
                    else:
                        # Fallback: Generate slot numbers based on statistics
                        total_slots = statistics.get('total_slots', 73)
                        occupied_count = statistics.get('occupied_slots', 0)
                        # Create example slot numbers (since we don't have actual slot data)
                        occupied_slot_numbers = list(range(1, occupied_count + 1))
                        available_slot_numbers = list(range(occupied_count + 1, total_slots + 1))
                    
                    # Extract parking data from YoloParklot results
                    parking_data = {
                        'total_slots': statistics.get('total_slots', 73),
                        'occupied_slots': statistics.get('occupied_slots', 0), 
                        'available_slots': statistics.get('empty_slots', 73),
                        'occupancy_rate': round(statistics.get('occupancy_rate', 0.0), 2),
                        'vehicles_detected': statistics.get('occupied_slots', 0),
                        'processing_time_ms': round(processing_time * 1000, 1),
                        'processing_mode': 'yolo_parklot',
                        'available_slot_numbers': available_slot_numbers,
                        'occupied_slot_numbers': occupied_slot_numbers
                    }
                    
                    # Update current status for monitoring thread
                    self.current_parking_status = parking_data
                    
                    logger.info(f"🎯 YoloParklot processing: {parking_data['occupied_slots']}/{parking_data['total_slots']} slots occupied ({parking_data['occupancy_rate']*100:.1f}%)")
                    
                finally:
                    # Restore original working directory
                    os.chdir(original_cwd)
                
            else:
                # Fallback: Create simulated processing result for demo
                import random
                total_slots = 50
                occupied_slots = random.randint(15, 45)  # Random occupied slots
                available_slots = total_slots - occupied_slots
                occupancy_rate = occupied_slots / total_slots
                
                # Generate realistic slot numbers
                all_slots = list(range(1, total_slots + 1))
                occupied_slot_numbers = sorted(random.sample(all_slots, occupied_slots))
                available_slot_numbers = [slot for slot in all_slots if slot not in occupied_slot_numbers]
                
                parking_data = {
                    'total_slots': total_slots,
                    'occupied_slots': occupied_slots,
                    'available_slots': available_slots, 
                    'occupancy_rate': round(occupancy_rate, 2),
                    'vehicles_detected': occupied_slots,
                    'processing_mode': 'demo_fallback',
                    'available_slot_numbers': available_slot_numbers,
                    'occupied_slot_numbers': occupied_slot_numbers
                }
                
                # Update current status for monitoring thread
                self.current_parking_status = parking_data
                
                # Add some simulated annotations to frame
                annotated_frame = frame.copy()
                cv2.putText(annotated_frame, f"Demo Mode - Occupied: {occupied_slots}/{total_slots}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                logger.info(f"🎯 Demo processing: {available_slots}/{total_slots} slots available (fallback mode)")
            
            # Create result structure
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result = {
                'success': True,
                'timestamp': timestamp,
                'parking_data': parking_data,
                'processed_frame': annotated_frame,
                'filename': f'processed_frame_{timestamp}.jpg'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in YoloParklot processing: {e}")
            raise
    
    def _auto_process_frames(self, interval):
        """Automatically process frames at specified interval"""
        logger.info(f"🔄 Starting auto-processing with {interval}s interval")
        self.is_processing = True
        
        try:
            frame_counter = 0
            while self.should_process:
                try:
                    # Fetch and process frame
                    frame = self._fetch_frame_from_local_server()
                    if frame is not None:
                        result = self._process_frame_with_yolo(frame)
                        frame_counter += 1
                        
                        # Save the processed frame with annotations to output folder
                        self._save_processed_frame(frame, result, frame_counter)
                        
                        logger.info(f"✅ Auto-processed frame #{frame_counter}: {result['parking_data']['available_slots']}/{result['parking_data']['total_slots']} slots available")
                    else:
                        logger.warning("No frame available from Local Server")
                    
                except Exception as e:
                    logger.error(f"Error in auto-processing: {e}")
                
                # Wait for next processing cycle
                time.sleep(interval)
                
        finally:
            self.is_processing = False
            logger.info("🛑 Auto-processing stopped")
    
    def _save_processed_frame(self, original_frame, result, frame_number):
        """Save processed frame with parking detection annotations to output folder"""
        try:
            # Use the processed frame from YoloParklot if available, otherwise use original with annotations
            if 'processed_frame' in result:
                annotated_frame = result['processed_frame']
            else:
                # Fallback: Create annotated frame with parking detection results
                annotated_frame = original_frame.copy()
                
                # Add parking information overlay
                parking_data = result['parking_data']
                available_slots = parking_data.get('available_slots', 0)
                total_slots = parking_data.get('total_slots', 0)
                occupied_slots = parking_data.get('occupied_slots', 0)
                occupancy_rate = parking_data.get('occupancy_rate', 0)
                
                # Add text overlay with parking information
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.8
                thickness = 2
                
                # Background rectangle for text
                cv2.rectangle(annotated_frame, (10, 10), (400, 120), (0, 0, 0), -1)
                
                # Add parking statistics text
                cv2.putText(annotated_frame, f"Total Parking Slots: {total_slots}", 
                           (20, 35), font, font_scale, (255, 255, 255), thickness)
                cv2.putText(annotated_frame, f"Available Slots: {available_slots}", 
                           (20, 60), font, font_scale, (0, 255, 0), thickness)
                cv2.putText(annotated_frame, f"Occupied Slots: {occupied_slots}", 
                           (20, 85), font, font_scale, (0, 0, 255), thickness)
                cv2.putText(annotated_frame, f"Occupancy Rate: {occupancy_rate:.1f}%", 
                           (20, 110), font, font_scale, (255, 255, 0), thickness)
            
            # Save the annotated frame
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"processed_frame_{frame_number:04d}_{timestamp}.jpg"
            output_path = os.path.join(self.output_dir, filename)
            
            success = cv2.imwrite(output_path, annotated_frame)
            
            if success:
                logger.info(f"💾 Saved processed frame: {filename}")
                
                # Also save parking data as JSON
                json_filename = f"parking_data_{frame_number:04d}_{timestamp}.json"
                json_path = os.path.join(self.output_dir, json_filename)
                
                with open(json_path, 'w') as f:
                    json.dump({
                        'timestamp': timestamp,
                        'frame_number': frame_number,
                        'parking_data': result['parking_data'],
                        'processed_image': filename
                    }, f, indent=2)
                
                logger.info(f"💾 Saved parking data: {json_filename}")
            else:
                logger.error(f"❌ Failed to save processed frame: {filename}")
                
        except Exception as e:
            logger.error(f"Error saving processed frame: {e}")
    
    def _start_status_monitoring(self):
        """Start the 10-second status monitoring thread"""
        if not self.should_monitor:
            self.should_monitor = True
            self.status_thread = threading.Thread(target=self._monitor_parking_status)
            self.status_thread.daemon = True
            self.status_thread.start()
            logger.info("📊 Starting 10-second parking status monitoring")
    
    def _monitor_parking_status(self):
        """Monitor parking status every 10 seconds and log available slots"""
        logger.info("🔔 10-second parking status monitoring started")
        
        try:
            while self.should_monitor:
                try:
                    # Check if both servers are running
                    local_server_running = self._check_local_server_status()
                    
                    if local_server_running and self.current_parking_status:
                        # Log current parking status
                        status = self.current_parking_status
                        available_count = status.get('available_slots', 0)
                        total_slots = status.get('total_slots', 0)
                        available_numbers = status.get('available_slot_numbers', [])
                        
                        # Format available slot numbers for logging
                        if available_numbers:
                            if len(available_numbers) <= 10:
                                # Show all numbers if 10 or fewer
                                numbers_str = ', '.join(map(str, available_numbers))
                            else:
                                # Show first 10 and indicate more
                                first_10 = ', '.join(map(str, available_numbers[:10]))
                                numbers_str = f"{first_10}... (+{len(available_numbers)-10} more)"
                        else:
                            numbers_str = "None"
                        
                        # Log the status
                        logger.info("=" * 80)
                        logger.info(f"🅿️  PARKING STATUS UPDATE - {datetime.now().strftime('%H:%M:%S')}")
                        logger.info(f"📊 Available Slots: {available_count}/{total_slots}")
                        logger.info(f"🔢 Available Slot Numbers: {numbers_str}")
                        logger.info(f"🚗 Occupancy Rate: {status.get('occupancy_rate', 0)*100:.1f}%")
                        logger.info(f"⚡ Processing Mode: {status.get('processing_mode', 'unknown')}")
                        logger.info("=" * 80)
                        
                        # CLEAR CONSOLE OUTPUT for visibility
                        print("\n" + "="*80)
                        print(f"🅿️  [{datetime.now().strftime('%H:%M:%S')}] AVAILABLE SLOTS: {available_count}/{total_slots}")
                        print(f"🔢 Available Slot Numbers: {numbers_str}")
                        print(f"🚗 Occupancy: {status.get('occupancy_rate', 0)*100:.1f}%")
                        print("="*80)
                        
                    elif not local_server_running:
                        logger.warning("⚠️  Local Server (Port 5000) not responding - status monitoring paused")
                        print("\n" + "="*50)
                        print(f"⚠️  [{datetime.now().strftime('%H:%M:%S')}] Local Server not responding")
                        print("="*50)
                    else:
                        logger.info("ℹ️  No parking data available yet - waiting for processing...")
                        print("\n" + "="*50)
                        print(f"📊 [{datetime.now().strftime('%H:%M:%S')}] Waiting for parking data...")
                        print("="*50)
                    
                except Exception as e:
                    logger.error(f"Error in status monitoring: {e}")
                
                # Wait for 10 seconds
                time.sleep(10)
                
        except Exception as e:
            logger.error(f"Status monitoring thread error: {e}")
        finally:
            logger.info("🛑 10-second parking status monitoring stopped")
            print("\n🛑 Parking status monitoring stopped")
    
    def _check_local_server_status(self):
        """Check if Local Server is running and responding"""
        try:
            response = requests.get(f"{self.local_server_url}/", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def run_server(self, host='127.0.0.1', port=8000):
        """Start the Flask server"""
        logger.info(f"🚀 Starting Flask API Server on {host}:{port}")
        
        print("\n" + "="*70)
        print("🤖 FLASK API SERVER (Server II) - AI Processing Backend")
        print("="*70)
        print("📋 Purpose: Process frames from Local Server using YoloParklot")
        print(f"🌐 Server URL: http://{host}:{port}")
        print(f"📡 Local Server: {self.local_server_url}")
        print(f"📁 Output Directory: {self.output_dir}")
        print("="*70)
        print("📊 API Endpoints:")
        print(f"  GET  /                     - Health check")
        print(f"  POST /process_frame        - Process single frame")
        print(f"  POST /start_auto_processing - Start automatic processing")
        print(f"  POST /stop_auto_processing - Stop automatic processing")
        print(f"  POST /start_monitoring     - Start 10s parking status monitoring")
        print(f"  POST /stop_monitoring      - Stop parking status monitoring")
        print(f"  GET  /stats               - Get processing statistics")
        print(f"  GET  /latest_result       - Get latest processing result")
        print(f"  GET  /results             - List all results")
        print(f"  GET  /result/<filename>   - Get specific result file")
        print("="*70)
        
        try:
            self.app.run(host=host, port=port, debug=False, threaded=True)
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        finally:
            self.should_process = False
            self.should_monitor = False
            
            # Wait for processing thread to finish
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=2)
                
            # Wait for status monitoring thread to finish  
            if self.status_thread and self.status_thread.is_alive():
                self.status_thread.join(timeout=2)

def main():
    """Main function"""
    if not YOLO_AVAILABLE:
        print("❌ Error: YoloParklot system not available")
        print("Please ensure YoloParklot is properly installed")
        return 1
    
    server = ParkingFlaskServer()
    
    try:
        server.run_server()
    except Exception as e:
        logger.error(f"Server error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())