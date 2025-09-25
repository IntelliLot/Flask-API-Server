# Complete System Setup Guide

This guide provides step-by-step instructions to set up and run the Two-Server YOLO Parking Detection system.

## 📋 Prerequisites

### Hardware Requirements
- **Camera**: USB webcam or built-in camera (for live detection)
- **CPU**: Multi-core processor (Intel i5+ or AMD Ryzen 5+)
- **RAM**: 8GB+ recommended (4GB minimum)
- **Storage**: 5GB+ free space
- **GPU**: Optional CUDA-compatible GPU for faster processing

### Software Requirements
- **Operating System**: Linux (Ubuntu 20.04+), macOS, or Windows 10+
- **Python**: 3.8+ (Python 3.9-3.11 recommended)
- **Git**: For repository cloning
- **Internet**: For downloading dependencies and models

## 🚀 Quick Installation

### Option 1: Automated Setup (Recommended)
```bash
# Clone the repository
git clone https://github.com/yourusername/MajorProject.git
cd MajorProject

# Make scripts executable
chmod +x *.sh Flask-API-1/*.sh Local-Server-1/*.sh

# Run automated setup
./setup_complete_system.sh
```

### Option 2: Manual Setup
Follow the step-by-step instructions below.

## 📦 Step-by-Step Manual Installation

### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/MajorProject.git
cd MajorProject
```

### Step 2: Setup Local-Server-1 (Camera Server)
```bash
cd Local-Server-1

# Create virtual environment
python3 -m venv venv_local
source venv_local/bin/activate  # Linux/Mac
# venv_local\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Test camera (optional)
python test_camera.py
```

### Step 3: Setup Flask-API-1 (AI Processing Server)
```bash
cd ../Flask-API-1

# Create virtual environment
python3 -m venv venv_flask
source venv_flask/bin/activate  # Linux/Mac
# venv_flask\Scripts\activate  # Windows

# Setup YoloParklot AI system
./setup_yoloparklot.sh

# Install dependencies
pip install -r requirements.txt

# Verify YoloParklot setup
ls -la YoloParklot/runs/detect/carpk_demo/weights/best.pt
ls -la YoloParklot/CarParkPos
```

### Step 4: Configuration (Optional)
```bash
# Configure Local Server (if needed)
cd Local-Server-1
cp simple_config.env.example simple_config.env
nano simple_config.env

# Configure Flask API Server (if needed)
cd ../Flask-API-1
nano config.ini
```

## 🏃‍♂️ Running the System

### Option A: Complete Background System (Recommended)
```bash
cd /path/to/MajorProject
./start_complete_system.sh

# Check system status
ps aux | grep python | grep -E "(frame_server|flask_server)"

# View console outputs
tail -f /tmp/flask_output.log    # Flask server output
tail -f /tmp/local_output.log    # Local server output
```

### Option B: Interactive Mode (Live Console)
```bash
cd /path/to/MajorProject
./run_interactive_system.sh

# Console output will be visible directly
# Press Ctrl+C to stop
```

### Option C: Background + Live Viewer
```bash
# Terminal 1: Start background system
./start_complete_system.sh

# Terminal 2: View live output
./view_live_output.sh
```

### Option D: Manual Start (Advanced)
```bash
# Terminal 1: Start Local Server
cd Local-Server-1
source venv_local/bin/activate
python frame_server.py

# Terminal 2: Start Flask API Server
cd Flask-API-1
source venv_flask/bin/activate
python flask_server.py
```

## 🔍 Verification & Testing

### System Health Check
```bash
# Check if servers are running
curl http://127.0.0.1:5000/    # Local Server health
curl http://127.0.0.1:8000/    # Flask API Server health

# Check server status
./check_system_status.sh
```

### Integration Testing
```bash
# Run complete pipeline test
./test_complete_pipeline.sh

# Run individual tests
python test_integration.py
python test_system.py
```

### Console Output Verification
The Flask API server displays parking status every 10 seconds:
```bash
========================================
=== PARKING STATUS UPDATE ===
Available Slots: 73/73
Slot Numbers: 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73
Processing Time: 89.3ms
Timestamp: 2024-12-27 04:28:15
========================================
```

## ⚙️ Configuration Options

### Local-Server-1 Configuration
Edit `Local-Server-1/simple_config.env`:
```env
USE_CAMERA=true
CAMERA_INDEX=0
FRAME_WIDTH=640
FRAME_HEIGHT=480
CAMERA_FPS=30
LOCAL_SERVER_HOST=127.0.0.1
LOCAL_SERVER_PORT=5000
```

### Flask-API-1 Configuration
Edit `Flask-API-1/config.ini`:
```ini
[SERVER]
HOST = 127.0.0.1
PORT = 8000

[LOCAL_SERVER]
URL = http://127.0.0.1:5000

[PROCESSING]
AUTO_PROCESSING_INTERVAL = 3
OUTPUT_DIRECTORY = output

[YOLO]
CONFIDENCE_THRESHOLD = 0.25
MODEL_PATH = YoloParklot/runs/detect/carpk_demo/weights/best.pt
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Camera Not Found
```bash
# List available cameras
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).read()[0]])"

# Try different camera index
export CAMERA_INDEX=1  # or 2, 3...
```

#### 2. Port Already in Use
```bash
# Find process using port
lsof -i :5000  # or :8000

# Kill process
kill -9 <PID>

# Or use different ports
export LOCAL_SERVER_PORT=5001
export FLASK_PORT=8001
```

#### 3. YoloParklot Model Missing
```bash
cd Flask-API-1

# Re-run setup
./setup_yoloparklot.sh

# Verify files exist
ls -la YoloParklot/runs/detect/carpk_demo/weights/best.pt
```

#### 4. Virtual Environment Issues
```bash
# Remove and recreate
rm -rf venv_local venv_flask
python3 -m venv venv_local
python3 -m venv venv_flask

# Reinstall dependencies
cd Local-Server-1 && pip install -r requirements.txt
cd Flask-API-1 && pip install -r requirements.txt
```

#### 5. Permission Issues (Linux)
```bash
# Add user to video group
sudo usermod -a -G video $USER

# Make scripts executable
chmod +x *.sh */*.sh

# Logout and login again
```

### Log Files
Check these files for detailed error information:
- `/tmp/flask_output.log` - Flask server logs
- `/tmp/local_output.log` - Local server logs
- `Flask-API-1/flask_server.log` - Flask processing logs
- `Local-Server-1/frame_server.log` - Camera capture logs

## 📊 System Monitoring

### Real-time Status
```bash
# Check system status
./check_system_status.sh

# Monitor live output
./view_live_output.sh

# Check processing statistics
curl http://127.0.0.1:8000/stats | jq
```

### Performance Metrics
- **Processing Time**: ~80-90ms per frame
- **Frame Rate**: 0.33 FPS (every 3 seconds)
- **Console Updates**: Every 10 seconds
- **Slot Coverage**: 73 parking slots
- **Memory Usage**: ~500MB total

## 🛑 Stopping the System

### Background Mode
```bash
# Stop all servers
./stop_system.sh

# Or manually
pkill -f "frame_server.py"
pkill -f "flask_server.py"
```

### Interactive Mode
Press `Ctrl+C` in the terminal running the servers.

## 📱 API Usage Examples

### Basic API Calls
```bash
# Get latest frame
curl http://127.0.0.1:5000/latest_frame | jq

# Process frame manually
curl -X POST http://127.0.0.1:8000/process_frame | jq

# Get processing results
curl http://127.0.0.1:8000/latest_result | jq

# List all results
curl http://127.0.0.1:8000/results | jq
```

### Python Integration
```python
import requests
import time

# Check system health
local_health = requests.get('http://127.0.0.1:5000/').json()
flask_health = requests.get('http://127.0.0.1:8000/').json()

print(f"Local Server: {local_health['status']}")
print(f"Flask API: {flask_health['status']}")

# Get parking data
result = requests.get('http://127.0.0.1:8000/latest_result').json()
if result['success']:
    parking = result['parking_data']
    print(f"Available slots: {parking['available_slots']}/{parking['total_slots']}")
    print(f"Occupancy rate: {parking['occupancy_rate']:.1%}")
```

## 🔧 Advanced Configuration

### GPU Acceleration (Optional)
```bash
# Install CUDA support for PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify GPU availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### Production Deployment
```bash
# Use production WSGI server
pip install gunicorn

# Run Flask with Gunicorn
cd Flask-API-1
gunicorn -w 4 -b 0.0.0.0:8000 flask_server:app

# Run Local Server with production settings
cd Local-Server-1
gunicorn -w 2 -b 0.0.0.0:5000 frame_server:app
```

### Docker Deployment (Optional)
```bash
# Build Docker images
docker build -t local-server Local-Server-1/
docker build -t flask-api Flask-API-1/

# Run containers
docker run -d -p 5000:5000 local-server
docker run -d -p 8000:8000 flask-api
```

## 📚 Additional Resources

### Documentation
- [Main README.md](README.md) - System overview
- [Flask-API-1 README](Flask-API-1/README.md) - AI processing server
- [Local-Server-1 README](Local-Server-1/README.md) - Camera server
- [YoloParklot Documentation](Flask-API-1/YoloParklot/README.md) - AI system

### Script Reference
- `start_complete_system.sh` - Complete background startup
- `run_interactive_system.sh` - Interactive mode
- `view_live_output.sh` - Live output viewer
- `test_complete_pipeline.sh` - Integration testing
- `check_system_status.sh` - System health check

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review log files for error details
3. Test individual components
4. Check GitHub issues
5. Create a new issue with system information

## 🎯 System Summary

**What this system does:**
- Captures camera frames via Local-Server-1 (port 5000)
- Processes frames with YoloParklot AI via Flask-API-1 (port 8000)
- Displays parking status every 10 seconds in console
- Tracks 73 parking slots with individual slot numbers
- Provides REST API for external integration
- Stores processed results as images and JSON metadata

**Key Features:**
- Real-time parking detection
- Console monitoring every 10 seconds
- Sub-100ms AI processing
- Multiple deployment options
- Comprehensive logging and monitoring
- RESTful API integration

Ready to detect parking spaces! 🚗🅿️