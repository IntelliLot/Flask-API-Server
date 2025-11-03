# Quick Reference - Raspberry Pi Edge Server

## 🚀 Quick Start

```bash
cd raspi-basic
./setup.sh                    # Interactive setup
python3 test_config.py        # Test configuration
python3 edge_server.py        # Run server
```

## 📋 Required Configuration

Edit `config.json`:

```json
{
    "api_endpoint": "http://SERVER_IP:5000/parking/updateRaw",
    "api_key": "your_token_here",
    "camera_id": "your_camera_name",
    "coordinates": [[x1,y1,x2,y2], ...]
}
```

## 🔑 Get API Key

**From Dashboard:**
1. Login to web dashboard
2. Go to Settings/Profile
3. Copy API key

**From API:**
```bash
curl -X POST http://SERVER_IP:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpass"}'
```

## 📍 Define Coordinates

**Method 1 - Visual Tool:**
```bash
python3 coordinate_picker.py
# Click and drag to draw parking slots
# Press 's' to save, 'u' to undo, 'q' to quit
```

**Method 2 - Manual:**
```json
"coordinates": [
    [100, 150, 250, 300],  // x1, y1, x2, y2
    [270, 150, 420, 300]
]
```

## ✅ Test & Validate

```bash
python3 test_config.py    # Validates config and tests connectivity
```

Output should show:
- ✅ Configuration is valid
- ✅ Server is reachable
- ✅ Authentication works

## 🏃 Run the Server

**Foreground (testing):**
```bash
python3 edge_server.py
```

**Background:**
```bash
nohup python3 edge_server.py > edge_server.log 2>&1 &
```

**View Logs:**
```bash
tail -f edge_server.log
```

**Stop Background:**
```bash
pkill -f edge_server.py
```

## 📊 Expected Output

```
✅ Configuration validated successfully
   API Endpoint: http://192.168.1.100:5000/parking/updateRaw
   Camera ID: parking_camera_1
   Parking Slots: 6
   
✅ Frame captured successfully
Sending frame to server...
✅ Frame processed successfully!
   Total Slots: 6
   Occupied: 4
   Empty: 2
   Occupancy Rate: 66.67%
   Processing Time: 245ms
   🌐 Images uploaded to Google Cloud Storage
```

## 🛠️ Camera Types

**Raspberry Pi Camera:**
```json
{"camera_type": "picamera"}
```

**USB Camera:**
```json
{
    "camera_type": "usb",
    "camera_index": 0
}
```

**RTSP Stream:**
```json
{
    "camera_type": "rtsp",
    "rtsp_url": "rtsp://user:pass@ip:554/stream"
}
```

## ⚠️ Common Issues

**"Missing api_key"**
→ Add your API key to config.json

**"Missing coordinates"**
→ Run `python3 coordinate_picker.py`

**"401 Unauthorized"**
→ Check your API key is valid

**"Cannot connect to server"**
→ Verify server IP and port
→ Check server is running: `curl http://IP:5000/health`

**Camera not found**
→ Pi Camera: Check ribbon cable
→ USB: Try camera_index 0, 1, 2
→ RTSP: Test URL in VLC

## 📁 Files Overview

| File | Purpose |
|------|---------|
| `edge_server.py` | Main server application |
| `config.json` | Configuration file |
| `test_config.py` | Validate configuration |
| `coordinate_picker.py` | Visual coordinate tool |
| `setup.sh` | Quick setup script |
| `README_UPDATERAW.md` | Full documentation |
| `UPDATE_SUMMARY.md` | What changed |

## 🔄 Update Interval

Default: 60 seconds

Change in config:
```json
{"interval": 30}  // 30 seconds
```

## 💾 Save Local Copies

To save frames locally:
```json
{
    "save_local_copy": true,
    "local_save_path": "./captured_frames"
}
```

## 📡 API Endpoint

Make sure to use the full endpoint:
```
http://YOUR_SERVER_IP:5000/parking/updateRaw
```

NOT:
- ~~http://YOUR_SERVER_IP:5000~~ (missing path)
- ~~http://YOUR_SERVER_IP:5000/api/upload~~ (old endpoint)

## 🎯 Coordinate Format

Each slot needs 4 values: `[x1, y1, x2, y2]`

- `x1, y1`: Top-left corner
- `x2, y2`: Bottom-right corner

Example:
```
(100,150)--------
    |            |
    |   SLOT 1   |
    |            |
    ---------(250,300)
```
Coordinates: `[100, 150, 250, 300]`

## 📞 Help Commands

```bash
# Test config
python3 test_config.py

# Pick coordinates
python3 coordinate_picker.py

# View logs
tail -f edge_server.log

# Check camera devices
ls /dev/video*

# Test server connection
curl http://YOUR_SERVER_IP:5000/health
```

## ✨ Pro Tips

1. **Test with one slot first** before defining all slots
2. **Use coordinate picker** - easier than manual definition
3. **Check logs regularly** - catch issues early
4. **Set appropriate interval** - balance freshness vs. load
5. **Save local copies** during setup for debugging

---

For detailed documentation, see: `README_UPDATERAW.md`
