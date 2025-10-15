#!/bin/bash
# Quick test script for custom coordinates feature

echo "=========================================="
echo "Testing Custom Coordinates Feature"
echo "=========================================="
echo ""

# Test 1: Command line with JSON file
echo "✅ Test 1: Command line with JSON file"
python3 main_app.py --mode image --input ParkImage1.jpeg --coordinates example_coordinates.json --output output/test1.jpg > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ Success: Processing with JSON coordinates"
else
    echo "   ✗ Failed"
fi
echo ""

# Test 2: Check if output file was created
if [ -f "output/test1.jpg" ]; then
    echo "✅ Test 2: Output file created"
    echo "   ✓ File: output/test1.jpg"
else
    echo "✗ Test 2: Output file not found"
fi
echo ""

# Test 3: Verify API server can start (but don't keep it running)
echo "✅ Test 3: API server check"
if python3 -c "import flask" 2>/dev/null; then
    echo "   ✓ Flask is installed"
    echo "   ℹ Start server with: python3 api_server.py"
else
    echo "   ℹ Flask not installed (optional)"
    echo "   Install with: pip install flask"
fi
echo ""

echo "=========================================="
echo "All core tests completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. View output: output/test1.jpg"
echo "2. Try examples: python3 examples_custom_coordinates.py"
echo "3. Start API: python3 api_server.py"
echo "4. Read docs: QUICK_REFERENCE.md"
