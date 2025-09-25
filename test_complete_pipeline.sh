#!/bin/bash
# Complete Processing Test - Populates Output Folder
# This script demonstrates the complete pipeline: Camera -> Local Server -> Flask API -> Output

echo "🎯 COMPLETE PROCESSING PIPELINE TEST"
echo "===================================="
echo "Purpose: Test full pipeline and populate output folder"
echo ""

# Navigate to project directory
cd /home/giyu/Desktop/MajorProject

# Start Local Server in background
echo "🎥 Step 1: Starting Local Server (Camera Input)..."
cd Local-Server-1
PYTHONPATH="$(pwd)/venv_local/lib/python3.12/site-packages" python3 frame_server.py > local_processing.log 2>&1 &
LOCAL_PID=$!
echo "   📡 Local Server PID: $LOCAL_PID"
cd ..

# Wait for Local Server to initialize
echo "   ⏱️  Waiting for Local Server to initialize..."
sleep 5

# Start Flask API Server in background
echo "🧠 Step 2: Starting Flask API Server (YoloParklot)..."
cd Flask-API-1
source venv_flask/bin/activate
python flask_server.py > flask_processing.log 2>&1 &
FLASK_PID=$!
echo "   📡 Flask API Server PID: $FLASK_PID"
cd ..

# Wait for Flask Server to initialize
echo "   ⏱️  Waiting for Flask API Server to initialize..."
sleep 8

# Test server connectivity
echo "🔍 Step 3: Testing server connectivity..."

# Test Local Server
LOCAL_STATUS=$(curl -s -w "%{http_code}" http://127.0.0.1:5000/ -o /dev/null)
if [ "$LOCAL_STATUS" = "200" ]; then
    echo "   ✅ Local Server: Connected"
else
    echo "   ❌ Local Server: Failed (Status: $LOCAL_STATUS)"
    kill $LOCAL_PID $FLASK_PID 2>/dev/null
    exit 1
fi

# Test Flask API Server
FLASK_STATUS=$(curl -s -w "%{http_code}" http://127.0.0.1:8000/ -o /dev/null)
if [ "$FLASK_STATUS" = "200" ]; then
    echo "   ✅ Flask API Server: Connected"
else
    echo "   ❌ Flask API Server: Failed (Status: $FLASK_STATUS)"
    kill $LOCAL_PID $FLASK_PID 2>/dev/null
    exit 1
fi

# Start automatic processing
echo "🔄 Step 4: Starting automatic processing..."
echo "   📡 Flask API Server will fetch frames from Local Server"
echo "   🧠 Process frames with YoloParklot (if available)"
echo "   💾 Save processed results to output folder"

# Start auto-processing with 3-second intervals
START_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/start_auto_processing \
    -H "Content-Type: application/json" \
    -d '{"interval": 3}' \
    -w "%{http_code}")

if [[ "$START_RESPONSE" == *"200" ]]; then
    echo "   ✅ Auto-processing started successfully"
else
    echo "   ⚠️  Auto-processing response: $START_RESPONSE"
fi

# Monitor processing for 20 seconds
echo ""
echo "📊 Step 5: Monitoring processing (20 seconds)..."
echo "   🔍 Watching for output files being created..."

for i in {1..10}; do
    # Check processing stats
    STATS=$(curl -s http://127.0.0.1:8000/stats 2>/dev/null)
    if [ $? -eq 0 ]; then
        PROCESSED=$(echo "$STATS" | grep -o '"total_processed":[0-9]*' | cut -d':' -f2)
        AUTO_STATUS=$(echo "$STATS" | grep -o '"auto_processing":[a-z]*' | cut -d':' -f2)
        echo "   📈 Cycle $i: Processed frames: ${PROCESSED:-0}, Auto-processing: ${AUTO_STATUS:-unknown}"
    else
        echo "   ⚠️  Cycle $i: Could not get stats"
    fi
    
    # Check if output files exist
    OUTPUT_COUNT=$(find Flask-API-1/output/ -name "*.jpg" -o -name "*.json" 2>/dev/null | wc -l)
    echo "   📁 Output files created: $OUTPUT_COUNT"
    
    sleep 2
done

# Stop auto-processing
echo ""
echo "🛑 Step 6: Stopping auto-processing..."
STOP_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/stop_auto_processing -w "%{http_code}")
if [[ "$STOP_RESPONSE" == *"200" ]]; then
    echo "   ✅ Auto-processing stopped"
else
    echo "   ⚠️  Stop response: $STOP_RESPONSE"
fi

# Check final output
echo ""
echo "📁 Step 7: Final Output Analysis..."
OUTPUT_IMAGES=$(find Flask-API-1/output/ -name "*.jpg" 2>/dev/null | wc -l)
OUTPUT_JSON=$(find Flask-API-1/output/ -name "*.json" 2>/dev/null | wc -l)
TOTAL_FILES=$(find Flask-API-1/output/ -type f 2>/dev/null | wc -l)

echo "   📸 Processed images: $OUTPUT_IMAGES"
echo "   📋 JSON metadata files: $OUTPUT_JSON" 
echo "   📁 Total output files: $TOTAL_FILES"

if [ $TOTAL_FILES -gt 0 ]; then
    echo "   ✅ SUCCESS: Output folder populated!"
    echo ""
    echo "   📂 Latest files in output folder:"
    ls -la Flask-API-1/output/ | tail -5
else
    echo "   ⚠️  Output folder still empty - Check logs for issues"
    echo ""
    echo "   📋 Recent Local Server log:"
    tail -5 Local-Server-1/local_processing.log 2>/dev/null || echo "   No Local Server log"
    echo ""
    echo "   📋 Recent Flask API Server log:"
    tail -5 Flask-API-1/flask_processing.log 2>/dev/null || echo "   No Flask API Server log"
fi

# Cleanup
echo ""
echo "🧹 Step 8: Cleaning up..."
kill $LOCAL_PID $FLASK_PID 2>/dev/null
echo "   🛑 Servers stopped"

echo ""
echo "🎯 COMPLETE PROCESSING PIPELINE TEST FINISHED"
echo "=============================================="
if [ $TOTAL_FILES -gt 0 ]; then
    echo "✅ SUCCESS: Full pipeline working!"
    echo "   📍 Camera frames captured by Local Server"
    echo "   📍 Frames processed by Flask API Server" 
    echo "   📍 Results saved to Flask-API-1/output/"
else
    echo "⚠️  PARTIAL: Servers working, but output generation needs investigation"
    echo "   💡 This may be due to YoloParklot model not being available"
    echo "   💡 Check Flask-API-1/flask_processing.log for details"
fi
echo "=============================================="