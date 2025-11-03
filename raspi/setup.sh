#!/bin/bash
# Setup script for Raspberry Pi Edge Server

echo "🚀 Setting up Raspberry Pi Edge Server..."

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p captured_frames

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-opencv libatlas-base-dev

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install -r requirements.txt

# Install Raspberry Pi camera support (if on Raspberry Pi)
if [ -f "/boot/config.txt" ]; then
    echo "🍓 Detected Raspberry Pi - Installing camera support..."
    
    # For Raspberry Pi OS Bullseye and later
    if grep -q "Bullseye" /etc/os-release || grep -q "Bookworm" /etc/os-release; then
        pip3 install picamera2
    else
        # For older versions
        pip3 install picamera
    fi
    
    # Enable camera in raspi-config
    echo "📷 Enabling camera interface..."
    sudo raspi-config nonint do_camera 0
fi

# Copy config example if config doesn't exist
if [ ! -f "config.json" ]; then
    echo "📝 Configuration file not found. Please edit config.json with your settings."
fi

# Make edge_server.py executable
chmod +x edge_server.py

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit config.json with your settings"
echo "2. Update api_endpoint and api_key"
echo "3. Configure your cameras in the 'cameras' section"
echo "4. Run: python3 edge_server.py"
echo ""
echo "To run as a service:"
echo "sudo cp edge_server.service /etc/systemd/system/"
echo "sudo systemctl enable edge_server"
echo "sudo systemctl start edge_server"
