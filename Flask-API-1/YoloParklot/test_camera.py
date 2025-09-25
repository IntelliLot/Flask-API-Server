#!/usr/bin/env python3
"""
Simple camera test script to verify camera access
"""

import cv2
import sys

def test_camera(camera_index=0):
    """Test camera access"""
    print(f"Testing camera with index: {camera_index}")
    
    # Try to open camera
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"❌ Failed to open camera with index {camera_index}")
        return False
    
    # Get camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    print(f"✅ Camera opened successfully!")
    print(f"   Resolution: {width}x{height}")
    print(f"   FPS: {fps}")
    
    # Try to read a frame
    ret, frame = cap.read()
    
    if not ret:
        print("❌ Failed to read frame from camera")
        cap.release()
        return False
    
    print(f"✅ Successfully read frame: {frame.shape}")
    
    # Show camera for 5 seconds
    print("Showing camera feed for 5 seconds... Press 'q' to quit early")
    
    frame_count = 0
    while frame_count < 150:  # ~5 seconds at 30fps
        ret, frame = cap.read()
        if not ret:
            break
        
        cv2.imshow('Camera Test', frame)
        
        # Break on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        frame_count += 1
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    print("✅ Camera test completed successfully!")
    return True

if __name__ == "__main__":
    # Test default camera (index 0)
    if test_camera(0):
        print("\n🎉 Your camera is working and ready for the parking detection system!")
    else:
        print("\n⚠️  Camera test failed. Please check:")
        print("   1. Camera is connected")
        print("   2. Camera permissions are granted")
        print("   3. No other application is using the camera")
        print("   4. Try different camera indices (1, 2, etc.)")
        
        # Try alternative camera indices
        for i in range(1, 4):
            print(f"\nTrying camera index {i}...")
            if test_camera(i):
                print(f"✅ Camera found at index {i}!")
                break
    
    sys.exit(0)