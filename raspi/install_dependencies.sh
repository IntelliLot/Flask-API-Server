#!/bin/bash
# Install system-wide dependencies for Raspberry Pi Edge Server

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  📦 Installing System Dependencies for Edge Server          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

echo "⚠️  Make sure you're NOT in a virtual environment!"
echo "   If you see (venv), type: deactivate"
echo ""
read -p "Continue with installation? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled"
    exit 1
fi

echo ""
echo "1️⃣  Updating package list..."
sudo apt update

echo ""
echo "2️⃣  Installing picamera2 (Pi Camera library)..."
sudo apt install -y python3-picamera2

echo ""
echo "3️⃣  Installing psutil (system monitoring)..."
sudo apt install -y python3-psutil

echo ""
echo "4️⃣  Installing OpenCV (if not already installed)..."
sudo apt install -y python3-opencv

echo ""
echo "5️⃣  Installing Python requests library..."
sudo apt install -y python3-requests || pip3 install requests --break-system-packages

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ Installation Complete!                                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Verifying installations..."
echo ""

# Verify picamera2
if python3 -c "from picamera2 import Picamera2" 2>/dev/null; then
    echo "✅ picamera2 installed"
else
    echo "❌ picamera2 NOT installed"
fi

# Verify psutil
if python3 -c "import psutil" 2>/dev/null; then
    echo "✅ psutil installed"
else
    echo "❌ psutil NOT installed"
fi

# Verify OpenCV
if python3 -c "import cv2" 2>/dev/null; then
    echo "✅ OpenCV installed"
else
    echo "❌ OpenCV NOT installed"
fi

# Verify requests
if python3 -c "import requests" 2>/dev/null; then
    echo "✅ requests installed"
else
    echo "❌ requests NOT installed"
fi

echo ""
echo "Next steps:"
echo "  1. Run: python3 check_camera_libs.py"
echo "  2. Test: python3 test_camera.py"
echo "  3. Start: python3 edge_server.py"
echo ""
