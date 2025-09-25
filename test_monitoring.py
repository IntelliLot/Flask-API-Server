#!/usr/bin/env python3
"""
Test script to demonstrate 10-second parking status monitoring
"""

import requests
import time
import json
import random
import base64
import numpy as np
import cv2

def create_test_frame():
    """Create a test frame as base64 encoded data"""
    # Create a simple test image (640x480, 3 channels)
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add some simple graphics to simulate a parking lot
    cv2.rectangle(img, (50, 50), (590, 430), (100, 100, 100), 2)
    cv2.putText(img, "Test Parking Lot", (200, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Encode to base64
    _, buffer = cv2.imencode('.jpg', img)
    frame_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return frame_base64

def test_flask_processing():
    """Test Flask server processing with mock frame data"""
    flask_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing Flask API Server 10-second monitoring...")
    print("="*60)
    
    try:
        # Test health check
        response = requests.get(f"{flask_url}/")
        if response.status_code == 200:
            print("✅ Flask server is running")
        else:
            print("❌ Flask server not responding")
            return
        
        # Create test frame
        test_frame = create_test_frame()
        
        # Send frame for processing
        print("📤 Sending test frame to Flask server...")
        payload = {"frame": test_frame}
        
        response = requests.post(f"{flask_url}/process_frame", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Frame processed successfully!")
            print(f"📊 Result: {result}")
            
            # Check if parking data is available
            parking_data = result.get('result', {}).get('parking_data', {})
            if parking_data:
                available_slots = parking_data.get('available_slots', 0)
                total_slots = parking_data.get('total_slots', 0)
                available_numbers = parking_data.get('available_slot_numbers', [])
                
                print(f"🅿️  Available Slots: {available_slots}/{total_slots}")
                print(f"🔢 Available Slot Numbers: {available_numbers[:10]}...")
                
                print("\n📊 Now monitoring will show this data every 10 seconds!")
                print("⏰ Check the Flask server console for 10-second status updates...")
        else:
            print(f"❌ Frame processing failed: {response.status_code}")
            print(f"Error: {response.text}")
        
        # Show monitoring status
        response = requests.get(f"{flask_url}/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"\n📈 Server Stats:")
            print(f"   Auto-processing: {stats.get('auto_processing_active', False)}")
            print(f"   Status monitoring: {stats.get('status_monitoring_active', False)}")
            print(f"   Current parking status available: {'Yes' if stats.get('current_parking_status') else 'No'}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_flask_processing()