# 🚀 Raspberry Pi Deployment Guide

This guide will help you deploy the edge server to your Raspberry Pi.

## Prerequisites

1. **Raspberry Pi Setup:**
   - Raspberry Pi OS installed
   - SSH enabled
   - Network connection (WiFi or Ethernet)
   - Know the IP address of your Raspberry Pi

2. **On Your PC:**
   - SSH client installed (comes with Linux/Mac, use PuTTY for Windows)
   - Raspberry Pi accessible on the network

## Method 1: Automated Deployment (Recommended)

### Step 1: Find Your Raspberry Pi's IP Address

On the Raspberry Pi, run:
```bash
hostname -I
```

Or from your PC:
```bash
# Scan network for Raspberry Pi
nmap -sn 192.168.1.0/24 | grep -B 2 "Raspberry Pi"

# Or use arp-scan
sudo arp-scan --localnet | grep -i raspberry
```

### Step 2: Enable SSH on Raspberry Pi (if not already enabled)

On Raspberry Pi:
```bash
sudo raspi-config
# Navigate to: Interface Options -> SSH -> Enable
```

### Step 3: Run Deployment Script

```bash
cd /home/anirudh-sharma/Desktop/Major\ Project/YoloParklot
./deploy_to_raspi.sh
```

The script will:
- ✅ Test SSH connection
- ✅ Create directories on Raspberry Pi
- ✅ Copy all raspi files
- ✅ Set correct permissions
- ✅ Create log and capture directories

## Method 2: Manual Deployment with SCP

### Using Command Line:

```bash
# Set variables
RASPI_USER="pi"
RASPI_HOST="192.168.1.xxx"  # Your Raspberry Pi IP
RASPI_PATH="~/YoloParklot"

# Create directory on Raspberry Pi
ssh ${RASPI_USER}@${RASPI_HOST} "mkdir -p ${RASPI_PATH}"

# Copy raspi folder
scp -r ./raspi ${RASPI_USER}@${RASPI_HOST}:${RASPI_PATH}/

# Set permissions
ssh ${RASPI_USER}@${RASPI_HOST} "cd ${RASPI_PATH}/raspi && chmod +x *.py *.sh"
```

### Using FileZilla (GUI):

1. **Install FileZilla** (if not installed)
   ```bash
   sudo apt-get install filezilla
   ```

2. **Connect to Raspberry Pi:**
   - Host: `sftp://192.168.1.xxx` (your Raspberry Pi IP)
   - Username: `pi` (or your username)
   - Password: your Raspberry Pi password
   - Port: `22`

3. **Transfer Files:**
   - Navigate to local: `/home/anirudh-sharma/Desktop/Major Project/YoloParklot/raspi`
   - Navigate to remote: `/home/pi/YoloParklot`
   - Drag and drop the `raspi` folder

## Method 3: Using rsync (Best for Updates)

```bash
# Sync raspi folder to Raspberry Pi
rsync -avz --progress ./raspi/ pi@192.168.1.xxx:~/YoloParklot/raspi/

# With specific port
rsync -avz -e "ssh -p 22" --progress ./raspi/ pi@192.168.1.xxx:~/YoloParklot/raspi/
```

## Post-Deployment Setup

### 1. SSH into Raspberry Pi

```bash
ssh pi@192.168.1.xxx
# Or with custom port
ssh -p 22 pi@192.168.1.xxx
```

### 2. Navigate to raspi folder

```bash
cd ~/YoloParklot/raspi
ls -la
```

### 3. Configure the Edge Server

```bash
nano config.json
```

Update the following:
- `api_endpoint`: Your server's IP and port (e.g., `http://192.168.1.100:5001/parking/updateRaw`)
- `api_key`: Your API key from the dashboard
- `device_id`: Unique ID for this edge device
- `cameras`: Enable and configure your cameras

### 4. Install Dependencies

```bash
./setup.sh
```

Or manually:
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-opencv libatlas-base-dev
pip3 install -r requirements.txt

# For Raspberry Pi Camera
pip3 install picamera2  # Bullseye/Bookworm
# or
pip3 install picamera   # Older versions
```

### 5. Test Camera Setup

```bash
python3 test_camera.py
```

This will capture test images from all enabled cameras.

### 6. Test Edge Server

```bash
python3 edge_server.py
```

Monitor the output for successful captures and uploads.

### 7. Setup as System Service (Optional)

For automatic startup on boot:

```bash
# Edit service file paths if needed
sudo nano edge_server.service

# Copy to systemd
sudo cp edge_server.service /etc/systemd/system/

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable edge_server
sudo systemctl start edge_server

# Check status
sudo systemctl status edge_server

# View logs
sudo journalctl -u edge_server -f
```

## Troubleshooting

### SSH Connection Issues

**Permission denied:**
```bash
# Generate SSH key pair (if not exists)
ssh-keygen -t rsa -b 4096

# Copy public key to Raspberry Pi
ssh-copy-id pi@192.168.1.xxx

# Or manually
cat ~/.ssh/id_rsa.pub | ssh pi@192.168.1.xxx "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

**Connection timeout:**
- Verify IP address: `ping 192.168.1.xxx`
- Check if SSH is enabled on Raspberry Pi
- Check firewall settings
- Ensure both devices are on the same network

### Camera Not Working

**Raspberry Pi Camera:**
```bash
# Enable camera
sudo raspi-config
# Interface Options -> Camera -> Enable

# Test camera
raspistill -o test.jpg

# Check camera status
vcgencmd get_camera
```

**USB Camera:**
```bash
# List video devices
ls -l /dev/video*

# Test with OpenCV
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAILED')"
```

### Upload Failures

1. **Check server connectivity:**
   ```bash
   curl http://YOUR_SERVER_IP:5001/health
   ```

2. **Verify API key in config.json**

3. **Check logs:**
   ```bash
   tail -f logs/edge_server.log
   ```

### High Resource Usage

- Lower camera resolution
- Increase capture interval
- Disable local copy saving
- Close other applications

## Environment Variables Method

You can also set environment variables for easier deployment:

```bash
# In ~/.bashrc or ~/.zshrc
export RASPI_USER="pi"
export RASPI_HOST="192.168.1.xxx"
export RASPI_PORT="22"
export RASPI_PATH="~/YoloParklot"

# Then simply run
./deploy_to_raspi.sh
```

## Security Recommendations

1. **Change default password:**
   ```bash
   passwd
   ```

2. **Use SSH keys instead of passwords**

3. **Configure firewall:**
   ```bash
   sudo ufw enable
   sudo ufw allow 22/tcp
   ```

4. **Keep API key secure in config.json**

5. **Use HTTPS for api_endpoint in production**

## Quick Command Reference

```bash
# Deploy
./deploy_to_raspi.sh

# SSH into Pi
ssh pi@RASPI_IP

# View logs
sudo journalctl -u edge_server -f

# Restart service
sudo systemctl restart edge_server

# Update deployment (after changes)
rsync -avz ./raspi/ pi@RASPI_IP:~/YoloParklot/raspi/
```

## Need Help?

Check:
1. Edge server logs: `~/YoloParklot/raspi/logs/edge_server.log`
2. System logs: `sudo journalctl -u edge_server`
3. Camera test: `python3 test_camera.py`
4. Network connectivity: `ping YOUR_SERVER_IP`
