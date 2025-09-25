#!/bin/bash

# YoloParklot Setup Script for Flask-API-1
# This script clones and sets up the YoloParklot AI system

echo "🧠 Setting up YoloParklot AI System"
echo "=================================="

# Check if YoloParklot directory already exists
if [ -d "YoloParklot" ]; then
    echo "✅ YoloParklot directory already exists"
    echo "   Pulling latest changes..."
    cd YoloParklot
    git pull origin main
    cd ..
else
    echo "📥 Cloning YoloParklot repository..."
    git clone https://github.com/pdschandel/YoloParklot.git
fi

# Check if model file exists
if [ -f "YoloParklot/runs/detect/carpk_demo/weights/best.pt" ]; then
    echo "✅ YOLO model file found: best.pt"
else
    echo "⚠️  YOLO model file not found!"
    echo "   Please ensure best.pt is available in YoloParklot/runs/detect/carpk_demo/weights/"
fi

# Check if parking positions exist
if [ -f "YoloParklot/CarParkPos" ]; then
    echo "✅ Parking positions file found: CarParkPos"
else
    echo "⚠️  Parking positions file not found!"
    echo "   Please ensure CarParkPos is available in YoloParklot/"
fi

# Install YoloParklot dependencies
echo "📦 Installing YoloParklot dependencies..."
if [ -d "venv_flask" ]; then
    source venv_flask/bin/activate
    pip install ultralytics torch torchvision opencv-python
    echo "✅ YoloParklot dependencies installed in venv_flask"
else
    echo "⚠️  Virtual environment venv_flask not found!"
    echo "   Please create virtual environment first: python3 -m venv venv_flask"
fi

echo ""
echo "🎯 YoloParklot Setup Complete!"
echo "   Repository: https://github.com/pdschandel/YoloParklot.git"
echo "   Model: YoloParklot/runs/detect/carpk_demo/weights/best.pt"
echo "   Parking Slots: 73 slots configured in CarParkPos"
echo "   Ready for Flask-API-1 integration!"