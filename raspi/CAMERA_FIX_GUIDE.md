# Raspberry Pi Camera Fix - Quick Guide

## Problem
Camera opens successfully but fails to capture frames with the error:
```
⚠️ Failed to capture from camera_1
```

## What Was Fixed

### 1. Improved Camera Initialization (camera_manager.py)
- Added proper resolution setting when using OpenCV fallback
- Added buffer size configuration to reduce lag
- Added 2-second warm-up period
- **Added test frame capture during initialization** to verify camera works
- Better error logging with more details

### 2. Enhanced Capture Method
- Added explicit checks for camera state before capture
- Better error messages to identify issues
- More robust null/error handling

## Testing on Your Raspberry Pi

### Step 1: Run Simple Test
Copy the updated files to your Pi, then run:
```bash
cd ~/YoloParklot/raspi
python3 test_camera_simple.py
```

This will:
- Test camera with default OpenCV backend
- Test camera with V4L2 backend
- Save test frames if successful
- Show detailed diagnostic info

### Step 2: If Test Fails, Enable V4L2 Driver
On Raspberry Pi, run:
```bash
sudo modprobe bcm2835-v4l2
```

To make it permanent, add to `/etc/modules`:
```bash
echo "bcm2835-v4l2" | sudo tee -a /etc/modules
```

### Step 3: Verify Camera Detection
```bash
# Check camera status
vcgencmd get_camera

# Should show: supported=1 detected=1

# List video devices
ls -l /dev/video*

# Should show /dev/video0
```

### Step 4: Run Edge Server
```bash
python3 edge_server.py
```

## Configuration Notes

Your current config has:
```json
{
  "type": "picamera",
  "resolution": [1920, 1080]
}
```

The updated code will:
1. Try picamera2 (modern library) ✗ Not installed
2. Try legacy picamera ✗ Not installed  
3. Fall back to OpenCV ✓ **This is where you are**
4. Now properly sets resolution and tests capture

## Common Issues & Solutions

### Issue: "Camera opened but cannot read frames"
**Solution**: Enable V4L2 driver
```bash
sudo modprobe bcm2835-v4l2
```

### Issue: Still no frames after V4L2
**Solution**: Try reducing resolution in config.json
```json
"resolution": [640, 480]
```

### Issue: Permission denied
**Solution**: Add user to video group
```bash
sudo usermod -a -G video $USER
# Then logout/login
```

### Issue: Camera busy
**Solution**: Check for other processes using camera
```bash
sudo fuser /dev/video0
# Kill any processes, then try again
```

## What Changed in the Code

### Before (Lines 114-120):
```python
self.camera = cv2.VideoCapture(0)
if self.camera.isOpened():
    self.is_opened = True
    self.using_opencv = True
    return True
```

### After (Lines 114-141):
```python
self.camera = cv2.VideoCapture(0)

if not self.camera.isOpened():
    raise Exception("Could not open camera with OpenCV")

# Set resolution
resolution = self.config.get('resolution', [1920, 1080])
self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

# Set buffer to reduce lag
self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# Warm up camera
import time
time.sleep(2)

# Test read a frame to ensure camera is working
ret, test_frame = self.camera.read()
if not ret or test_frame is None:
    logger.error("Camera opened but cannot read frames")
    self.camera.release()
    raise Exception("Camera opened but cannot read frames")

self.is_opened = True
self.using_opencv = True
```

## Next Steps on Your Pi

1. **Copy files to Pi**
2. **Run test**: `python3 raspi/test_camera_simple.py`
3. **If test passes**: Run `python3 raspi/edge_server.py`
4. **If test fails**: Follow troubleshooting steps above
5. **Report back** with test results

The key improvement is that the camera is now properly configured and tested during initialization, so you'll know immediately if there's an issue rather than failing silently at capture time.
