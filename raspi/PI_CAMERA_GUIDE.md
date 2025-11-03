# 📷 Pi Camera Usage Guide

## Overview

The edge server now has improved Raspberry Pi Camera support with automatic detection and fallback:

1. **picamera2** (Modern - Raspberry Pi OS Bullseye+)
2. **picamera** (Legacy - Older Raspberry Pi OS versions)
3. **OpenCV** (Fallback if neither picamera library is available)

## Camera Libraries

### picamera2 (Recommended for new setups)

**For Raspberry Pi OS Bullseye/Bookworm:**
```bash
sudo apt update
sudo apt install -y python3-picamera2
```

### Legacy picamera

**For older Raspberry Pi OS:**
```bash
pip3 install picamera
```

## Configuration

### In config.json:

```json
{
    "cameras": [
        {
            "node_id": "picam_main",
            "type": "picamera",
            "enabled": true,
            "resolution": [1920, 1080],
            "framerate": 30,
            "rotation": 0,
            "description": "Raspberry Pi Camera Module v2"
        }
    ]
}
```

### Resolution Options:

Common resolutions:
- `[1920, 1080]` - Full HD
- `[1280, 720]` - HD
- `[640, 480]` - VGA (fast)

### Rotation:

- `0` - No rotation
- `90` - 90° clockwise
- `180` - 180° rotation
- `270` - 270° clockwise

## How It Works

### Automatic Detection:

1. **First Try: picamera2**
   - Checks if `picamera2` is installed
   - Configures still capture mode
   - Warms up for 2 seconds
   - Tests with a capture

2. **Second Try: legacy picamera**
   - Falls back if picamera2 not available
   - Uses PiRGBArray for capture
   - Configures resolution, framerate, rotation

3. **Final Fallback: OpenCV**
   - Uses OpenCV's VideoCapture(0)
   - Works but may have compatibility issues

### Frame Capture:

The system automatically:
- Converts RGB to BGR for OpenCV compatibility (picamera2)
- Handles BGR directly (legacy picamera)
- Clears the stream buffer after each capture (legacy)
- Logs frame shapes for debugging

## Enable Camera on Raspberry Pi

```bash
# Using raspi-config
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable

# Verify camera is enabled
vcgencmd get_camera

# Test camera
raspistill -o test.jpg
```

## Testing

### Quick Test:

```bash
cd ~/YoloParklot/raspi
python3 test_camera.py
```

### Manual Test:

```python
from camera_manager import CameraManager

config = {
    "node_id": "test_cam",
    "type": "picamera",
    "enabled": true,
    "resolution": [1280, 720]
}

# Initialize
cam_manager = CameraManager([config])

# Open camera
cam_manager.open_all()

# Capture frame
frames = cam_manager.capture_all()

# Check result
if frames:
    print(f"✅ Captured frame: {frames['test_cam'].shape}")
else:
    print("❌ Failed to capture")

# Cleanup
cam_manager.release_all()
```

## Troubleshooting

### Camera not detected:

```bash
# Check if camera is connected
vcgencmd get_camera
# Should show: supported=1 detected=1

# Check camera interface
ls -l /dev/video0
```

### picamera2 not found:

```bash
# Install for Raspberry Pi OS Bullseye+
sudo apt update
sudo apt install -y python3-picamera2

# Check Python version (picamera2 requires Python 3.9+)
python3 --version
```

### Legacy picamera issues:

```bash
# Install legacy picamera
pip3 install picamera

# If fails, try:
sudo apt install python3-picamera
```

### Permission issues:

```bash
# Add user to video group
sudo usermod -a -G video $USER

# Logout and login again for changes to take effect
```

### Black/corrupted images:

- Check camera is properly connected to CSI port
- Ensure ribbon cable is inserted correctly
- Try lower resolution: `[640, 480]`
- Increase warm-up time in code

## Performance Tips

### For faster capture:

```json
{
    "resolution": [640, 480],  // Lower resolution
    "framerate": 15,           // Lower framerate
}
```

### For better quality:

```json
{
    "resolution": [1920, 1080],
    "framerate": 30,
    "quality": 95  // In capture_settings
}
```

## Logs

Check logs for camera initialization:

```bash
tail -f ~/YoloParklot/raspi/logs/edge_server.log
```

Look for:
```
✅ Pi Camera picam_main opened using picamera2
   Resolution: 1920x1080
```

Or:
```
✅ Pi Camera picam_main opened using legacy picamera
   Resolution: 1920x1080
```

## Multiple Cameras

You can run multiple cameras with unique node_ids:

```json
{
    "cameras": [
        {
            "node_id": "picam_1",
            "type": "picamera",
            "enabled": true,
            "resolution": [1920, 1080]
        },
        {
            "node_id": "usb_cam_1",
            "type": "usb",
            "enabled": true,
            "camera_index": 0
        },
        {
            "node_id": "ip_cam_1",
            "type": "rtsp",
            "enabled": true,
            "rtsp_url": "rtsp://camera:554/stream"
        }
    ]
}
```

## Camera Module Versions

- **v1** (5MP): Up to 1920x1080 @ 30fps
- **v2** (8MP): Up to 3280x2464 @ 15fps, 1920x1080 @ 30fps
- **HQ** (12.3MP): Up to 4056x3040, C/CS-mount lens support
- **v3** (12MP): Up to 4608x2592, better low-light

All versions work with this edge server! 🎉

## Advanced Configuration

### Custom Capture Settings:

```python
# In camera_manager.py PiCamera class:

# For picamera2:
camera_config = self.camera.create_still_configuration(
    main={
        "size": (1920, 1080),
        "format": "RGB888"
    },
    controls={
        "ExposureTime": 20000,  # microseconds
        "AnalogueGain": 1.0
    }
)

# For legacy picamera:
self.camera.iso = 400
self.camera.shutter_speed = 20000
self.camera.brightness = 50
```

##Summary

✅ Automatic library detection  
✅ Three-level fallback system  
✅ Proper BGR/RGB conversion  
✅ Stream buffer management  
✅ Warm-up and test capture  
✅ Detailed logging  
✅ Resolution & rotation support  
✅ Works with all Pi Camera versions  

Your Raspberry Pi Camera is now production-ready! 🍓📷
