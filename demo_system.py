#!/usr/bin/env python3
"""
Demo script for Two-Server YOLO Parking Detection System
Demonstrates camera input -> Local Server -> Flask API Server -> Processed output
"""

import requests
import json
import time

def main():
    print("🎥 Two-Server YOLO Parking Detection Demo")
    print("=" * 60)
    print("📋 System Architecture:")
    print("   1. Local Server (Port 5000) - Camera input & frame serving")
    print("   2. Flask API Server (Port 8000) - YoloParklot processing")
    print("   3. Automatic frame processing & storage")
    print("=" * 60)
    
    # Check if servers are running
    print("🔍 Checking server status...")
    
    try:
        # Check Local Server (Server 1)
        response = requests.get('http://127.0.0.1:5000/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Local Server: {data['status']} - {data.get('video_source', 'Camera')}")
        else:
            print("❌ Local Server not responding")
            return
            
        # Check Flask API Server (Server 2)
        response = requests.get('http://127.0.0.1:8000/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Flask API Server: {data['status']} - {data['server']}")
        else:
            print("❌ Flask API Server not responding")
            return
            
    except Exception as e:
        print(f"❌ Error checking servers: {e}")
        print("💡 Please start both servers using: ./start_servers.sh")
        return
    
    print()
    print("🚀 Starting automatic frame processing...")
    
    # Start automatic processing
    try:
        response = requests.post('http://127.0.0.1:8000/start_auto_processing', 
                               json={'interval': 3})  # Process every 3 seconds
        if response.status_code == 200:
            print("✅ Auto-processing started!")
            data = response.json()
            print(f"   Interval: {data.get('interval', 3)} seconds")
        else:
            print(f"❌ Failed to start auto-processing: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error starting auto-processing: {e}")
        return
    
    print()
    print("📊 Monitoring processing (press Ctrl+C to stop)...")
    print("   - Frames are being fetched from camera via Local Server")
    print("   - Flask API Server processes frames using YoloParklot")
    print("   - Processed frames saved to Flask-API-1/output/")
    print()
    
    try:
        for i in range(10):  # Monitor for 10 cycles
            time.sleep(5)
            
            # Get processing stats
            response = requests.get('http://127.0.0.1:8000/stats', timeout=5)
            if response.status_code == 200:
                stats = response.json()
                print(f"📈 Cycle {i+1}: Processed {stats.get('total_processed', 0)} frames")
            else:
                print(f"⚠️  Could not get stats (Status: {response.status_code})")
    
    except KeyboardInterrupt:
        print("\n🛑 Stopping demo...")
    
    # Stop auto-processing
    try:
        response = requests.post('http://127.0.0.1:8000/stop_auto_processing')
        if response.status_code == 200:
            print("✅ Auto-processing stopped")
        else:
            print("⚠️  Could not stop auto-processing")
    except Exception as e:
        print(f"⚠️  Error stopping auto-processing: {e}")
    
    print()
    print("✅ Demo completed!")
    print("📁 Check Flask-API-1/output/ folder for processed frames")
    print("💡 Each processed frame includes parking detection annotations")

if __name__ == "__main__":
    main()