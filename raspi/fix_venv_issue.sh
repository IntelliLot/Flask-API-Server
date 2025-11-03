#!/bin/bash
# Fix for virtual environment issue with system packages

echo "🔧 Virtual Environment Issue Detected"
echo "══════════════════════════════════════"
echo ""
echo "picamera2 is installed system-wide, but you're in a venv"
echo ""
echo "Choose a solution:"
echo ""
echo "OPTION 1 (Recommended): Exit venv and run directly"
echo "─────────────────────────────────────────────────"
echo "  deactivate"
echo "  python3 check_camera_libs.py"
echo "  python3 test_camera.py"
echo "  python3 edge_server.py"
echo ""
echo "OPTION 2: Recreate venv with system packages"
echo "─────────────────────────────────────────────────"
echo "  deactivate"
echo "  rm -rf venv"
echo "  python3 -m venv --system-site-packages venv"
echo "  source venv/bin/activate"
echo "  python3 check_camera_libs.py"
echo ""
echo "OPTION 3: Use system Python (no venv)"
echo "─────────────────────────────────────────────────"
echo "  deactivate"
echo "  # Just use python3 directly"
echo ""

read -p "Auto-fix with Option 1 (exit venv)? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -n "$VIRTUAL_ENV" ]; then
        echo "Exiting virtual environment..."
        deactivate 2>/dev/null || true
        echo "✅ Done! Now run:"
        echo "  python3 check_camera_libs.py"
    else
        echo "Not in a virtual environment"
    fi
fi
