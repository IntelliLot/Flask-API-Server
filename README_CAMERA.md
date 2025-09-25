# 🎥 Two-Server YOLO Parking Detection System

A distributed parking detection system using two independent servers:
- **Local Server 1**: Camera frame capture and serving
- **Flask API Server 2**: YoloParklot AI processing and result storage

## 🏗️ Architecture

```
Camera Input → Local Server → Flask API Server → Processed Output
     📷            🌐             🤖               📁
   (Port 5000)              (Port 8000)        (output/)
```

### Server 1 - Local Frame Server (Port 5000)
- **Purpose**: Capture frames from camera and serve via REST API
- **Input**: Live camera feed (configurable camera index)
- **Output**: Base64 encoded frames via `/latest_frame` endpoint
- **Technology**: Flask + OpenCV
- **Independent Operation**: Can run standalone

### Server 2 - Flask API Server (Port 8000) 
- **Purpose**: Process frames using YoloParklot and store results
- **Input**: Frames fetched from Local Server
- **Output**: Processed frames with parking annotations saved to `output/`
- **Technology**: Flask + YoloParklot + YOLO
- **AI Processing**: Vehicle detection, parking slot analysis
- **Independent Operation**: Can run standalone

## 🚀 Quick Start

### 1. Start Both Servers
```bash
./start_servers.sh
```

### 2. Start Automatic Processing
```bash
python3 demo_system.py
```

### 3. Manual Testing
```bash
# Test Local Server (Camera)
curl http://127.0.0.1:5000/

# Test Flask API Server  
curl http://127.0.0.1:8000/

# Get frame from camera
curl http://127.0.0.1:5000/latest_frame

# Start auto-processing
curl -X POST http://127.0.0.1:8000/start_auto_processing \
  -H "Content-Type: application/json" \
  -d '{"interval": 3}'
```

## 📁 Output

Processed frames are automatically saved to `Flask-API-1/output/`:
- `processed_frame_XXXX_timestamp.jpg` - Annotated images
- `parking_data_XXXX_timestamp.json` - Parking metadata

Each processed frame includes:
- ✅ Parking slot detection overlay
- 📊 Available/Occupied slot counts  
- 📈 Occupancy rate percentage
- 🕐 Processing timestamp

## 🔧 Configuration

### Camera Settings (Local Server)
Edit `Local-Server-1/.env`:
```env
USE_CAMERA=true
CAMERA_INDEX=0          # Change camera index if needed
FRAME_WIDTH=640
FRAME_HEIGHT=480
```

### Processing Settings (Flask API Server)
Edit `Flask-API-1/config.ini`:
```ini
[SERVER]
LOCAL_SERVER_URL = http://127.0.0.1:5000
PROCESSING_INTERVAL = 3  # seconds between frames
```

## 📊 API Endpoints

### Local Server (Port 5000)
- `GET /` - Server health check
- `GET /latest_frame` - Get latest camera frame
- `GET /stats` - Server statistics

### Flask API Server (Port 8000)  
- `GET /` - Server health check
- `POST /process_frame` - Process single frame
- `POST /start_auto_processing` - Start automatic processing
- `POST /stop_auto_processing` - Stop automatic processing
- `GET /stats` - Processing statistics
- `GET /results` - List processed results

## 🔍 Monitoring

### Real-time Logs
```bash
# Local Server logs
tail -f Local-Server-1/local_server.log

# Flask API Server logs  
tail -f Flask-API-1/flask_server.log
```

### Processing Status
```bash
# Check auto-processing status
curl http://127.0.0.1:8000/stats
```

## 🛠️ System Requirements

- Python 3.8+
- OpenCV
- Camera/Webcam connected
- YOLO model weights (for parking detection)

## 📦 Dependencies

### Local Server
- Flask
- OpenCV-Python
- NumPy

### Flask API Server  
- Flask
- OpenCV-Python
- ultralytics (YOLO)
- Requests
- NumPy

## 🎯 Key Features

- ✅ **Camera Input**: Real-time camera frame capture
- ✅ **Independent Servers**: Both servers operate separately  
- ✅ **REST API Communication**: Standard HTTP endpoints
- ✅ **YOLO Processing**: Advanced parking detection
- ✅ **Automatic Storage**: Processed frames saved locally
- ✅ **Real-time Monitoring**: Live logs and statistics
- ✅ **Configurable**: Customizable camera and processing settings