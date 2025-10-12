# Two-Server YOLO Parking Detection Architecture

## Overview
A complete two-server architecture for AI-powered parking space detection using YOLOv8. The system provides real-time parking lot monitoring with automated console output every 10 seconds, displaying available parking slots and precise slot numbers. Designed with clear separation of concerns between frame capture and AI processing.

## Key Features
- **Real-time Monitoring**: Automatic 10-second interval updates showing parking status
- **Console Output**: Live updates displaying available slots and specific slot numbers (1,2,3...)
- **73 Parking Slots**: Complete parking lot coverage with individual slot tracking
- **Sub-100ms Processing**: Fast AI processing with YOLOv8 vehicle detection
- **Multiple Deployment Options**: Background, interactive, and live viewing modes

## Architecture

```
┌─────────────────────────────┐         ┌─────────────────────────────┐
│      Local Server           │         │     Flask API Server        │
│      (Server I)             │         │     (Server II)             │
│      Port: 5000             │ ◄────── │     Port: 8000             │
│                             │  Fetch  │                             │
│ ┌─────────────────────────┐ │ Frames  │ ┌─────────────────────────┐ │
│ │   Frame Capture         │ │         │ │   YoloParklot           │ │
│ │   • Camera/Video        │ │         │ │   • AI Processing       │ │
│ │   • OpenCV              │ │         │ │   • Vehicle Detection   │ │
│ │   • REST API            │ │         │ │   • Parking Analysis    │ │
│ │                         │ │         │ │   • Metadata Extract    │ │
│ │ Endpoints:              │ │         │ │                         │ │
│ │ • GET /                 │ │         │ │ Endpoints:              │ │
│ │ • GET /latest_frame     │ │         │ │ • POST /process_frame   │ │
│ │ • GET /stats            │ │         │ │ • POST /start_auto_*    │ │
│ └─────────────────────────┘ │         │ │ • GET /stats            │ │
└─────────────────────────────┘         │ │ • GET /results          │ │
                                        │ └─────────────────────────┘ │
                                        │                             │
                                        │ ┌─────────────────────────┐ │
                                        │ │   Local Storage         │ │
                                        │ │   • output/             │ │
                                        │ │   • Processed frames    │ │
                                        │ │   • JSON results        │ │
                                        │ │   • Parking metadata    │ │
                                        │ └─────────────────────────┘ │
                                        └─────────────────────────────┘
```

## Components

### Server I - Local Server (Frame Provider)
**Purpose**: Captures video frames and serves them via REST API  
**Location**: `Local-Server-1/`  
**Main File**: `frame_server.py`  
**Port**: 5000

**Features**:
- Real-time frame capture from camera or video file
- REST API with `/latest_frame` endpoint
- Base64 encoded frame delivery
- Thread-safe frame storage
- Health check and statistics

**API Endpoints**:
- `GET /` - Health check
- `GET /latest_frame` - Returns base64 encoded frame
- `GET /stats` - Server statistics

### Server II - Flask API Server (AI Processor)
**Purpose**: Processes frames using YoloParklot and extracts parking metadata  
**Location**: `Flask-API-1/`  
**Main File**: `flask_server.py`  
**Port**: 8000

**Features**:
- Fetches frames from Local Server every 10 seconds
- YoloParklot integration for vehicle detection (73 parking slots)
- Real-time console monitoring with parking status updates
- Parking space analysis and occupancy detection
- Automatic processing with configurable intervals
- Local result storage (JSON + processed images)
- RESTful API for client integration
- Console output format: "=== PARKING STATUS UPDATE === | Available Slots: X/73 | Slot Numbers: 1,2,3,..."

**API Endpoints**:
- `GET /` - Health check
- `POST /process_frame` - Process single frame
- `POST /start_auto_processing` - Start automatic processing
- `POST /stop_auto_processing` - Stop automatic processing
- `GET /stats` - Processing statistics
- `GET /latest_result` - Latest processing result
- `GET /results` - List all results
- `GET /result/<filename>` - Get specific result file

## Metadata Extracted

The Flask API Server extracts and stores the following parking metadata:

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "parking_data": {
    "total_slots": 50,
    "occupied_slots": 32,
    "available_slots": 18,
    "occupancy_rate": 0.64
  },
  "detections": {
    "vehicle_count": 32,
    "vehicles": [
      {
        "confidence": 0.85,
        "bbox": [100, 200, 150, 250],
        "class_name": "car"
      }
    ]
  },
  "output_files": {
    "processed_frame": "processed_frame_20240101_120000.jpg"
  }
}
```

## Quick Start

### 1. Setup Dependencies

**Local Server (Server I)**:
```bash
cd Local-Server-1
pip install -r requirements.txt
```

**Flask API Server (Server II)**:
```bash
cd Flask-API-1
# Setup YoloParklot
./setup_yoloparklot.sh

# Install dependencies
pip install -r requirements.txt
```

### 2. Start System (Choose One Method)

**Option A: Complete Background System (Recommended)**
```bash
./start_complete_system.sh
# View outputs: check /tmp/flask_output.log and /tmp/local_output.log
```

**Option B: Interactive Mode (Live Console Output)**
```bash
./run_interactive_system.sh
# Flask console output visible directly in terminal
```

**Option C: Background + Live Viewer**
```bash
./start_complete_system.sh
./view_live_output.sh  # In another terminal to see live console output
```

**Option D: Manual Start**
```bash
# Terminal 1 - Local Server
cd Local-Server-1
python frame_server.py

# Terminal 2 - Flask API Server  
cd Flask-API-1
python flask_server.py
```

### 3. Monitor Console Output

The Flask API server automatically displays parking status every 10 seconds:
```
========================================
=== PARKING STATUS UPDATE ===
Available Slots: 73/73
Slot Numbers: 1,2,3,4,5,6,7,8,9,10,...
Processing Time: 82.5ms
Timestamp: 2024-12-27 04:26:37
========================================
```

### 4. Verify System
```bash
# Check system health
curl http://127.0.0.1:5000/    # Local Server
curl http://127.0.0.1:8000/    # Flask API Server
```

## Monitoring Features

### Console Output
The Flask API server provides real-time monitoring with console updates every 10 seconds:

```bash
# Example Console Output:
========================================
=== PARKING STATUS UPDATE ===
Available Slots: 69/73
Slot Numbers: 1,2,3,8,12,15,18,21,24,27,30,33,36,39,42,45,48,51,54,57,60,63,66,69,72
Processing Time: 89.3ms
Timestamp: 2024-12-27 04:28:15
========================================
```

### Log Files (Background Mode)
When using background mode, outputs are saved to:
- Flask Server: `/tmp/flask_output.log`
- Local Server: `/tmp/local_output.log`

### Live Output Viewing
```bash
# View live Flask console output
tail -f /tmp/flask_output.log

# View live Local server output  
tail -f /tmp/local_output.log

# Or use the provided script
./view_live_output.sh
```

### System Status Scripts
Available utility scripts for monitoring:
- `start_complete_system.sh` - Complete background startup
- `run_interactive_system.sh` - Interactive mode with live console
- `view_live_output.sh` - Live output viewer

### Basic Frame Processing
```bash
# Get health status
curl http://127.0.0.1:5000/        # Local Server
curl http://127.0.0.1:8000/        # Flask API Server

# Get latest frame from Local Server
curl http://127.0.0.1:5000/latest_frame

# Process single frame
curl -X POST http://127.0.0.1:8000/process_frame
```

### Automatic Processing
```bash
# Start auto-processing (every 5 seconds)
curl -X POST http://127.0.0.1:8000/start_auto_processing \
  -H 'Content-Type: application/json' \
  -d '{"interval": 5}'

# Check processing stats
curl http://127.0.0.1:8000/stats

# Get latest result
curl http://127.0.0.1:8000/latest_result

# Stop auto-processing
curl -X POST http://127.0.0.1:8000/stop_auto_processing
```

### Results Management
```bash
# List all results
curl http://127.0.0.1:8000/results

# Get specific result file
curl http://127.0.0.1:8000/result/result_20240101_120000.json

# Download processed image
curl http://127.0.0.1:8000/result/processed_frame_20240101_120000.jpg -O
```

## Configuration

### Local Server Configuration
Edit `Local-Server-1/config.py`:
```python
USE_CAMERA = True           # True for camera, False for video file
CAMERA_INDEX = 0           # Camera device index  
VIDEO_SOURCE = "../YoloParklot/carPark.mp4"  # Video file path
```

### Flask API Server Configuration
Edit `Flask-API-1/config.ini`:
```ini
[SERVER]
HOST = 127.0.0.1
PORT = 8000

[LOCAL_SERVER]
URL = http://127.0.0.1:5000

[PROCESSING]
AUTO_PROCESSING_INTERVAL = 5
OUTPUT_DIRECTORY = output
```

## Output Structure

Results are stored locally in `Flask-API-1/output/`:
```
output/
├── processed_frame_20240101_120000.jpg    # Processed images with overlays
├── result_20240101_120000.json            # Parking metadata JSON
├── processed_frame_20240101_120005.jpg
├── result_20240101_120005.json
└── ...
```

## System Requirements

### Hardware
- **Camera**: USB webcam or IP camera (optional)
- **CPU**: Multi-core processor for real-time processing
- **RAM**: 4GB+ recommended
- **Storage**: Space for output images and results

### Software
- **Python**: 3.8+
- **OpenCV**: Computer vision operations
- **YOLOv8**: AI model for vehicle detection  
- **Flask**: Web framework for API
- **CUDA**: Optional, for GPU acceleration

## Development

### Project Structure
```
MajorProject/
├── Local-Server-1/              # Frame provider server
│   ├── frame_server.py          # Main server implementation
│   ├── config.py               # Configuration
│   ├── requirements.txt        # Dependencies
│   └── README.md              # Local server docs
├── Flask-API-1/               # AI processing server
│   ├── flask_server.py        # Main server implementation
│   ├── config.ini            # Configuration  
│   ├── requirements.txt      # Dependencies
│   └── YoloParklot/         # YOLOv8 parking detection system
├── start_complete_system.sh     # Background system startup
├── run_interactive_system.sh    # Interactive mode with live console
├── view_live_output.sh          # Live output viewer
└── README.md                # This file
```

### Adding New Features

**To Local Server**:
- Add new endpoints in `frame_server.py`
- Modify frame capture logic for different sources
- Add preprocessing capabilities

**To Flask API Server**:
- Extend YoloParklot integration
- Add new processing endpoints
- Implement additional storage backends
- Add authentication/authorization

## Troubleshooting

### Common Issues

**Local Server not capturing frames**:
- Check camera permissions
- Verify camera index or video file path
- Try different camera indices (0, 1, 2...)

**Flask API Server connection errors**:
- Ensure Local Server is running on port 5000
- Check firewall settings
- Verify network connectivity

**YoloParklot processing errors**:
- Ensure model weights exist in `YoloParklot/runs/detect/carpk_demo/weights/best.pt`
- Check CUDA/GPU availability for faster processing
- Verify all YoloParklot dependencies are installed

**Performance Issues**:
- Reduce processing interval
- Lower camera resolution
- Use GPU acceleration if available

### Debug Mode

Enable detailed logging:
```bash
# Set log level to DEBUG in the servers
# Check log files: flask_server.log, frame_server.log
```

## Integration with Client Apps

### Mobile/Web App Integration

The Flask API Server provides RESTful endpoints that can be consumed by mobile or web applications:

```javascript
// Example: Fetch latest parking data
fetch('http://127.0.0.1:8000/latest_result')
  .then(response => response.json())
  .then(data => {
    console.log(`Available slots: ${data.parking_data.available_slots}`);
    console.log(`Total slots: ${data.parking_data.total_slots}`);
    console.log(`Occupancy: ${data.parking_data.occupancy_rate * 100}%`);
  });

// Example: Start automatic processing
fetch('http://127.0.0.1:8000/start_auto_processing', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({interval: 10})
});
```

### Real-time Updates

For real-time parking updates, implement polling or WebSocket connections:

```python
import requests
import time

# Polling example
while True:
    response = requests.get('http://127.0.0.1:8000/latest_result')
    if response.status_code == 200:
        data = response.json()
        print(f"Parking update: {data['parking_data']['available_slots']} slots available")
    time.sleep(30)  # Poll every 30 seconds
```

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section
- Review server logs
- Test individual components
- Create an issue in the repository