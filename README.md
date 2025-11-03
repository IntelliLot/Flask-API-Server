# YOLOv8 Parking Detection System

A comprehensive computer vision system for parking space detection and occupancy monitoring using YOLOv8, with MongoDB integration and multi-tenant authentication.

## Description

This system detects vehicles in parking lots and determines which parking slots are occupied or empty. It provides:

- **Vehicle Detection**: YOLOv8-based car detection
- **Occupancy Monitoring**: Real-time parking slot status tracking  
- **User Authentication**: JWT-based authentication for parking owners
- **MongoDB Integration**: Persistent storage of parking data
- **Multiple Interfaces**: Web UI, REST API, and command-line
- **Multi-tenant Support**: Each parking owner has their own account and data
- **Custom Coordinates**: Support for flexible parking slot definitions with rectangle format [x1,y1,x2,y2]
- **SVG Visualization**: Scalable vector graphics output with color-coded slots (green=empty, red=occupied)
- **Edge Device Support**: APIs for both raw image processing and pre-processed data from edge devices

## Features

### Authentication & User Management
- **User Registration**: Create parking owner accounts with organization details
- **Secure Login**: JWT token-based authentication  
- **Account Management**: User profiles with organization information

### Data Management
- **Real-time Processing**: Process camera frames and detect parking occupancy
- **Edge Processing Support**: Accept pre-processed data from edge devices
- **Historical Data**: Query past parking data with filtering options
- **Multi-camera Support**: Track multiple cameras per parking area
- **Cloud Storage**: Automatic image upload to Google Cloud Storage with hierarchical organization (user_id/node_id/date/time)

### API Endpoints
- `POST /register` - Register new parking owner
- `POST /login` - Authenticate and get JWT token
- `POST /updateRaw` - Process raw images (React app → Server → MongoDB)
- `POST /update` - Store pre-processed data (Edge device → MongoDB)
- `GET /parking-data/<user_id>` - Retrieve parking history with filters
- `POST /api/detect` - Basic detection (no auth/storage)
- `GET /` - Interactive web interface

## Project Structure

```
YoloParklot/
├── apis/                      # API route handlers (modular)
│   ├── auth_api.py           # Authentication endpoints
│   ├── parking_api.py        # Parking detection endpoints
│   └── web_api.py            # Web UI endpoints
├── auth/                      # Authentication modules
│   ├── jwt_handler.py        # JWT token management
│   └── password.py           # Password hashing
├── config/                    # Configuration
│   └── database.py           # MongoDB connection
├── middlewares/               # Request middlewares
│   └── auth_middleware.py    # JWT authentication
├── models/                    # Data models
│   ├── user.py               # User account model
│   └── parking_data.py       # Parking data model
├── templates/                 # HTML templates
│   ├── index.html            # Main web interface
│   └── testing.html          # API testing dashboard
├── utils/                     # Utility modules
│   ├── image_utils.py        # Image processing
│   └── svg_generator.py      # SVG visualization
├── parking_detection/         # Core detection package
│   ├── core/                 # Detection, management, visualization
│   ├── config/               # System configuration
│   └── utils/                # Helper functions
├── app.py                    # Main Flask application
├── main_app.py               # Command-line interface
├── requirements_full.txt     # Full dependencies (with MongoDB/JWT)
├── requirements.txt          # Basic dependencies
├── .env.example             # Environment configuration template
├── API_DOCUMENTATION.md      # Complete API documentation
├── EDGE_APP_API_DOCUMENTATION.md  # Edge app integration guide
├── EDGE_APP_QUICK_START.md   # Quick start for edge developers
├── ARCHITECTURE.md           # System architecture
├── TESTING_GUIDE.md          # Testing documentation
└── runs/detect/carpk_demo/   # YOLOv8 trained model
```

## Documentation

📚 **Complete Documentation Set:**

- **[DOCKER_DEPLOYMENT_GUIDE.md](DOCKER_DEPLOYMENT_GUIDE.md)** - 🐳 Docker deployment for development & production
- **[GCS_SETUP_GUIDE.md](GCS_SETUP_GUIDE.md)** - 📦 Google Cloud Storage setup and integration guide
- **[UPDATERAW_API_EXPLAINED.md](UPDATERAW_API_EXPLAINED.md)** - Complete `/updateRaw` API documentation  
- **[RASPBERRY_PI_AUTHENTICATION_GUIDE.md](RASPBERRY_PI_AUTHENTICATION_GUIDE.md)** - 🍓 Authentication guide for Raspberry Pi/IoT devices
- **[API Documentation](API_DOCUMENTATION.md)** - Full REST API reference
- **[Edge App Quick Start](EDGE_APP_QUICK_START.md)** - 5-minute integration guide for edge devices
- **[Edge App API Docs](EDGE_APP_API_DOCUMENTATION.md)** - Comprehensive edge integration documentation
- **[Architecture Guide](ARCHITECTURE.md)** - System design and components
- **[Testing Guide](TESTING_GUIDE.md)** - API testing and validation
- **[Migration Guide](MIGRATION_GUIDE.md)** - Upgrading from monolithic to modular structure

## Quick Start

### 1. Install Dependencies

**Full installation (with authentication & MongoDB):**
```bash
pip install -r requirements_full.txt
```

**Basic installation (detection only):**
```bash
pip install -r requirements.txt
```

### 2. Setup MongoDB

**Option A: Local MongoDB**
```bash
sudo apt-get install mongodb
sudo systemctl start mongodb
```

**Option B: MongoDB Docker**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

**Option C: MongoDB Atlas** (Cloud)
Visit https://www.mongodb.com/cloud/atlas

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

Key settings in `.env`:
```bash
MONGODB_URI=mongodb://localhost:27017/
JWT_SECRET_KEY=change-this-to-secure-random-key
JWT_ACCESS_TOKEN_EXPIRES=3600
```

### 4. Run Application

```bash
python app.py
```

Access at: **http://localhost:5001/**

## Setup (Detailed)

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone or navigate to the project directory**
```bash
cd YoloParklot
```

2. **Create and activate virtual environment** (recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

## Usage

### 1. Web Interface (Easiest)

Start the Flask server with interactive web UI:

```bash
python app.py
```

Then open your browser to: `http://localhost:5001/`

**Features:**
- Upload parking lot images
- Define parking slot coordinates in JSON format: `[[x1, y1, x2, y2], ...]`
- View real-time detection results with SVG visualization
- Download SVG and JSON results

### 2. REST API with Authentication

**Complete API Documentation:** See [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

**Quick Start:**

```python
import requests
import json

BASE_URL = "http://localhost:5001"

# Register and Login
response = requests.post(f"{BASE_URL}/register", json={
    "username": "parking_owner",
    "password": "secure123",
    "organization_name": "My Parking Lot",
    "location": "123 Main St",
    "size": 100
})
user_id = response.json()['user_id']

response = requests.post(f"{BASE_URL}/login", json={
    "username": "parking_owner",
    "password": "secure123"
})
token = response.json()['access_token']

# Process image and save to MongoDB
headers = {"Authorization": f"Bearer {token}"}
files = {'image': open('parking.jpg', 'rb')}
data = {
    'coordinates': json.dumps([[401, 238, 508, 286], [752, 377, 859, 425]]),
    'camera_id': 'camera_entrance_1'
}
response = requests.post(f"{BASE_URL}/updateRaw", headers=headers, files=files, data=data)
result = response.json()
print(f"Cars Detected: {result['total_cars_detected']}")
print(f"Occupancy: {result['occupancy_rate']}%")

# Get parking data
response = requests.get(f"{BASE_URL}/parking-data/{user_id}?limit=10", headers=headers)
print(f"Total records: {response.json()['total_count']}")
```

**React Edge App Integration:**

```javascript
// Upload frames from React app
const uploadFrame = async (imageBlob, coordinates, cameraId) => {
  const token = localStorage.getItem('token');
  const formData = new FormData();
  formData.append('image', imageBlob);
  formData.append('coordinates', JSON.stringify(coordinates));
  formData.append('camera_id', cameraId);
  
  const response = await fetch('http://localhost:5001/updateRaw', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  
  return response.json();
};
```

**cURL example:**
```bash
# Register
curl -X POST http://localhost:5001/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123","organization_name":"Test","location":"Test St","size":50}'

# Login
curl -X POST http://localhost:5001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'

# Process image (use token from login)
curl -X POST http://localhost:5001/updateRaw \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "image=@parking.jpg" \
  -F 'coordinates=[[100,200,207,248],[220,200,327,248]]'
```

### 3. Command Line

**Process images or videos directly:**

```bash
# Process image with default coordinates
python main_app.py --mode image --input parking.jpg --output result.jpg

# Process with custom coordinates from JSON file
python main_app.py --mode image --input parking.jpg --coordinates coords.json

# Process video
python main_app.py --mode video --input parking.mp4 --output result.mp4

# Real-time display
python main_app.py --mode realtime --input parking.mp4
```

### 4. Python API

```python
from parking_detection import ParkingDetectionSystem

# With custom coordinates
coordinates = [
    [401, 238, 508, 286],
    [752, 377, 859, 425],
    [55, 100, 162, 148]
]

system = ParkingDetectionSystem(parking_positions=coordinates)
system.process_single_image("parking.jpg", "result.jpg")
```

## Coordinate Format

Each parking slot is defined by 4 coordinates representing a rectangle:

```
[x1, y1, x2, y2]
```

Where:
- `(x1, y1)` = Top-left corner
- `(x2, y2)` = Bottom-right corner

**Example:**
```json
[
  [401, 238, 508, 286],
  [752, 377, 859, 425],
  [55, 100, 162, 148]
]
```

## API Response Format

```json
{
  "success": true,
  "total_slots": 5,
  "total_cars_detected": 29,
  "occupied_slots": 2,
  "empty_slots": 3,
  "occupancy_rate": 40.0,
  "svg_code": "<svg>...</svg>",
  "slots_details": [...],
  "processing_time_ms": 435.2
}
```

## Edge App Integration

**For edge device developers**, we provide comprehensive documentation:

📱 **[Edge App Quick Start Guide](EDGE_APP_QUICK_START.md)**
- Get started in 5 minutes
- Simple code examples
- Step-by-step integration
- Testing with cURL

📚 **[Complete Edge App API Documentation](EDGE_APP_API_DOCUMENTATION.md)**
- Detailed API specifications
- Python client library
- Integration flow diagrams
- Error handling patterns
- Best practices

### Quick Integration Example

```python
import requests

# 1. Register device (one-time)
requests.post('http://localhost:5001/auth/register', json={
    "username": "edge_device_01",
    "password": "secure_pass",
    "organization_name": "My Parking Lot",
    "location": "123 Main St",
    "size": 50
})

# 2. Login
response = requests.post('http://localhost:5001/auth/login', json={
    "username": "edge_device_01",
    "password": "secure_pass"
})
token = response.json()['access_token']
user_id = response.json()['user_id']

# 3. Send parking updates
requests.post('http://localhost:5001/parking/update',
    headers={"Authorization": f"Bearer {token}"},
    json={
        "user_id": user_id,
        "camera_id": "cam_01",
        "total_slots": 50,
        "occupied_slots": 35,
        "empty_slots": 15,
        "occupancy_rate": 70.0
    }
)
```

## Configuration

Server can be configured via command-line options:

```bash
python app.py --host 0.0.0.0 --port 5001 --debug
```

Options:
- `--host`: Host to bind to (default: 0.0.0.0)
- `--port`: Port number (default: 5001)
- `--debug`: Enable debug mode

## Requirements

Main dependencies (see `requirements.txt` for full list):
- Flask >= 2.0.0
- opencv-python >= 4.5.0
- ultralytics >= 8.0.0
- numpy >= 1.21.0

## Troubleshooting

**Server won't start:**
```bash
# Try a different port
python api_server_svg.py --port 5002
```

**Module not found:**
```bash
pip install -r requirements.txt
```

**Coordinates not working:**
- Each coordinate must have exactly 4 values: `[x1, y1, x2, y2]`
- Ensure `x2 > x1` and `y2 > y1`
- Coordinates must be within image bounds

## License

MIT License

## Acknowledgments

- Ultralytics YOLOv8 for object detection
- OpenCV for computer vision
- Flask for web framework
