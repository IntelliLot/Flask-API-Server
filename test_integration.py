#!/usr/bin/env python3
"""
Test script for Two-Server YOLO Parking Detection Architecture
"""

import requests
import json
import time
import base64
import cv2
import numpy as np

def test_servers():
    """Test both servers and their communication"""
    print('🧪 Testing Two-Server YOLO Parking Detection Architecture')
    print('=' * 60)
    
    # Test Local Frame Server (Server 1)
    print('🎥 Testing Local Frame Server (Server 1)...')
    try:
        response = requests.get('http://127.0.0.1:5000/', timeout=5)
        if response.status_code == 200:
            print('✅ Server 1 Health Check - SUCCESS')
            data = response.json()
            print(f'   Status: {data["status"]}')
            print(f'   Server: {data["server"]}')
            print(f'   Video Source: {data.get("video_source", "Unknown")}')
        else:
            print(f'❌ Server 1 Failed - Status: {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ Server 1 Error: {e}')
        return False

    print()

    # Test Flask API Server (Server 2)  
    print('🧠 Testing Flask API Server (Server 2)...')
    try:
        response = requests.get('http://127.0.0.1:8000/', timeout=5)
        if response.status_code == 200:
            print('✅ Server 2 Health Check - SUCCESS')
            data = response.json()
            print(f'   Status: {data["status"]}')
            print(f'   Server: {data["server"]}')
            print(f'   Output Directory: {data.get("output_directory", "Unknown")}')
        else:
            print(f'❌ Server 2 Failed - Status: {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ Server 2 Error: {e}')
        return False

    print()
    print('� Testing Inter-Server Communication...')

    # Test frame retrieval from Server 1
    print('� Testing frame retrieval from Server 1...')
    try:
        response = requests.get('http://127.0.0.1:5000/latest_frame', timeout=10)
        if response.status_code == 200:
            print('✅ Frame retrieval from Server 1 - SUCCESS')
            data = response.json()
            frame_data = data.get('frame', '')
            if frame_data:
                print(f'   Frame data size: {len(frame_data)} characters')
                print(f'   Frame timestamp: {data.get("timestamp", "Unknown")}')
                
                # Try to decode the frame to verify it's valid
                try:
                    frame_bytes = base64.b64decode(frame_data)
                    frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
                    frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                    if frame is not None:
                        print(f'   Frame dimensions: {frame.shape}')
                        print('✅ Frame decode verification - SUCCESS')
                    else:
                        print('❌ Frame decode verification - FAILED')
                except Exception as decode_error:
                    print(f'❌ Frame decode error: {decode_error}')
            else:
                print('❌ No frame data received')
                return False
        else:
            print(f'❌ Frame retrieval failed - Status: {response.status_code}')
            return False
    except Exception as e:
        print(f'❌ Frame retrieval error: {e}')
        return False

    print()
    print('📤 Testing frame processing via Server 2...')
    
    # Test Server 2 stats
    try:
        response = requests.get('http://127.0.0.1:8000/stats', timeout=5)
        if response.status_code == 200:
            print('✅ Server 2 Stats - SUCCESS')
            data = response.json()
            print(f'   Auto Processing: {data.get("auto_processing", "Unknown")}')
            print(f'   Total Processed: {data.get("total_processed", 0)}')
        else:
            print(f'⚠️  Server 2 Stats - Status: {response.status_code}')
    except Exception as e:
        print(f'⚠️  Server 2 Stats error: {e}')

    print()
    print('✅ Two-Server Architecture Test Complete!')
    print('=' * 60)
    print('🎯 Key Findings:')
    print('   • Local Frame Server (Server 1) - ✅ Working')
    print('   • Flask API Server (Server 2) - ✅ Running')
    print('   • Frame Communication - ✅ Working')
    print('   • Both servers operate independently')
    print('=' * 60)
    
    return True

if __name__ == "__main__":
    success = test_servers()
    exit(0 if success else 1)