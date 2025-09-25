# Local-Server-1: Camera Input Server

A Python-based camera capture server that provides real-time video frames for parking detection analysis.

## 🎯 Overview

**Local-Server-1** is the first component of a two-server parking detection system. It captures live video frames from a camera and serves them via REST API endpoints for processing by the Flask API Server.

## 🚀 Features

- **Real-time Camera Capture**: Live video feed from webcam/USB camera
- **REST API Endpoints**: HTTP endpoints for frame access
- **Base64 Frame Encoding**: Efficient frame transmission
- **Configurable Camera Settings**: Adjustable resolution, FPS, and camera index
- **Health Monitoring**: Server status and connectivity checks
- **Auto-retry Logic**: Robust camera initialization with fallback
- **Frame Buffering**: Smooth frame delivery with timestamp metadata

## 📋 Requirements

- Python 3.8+
- OpenCV (cv2)
- Flask
- NumPy
- A connected camera (USB webcam or built-in camera)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd Local-Server-1
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv_local
   source venv_local/bin/activate  # On Windows: venv_local\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure camera settings** (optional):
   ```bash
   cp simple_config.env.example simple_config.env
   # Edit simple_config.env with your camera preferences
   ```

## ⚙️ Configuration

Edit `simple_config.env` or `.env` file:

```env
# Camera Settings
USE_CAMERA=true
CAMERA_INDEX=0
FRAME_WIDTH=640
FRAME_HEIGHT=480
CAMERA_FPS=30

# Server Settings  
LOCAL_SERVER_HOST=127.0.0.1
LOCAL_SERVER_PORT=5000

# Processing
MAX_RETRY_ATTEMPTS=3
FRAME_BUFFER_SIZE=10
```

## 🏃‍♂️ Usage

### Start the Camera Server

```bash
# Method 1: Direct execution
python3 frame_server.py

# Method 2: Using start script
./start_local_server.sh

# Method 3: Background execution
python3 frame_server.py &
```

The server will start on `http://127.0.0.1:5000` by default.

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check and server status |
| `/latest_frame` | GET | Get the latest camera frame (Base64 encoded) |
| `/camera_info` | GET | Camera settings and capabilities |
| `/stats` | GET | Server statistics and metrics |

### Example API Calls

```bash
# Health check
curl http://127.0.0.1:5000/

# Get latest frame
curl http://127.0.0.1:5000/latest_frame

# Get camera information
curl http://127.0.0.1:5000/camera_info
```

### Response Format

```json
{
  "server": "Local Server (Server I)",
  "status": "running", 
  "timestamp": "2025-09-26T02:43:00.000000",
  "video_source": "Camera",
  "camera_index": 0,
  "frame": "base64_encoded_image_data",
  "frame_width": 640,
  "frame_height": 480,
  "fps": 30
}
```

## 🔧 Architecture

```
┌─────────────────┐    HTTP/REST    ┌─────────────────┐
│ Camera Hardware │ ──────────────► │ Local-Server-1  │
│                 │                 │                 │
│ • USB Webcam    │                 │ • Frame Capture │
│ • Built-in Cam  │                 │ • Base64 Encode │
│ • IP Camera     │                 │ • REST API      │
└─────────────────┘                 │ • Health Check  │
                                    └─────────────────┘
                                             │
                                             │ HTTP API
                                             ▼
                                    ┌─────────────────┐
                                    │ Flask-API-1     │
                                    │ (YoloParklot)   │
                                    └─────────────────┘
```

## 🧪 Testing

```bash
# Test camera capture
python3 test_camera.py

# Test server connectivity
python3 test_verification.py

# Integration test with Flask API
python3 ../test_complete_pipeline.sh
```

## 📊 Monitoring

The server provides built-in monitoring:

- **Frame Rate**: Actual FPS vs configured FPS
- **Camera Status**: Connection health and error rates
- **API Metrics**: Request counts and response times
- **System Resources**: CPU and memory usage

Access monitoring at: `http://127.0.0.1:5000/stats`

## 🐛 Troubleshooting

### Camera Not Detected
```bash
# Check available cameras
python3 -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).read()[0]])"

# Try different camera indices
export CAMERA_INDEX=1  # or 2, 3, etc.
```

### Permission Issues (Linux)
```bash
sudo usermod -a -G video $USER
# Logout and login again
```

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000
kill -9 <PID>

# Or change port in configuration
export LOCAL_SERVER_PORT=5001
```

## 📝 Logs

Logs are written to:
- `frame_server.log` - Main server logs
- `local_processing.log` - Frame processing logs
- Console output for real-time monitoring

## 🚦 System Integration

This server works as part of a two-server architecture:

1. **Local-Server-1** (this server): Camera capture and frame serving
2. **Flask-API-1**: YoloParklot processing and parking detection

Communication flow:
```
Camera → Local-Server-1 → Flask-API-1 → Processed Results
```

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 🔗 Related Projects

- [Flask-API-1](../Flask-API-1/README.md) - YoloParklot processing server
- [YoloParklot](../Flask-API-1/YoloParklot/README.md) - Parking detection AI system

---

**Local-Server-1** - Real-time camera capture for intelligent parking detection systems.