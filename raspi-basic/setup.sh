#!/bin/bash

echo "============================================================"
echo "Raspberry Pi Edge Server - Quick Setup"
echo "============================================================"
echo ""

# Check if config.json exists
if [ ! -f "config.json" ]; then
    echo "⚠️  config.json not found"
    
    if [ -f "config_picamera.json" ]; then
        echo "📋 Copying config_picamera.json to config.json"
        cp config_picamera.json config.json
        echo "✅ config.json created from template"
    else
        echo "❌ No configuration template found"
        echo "   Please create config.json manually"
        exit 1
    fi
else
    echo "✅ config.json exists"
fi

echo ""
echo "============================================================"
echo "Installing Python dependencies..."
echo "============================================================"
echo ""

# Install Python dependencies
pip3 install -r requirements.txt

echo ""
echo "============================================================"
echo "Configuration Setup"
echo "============================================================"
echo ""
echo "Please edit config.json and update the following fields:"
echo ""
echo "  1. api_endpoint - Your server URL"
echo "     Example: http://192.168.1.100:5000/parking/updateRaw"
echo ""
echo "  2. api_key - Your authentication token"
echo "     Get this from your dashboard or by logging in"
echo ""
echo "  3. camera_id - Unique identifier for this camera"
echo "     Example: parking_lot_entrance"
echo ""
echo "  4. coordinates - Parking slot coordinates"
echo "     Format: [[x1,y1,x2,y2], [x1,y1,x2,y2], ...]"
echo "     Use the coordinate picker tool or define manually"
echo ""
echo "  5. camera_type - Type of camera"
echo "     Options: 'picamera', 'usb', or 'rtsp'"
echo ""

read -p "Press Enter to open config.json for editing... " 

# Try to open with common editors
if command -v nano &> /dev/null; then
    nano config.json
elif command -v vim &> /dev/null; then
    vim config.json
elif command -v vi &> /dev/null; then
    vi config.json
else
    echo "No text editor found. Please edit config.json manually."
fi

echo ""
echo "============================================================"
echo "Testing Configuration"
echo "============================================================"
echo ""

# Test configuration
python3 test_config.py

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "Setup Complete!"
    echo "============================================================"
    echo ""
    echo "To start the edge server:"
    echo "  python3 edge_server.py"
    echo ""
    echo "To run in background:"
    echo "  nohup python3 edge_server.py > edge_server.log 2>&1 &"
    echo ""
    echo "To view logs:"
    echo "  tail -f edge_server.log"
    echo ""
else
    echo ""
    echo "============================================================"
    echo "Configuration Test Failed"
    echo "============================================================"
    echo ""
    echo "Please fix the errors above and run: python3 test_config.py"
    echo ""
fi
