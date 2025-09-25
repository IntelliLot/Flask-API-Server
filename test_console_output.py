#!/usr/bin/env python3
"""
Test script to demonstrate 10-second console output for parking monitoring
"""
import time
import requests
import threading
from datetime import datetime

def test_monitoring():
    """Test the monitoring output"""
    print("🧪 Testing Flask Server Console Output...")
    print("=" * 60)
    
    try:
        # Start monitoring
        response = requests.post("http://127.0.0.1:8000/start_monitoring")
        if response.status_code == 200:
            print("✅ Monitoring started successfully!")
            print("👀 Watch the Flask server console for output every 10 seconds...")
            print("=" * 60)
            
            # Watch for 60 seconds to see several monitoring cycles
            for i in range(6):
                print(f"⏰ Waiting... {(i+1)*10} seconds elapsed")
                time.sleep(10)
            
            print("=" * 60)
            print("🎉 Test completed! Check Flask server console for:")
            print("   📊 [HH:MM:SS] Waiting for parking data...")
            print("   ⚠️  [HH:MM:SS] Local Server not responding")
            print("   🅿️  [HH:MM:SS] AVAILABLE SLOTS: XX/73")
            print("   🔢 Available Slot Numbers: X, X, X...")
            
        else:
            print(f"❌ Failed to start monitoring: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure Flask server is running on port 8000")

if __name__ == "__main__":
    test_monitoring()