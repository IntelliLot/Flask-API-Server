# 🍓 Raspberry Pi Authentication Guide for UpdateRaw API

## Overview

This guide shows you how to authenticate from your Raspberry Pi and upload images to the `/parking/updateRaw` API endpoint.

---

## 🔐 Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      RASPBERRY PI                                │
│                                                                  │
│  Step 1: Register Account (One-time)                            │
│  POST /auth/register                                             │
│  {username, password, organization_name, location, size}         │
│       │                                                           │
│       ▼                                                           │
│  Step 2: Login & Get Token                                       │
│  POST /auth/login                                                │
│  {username, password}                                            │
│       │                                                           │
│       ▼                                                           │
│  Receive JWT Token                                               │
│  {access_token: "eyJhbGciOiJIUzI1NiIs...", expires_in: 3600}    │
│       │                                                           │
│       ▼                                                           │
│  Step 3: Store Token (in memory or file)                         │
│  token = response['access_token']                                │
│       │                                                           │
│       ▼                                                           │
│  Step 4: Upload Image with Token                                 │
│  POST /parking/updateRaw                                         │
│  Headers: Authorization: Bearer <token>                          │
│  Body: {image, coordinates, camera_id}                           │
│       │                                                           │
│       ▼                                                           │
│  Step 5: Token Refresh (when expired)                            │
│  Re-login to get new token                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📝 Step 1: Register Account (One-Time Setup)

### Register Endpoint
```
POST /auth/register
Content-Type: application/json
```

### Request Body
```json
{
  "username": "raspi_parkinglot_01",
  "password": "SecurePassword123!",
  "organization_name": "My Parking Facility",
  "location": "123 Main St, City, State",
  "size": 50
}
```

### Response (Success)
```json
{
  "success": true,
  "message": "Registration successful",
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "username": "raspi_parkinglot_01",
  "organization_name": "My Parking Facility"
}
```

### Python Code for Registration
```python
import requests
import json

SERVER_URL = "http://your-server-ip:5001"  # Change to your server IP

def register_account():
    """Register a new account (run once)"""
    url = f"{SERVER_URL}/auth/register"
    
    payload = {
        "username": "raspi_parkinglot_01",
        "password": "SecurePassword123!",
        "organization_name": "My Parking Facility",
        "location": "123 Main St, City, State",
        "size": 50
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Registration successful!")
        print(f"User ID: {data['user_id']}")
        print(f"Username: {data['username']}")
        return data
    else:
        print(f"❌ Registration failed: {response.text}")
        return None

# Run once to register
# register_account()
```

---

## 🔑 Step 2: Login & Get JWT Token

### Login Endpoint
```
POST /auth/login
Content-Type: application/json
```

### Request Body
```json
{
  "username": "raspi_parkinglot_01",
  "password": "SecurePassword123!"
}
```

### Response (Success)
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYTFiMmMzZDQtZTVmNi03ODkwLWFiY2QtZWYxMjM0NTY3ODkwIiwidXNlcm5hbWUiOiJyYXNwaV9wYXJraW5nbG90XzAxIiwib3JnYW5pemF0aW9uIjoiTXkgUGFya2luZyBGYWNpbGl0eSIsImV4cCI6MTY5NzQ2MzYwMH0.abc123xyz",
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "username": "raspi_parkinglot_01",
  "organization_name": "My Parking Facility",
  "expires_in": 3600
}
```

### Python Code for Login
```python
import requests

SERVER_URL = "http://your-server-ip:5001"

def login():
    """Login and get JWT token"""
    url = f"{SERVER_URL}/auth/login"
    
    payload = {
        "username": "raspi_parkinglot_01",
        "password": "SecurePassword123!"
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful!")
        print(f"Token: {data['access_token'][:50]}...")
        return data['access_token']
    else:
        print(f"❌ Login failed: {response.text}")
        return None

# Get token
token = login()
```

---

## 📤 Step 3: Upload Image with Authentication

### UpdateRaw Endpoint
```
POST /parking/updateRaw
Authorization: Bearer <your_jwt_token>
Content-Type: multipart/form-data
```

### Python Code for Uploading Image
```python
import requests
import json

SERVER_URL = "http://your-server-ip:5001"

def upload_parking_image(token, image_path, coordinates, camera_id):
    """Upload image to updateRaw API with authentication"""
    url = f"{SERVER_URL}/parking/updateRaw"
    
    # Prepare headers with JWT token
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    # Prepare files and data
    with open(image_path, 'rb') as image_file:
        files = {
            'image': image_file
        }
        
        data = {
            'coordinates': json.dumps(coordinates),
            'camera_id': camera_id
        }
        
        # Send request
        response = requests.post(url, headers=headers, files=files, data=data)
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Upload successful!")
        print(f"Document ID: {result['document_id']}")
        print(f"Occupancy: {result['occupied_slots']}/{result['total_slots']} slots")
        print(f"Occupancy Rate: {result['occupancy_rate']}%")
        return result
    else:
        print(f"❌ Upload failed: {response.text}")
        return None

# Example usage
coordinates = [
    [100, 150, 200, 250],
    [220, 150, 320, 250],
    [340, 150, 440, 250]
]

result = upload_parking_image(
    token=token,
    image_path="/home/pi/parking_image.jpg",
    coordinates=coordinates,
    camera_id="raspi_camera_01"
)
```

---

## 🤖 Complete Raspberry Pi Script

Here's a complete Python script for your Raspberry Pi:

```python
#!/usr/bin/env python3
"""
Raspberry Pi Parking Detection Client
Authenticates and uploads images to updateRaw API
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
SERVER_URL = "http://your-server-ip:5001"  # Change to your server IP
USERNAME = "raspi_parkinglot_01"
PASSWORD = "SecurePassword123!"
CAMERA_ID = "raspi_camera_01"

# Parking slot coordinates (customize for your parking lot)
PARKING_COORDINATES = [
    [100, 150, 200, 250],
    [220, 150, 320, 250],
    [340, 150, 440, 250],
    [460, 150, 560, 250],
    # Add more coordinates as needed
]

class ParkingClient:
    def __init__(self, server_url, username, password):
        self.server_url = server_url
        self.username = username
        self.password = password
        self.token = None
        self.token_expiry = 0
    
    def login(self):
        """Login and get JWT token"""
        url = f"{self.server_url}/auth/login"
        
        payload = {
            "username": self.username,
            "password": self.password
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                self.token_expiry = time.time() + data.get('expires_in', 3600)
                print(f"✅ [{datetime.now()}] Login successful")
                return True
            else:
                print(f"❌ [{datetime.now()}] Login failed: {response.text}")
                return False
        except Exception as e:
            print(f"❌ [{datetime.now()}] Login error: {e}")
            return False
    
    def is_token_valid(self):
        """Check if token is still valid"""
        if not self.token:
            return False
        # Refresh token 5 minutes before expiry
        return time.time() < (self.token_expiry - 300)
    
    def ensure_authenticated(self):
        """Ensure we have a valid token"""
        if not self.is_token_valid():
            print(f"⚠️ [{datetime.now()}] Token expired or missing, logging in...")
            return self.login()
        return True
    
    def upload_image(self, image_path, coordinates, camera_id):
        """Upload image to updateRaw API"""
        # Ensure we're authenticated
        if not self.ensure_authenticated():
            return None
        
        url = f"{self.server_url}/parking/updateRaw"
        
        headers = {
            'Authorization': f'Bearer {self.token}'
        }
        
        try:
            with open(image_path, 'rb') as image_file:
                files = {
                    'image': image_file
                }
                
                data = {
                    'coordinates': json.dumps(coordinates),
                    'camera_id': camera_id
                }
                
                response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                print(f"✅ [{datetime.now()}] Upload successful!")
                print(f"   Document ID: {result['document_id']}")
                print(f"   Occupancy: {result['occupied_slots']}/{result['total_slots']} slots ({result['occupancy_rate']}%)")
                print(f"   Processing time: {result['processing_time_ms']}ms")
                return result
            elif response.status_code == 401:
                # Token expired, try to re-login
                print(f"⚠️ [{datetime.now()}] Token expired, re-authenticating...")
                self.token = None
                return self.upload_image(image_path, coordinates, camera_id)
            else:
                print(f"❌ [{datetime.now()}] Upload failed: {response.text}")
                return None
        except Exception as e:
            print(f"❌ [{datetime.now()}] Upload error: {e}")
            return None
    
    def capture_and_upload(self, camera_id, coordinates):
        """Capture image from Pi Camera and upload"""
        try:
            from picamera import PiCamera
            
            # Capture image
            image_path = "/tmp/parking_capture.jpg"
            camera = PiCamera()
            camera.resolution = (1920, 1080)
            time.sleep(2)  # Camera warm-up
            camera.capture(image_path)
            camera.close()
            
            print(f"📸 [{datetime.now()}] Image captured: {image_path}")
            
            # Upload image
            result = self.upload_image(image_path, coordinates, camera_id)
            
            # Clean up
            if os.path.exists(image_path):
                os.remove(image_path)
            
            return result
        except ImportError:
            print("❌ picamera module not installed. Install with: sudo apt-get install python3-picamera")
            return None
        except Exception as e:
            print(f"❌ [{datetime.now()}] Capture error: {e}")
            return None


def main():
    """Main function - runs continuously"""
    print("🚀 Raspberry Pi Parking Detection Client")
    print(f"Server: {SERVER_URL}")
    print(f"Username: {USERNAME}")
    print(f"Camera ID: {CAMERA_ID}")
    print("-" * 60)
    
    # Initialize client
    client = ParkingClient(SERVER_URL, USERNAME, PASSWORD)
    
    # Initial login
    if not client.login():
        print("❌ Initial login failed. Exiting.")
        return
    
    # Main loop - capture and upload every 60 seconds
    interval = 60  # seconds
    
    while True:
        try:
            print(f"\n📸 [{datetime.now()}] Starting capture and upload...")
            
            # Option 1: Use PiCamera (if available)
            # result = client.capture_and_upload(CAMERA_ID, PARKING_COORDINATES)
            
            # Option 2: Upload existing image file
            image_path = "/home/pi/parking_image.jpg"  # Update with your image path
            if os.path.exists(image_path):
                result = client.upload_image(image_path, PARKING_COORDINATES, CAMERA_ID)
            else:
                print(f"❌ Image not found: {image_path}")
            
            # Wait before next upload
            print(f"⏳ Waiting {interval} seconds until next upload...")
            time.sleep(interval)
            
        except KeyboardInterrupt:
            print("\n⚠️ Interrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            time.sleep(interval)


if __name__ == "__main__":
    main()
```

---

## 🎯 Quick Start Guide

### 1. Install Dependencies on Raspberry Pi
```bash
sudo apt-get update
sudo apt-get install python3-pip python3-picamera
pip3 install requests
```

### 2. Create the Script
```bash
nano raspi_parking_client.py
# Paste the complete script above
chmod +x raspi_parking_client.py
```

### 3. Configure the Script
Edit the configuration section:
```python
SERVER_URL = "http://192.168.1.100:5001"  # Your server IP
USERNAME = "raspi_parkinglot_01"
PASSWORD = "SecurePassword123!"
CAMERA_ID = "raspi_camera_01"
```

### 4. Register Account (First Time Only)
```python
python3 -c "
import requests
response = requests.post('http://192.168.1.100:5001/auth/register', json={
    'username': 'raspi_parkinglot_01',
    'password': 'SecurePassword123!',
    'organization_name': 'My Parking Facility',
    'location': 'Raspberry Pi Location',
    'size': 50
})
print(response.json())
"
```

### 5. Run the Client
```bash
python3 raspi_parking_client.py
```

### 6. Run as Background Service (Optional)
```bash
# Create systemd service
sudo nano /etc/systemd/system/parking-client.service
```

Add:
```ini
[Unit]
Description=Parking Detection Client
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/bin/python3 /home/pi/raspi_parking_client.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable parking-client
sudo systemctl start parking-client
sudo systemctl status parking-client
```

---

## 🔄 Token Management

### Token Expiry
- JWT tokens expire after **1 hour** (3600 seconds)
- The client script automatically re-authenticates before expiry
- If upload fails with 401, the script will re-login automatically

### Storing Credentials Securely
Instead of hardcoding credentials, use environment variables:

```python
import os

USERNAME = os.getenv('PARKING_USERNAME', 'default_username')
PASSWORD = os.getenv('PARKING_PASSWORD', 'default_password')
```

Set environment variables:
```bash
export PARKING_USERNAME="raspi_parkinglot_01"
export PARKING_PASSWORD="SecurePassword123!"
```

Or create a `.env` file:
```bash
# .env
PARKING_USERNAME=raspi_parkinglot_01
PARKING_PASSWORD=SecurePassword123!
PARKING_SERVER_URL=http://192.168.1.100:5001
PARKING_CAMERA_ID=raspi_camera_01
```

Load with python-dotenv:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 🐛 Troubleshooting

### Problem: "Connection refused"
```
❌ Login error: Connection refused
```
**Solution:**
- Check server is running: `curl http://your-server-ip:5001/health`
- Check firewall: `sudo ufw allow 5001`
- Check server IP address

### Problem: "Invalid username or password"
```
❌ Login failed: Invalid username or password
```
**Solution:**
- Verify credentials are correct
- Register account first if not done
- Check MongoDB connection on server

### Problem: "Token expired"
```
❌ Upload failed: Token expired or invalid
```
**Solution:**
- The script handles this automatically
- If persists, check system time: `date`
- Sync time: `sudo ntpdate -s time.nist.gov`

### Problem: "Image too large"
```
❌ Upload failed: Payload too large
```
**Solution:**
- Resize image before upload:
```python
from PIL import Image
img = Image.open('image.jpg')
img.thumbnail((1920, 1080))
img.save('resized.jpg', quality=85)
```

---

## 📊 Testing Authentication

### Test Login
```bash
curl -X POST http://your-server-ip:5001/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "raspi_parkinglot_01",
    "password": "SecurePassword123!"
  }'
```

### Test Upload with Token
```bash
TOKEN="your_jwt_token_here"

curl -X POST http://your-server-ip:5001/parking/updateRaw \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@parking_image.jpg" \
  -F 'coordinates=[[100,150,200,250]]' \
  -F "camera_id=raspi_camera_01"
```

---

## 🔒 Security Best Practices

1. **Use HTTPS in Production**
   ```python
   SERVER_URL = "https://your-domain.com:5001"
   ```

2. **Strong Passwords**
   - Minimum 12 characters
   - Mix of uppercase, lowercase, numbers, symbols

3. **Secure Credential Storage**
   - Use environment variables
   - Don't commit credentials to Git
   - Use `.env` file and add to `.gitignore`

4. **Network Security**
   - Use VPN or private network
   - Enable firewall rules
   - Restrict API access by IP if possible

5. **Regular Token Rotation**
   - Implement token refresh endpoint (future enhancement)
   - Change passwords periodically

---

## 📚 Related Documentation

- [UPDATERAW_API_EXPLAINED.md](UPDATERAW_API_EXPLAINED.md) - Complete API documentation
- [README.md](README.md) - Project overview
- [QUICK_START.md](QUICK_START.md) - Quick start guide

---

## 🎯 Summary

**To authenticate from Raspberry Pi:**

1. ✅ Register account once: `POST /auth/register`
2. ✅ Login to get JWT token: `POST /auth/login`
3. ✅ Add token to headers: `Authorization: Bearer <token>`
4. ✅ Upload images: `POST /parking/updateRaw`
5. ✅ Re-login when token expires (1 hour)

The provided script handles all of this automatically! 🚀
