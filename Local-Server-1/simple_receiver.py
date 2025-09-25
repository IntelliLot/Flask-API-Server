#!/usr/bin/env python3
"""
Simple Test Receiver (Server II)
Receives frames from Video Feed Server for testing
"""

from flask import Flask, request, jsonify
import os
from datetime import datetime

app = Flask(__name__)

# Create directory for received frames
RECEIVED_DIR = 'received_frames'
os.makedirs(RECEIVED_DIR, exist_ok=True)

@app.route('/')
def index():
    """Simple status page"""
    frame_count = len([f for f in os.listdir(RECEIVED_DIR) if f.endswith('.jpg')])
    return f"""
    <h1>Video Feed Receiver (Server II)</h1>
    <p>Status: Active</p>
    <p>Frames received: {frame_count}</p>
    <p>Upload endpoint: <code>/upload</code></p>
    <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    """

@app.route('/upload', methods=['POST'])
def receive_frame():
    """Receive frame from Video Feed Server"""
    try:
        # Check if image was uploaded
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        image_file = request.files['image']
        
        # Get metadata
        timestamp = request.form.get('timestamp', datetime.now().isoformat())
        camera_id = request.form.get('camera_id', 'unknown')
        server_type = request.form.get('server_type', 'unknown')
        
        # Create filename
        dt = datetime.now()
        filename = f"frame_{dt.strftime('%Y%m%d_%H%M%S')}_cam{camera_id}.jpg"
        filepath = os.path.join(RECEIVED_DIR, filename)
        
        # Save the frame
        image_file.save(filepath)
        
        file_size = os.path.getsize(filepath)
        
        print(f"📸 Received frame: {filename} ({file_size} bytes) from {server_type}")
        
        return jsonify({
            'status': 'success',
            'message': 'Frame received',
            'filename': filename,
            'size': file_size,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"❌ Error receiving frame: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'server': 'Video Feed Receiver'})

if __name__ == '__main__':
    print("🚀 Starting Video Feed Receiver (Server II)")
    print(f"📁 Saving frames to: {RECEIVED_DIR}")
    print("🌐 Access at: http://localhost:5000/")
    print("📤 Upload endpoint: http://localhost:5000/upload")
    print()
    
    app.run(host='0.0.0.0', port=5000, debug=True)