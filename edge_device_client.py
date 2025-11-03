#!/usr/bin/env python3
"""
Edge Device Client Example - Using API Key Authentication

This example shows how to send parking data from your edge device
(Raspberry Pi, NVIDIA Jetson, etc.) to the IntelliLot cloud API
using the API key generated from your dashboard.

Setup:
1. Visit http://your-server.com/
2. Create an account
3. Login to dashboard
4. Generate an API key
5. Copy the API key and paste below
6. Run this script: python edge_device_client.py
"""

import requests
import json
import time
from datetime import datetime
from typing import List, Tuple

# ============================================================================
# CONFIGURATION - Update these values
# ============================================================================

API_URL = "http://localhost:5001"  # Your server URL
API_KEY = "YOUR_API_KEY_FROM_DASHBOARD"  # 64-char key from dashboard
CAMERA_ID = "entrance_camera_01"  # Unique identifier for this camera

# Your parking slot coordinates (replace with actual coordinates)
PARKING_COORDINATES = [
    [100, 150, 200, 250],   # Slot 1: [x1, y1, x2, y2]
    [220, 150, 320, 250],   # Slot 2
    [340, 150, 440, 250],   # Slot 3
    [100, 270, 200, 370],   # Slot 4
    [220, 270, 320, 370],   # Slot 5
    # Add more coordinates...
]

UPDATE_INTERVAL = 30  # Seconds between updates

# ============================================================================
# API Client Class
# ============================================================================


class ParkingAPIClient:
    """Client for sending parking data to IntelliLot cloud API"""

    def __init__(self, api_url: str, api_key: str, camera_id: str):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.camera_id = camera_id
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })

    def send_update(self, coordinates: List[List[int]],
                    occupied_count: int, total_count: int,
                    slots_details: List[dict] = None) -> dict:
        """
        Send parking occupancy update to cloud API

        Args:
            coordinates: List of parking slot coordinates [[x1,y1,x2,y2], ...]
            occupied_count: Number of occupied parking slots
            total_count: Total number of parking slots
            slots_details: Optional detailed info for each slot

        Returns:
            API response as dictionary
        """
        url = f"{self.api_url}/parking/update"

        empty_count = total_count - occupied_count
        occupancy_rate = (occupied_count / total_count *
                          100) if total_count > 0 else 0

        payload = {
            'camera_id': self.camera_id,
            'coordinates': coordinates,
            'total_slots': total_count,
            'occupied_slots': occupied_count,
            'empty_slots': empty_count,
            'occupancy_rate': round(occupancy_rate, 2),
            'timestamp': datetime.utcnow().isoformat()
        }

        if slots_details:
            payload['slots_details'] = slots_details

        try:
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()

            result = response.json()
            print(
                f"✅ Data sent successfully at {datetime.now().strftime('%H:%M:%S')}")
            print(
                f"   Occupancy: {occupied_count}/{total_count} ({occupancy_rate:.1f}%)")

            return result

        except requests.exceptions.RequestException as e:
            print(f"❌ Error sending data: {e}")
            return {'error': str(e)}

    def send_raw_image(self, image_path: str, coordinates: List[List[int]]) -> dict:
        """
        Send raw image for server-side processing

        Args:
            image_path: Path to parking lot image
            coordinates: Parking slot coordinates

        Returns:
            API response with detection results
        """
        url = f"{self.api_url}/parking/updateRaw"

        try:
            with open(image_path, 'rb') as f:
                files = {'image': f}
                data = {
                    'coordinates': json.dumps(coordinates),
                    'camera_id': self.camera_id
                }
                headers = {'Authorization': f'Bearer {self.api_key}'}

                response = requests.post(url, files=files, data=data,
                                         headers=headers, timeout=30)
                response.raise_for_status()

                result = response.json()
                print(f"✅ Image processed successfully")
                print(
                    f"   Detected: {result.get('occupied_slots')}/{result.get('total_slots')} occupied")

                return result

        except Exception as e:
            print(f"❌ Error sending image: {e}")
            return {'error': str(e)}

    def test_connection(self) -> bool:
        """Test API connection and authentication"""
        url = f"{self.api_url}/health"

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            print("✅ Server connection successful")
            return True
        except:
            print("❌ Cannot connect to server")
            return False


# ============================================================================
# Mock Detection (Replace with real YOLO detection)
# ============================================================================

def detect_parking_occupancy(coordinates: List[List[int]]) -> Tuple[int, List[dict]]:
    """
    Mock detection function - Replace with your actual YOLO detection

    In production, this would:
    1. Capture frame from camera
    2. Run YOLOv8 vehicle detection
    3. Check which parking slots contain vehicles
    4. Return occupied count and slot details

    Args:
        coordinates: Parking slot coordinates

    Returns:
        (occupied_count, slots_details)
    """
    import random

    # Simulate detection - replace with actual YOLO
    occupied_count = random.randint(0, len(coordinates))

    slots_details = []
    occupied_indices = random.sample(range(len(coordinates)), occupied_count)

    for i, coord in enumerate(coordinates):
        slots_details.append({
            'slot_id': i,
            'coordinates': coord,
            'is_occupied': i in occupied_indices
        })

    return occupied_count, slots_details


# ============================================================================
# Main Application
# ============================================================================

def main():
    """Main application loop"""

    print("="*70)
    print("🚗 IntelliLot Edge Device Client")
    print("="*70)
    print(f"Server: {API_URL}")
    print(f"Camera: {CAMERA_ID}")
    print(f"Parking Slots: {len(PARKING_COORDINATES)}")
    print(f"Update Interval: {UPDATE_INTERVAL}s")
    print("="*70)

    # Validate configuration
    if API_KEY == "YOUR_API_KEY_FROM_DASHBOARD":
        print("\n⚠️  ERROR: Please update API_KEY in the configuration!")
        print("Steps:")
        print("1. Visit your dashboard at http://your-server.com/dashboard")
        print("2. Generate an API key")
        print("3. Copy and paste it into this file")
        return

    # Initialize client
    client = ParkingAPIClient(API_URL, API_KEY, CAMERA_ID)

    # Test connection
    print("\n🔍 Testing server connection...")
    if not client.test_connection():
        print("⚠️  Cannot reach server. Check API_URL and network connection.")
        return

    print("\n✅ Ready to send parking data!")
    print("Press Ctrl+C to stop\n")

    # Main loop
    try:
        iteration = 0
        while True:
            iteration += 1
            print(
                f"\n[Iteration {iteration}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # Detect parking occupancy
            # TODO: Replace with your actual YOLO detection
            occupied_count, slots_details = detect_parking_occupancy(
                PARKING_COORDINATES)

            # Send to cloud API
            result = client.send_update(
                coordinates=PARKING_COORDINATES,
                occupied_count=occupied_count,
                total_count=len(PARKING_COORDINATES),
                slots_details=slots_details
            )

            if 'document_id' in result:
                print(f"   Document ID: {result['document_id']}")

            # Wait before next update
            print(f"   Waiting {UPDATE_INTERVAL}s...")
            time.sleep(UPDATE_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
        print("Total iterations:", iteration)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise


# ============================================================================
# Example: Send Single Image for Processing
# ============================================================================

def send_single_image_example():
    """Example of sending a single image for server-side processing"""

    client = ParkingAPIClient(API_URL, API_KEY, CAMERA_ID)

    # Send image to server for YOLO processing
    result = client.send_raw_image(
        image_path="parking_lot.jpg",  # Your image file
        coordinates=PARKING_COORDINATES
    )

    if result.get('success'):
        print(f"Occupancy Rate: {result['occupancy_rate']}%")
        print(f"SVG visualization saved in response")


# ============================================================================
# Production Integration Example with OpenCV
# ============================================================================

def production_example_with_camera():
    """
    Example of integrating with actual camera and YOLO detection

    Requirements:
        pip install opencv-python ultralytics
    """
    try:
        import cv2
        from ultralytics import YOLO
    except ImportError:
        print("Install required packages:")
        print("pip install opencv-python ultralytics")
        return

    # Initialize
    client = ParkingAPIClient(API_URL, API_KEY, CAMERA_ID)
    model = YOLO('yolov8n.pt')  # Load YOLO model
    cap = cv2.VideoCapture(0)  # Open camera (0 = default camera)

    print("Camera opened. Processing frames...")

    try:
        while True:
            # Capture frame
            ret, frame = cap.read()
            if not ret:
                break

            # Run YOLO detection
            results = model(frame)

            # Process detections to check parking slot occupancy
            # (Your parking occupancy logic here)
            occupied_count = 0  # Calculate from YOLO results

            # Send to cloud
            client.send_update(
                coordinates=PARKING_COORDINATES,
                occupied_count=occupied_count,
                total_count=len(PARKING_COORDINATES)
            )

            time.sleep(UPDATE_INTERVAL)

    finally:
        cap.release()
        print("Camera released")


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    # Run the main continuous monitoring loop
    main()

    # Alternative: Send single image
    # send_single_image_example()

    # Alternative: Production with camera
    # production_example_with_camera()
