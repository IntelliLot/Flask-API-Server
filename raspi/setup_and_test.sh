#!/bin/bash
# Complete setup and test script for Raspberry Pi

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     🚀 Raspberry Pi Camera Setup & Test                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Step 1: Check Python version
echo "1️⃣  Checking Python version..."
PYTHON_VERSION=$(python3 --version)
echo "   $PYTHON_VERSION"
echo ""

# Step 2: Check for picamera2
echo "2️⃣  Checking for picamera2..."
if python3 -c "from picamera2 import Picamera2" 2>/dev/null; then
    echo "   ✅ picamera2 is installed"
else
    echo "   ❌ picamera2 NOT found"
    echo ""
    echo "   Installing picamera2..."
    sudo apt update
    sudo apt install -y python3-picamera2
    
    if python3 -c "from picamera2 import Picamera2" 2>/dev/null; then
        echo "   ✅ picamera2 installed successfully"
    else
        echo "   ❌ Failed to install picamera2"
        echo "   Please check your Raspberry Pi OS version (needs Bullseye or later)"
        exit 1
    fi
fi
echo ""

# Step 3: Check camera hardware
echo "3️⃣  Checking camera hardware..."
if command -v vcgencmd &> /dev/null; then
    vcgencmd get_camera
else
    echo "   ⚠️  vcgencmd not available (not a Raspberry Pi?)"
fi
echo ""

# Step 4: Check video devices
echo "4️⃣  Checking video devices..."
if ls /dev/video* 2>/dev/null; then
    ls -l /dev/video*
else
    echo "   ⚠️  No /dev/video* devices found"
    echo "   You may need to enable legacy camera support"
fi
echo ""

# Step 5: Clean Python cache
echo "5️⃣  Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
echo "   ✅ Cache cleaned"
echo ""

# Step 6: Run library check
echo "6️⃣  Running detailed library check..."
python3 check_camera_libs.py
echo ""

# Step 7: Offer to run camera test
echo "7️⃣  Ready to test camera!"
echo ""
read -p "   Run camera test now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "   🧪 Running camera test..."
    echo "   ──────────────────────────────────────────────────────────"
    python3 test_camera.py
    TEST_RESULT=$?
    echo ""
    
    if [ $TEST_RESULT -eq 0 ]; then
        echo "   ✅ Camera test PASSED!"
        echo ""
        read -p "   Start edge server? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo ""
            echo "   🚀 Starting edge server..."
            echo "   ──────────────────────────────────────────────────────────"
            python3 edge_server.py
        fi
    else
        echo "   ❌ Camera test FAILED"
        echo ""
        echo "   Troubleshooting:"
        echo "   - Check camera connection"
        echo "   - Enable camera: sudo raspi-config → Interface → Camera"
        echo "   - Check: vcgencmd get_camera"
        echo "   - Reboot if needed: sudo reboot"
    fi
else
    echo ""
    echo "   To test manually, run:"
    echo "     python3 test_camera.py"
    echo ""
    echo "   To start edge server:"
    echo "     python3 edge_server.py"
fi

echo ""
echo "╚══════════════════════════════════════════════════════════════╝"
