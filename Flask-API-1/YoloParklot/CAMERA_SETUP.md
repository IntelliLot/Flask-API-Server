# YoloParklot - Live Camera Setup

## 🎉 Setup Complete!

Your YoloParklot parking detection system is now configured and ready to use with live camera feed!

## 🚀 Quick Start - Live Camera

### Option 1: Direct Camera Mode (Recommended)
```bash
# Activate virtual environment
source .venv/bin/activate

# Run with default camera (index 0)
python main_app.py --mode camera

# Run with specific camera index
python main_app.py --mode camera --camera-index 1
```

### Option 2: Interactive Mode
```bash
# Activate virtual environment
source .venv/bin/activate

# Run interactive mode
python main_app.py --interactive

# Then select option 4 for "Live camera processing"
```

## 🎮 Camera Controls

When the camera feed is running, you can use these keyboard shortcuts:

- **'q'** - Quit the application
- **'s'** - Save current frame as image
- **'p'** - Pause/Resume camera feed
- **'r'** - Start/Stop recording to video file

## 📋 Other Available Modes

1. **Video Processing**: Process a video file and save result
   ```bash
   python main_app.py --mode video --input your_video.mp4 --output result.mp4
   ```

2. **Real-time Video**: Play video with real-time detection display
   ```bash
   python main_app.py --mode realtime --input your_video.mp4
   ```

3. **Image Processing**: Process a single image
   ```bash
   python main_app.py --mode image --input your_image.jpg --output result.jpg
   ```

## 🔧 Troubleshooting

### Camera Issues
- **Camera not found**: Try different camera indices (0, 1, 2, etc.)
- **Permission denied**: Ensure your user has camera access permissions
- **Camera busy**: Close other applications using the camera

### Display Issues
- If you see Qt warnings, these are normal and don't affect functionality
- The system will work even without a GUI display server

### Performance Tips
- The system works best with good lighting
- Position camera to get clear view of parking area
- Ensure parking spots are clearly defined in the camera view

## 📁 File Outputs

All processed files are saved to the `output/` directory:
- Saved frames: `camera_frame_YYYYMMDD_HHMMSS.jpg`
- Recorded videos: `camera_recording_YYYYMMDD_HHMMSS.mp4`

## 🎯 Next Steps

1. Position your camera to view the parking area
2. Run the camera mode to see live detection
3. The system will automatically detect vehicles and parking spot occupancy
4. Use saved frames to fine-tune parking spot positions if needed

Happy parking detection! 🚗📹