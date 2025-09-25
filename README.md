# Flask API Server (Server 2) - YOLO Processing Engine# Flask API Server - Parking Detection System



## Overview**Server II: Flask Backend + AI Processing**

Server 2 in a two-server architecture that processes frames from Local Server (Server 1) using YOLO parking detection.

This Flask API server receives snapshots from the Local Video Feed Server (Server I), processes them using YOLO-based parking detection, and pushes the results to Firebase Realtime Database.

## Architecture

```## 🏗️ Architecture Overview

Local Server (Port 5000) → Flask API Server (Port 8000) → Output Storage

[Frame Provider]           [YOLO Processing]            [Results Storage]```

```Local Server (Server I) → Flask API Server (Server II) → Firebase Database

     ↓                          ↓                           ↓

## Quick Start  Video Feed              YOLO Processing              Real-time Data

  Snapshots              Parking Detection            for Client Apps

### 1. Install Dependencies```

```bash

pip install -r requirements.txt## 🚀 Features

```

- **RESTful API**: Receive snapshots via HTTP POST requests

### 2. Start Local Server (Server 1) First- **YOLO Integration**: Process images using YOLOv8 parking detection system

```bash- **Firebase Integration**: Push results to Firebase Realtime Database

cd ../Local-Server-1- **Real-time Processing**: Process images as they arrive from Local Server

python3 realtime_server.py- **Statistics Tracking**: Track parking slot occupancy, availability rates

```- **Image Storage**: Optionally save processed images with annotations

- **Health Monitoring**: Status endpoints for system monitoring

### 3. Start Flask API Server (Server 2)- **Error Handling**: Comprehensive error handling and logging

```bash

python3 realtime_flask_server.py## 📊 Data Structure

```

The system tracks and provides the following parking data:

### 4. Use Automated Script (Optional)

```bash```json

./start_integrated_servers.sh{

```  "total_slots": 50,

  "occupied_slots": 23,

## Configuration  "available_slots": 27,

Edit configuration in `realtime_flask_server.py`:  "occupancy_rate": 46.0,

- `LOCAL_SERVER_URL`: Local Server address (default: http://127.0.0.1:5000)  "vehicle_count": 25,

- `YOLO_MODEL_PATH`: Path to YOLO model weights  "processing_time_ms": 145.2,

- `OUTPUT_DIR`: Output directory for results  "camera_id": "0",

  "timestamp": "2025-09-23T14:30:15",

## Output Structure  "last_updated": "2025-09-23 14:30:15"

```}

output/```

├── realtime_results.json      # Parking detection results

├── processed_frames/          # YOLO-annotated images## 🔧 Installation & Setup

└── raw_frames/               # Original frames from Local Server

```### 1. Clone and Navigate

```bash

## API Endpoints (Port 8000)cd MajorProject/Flask-API-1

- `GET /health` - Server health status```

- `GET /stats` - Processing statistics

- `GET /results` - Recent results### 2. Install Dependencies

- `GET /results/latest` - Latest result```bash

- `POST /upload` - Manual frame uploadpip install -r requirements.txt

```

## Server Responsibilities

✅ **What Server 2 Does:**### 3. Firebase Setup

- Fetch frames from Local Server

- Process frames with YOLO#### Option A: Using the Setup Helper (Recommended)

- Store results in output folder```bash

- Provide API endpointspython firebase_setup.py

```

❌ **What Server 2 Does NOT Do:**

- Camera capture#### Option B: Manual Setup

- Hardware interaction1. Go to [Firebase Console](https://console.firebase.google.com/)

- Frame generation2. Create a new project or select existing project
3. Enable **Realtime Database**
4. Go to **Project Settings > Service Accounts**
5. Click **"Generate new private key"** and download the JSON file
6. Rename it to `firebase_credentials.json` and place in this directory
7. Copy your Realtime Database URL

### 4. Environment Configuration
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file with your Firebase configuration
nano .env
```

Update these important settings in `.env`:
```env
FIREBASE_DATABASE_URL=https://your-project-default-rtdb.firebaseio.com/
FIREBASE_CREDENTIALS_PATH=firebase_credentials.json
FIREBASE_NODE_NAME=parking_data
```

### 5. Verify Setup
```bash
python firebase_setup.py
```

## 🚀 Running the Server

### Start the Flask API Server
```bash
python app.py
```

The server will start on `http://localhost:5000` by default.

### Production Deployment
For production, consider using Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 🌐 API Endpoints

### 1. Health Check
```bash
GET /
```
Returns server status and health information.

### 2. Upload Snapshot (Main Endpoint)
```bash
POST /upload
```
**Purpose**: Receive and process snapshots from Local Server

**Request Format**:
- Content-Type: `multipart/form-data`
- File field: `image` (JPEG image)
- Additional data:
  - `timestamp`: ISO timestamp string
  - `camera_id`: Camera identifier

**Response**:
```json
{
  "success": true,
  "message": "Image processed successfully",
  "data": {
    "total_slots": 50,
    "occupied_slots": 23,
    "available_slots": 27,
    "occupancy_rate": 46.0,
    "vehicle_count": 25,
    "processing_time_ms": 145.2,
    "camera_id": "0",
    "timestamp": "2025-09-23T14:30:15"
  },
  "firebase_push": true
}
```

### 3. Get Parking Data
```bash
GET /parking-data
```
Returns the latest parking data from Firebase.

### 4. System Status
```bash
GET /status
```
Returns detailed system status and configuration.

## 🔥 Firebase Database Structure

Data is stored in Firebase Realtime Database with the following structure:

```
parking_data/
├── total_slots: 50
├── occupied_slots: 23
├── available_slots: 27
├── occupancy_rate: 46.0
├── vehicle_count: 25
├── processing_time_ms: 145.2
├── camera_id: "0"
├── timestamp: "2025-09-23T14:30:15"
└── last_updated: "2025-09-23 14:30:15"
```

## 🔗 Integration with Local Server

The Local Server (Server I) should be configured to send POST requests to:
```
http://your-flask-server:5000/upload
```

Update the Local Server's `config.py`:
```python
REMOTE_SERVER_URL = 'http://localhost:5000/upload'  # or your server IP
```

## 📁 Project Structure

```
Flask-API-1/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── firebase_setup.py          # Firebase setup helper
├── .env.example               # Environment template
├── .env                       # Your environment variables
├── firebase_credentials.json  # Firebase service account key
├── processed_images/          # Processed images (if enabled)
├── flask_api_server.log      # Application logs
└── README.md                 # This file
```

## ⚙️ Configuration Options

### Environment Variables (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_HOST` | `0.0.0.0` | Server host address |
| `FLASK_PORT` | `5000` | Server port |
| `FLASK_DEBUG` | `False` | Debug mode |
| `FIREBASE_DATABASE_URL` | Required | Firebase Realtime Database URL |
| `FIREBASE_CREDENTIALS_PATH` | `firebase_credentials.json` | Path to credentials file |
| `FIREBASE_NODE_NAME` | `parking_data` | Firebase data node name |
| `YOLO_MODEL_PATH` | `../YoloParklot/...` | Path to YOLO model |
| `PARKING_POSITIONS_FILE` | `../YoloParklot/CarParkPos` | Parking positions file |
| `SAVE_PROCESSED_IMAGES` | `True` | Save annotated images |
| `PROCESSED_IMAGES_DIR` | `processed_images` | Directory for processed images |

## 🔧 Testing the System

### 1. Test Server Health
```bash
curl http://localhost:5000/
```

### 2. Test Image Upload
```bash
curl -X POST \
  -F "image=@test_image.jpg" \
  -F "camera_id=test_camera" \
  -F "timestamp=$(date -Iseconds)" \
  http://localhost:5000/upload
```

### 3. Get Parking Data
```bash
curl http://localhost:5000/parking-data
```

## 📊 Monitoring & Logging

- **Application Logs**: `flask_api_server.log`
- **System Status**: `/status` endpoint
- **Health Check**: `/` endpoint
- **Firebase Console**: Monitor database updates
- **Processed Images**: `processed_images/` directory

## 🐛 Troubleshooting

### Common Issues

1. **Firebase Connection Failed**
   - Check `firebase_credentials.json` file exists
   - Verify `FIREBASE_DATABASE_URL` is correct
   - Ensure Firebase Realtime Database is enabled

2. **YOLO Model Not Found**
   - Check `YOLO_MODEL_PATH` in `.env`
   - Ensure YoloParklot system is properly set up

3. **Import Errors**
   - Install all requirements: `pip install -r requirements.txt`
   - Check Python path and dependencies

4. **Images Not Processing**
   - Verify parking positions file exists
   - Check image format (JPEG recommended)
   - Review logs for detailed error messages

### Debug Mode
Enable debug mode in `.env`:
```env
FLASK_DEBUG=True
```

## 🔄 Integration with Complete System

This Flask API Server is part of a complete parking management system:

1. **Local Server (Server I)**: Captures video feed and sends snapshots
2. **Flask API Server (Server II)**: This component - processes images and manages data
3. **YOLO Detection System**: AI/ML processing for vehicle detection
4. **Firebase Database**: Real-time data storage
5. **Client Applications**: Mobile/web apps consuming the data

## 🚀 Next Steps

1. Start the Flask API Server: `python app.py`
2. Configure and start the Local Server (Server I)
3. Monitor Firebase Console for real-time updates
4. Build client applications using the `/parking-data` endpoint

## 📞 Support

For issues and questions:
1. Check the logs: `flask_api_server.log`
2. Use the Firebase setup helper: `python firebase_setup.py`
3. Test system status: `http://localhost:5000/status`
4. Review the troubleshooting section above

---

**🎯 Ready to detect parking spaces in real-time!**