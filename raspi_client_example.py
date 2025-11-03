#!/usr/bin/env python3
"""
Simple Raspberry Pi Client for UpdateRaw API
Usage: python3 raspi_client_example.py
"""

import requests
import json
import time
from datetime import datetime

# ============================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================
SERVER_URL = "http://192.168.1.100:5001"  # Change to your server IP/domain
USERNAME = "raspi_parkinglot_01"
PASSWORD = "SecurePassword123!"
CAMERA_ID = "raspi_camera_01"
NODE_ID = "node_raspberry_pi_01"  # Unique identifier for this device/node
IMAGE_PATH = "/home/pi/parking_image.jpg"  # Path to your parking lot image

# Define your parking slot coordinates [x1, y1, x2, y2]
PARKING_COORDINATES = [
    [100, 150, 200, 250],
    [220, 150, 320, 250],
    [340, 150, 440, 250],
    # Add more parking slot coordinates here
]
# ============================================


class ParkingAPIClient:
    """Simple client for parking detection API"""

    def __init__(self, server_url, username, password):
        self.server_url = server_url
        self.username = username
        self.password = password
        self.token = None
        self.token_expiry = 0

    def login(self):
        """Login and get JWT token"""
        url = f"{self.server_url}/auth/login"
        payload = {"username": self.username, "password": self.password}

        try:
            print(f"[{datetime.now()}] Logging in as {self.username}...")
            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                self.token_expiry = time.time() + data.get('expires_in', 3600)
                print(
                    f"✅ Login successful! Token expires in {data.get('expires_in', 3600)}s")
                return True
            else:
                print(
                    f"❌ Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def is_token_valid(self):
        """Check if token is still valid (with 5min buffer)"""
        if not self.token:
            return False
        return time.time() < (self.token_expiry - 300)

    def upload_image(self, image_path, coordinates, camera_id, node_id=None):
        """Upload image to updateRaw API"""
        # Ensure we have a valid token
        if not self.is_token_valid():
            print("⚠️ Token expired or missing, re-authenticating...")
            if not self.login():
                return None

        url = f"{self.server_url}/parking/updateRaw"
        headers = {'Authorization': f'Bearer {self.token}'}

        try:
            print(f"[{datetime.now()}] Uploading {image_path}...")

            with open(image_path, 'rb') as img_file:
                files = {'image': img_file}
                data = {
                    'coordinates': json.dumps(coordinates),
                    'camera_id': camera_id,
                    'node_id': node_id or camera_id  # Include node_id
                }

                response = requests.post(
                    url, headers=headers, files=files, data=data, timeout=30)

            if response.status_code == 201:
                result = response.json()
                print(f"✅ Upload successful!")
                print(f"   Document ID: {result['document_id']}")
                print(f"   Total Slots: {result['total_slots']}")
                print(
                    f"   Occupied: {result['occupied_slots']} ({result['occupancy_rate']}%)")
                print(f"   Empty: {result['empty_slots']}")
                print(f"   Processing time: {result['processing_time_ms']}ms")

                # Display GCS storage info if available
                gcs = result.get('gcs_storage', {})
                if gcs.get('enabled'):
                    print(f"   📦 Cloud Storage:")
                    if gcs.get('raw_image'):
                        print(f"      Raw Image: {gcs['raw_image']['path']}")
                    if gcs.get('annotated_image'):
                        print(
                            f"      Annotated: {gcs['annotated_image']['path']}")

                return result
            elif response.status_code == 401:
                # Token expired, retry once
                print("⚠️ Token invalid, re-authenticating...")
                self.token = None
                if self.login():
                    return self.upload_image(image_path, coordinates, camera_id, node_id)
                return None
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None

        except FileNotFoundError:
            print(f"❌ Image file not found: {image_path}")
            return None
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return None


def main():
    """Main function"""
    print("=" * 70)
    print("🍓 Raspberry Pi Parking Detection Client")
    print("=" * 70)
    print(f"Server: {SERVER_URL}")
    print(f"Username: {USERNAME}")
    print(f"Camera ID: {CAMERA_ID}")
    print(f"Node ID: {NODE_ID}")
    print(f"Image: {IMAGE_PATH}")
    print(f"Parking Slots: {len(PARKING_COORDINATES)}")
    print("=" * 70)

    # Initialize client
    client = ParkingAPIClient(SERVER_URL, USERNAME, PASSWORD)

    # Login
    if not client.login():
        print("\n❌ Login failed. Please check:")
        print("   1. Server URL is correct and accessible")
        print("   2. Username and password are correct")
        print("   3. Account is registered (see RASPBERRY_PI_AUTHENTICATION_GUIDE.md)")
        return

    # Upload image
    print("\n" + "=" * 70)
    result = client.upload_image(
        IMAGE_PATH, PARKING_COORDINATES, CAMERA_ID, NODE_ID)
    print("=" * 70)

    if result:
        print("\n✅ Process completed successfully!")
        print(f"\nYou can view the results in MongoDB or query via API:")
        print(
            f"   GET {SERVER_URL}/parking/data/{result.get('user_id', 'USER_ID')}")
    else:
        print("\n❌ Upload failed. Check error messages above.")


if __name__ == "__main__":
    main()
