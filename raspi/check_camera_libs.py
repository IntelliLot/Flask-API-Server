#!/usr/bin/env python3
"""
Quick check for Pi Camera libraries
"""

import sys
import os

print("=" * 60)
print("🔍 Checking Pi Camera Libraries")
print("=" * 60)
print()

# Check if in virtual environment
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("⚠️  WARNING: Running in virtual environment!")
    print(f"   VIRTUAL_ENV: {os.environ.get('VIRTUAL_ENV', 'unknown')}")
    print("   System packages (like picamera2) may not be accessible")
    print()

# Check Python version
print(f"Python version: {sys.version}")
print()

# Check picamera2 (system package)
print("1️⃣ Checking picamera2 (modern, system library)...")
try:
    from picamera2 import Picamera2
    print("   ✅ picamera2 is available!")
    print("   This is what we need!")
except ImportError as e:
    print(f"   ❌ picamera2 not found: {e}")
    print("   Install with: sudo apt install python3-picamera2")

print()

# Check legacy picamera
print("2️⃣ Checking picamera (legacy)...")
try:
    from picamera import PiCamera
    print("   ✅ picamera is available")
except ImportError as e:
    print(f"   ❌ picamera not found: {e}")
    print("   (This is OK, picamera2 is preferred)")

print()

# Check OpenCV
print("3️⃣ Checking OpenCV...")
try:
    import cv2
    print(f"   ✅ OpenCV {cv2.__version__} is available")
except ImportError as e:
    print(f"   ❌ OpenCV not found: {e}")

print()
print("=" * 60)
print("📋 Recommendation:")
print("=" * 60)

try:
    from picamera2 import Picamera2
    print("✅ You have picamera2 - camera_manager.py should work!")
    print()
    print("Next step: Run the test")
    print("  python3 test_camera.py")
except ImportError:
    print("⚠️  picamera2 not found. Install it:")
    print("  sudo apt update")
    print("  sudo apt install -y python3-picamera2")
    print()

    # Check if in venv
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  You're in a virtual environment!")
        print()
        print("SOLUTION 1 (Recommended): Exit venv")
        print("  deactivate")
        print("  python3 check_camera_libs.py")
        print()
        print("SOLUTION 2: Recreate venv with system packages")
        print("  deactivate")
        print("  rm -rf venv")
        print("  python3 -m venv --system-site-packages venv")
        print("  source venv/bin/activate")
    else:
        print("Then run the test:")
        print("  python3 test_camera.py")

print("=" * 60)
