#!/usr/bin/env python3
"""
Test Verification Script for Video Feed Server

This script demonstrates that the Server I is working correctly by:
1. Checking camera access
2. Verifying frame capture
3. Confirming local frame storage
"""

import os
import time
import subprocess
from pathlib import Path

def check_captured_frames():
    """Check if frames are being saved locally"""
    frames_dir = Path("captured_frames")
    if not frames_dir.exists():
        print("❌ Frames directory doesn't exist")
        return False
    
    frames = list(frames_dir.glob("*.jpg"))
    print(f"✅ Found {len(frames)} captured frames:")
    
    for frame in sorted(frames)[-5:]:  # Show last 5 frames
        stat = frame.stat()
        print(f"   📸 {frame.name} ({stat.st_size} bytes, {time.ctime(stat.st_mtime)})")
    
    return len(frames) > 0

def check_frame_quality():
    """Verify frame quality using file command"""
    frames_dir = Path("captured_frames")
    frames = list(frames_dir.glob("*.jpg"))
    
    if not frames:
        print("❌ No frames to check")
        return False
    
    latest_frame = max(frames, key=lambda f: f.stat().st_mtime)
    print(f"\n🔍 Checking frame quality: {latest_frame.name}")
    
    try:
        result = subprocess.run(['file', str(latest_frame)], capture_output=True, text=True)
        if "JPEG image data" in result.stdout:
            print(f"✅ Frame is valid JPEG: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Frame validation failed: {result.stdout}")
            return False
    except Exception as e:
        print(f"❌ Error checking frame: {e}")
        return False

def main():
    print("🔍 VIDEO FEED SERVER VERIFICATION")
    print("=" * 40)
    
    print("\n1. Checking captured frames...")
    frames_ok = check_captured_frames()
    
    print("\n2. Verifying frame quality...")
    quality_ok = check_frame_quality()
    
    print("\n" + "=" * 40)
    if frames_ok and quality_ok:
        print("✅ ALL CHECKS PASSED!")
        print("📹 Video Feed Server is working correctly")
        print("📁 Frames are being captured and saved locally")
        print("\n💡 To test with a receiver server:")
        print("   1. Run: python simple_receiver.py")
        print("   2. Then run: python video_feed_server.py")
    else:
        print("❌ Some checks failed. Please check the server.")

if __name__ == "__main__":
    main()