# Flask-API-1: YoloParklot Processing Server

An AI-powered Flask server that processes camera frames using YoloParklot for intelligent parking space detection with real-time console monitoring every 10 seconds.

## 🎯 Overview

**Flask-API-1** is the second component of a two-server parking detection system. It receives video frames from Local-Server-1, processes them using the advanced YoloParklot system, and provides real-time console updates showing parking slot availability every 10 seconds.

## 🔄 Console Monitoring

The server automatically displays parking status updates every 10 seconds in the console:

```bash
========================================
=== PARKING STATUS UPDATE ===
Available Slots: 73/73
Slot Numbers: 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73
Processing Time: 82.5ms
Timestamp: 2024-12-27 04:26:37
========================================
```

## 🧠 AI Features

- **YoloParklot Integration**: Advanced YOLOv8-based parking detection
- **Real-time Processing**: Live camera frame analysis (~80-90ms per frame)
- **73-Slot Analysis**: Complete parking lot coverage with individual slot tracking
- **10-Second Monitoring**: Automatic console updates with parking status
- **Vehicle Detection**: Precise vehicle identification and tracking
- **Visual Annotations**: Rich overlays showing parking slots and occupancy
- **Parking Analytics**: Comprehensive statistics and occupancy rates

## 🚀 Core Features

- **REST API**: HTTP endpoints for frame processing
- **Auto-processing**: Continuous frame fetching and analysis every 10 seconds
- **Console Monitoring**: Real-time parking status updates with slot numbers
- **Output Storage**: Processed frames and JSON metadata
- **Performance Monitoring**: Processing time and statistics tracking
- **Background Mode Support**: Log file output for background execution
- **Health Monitoring**: System status and AI model availability

## 📋 Requirements

- Python 3.8+
- YOLOv8 (Ultralytics)
- OpenCV (cv2)
- Flask
- NumPy
- Requests
- Pre-trained YOLO model (`best.pt`)
- Parking positions configuration (`CarParkPos`)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd Flask-API-1
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv_flask
   source venv_flask/bin/activate  # On Windows: venv_flask\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup YoloParklot AI system**:
   ```bash
   # Automated setup (recommended)
   ./setup_yoloparklot.sh
   
   # Or manual setup
   git clone https://github.com/pdschandel/YoloParklot.git
   
   # Verify setup
   ls -la YoloParklot/runs/detect/carpk_demo/weights/best.pt
   ls -la YoloParklot/CarParkPos
   ```

## ⚙️ Configuration

The server automatically configures YoloParklot with:

```python
# Model Configuration
MODEL_PATH = "YoloParklot/runs/detect/carpk_demo/weights/best.pt"
PARKING_POSITIONS = "YoloParklot/CarParkPos"
CONFIDENCE_THRESHOLD = 0.25
TOTAL_SLOTS = 73

# Server Configuration
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 8000
LOCAL_SERVER_URL = "http://127.0.0.1:5000"
OUTPUT_DIRECTORY = "output"
AUTO_PROCESS_INTERVAL = 3  # seconds
```

## 🏃‍♂️ Usage

### Start the Flask API Server

```bash
# Method 1: Direct execution
python3 flask_server.py

# Method 2: Using start script
./start_flask_server.sh

# Method 3: Background execution
python3 flask_server.py &
```

The server will start on `http://127.0.0.1:8000` by default.

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check and YoloParklot status |
| `/process_frame` | POST | Process single frame with YoloParklot |
| `/start_auto_processing` | POST | Start continuous processing |
| `/stop_auto_processing` | POST | Stop continuous processing |
| `/stats` | GET | Processing statistics and metrics |
| `/latest_result` | GET | Get latest processing result |
| `/results` | GET | List all processed results |
| `/result/<filename>` | GET | Download specific result file |

### Example API Calls

```bash
# Health check (shows YoloParklot status)
curl http://127.0.0.1:8000/

# Process a single frame
curl -X POST http://127.0.0.1:8000/process_frame \
  -H "Content-Type: application/json" \
  -d '{"frame": "base64_encoded_frame_data"}'

# Start auto-processing
curl -X POST http://127.0.0.1:8000/start_auto_processing \
  -H "Content-Type: application/json" \
  -d '{"interval": 3}'

# Get processing statistics
curl http://127.0.0.1:8000/stats
```

### YoloParklot Response Format

```json
{
  "status": "success",
  "result": {
    "success": true,
    "timestamp": "20250926_024342",
    "parking_data": {
      "total_slots": 73,
      "occupied_slots": 1,
      "available_slots": 72,
      "occupancy_rate": 0.01,
      "vehicles_detected": 1,
      "processing_time_ms": 43.2,
      "processing_mode": "yolo_parklot"
    },
    "filename": "processed_frame_0007_20250926_024342.jpg"
  }
}
```

## 🔧 YoloParklot Architecture

```
┌─────────────────┐    HTTP/REST    ┌─────────────────┐
│ Local-Server-1  │ ──────────────► │ Flask-API-1     │
│                 │                 │                 │
│ • Camera Input  │                 │ • Frame Decode  │
│ • Base64 Encode │                 │ • YoloParklot   │
│ • REST API      │                 │ • AI Processing │
└─────────────────┘                 │ • Annotations   │
                                    └─────────────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │ YoloParklot AI  │
                                    │                 │
                                    │ • YOLOv8 Model  │
                                    │ • 73 Slots      │
                                    │ • Vehicle Det.  │
                                    │ • Occupancy     │
                                    └─────────────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │ Output Storage  │
                                    │                 │
                                    │ • Processed JPG │
                                    │ • JSON Metadata │
                                    │ • Statistics    │
                                    └─────────────────┘
```

## 🧪 Testing

### Test YoloParklot Integration
```bash
# Test YoloParklot directly
cd YoloParklot
python3 -c "
from parking_detection import ParkingDetectionSystem
import numpy as np
import cv2

system = ParkingDetectionSystem()
test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
result = system.process_frame(test_frame)
print('YoloParklot working:', result[1])
"
```

### Test Complete Pipeline
```bash
# Verify YoloParklot setup
ls -la YoloParklot/runs/detect/carpk_demo/weights/best.pt
ls -la YoloParklot/CarParkPos

# Test API endpoints
curl -X POST http://127.0.0.1:8000/process_frame
curl http://127.0.0.1:8000/stats
```

## 📊 YoloParklot Capabilities

### Parking Detection Features
- **73 Parking Slots**: Pre-configured parking layout analysis
- **Vehicle Detection**: YOLOv8-powered vehicle identification
- **Occupancy Analysis**: Real-time slot availability
- **Visual Annotations**: Color-coded slot status overlays
- **Performance Metrics**: Processing time and accuracy tracking

### Detection Accuracy
- **Confidence Threshold**: 0.25 (configurable)
- **Processing Time**: ~40-50ms per frame
- **Slot Detection**: 107x48 pixel slot analysis
- **Occupancy Threshold**: 30% overlap detection

### Output Files
```
output/
├── processed_frame_0001_20250926_024342.jpg  # Annotated image
├── parking_data_0001_20250926_024342.json    # Metadata
├── processed_frame_0002_20250926_024345.jpg
├── parking_data_0002_20250926_024345.json
└── ...
```

## 📈 Monitoring & Analytics

### Real-time Metrics
- Processing FPS and latency
- YoloParklot model performance
- Parking occupancy trends
- System resource usage

### Log Analysis
```bash
# Monitor YoloParklot processing
tail -f flask_server.log | grep "YoloParklot processing"

# Track processing performance
grep "processing_time_ms" flask_server.log
```

## 🐛 Troubleshooting

### YoloParklot Model Issues
```bash
# Check model file
ls -la YoloParklot/runs/detect/carpk_demo/weights/best.pt

# Verify parking positions
ls -la YoloParklot/CarParkPos

# Test model loading
cd YoloParklot && python3 -c "from parking_detection import ParkingDetectionSystem; ParkingDetectionSystem()"
```

### Processing Errors
```bash
# Check Flask logs
tail -50 flask_server.log

# Verify dependencies
pip install ultralytics opencv-python torch

# Test with fallback mode
export YOLO_AVAILABLE=false
```

### Connection Issues
```bash
# Verify Local-Server-1 is running
curl http://127.0.0.1:5000/

# Check port availability
lsof -i :8000

# Test network connectivity
ping 127.0.0.1
```

## 🎯 Performance Optimization

### YoloParklot Tuning
- Adjust confidence threshold for accuracy vs speed
- Configure slot dimensions for better detection
- Optimize image resolution for processing speed

### Processing Optimization
- Batch processing for multiple frames
- GPU acceleration with CUDA (if available)
- Memory optimization for continuous processing

## 📝 Logs & Output

### Log Files
- `flask_server.log` - Main Flask server logs
- `flask_processing.log` - YoloParklot processing logs
- Console output for real-time monitoring

### Output Directory Structure
```
output/
├── processed_frames/     # Annotated images
├── parking_data/        # JSON metadata  
├── statistics/         # Performance metrics
└── debug/             # Debug information
```

## 🚦 System Integration

This server integrates seamlessly with:

1. **Local-Server-1**: Receives camera frames via HTTP
2. **YoloParklot**: Advanced AI parking detection
3. **Output Storage**: Processed results and analytics

Complete pipeline:
```
Camera → Local-Server-1 → Flask-API-1 → YoloParklot → Results
```

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Ensure YoloParklot tests pass
4. Commit your changes
5. Push to the branch
6. Create a Pull Request

## 🔗 Related Projects

- [Local-Server-1](../Local-Server-1/README.md) - Camera input server
- [YoloParklot](./YoloParklot/README.md) - AI parking detection system
- [Complete Pipeline Tests](../test_complete_pipeline.sh) - Integration testing

## 🏆 Achievements

- ✅ Real-time YOLOv8 integration
- ✅ 73-slot parking analysis
- ✅ Sub-50ms processing time
- ✅ Continuous auto-processing
- ✅ Rich visual annotations
- ✅ Comprehensive analytics

---

**Flask-API-1** - AI-powered parking detection with YoloParklot integration for intelligent transportation systems.