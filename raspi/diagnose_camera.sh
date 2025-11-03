#!/bin/bash
# Raspberry Pi Camera Diagnostic Script

echo "=================================================="
echo "  Raspberry Pi Camera Diagnostics"
echo "=================================================="
echo ""

# Check camera hardware
echo "🔍 Checking camera hardware..."
vcgencmd get_camera
echo ""

# Check video devices
echo "📹 Video devices:"
ls -l /dev/video* 2>/dev/null || echo "❌ No video devices found"
echo ""

# Check V4L2 driver
echo "🔧 Checking V4L2 driver..."
lsmod | grep bcm2835_v4l2
if [ $? -eq 0 ]; then
    echo "✅ V4L2 driver is loaded"
else
    echo "⚠️  V4L2 driver not loaded"
    echo "   Loading driver..."
    sudo modprobe bcm2835-v4l2
    if [ $? -eq 0 ]; then
        echo "✅ Driver loaded successfully"
    else
        echo "❌ Failed to load driver"
    fi
fi
echo ""

# Check user groups
echo "👤 Checking user permissions..."
groups | grep video > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ User is in 'video' group"
else
    echo "⚠️  User is NOT in 'video' group"
    echo "   Run: sudo usermod -a -G video $USER"
    echo "   Then logout and login again"
fi
echo ""

# Check Python packages
echo "🐍 Checking Python packages..."
python3 -c "import cv2; print(f'✅ OpenCV {cv2.__version__}')" 2>/dev/null || echo "❌ OpenCV not found"
python3 -c "import picamera2; print('✅ picamera2 installed')" 2>/dev/null || echo "⚠️  picamera2 not installed"
python3 -c "import picamera; print('✅ picamera installed')" 2>/dev/null || echo "⚠️  picamera not installed"
echo ""

# Check camera processes
echo "🔍 Checking for processes using camera..."
sudo fuser /dev/video0 2>/dev/null
if [ $? -eq 0 ]; then
    echo "⚠️  Camera is being used by another process"
else
    echo "✅ Camera is free"
fi
echo ""

# Test with v4l2-ctl (if available)
echo "📊 Camera information (v4l2-ctl)..."
if command -v v4l2-ctl &> /dev/null; then
    v4l2-ctl --list-devices
    echo ""
    v4l2-ctl --list-formats-ext
else
    echo "⚠️  v4l2-ctl not installed"
    echo "   Install: sudo apt install v4l-utils"
fi
echo ""

echo "=================================================="
echo "  Diagnostic complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Run test: python3 test_camera_simple.py"
echo "2. If successful, run: python3 edge_server.py"
echo ""
