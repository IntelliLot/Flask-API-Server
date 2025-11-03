# Raspberry Pi Edge Server - Update Summary

## What Was Updated

Your Raspberry Pi edge server (`raspi-basic/`) has been updated to support the new **`/parking/updateRaw`** API endpoint.

## Files Modified

### 1. `edge_server.py` ✅
**Key Changes:**
- Updated `__init__` to load new config fields:
  - `api_key`: Authentication token
  - `camera_id`: Camera identifier
  - `node_id`: Node identifier (optional)
  - `coordinates`: Parking slot coordinates
- Added `validate_config()` method to check configuration on startup
- Completely rewrote `send_frame_to_cloud()` to:
  - Send data to `/parking/updateRaw` endpoint
  - Include authentication header
  - Send parking coordinates with each request
  - Parse and log detailed detection results
  - Display GCS storage information

### 2. `config_picamera.json` ✅
**Updated with new required fields:**
```json
{
    "api_endpoint": "http://YOUR_SERVER_IP:5000/parking/updateRaw",
    "api_key": "YOUR_API_KEY_OR_JWT_TOKEN",
    "camera_id": "raspberry_pi_camera_1",
    "node_id": "raspberry_pi_edge_1",
    "coordinates": [[100, 150, 250, 300], ...]
}
```

## New Files Created

### 3. `README_UPDATERAW.md` 📖
Comprehensive documentation including:
- Overview of changes
- Complete configuration guide
- How to get API keys
- How to define parking coordinates
- Installation & setup instructions
- Running the server (manual, background, systemd)
- Monitoring & logs
- Troubleshooting guide
- Example configurations

### 4. `test_config.py` 🧪
Configuration validation and testing tool:
- Validates all required config fields
- Tests API connectivity
- Tests authentication
- Provides detailed error messages
- Usage: `python3 test_config.py`

### 5. `setup.sh` 🚀
Quick setup script that:
- Creates config.json from template
- Installs Python dependencies
- Opens editor for configuration
- Runs configuration test
- Usage: `./setup.sh`

### 6. `coordinate_picker.py` 🎯
Interactive visual tool to define parking slots:
- Captures frame from camera
- Draw rectangles with mouse
- Saves coordinates to config
- Usage: `python3 coordinate_picker.py`

### 7. `requirements.txt` 📦
Python dependencies:
- opencv-python
- requests
- numpy

## How the New API Works

### Old Workflow (v1.0):
1. Capture frame
2. Send to `/api/upload`
3. Receive basic acknowledgment

### New Workflow (v2.0):
1. Capture frame from camera
2. Send to `/parking/updateRaw` with:
   - Raw image (JPEG)
   - Parking coordinates
   - Camera ID
   - Node ID
   - Authentication token
3. Server processes frame:
   - Uploads raw image to Google Cloud Storage
   - Runs YOLO detection
   - Detects parking occupancy
   - Creates annotated image
   - Uploads annotated image to GCS
   - Saves data to MongoDB
4. Receive detailed response:
   - Document ID
   - Total slots, occupied, empty
   - Occupancy rate
   - Processing time
   - GCS URLs for images
   - SVG visualization code

## API Response Example

The edge server now receives and logs:

```json
{
    "success": true,
    "document_id": "6728a1b2c3d4e5f678901234",
    "total_slots": 6,
    "total_cars_detected": 4,
    "occupied_slots": 4,
    "empty_slots": 2,
    "occupancy_rate": 66.67,
    "processing_time_ms": 245.67,
    "gcs_storage": {
        "enabled": true,
        "raw_image": {
            "path": "users/user123/node456/raw/...",
            "url": "https://storage.googleapis.com/..."
        },
        "annotated_image": {
            "path": "users/user123/node456/annotated/...",
            "url": "https://storage.googleapis.com/..."
        }
    }
}
```

## Enhanced Log Output

The updated server now provides rich logging:

```
2025-11-04 10:30:07 - EdgeServer - INFO - ✅ Frame processed successfully!
2025-11-04 10:30:07 - EdgeServer - INFO -    Document ID: 6728a1b2c3d4e5f678901234
2025-11-04 10:30:07 - EdgeServer - INFO -    Total Slots: 6
2025-11-04 10:30:07 - EdgeServer - INFO -    Occupied: 4
2025-11-04 10:30:07 - EdgeServer - INFO -    Empty: 2
2025-11-04 10:30:07 - EdgeServer - INFO -    Occupancy Rate: 66.67%
2025-11-04 10:30:07 - EdgeServer - INFO -    Processing Time: 245ms
2025-11-04 10:30:07 - EdgeServer - INFO -    🌐 Images uploaded to Google Cloud Storage
2025-11-04 10:30:07 - EdgeServer - INFO -       Raw: users/user123/node456/raw/...
2025-11-04 10:30:07 - EdgeServer - INFO -       Annotated: users/user123/node456/annotated/...
```

## Configuration Validation

The server now validates configuration on startup:

```
✅ Configuration validated successfully
   API Endpoint: http://192.168.1.100:5000/parking/updateRaw
   Camera ID: raspberry_pi_camera_1
   Node ID: raspberry_pi_edge_1
   Parking Slots: 6
   Update Interval: 60 seconds
```

Catches errors like:
- ❌ Missing 'api_endpoint'
- ❌ Missing or empty 'coordinates'
- ❌ Invalid coordinate format
- ⚠️ No 'api_key' provided

## Quick Start Guide

### For New Setup:
```bash
cd raspi-basic
./setup.sh
```

### For Existing Users:
1. Update `config.json` with:
   - `api_endpoint`: Change to `/parking/updateRaw`
   - `api_key`: Add your token
   - `coordinates`: Define parking slots
   - `camera_id`: Add camera identifier

2. Test configuration:
   ```bash
   python3 test_config.py
   ```

3. Run the server:
   ```bash
   python3 edge_server.py
   ```

## Migration Checklist

- [ ] Update `api_endpoint` to use `/parking/updateRaw`
- [ ] Add `api_key` (get from dashboard or login API)
- [ ] Add `camera_id` for camera identification
- [ ] Define `coordinates` for parking slots
- [ ] Optional: Add `node_id` if different from camera_id
- [ ] Test configuration: `python3 test_config.py`
- [ ] Run server and verify logs show detection results
- [ ] Check dashboard to see uploaded images and data

## Breaking Changes

### Required Config Changes:
- `api_endpoint` must point to `/parking/updateRaw`
- `api_key` is now required for authentication
- `coordinates` array is mandatory
- `camera_id` is required (can use existing `device_id`)

### API Changes:
- Old `/api/upload` endpoint is no longer used
- New endpoint requires authentication
- New endpoint expects parking coordinates
- Response format has changed (more detailed)

## Benefits of New System

✅ **Full parking detection** - Server processes images with YOLO  
✅ **Cloud storage** - Images stored in Google Cloud Storage  
✅ **Rich analytics** - Detailed occupancy statistics  
✅ **Better tracking** - Camera and node identification  
✅ **Security** - Authentication required  
✅ **Visualization** - SVG parking lot views  
✅ **Historical data** - All data saved to MongoDB  
✅ **Flexible coordinates** - Define any parking layout  

## Support & Troubleshooting

See `README_UPDATERAW.md` for:
- Detailed configuration guide
- Troubleshooting common issues
- Example configurations
- Step-by-step setup instructions

## Version Info

- **Previous**: v1.0 - Basic frame upload
- **Current**: v2.0 - Full updateRaw API integration
- **Compatible with**: Flask API Server v2.0+
- **Python**: 3.7+
- **Camera Support**: USB, RTSP, Raspberry Pi Camera Module
