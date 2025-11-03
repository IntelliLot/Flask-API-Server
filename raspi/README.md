# 🍓 Raspberry Pi Edge Server

Edge server for capturing parking lot images from multiple cameras and uploading to the central IntelliLot server.

## 📋 Features

- **Multi-Camera Support**: 
  - Raspberry Pi Camera Module (picamera/picamera2)
  - USB Webcams
  - RTSP/IP Cameras
  - Multiple cameras simultaneously with unique node IDs

- **Robust Upload System**:
  - Automatic retry on failure
  - Configurable retry attempts and delays
  - JWT/API key authentication
  - Batch upload support (optional)

- **System Monitoring**:
  - CPU, Memory, Disk usage tracking
  - Temperature monitoring (Raspberry Pi)
  - Health checks and auto-restart
  - Detailed logging

- **Local Storage**:
  - Optional local image backup
  - Automatic cleanup of old files
  - Configurable retention policy

## 🚀 Quick Start

### 1. Installation

```bash
cd raspi
chmod +x setup.sh
./setup.sh
```

### 2. Configuration

Edit `config.json` with your settings:

```json
{
    "api_endpoint": "http://YOUR_PC_IP:5001/parking/updateRaw",
    "api_key": "YOUR_API_KEY_HERE",
    "device_id": "raspberry_pi_edge_1",
    ...
}
```

**Important Configuration:**
- `api_endpoint`: Your server's IP address and port
- `api_key`: API key from your IntelliLot dashboard
- `device_id`: Unique identifier for this edge device
- `cameras`: Configure each camera with unique `node_id`

### 3. Run

```bash
# Run directly
python3 edge_server.py

# Or with custom config
python3 edge_server.py --config custom_config.json
```

## 📷 Camera Configuration

### Raspberry Pi Camera Module

```json
{
    "node_id": "camera_1",
    "type": "picamera",
    "enabled": true,
    "resolution": [1920, 1080],
    "framerate": 30,
    "rotation": 0,
    "description": "Raspberry Pi Camera Module"
}
```

### USB Webcam

```json
{
    "node_id": "camera_2",
    "type": "usb",
    "enabled": true,
    "camera_index": 0,
    "resolution": [1280, 720],
    "description": "USB Webcam - Front Entrance"
}
```

### RTSP/IP Camera

```json
{
    "node_id": "camera_3",
    "type": "rtsp",
    "enabled": true,
    "rtsp_url": "rtsp://username:password@192.168.1.100:554/stream",
    "description": "IP Camera - Main Parking Lot"
}
```

## 🔧 Advanced Configuration

### Capture Settings

```json
"capture_settings": {
    "interval": 60,              // Capture every 60 seconds
    "quality": 85,               // JPEG quality (0-100)
    "format": "jpg",             // Image format
    "save_local_copy": true,     // Save locally before upload
    "local_save_path": "./captured_frames",
    "max_local_images": 100      // Keep only last 100 images
}
```

### Upload Settings

```json
"upload_settings": {
    "retry_attempts": 3,         // Retry 3 times on failure
    "retry_delay": 5,            // Wait 5 seconds between retries
    "timeout": 30,               // Request timeout in seconds
    "verify_ssl": true,          // Verify SSL certificates
    "batch_upload": false,       // Upload images in batches
    "batch_size": 5              // Batch size if enabled
}
```

### System Monitoring

```json
"monitoring": {
    "enable_system_stats": true,
    "cpu_threshold": 80,         // Warning if CPU > 80%
    "memory_threshold": 85,      // Warning if Memory > 85%
    "disk_threshold": 90,        // Warning if Disk > 90%
    "temperature_threshold": 70  // Warning if Temp > 70°C
}
```

## 🔄 Running as a Service

To run the edge server automatically on boot:

```bash
# Copy service file
sudo cp edge_server.service /etc/systemd/system/

# Edit the service file with correct paths
sudo nano /etc/systemd/system/edge_server.service

# Enable and start service
sudo systemctl enable edge_server
sudo systemctl start edge_server

# Check status
sudo systemctl status edge_server

# View logs
sudo journalctl -u edge_server -f
```

## 📊 Monitoring

### View Logs

```bash
# Real-time logs
tail -f logs/edge_server.log

# Or with systemd
sudo journalctl -u edge_server -f
```

### Check Status

The server prints status every 5 minutes (configurable):

```
============================================================
📊 Edge Server Status
============================================================
⏱️  Uptime: 0:15:30
📷 Active Cameras: 3
📸 Total Captures: 45
✅ Successful Uploads: 43
❌ Failed Uploads: 2
⚠️  Errors: 0
🖥️  CPU: 25.3%
💾 Memory: 45.2%
💽 Disk: 62.1%
🌡️  Temperature: 48.5°C
============================================================
```

## 🛠️ Troubleshooting

### Camera Not Detected

**Raspberry Pi Camera:**
```bash
# Check if camera is enabled
vcgencmd get_camera

# Enable camera
sudo raspi-config
# Navigate to: Interface Options -> Camera -> Enable
```

**USB Camera:**
```bash
# List available cameras
ls -l /dev/video*

# Test camera with OpenCV
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Failed')"
```

**RTSP Camera:**
```bash
# Test RTSP stream with ffplay
ffplay rtsp://username:password@ip:port/stream
```

### Upload Failures

1. **Check API endpoint**: Ensure server is accessible
   ```bash
   curl http://YOUR_PC_IP:5001/health
   ```

2. **Verify API key**: Check that API key is valid in dashboard

3. **Network connectivity**: 
   ```bash
   ping YOUR_PC_IP
   ```

### High CPU/Memory Usage

- Reduce capture interval
- Lower image resolution
- Disable local storage
- Reduce JPEG quality

### Temperature Issues

- Ensure proper ventilation
- Add heatsink/fan to Raspberry Pi
- Reduce capture frequency
- Lower camera resolution

## 📁 Project Structure

```
raspi/
├── edge_server.py          # Main edge server application
├── camera_manager.py       # Multi-camera support
├── system_monitor.py       # System resource monitoring
├── config.json            # Configuration file
├── requirements.txt       # Python dependencies
├── setup.sh              # Installation script
├── edge_server.service   # Systemd service file
├── README.md             # This file
├── logs/                 # Log files
└── captured_frames/      # Local image storage
```

## 🔐 Security Notes

- Keep your `api_key` secure
- Use HTTPS for `api_endpoint` in production
- Change default passwords for RTSP cameras
- Restrict network access to the edge server
- Regularly update system and dependencies

## 📝 License

Part of the IntelliLot Parking Detection System

## 🤝 Support

For issues or questions:
1. Check the logs: `logs/edge_server.log`
2. Review configuration: `config.json`
3. Check system status: `sudo systemctl status edge_server`
4. Contact support with logs and error messages
