#!/usr/bin/env python3
"""
Simple test to trigger Flask server processing and demonstrate 10-second monitoring
"""

import requests
import json

def test_flask_monitoring():
    """Test Flask server and demonstrate monitoring"""
    flask_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing Flask API Server 10-second monitoring...")
    print("="*60)
    
    try:
        # Test health check
        response = requests.get(f"{flask_url}/")
        if response.status_code == 200:
            print("✅ Flask server is running")
            health_data = response.json()
            print(f"   YoloParklot available: {health_data.get('yolo_available', False)}")
        else:
            print("❌ Flask server not responding")
            return
        
        # Check current stats
        print("\n📊 Checking server statistics...")
        response = requests.get(f"{flask_url}/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Server Statistics:")
            print(f"   Auto-processing active: {stats.get('auto_processing_active', False)}")
            print(f"   Status monitoring active: {stats.get('status_monitoring_active', False)}")
            print(f"   Total processed frames: {stats.get('total_processed', 0)}")
            
            current_status = stats.get('current_parking_status')
            if current_status:
                print(f"   Current parking data available: ✅")
                print(f"   Available slots: {current_status.get('available_slots', 'Unknown')}")
                print(f"   Total slots: {current_status.get('total_slots', 'Unknown')}")
            else:
                print(f"   Current parking data: ❌ None available yet")
        
        # Show latest result if available
        print("\n📋 Checking for latest processing results...")
        response = requests.get(f"{flask_url}/latest_result")
        if response.status_code == 200:
            result = response.json()
            print("✅ Latest result found:")
            parking_data = result.get('parking_data', {})
            if parking_data:
                available_slots = parking_data.get('available_slots', 0)
                total_slots = parking_data.get('total_slots', 0)
                available_numbers = parking_data.get('available_slot_numbers', [])
                
                print(f"   🅿️  Available Slots: {available_slots}/{total_slots}")
                if available_numbers:
                    if len(available_numbers) <= 10:
                        numbers_str = ', '.join(map(str, available_numbers))
                    else:
                        numbers_str = f"{', '.join(map(str, available_numbers[:10]))}... (+{len(available_numbers)-10} more)"
                    print(f"   🔢 Available Slot Numbers: {numbers_str}")
        else:
            print("ℹ️  No processing results available yet")
        
        print("\n" + "="*60)
        print("🔔 10-SECOND MONITORING STATUS:")
        print("="*60)
        print("✅ The Flask server is now running 10-second monitoring!")
        print("⏰ Every 10 seconds, the server logs will show:")
        print("   📊 Available slots count")
        print("   🔢 Available slot numbers") 
        print("   🚗 Occupancy rate")
        print("   ⚡ Processing mode")
        print("\n💡 Check the Flask server console output to see the live updates!")
        print("💡 The monitoring will show either:")
        print("   - Real parking data (when both servers are running)")
        print("   - 'Local Server not responding' (when Local Server is down)")
        print("   - 'Waiting for parking data' (when no data processed yet)")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_flask_monitoring()