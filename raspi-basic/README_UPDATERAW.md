# Raspberry Pi Edge Server - updateRaw API Integration

## Overview

This edge server has been updated to work with the new `/parking/updateRaw` API endpoint. It captures frames from a camera (USB, RTSP, or Raspberry Pi Camera Module) and sends them to the cloud server for real-time parking detection.

## What's New

### Key Changes
1. **API Endpoint Update**: Now uses `/parking/updateRaw` instead of the old `/api/upload`
2. **Authentication**: Supports API key or JWT token authentication
3. **Parking Coordinates**: Requires parking slot coordinates to be defined in config
4. **Camera/Node IDs**: Supports separate `camera_id` and `node_id` for better tracking
5. **Enhanced Logging**: Detailed response logging including occupancy stats and GCS URLs

## Configuration

### Required Fields in `config.json`

```json
{
    "camera_type": "picamera",
    "api_endpoint": "http://YOUR_SERVER_IP:5000/parking/updateRaw",
    "api_key": "YOUR_API_KEY_OR_JWT_TOKEN",
    "camera_id": "raspberry_pi_camera_1",
    "node_id": "raspberry_pi_edge_1",
    "coordinates": [
        [100, 150, 250, 300],
        [270, 150, 420, 300],
        [440, 150, 590, 300]
    ],
    "interval": 60,
    "device_id": "raspberry_pi_edge_1",
    "retry_attempts": 3,
    "retry_delay": 5,
    "save_local_copy": false,
    "local_save_path": "./captured_frames"
}
```

### Configuration Fields Explained

#### New/Updated Fields:
- **`api_endpoint`**: Full URL to the updateRaw endpoint (e.g., `http://192.168.1.100:5000/parking/updateRaw`)
- **`api_key`**: Your API key or JWT token for authentication (get this from your user account)
- **`camera_id`**: Unique identifier for this camera (used for tracking and filtering)
- **`node_id`**: Optional node identifier (defaults to `camera_id` if not provided)
- **`coordinates`**: Array of parking slot coordinates in format `[[x1, y1, x2, y2], ...]`
  - `x1, y1`: Top-left corner of parking slot
  - `x2, y2`: Bottom-right corner of parking slot
  - Example: `[100, 150, 250, 300]` defines a slot from (100,150) to (250,300)

#### Existing Fields:
- **`camera_type`**: Type of camera - `"picamera"`, `"usb"`, or `"rtsp"`
- **`camera_index`**: For USB cameras, the device index (0, 1, 2, etc.)
- **`rtsp_url`**: For RTSP cameras, the full stream URL
- **`interval`**: Time in seconds between frame captures (default: 60)
- **`retry_attempts`**: Number of retry attempts on network failure (default: 3)
- **`retry_delay`**: Seconds to wait between retries (default: 5)
- **`save_local_copy`**: Whether to save frames locally (default: false)
- **`local_save_path`**: Directory for local frame storage

## Getting Your API Key

### Method 1: From Dashboard
1. Log in to the web dashboard
2. Go to Settings or Profile
3. Generate or copy your API key

### Method 2: Using the API
```bash
# Register/Login to get JWT token
curl -X POST http://YOUR_SERVER_IP:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpassword"}'

# Use the returned token as your api_key
```

## Defining Parking Coordinates

### Method 1: Use Test Tool
Run the coordinate picker tool to visually select parking slots:
```bash
python3 test_coordinate_picker.py
```

### Method 2: Manual Definition
Define coordinates based on your camera's field of view:

```json
"coordinates": [
    [x1, y1, x2, y2],  // Slot 1
    [x1, y1, x2, y2],  // Slot 2
    [x1, y1, x2, y2]   // Slot 3
]
```

**Example for 1280x720 camera:**
```json
"coordinates": [
    [100, 150, 250, 300],   // Top-left slot
    [270, 150, 420, 300],   // Top-middle slot
    [440, 150, 590, 300],   // Top-right slot
    [100, 320, 250, 470],   // Bottom-left slot
    [270, 320, 420, 470],   // Bottom-middle slot
    [440, 320, 590, 470]    // Bottom-right slot
]
```

### Tips for Defining Coordinates:
- Capture a test image from your camera first
- Use image editing software to identify pixel coordinates
- Ensure coordinates match your camera's resolution
- Leave some margin around actual parking spaces
- Test with one or two slots first before defining all

## Installation & Setup

### 1. Install Dependencies
```bash
cd raspi-basic
pip3 install -r requirements.txt

# For Raspberry Pi Camera Module (Bullseye or later)
sudo apt install python3-picamera2

# For older Raspberry Pi OS
pip3 install picamera
```

### 2. Configure Settings
```bash
# Copy and edit the config file
cp config_picamera.json config.json
nano config.json

# Update these fields:
# - api_endpoint: Your server URL
# - api_key: Your authentication token
# - camera_id: Your camera identifier
# - coordinates: Your parking slot coordinates
```

### 3. Test the Configuration
```bash
# Validate configuration
python3 edge_server.py

# Check for validation errors in output:
# ✅ Configuration validated successfully
# ✅ API Endpoint: http://...
# ✅ Parking Slots: 6
```

## Running the Server

### Manual Run
```bash
python3 edge_server.py
```

### Run as Background Service
```bash
# Run with nohup
nohup python3 edge_server.py > edge_server.log 2>&1 &

# Or use screen
screen -S edge-server
python3 edge_server.py
# Press Ctrl+A, then D to detach
```

### Run as Systemd Service
Create `/etc/systemd/system/edge-server.service`:
```ini
[Unit]
Description=Parking Detection Edge Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/raspi-basic
ExecStart=/usr/bin/python3 /home/pi/raspi-basic/edge_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable edge-server.service
sudo systemctl start edge-server.service
sudo systemctl status edge-server.service
```

## Monitoring & Logs

### Check Logs
```bash
# View real-time logs
tail -f edge_server.log

# View systemd logs
sudo journalctl -u edge-server -f
```

### Expected Log Output
```
2025-11-04 10:30:00 - EdgeServer - INFO - Configuration loaded from config.json
2025-11-04 10:30:00 - EdgeServer - INFO - Configured for Raspberry Pi Camera Module
2025-11-04 10:30:00 - EdgeServer - INFO - ✅ Configuration validated successfully
2025-11-04 10:30:00 - EdgeServer - INFO -    API Endpoint: http://192.168.1.100:5000/parking/updateRaw
2025-11-04 10:30:00 - EdgeServer - INFO -    Camera ID: raspberry_pi_camera_1
2025-11-04 10:30:00 - EdgeServer - INFO -    Parking Slots: 6
2025-11-04 10:30:05 - EdgeServer - INFO - Frame captured via picamera2 - Shape: (720, 1280, 3)
2025-11-04 10:30:05 - EdgeServer - INFO - Sending frame to http://192.168.1.100:5000/parking/updateRaw
2025-11-04 10:30:07 - EdgeServer - INFO - ✅ Frame processed successfully!
2025-11-04 10:30:07 - EdgeServer - INFO -    Document ID: 6728a1b2c3d4e5f678901234
2025-11-04 10:30:07 - EdgeServer - INFO -    Total Slots: 6
2025-11-04 10:30:07 - EdgeServer - INFO -    Occupied: 4
2025-11-04 10:30:07 - EdgeServer - INFO -    Empty: 2
2025-11-04 10:30:07 - EdgeServer - INFO -    Occupancy Rate: 66.67%
2025-11-04 10:30:07 - EdgeServer - INFO -    Processing Time: 245ms
2025-11-04 10:30:07 - EdgeServer - INFO -    🌐 Images uploaded to Google Cloud Storage
```

## API Response

The server receives detailed information about each processed frame:

```json
{
    "success": true,
    "document_id": "6728a1b2c3d4e5f678901234",
    "total_slots": 6,
    "total_cars_detected": 4,
    "occupied_slots": 4,
    "empty_slots": 2,
    "occupancy_rate": 66.67,
    "svg_code": "<svg>...</svg>",
    "slots_details": [...],
    "timestamp": "2025-11-04T10:30:07.123Z",
    "processing_time_ms": 245.67,
    "gcs_storage": {
        "enabled": true,
        "raw_image": {
            "path": "users/user123/node456/raw/20251104_103007_123.jpg",
            "url": "https://storage.googleapis.com/..."
        },
        "annotated_image": {
            "path": "users/user123/node456/annotated/20251104_103007_123.jpg",
            "url": "https://storage.googleapis.com/..."
        }
    }
}
```

## Troubleshooting

### "Missing 'api_key' in configuration"
- Add your API key to `config.json`
- Get it from the dashboard or by logging in via API

### "Missing or empty 'coordinates'"
- Define parking slot coordinates in `config.json`
- Use the coordinate picker tool or manual definition
- Ensure at least one coordinate is defined

### "401 Unauthorized"
- Your API key is invalid or expired
- Generate a new API key from the dashboard
- Ensure you're using the correct user account

### "400 Bad Request - Invalid coordinates"
- Check coordinate format: `[[x1,y1,x2,y2], ...]`
- Ensure all coordinates have exactly 4 values
- Verify coordinates are within camera frame bounds

### Camera Connection Issues
- For Pi Camera: Check ribbon cable connection
- For USB Camera: Verify device index (try 0, 1, 2)
- For RTSP: Test stream URL with VLC first
- Run: `ls /dev/video*` to see available cameras

### Network Issues
- Verify server IP address and port
- Check firewall rules (port 5000 must be open)
- Test connectivity: `curl http://YOUR_SERVER_IP:5000/health`

## Example Configurations

### Pi Camera with 3 Parking Slots
```json
{
    "camera_type": "picamera",
    "api_endpoint": "http://192.168.1.100:5000/parking/updateRaw",
    "api_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "camera_id": "parking_lot_entrance",
    "coordinates": [
        [200, 300, 400, 500],
        [450, 300, 650, 500],
        [700, 300, 900, 500]
    ],
    "interval": 30
}
```

### USB Camera with 8 Slots
```json
{
    "camera_type": "usb",
    "camera_index": 0,
    "api_endpoint": "http://192.168.1.100:5000/parking/updateRaw",
    "api_key": "your_api_key_here",
    "camera_id": "parking_lot_main",
    "coordinates": [
        [100, 100, 250, 280], [280, 100, 430, 280],
        [460, 100, 610, 280], [640, 100, 790, 280],
        [100, 300, 250, 480], [280, 300, 430, 480],
        [460, 300, 610, 480], [640, 300, 790, 480]
    ],
    "interval": 45,
    "save_local_copy": true
}
```

### RTSP Camera
```json
{
    "camera_type": "rtsp",
    "rtsp_url": "rtsp://admin:password@192.168.1.50:554/stream",
    "api_endpoint": "http://192.168.1.100:5000/parking/updateRaw",
    "api_key": "your_api_key_here",
    "camera_id": "parking_lot_rear",
    "coordinates": [
        [150, 200, 350, 400],
        [400, 200, 600, 400]
    ],
    "interval": 60
}
```

## Support

For issues or questions:
1. Check the logs: `tail -f edge_server.log`
2. Verify configuration: Look for validation messages on startup
3. Test API endpoint: Use curl or Postman
4. Review main documentation: Check project README files

## Version History

### v2.0 (Current)
- ✅ Updated to use `/parking/updateRaw` API
- ✅ Added authentication support
- ✅ Added coordinate configuration
- ✅ Enhanced logging with detection statistics
- ✅ Configuration validation on startup
- ✅ Support for camera_id and node_id

### v1.0 (Legacy)
- Basic frame upload to `/api/upload`
- No authentication
- No parking detection
