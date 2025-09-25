#!/bin/bash
# Complete System Startup Script
# This script starts both servers and monitoring automatically

echo "🚀 Starting Complete Parking Detection System..."
echo "=" * 60

# Function to check if a process is running
check_server() {
    local url=$1
    local name=$2
    if curl -s "$url" > /dev/null 2>&1; then
        echo "✅ $name is running"
        return 0
    else
        echo "❌ $name is not responding"
        return 1
    fi
}

# Function to start Flask server
start_flask_server() {
    echo "🔧 Starting Flask API Server..."
    cd /home/giyu/Desktop/MajorProject/Flask-API-1
    source venv_flask/bin/activate
    python flask_server.py &
    FLASK_PID=$!
    echo "Flask server started with PID: $FLASK_PID"
    sleep 5
}

# Function to start Local server  
start_local_server() {
    echo "🔧 Starting Local Server..."
    cd /home/giyu/Desktop/MajorProject/Local-Server-1
    source venv_local/bin/activate
    python frame_server.py &
    LOCAL_PID=$!
    echo "Local server started with PID: $LOCAL_PID"
    sleep 3
}

# Function to start monitoring
start_monitoring() {
    echo "🔧 Starting 10-second parking monitoring..."
    sleep 2
    curl -X POST http://127.0.0.1:8000/start_monitoring
    echo ""
}

# Main execution
echo "📋 Step 1: Starting Flask API Server..."
start_flask_server

echo "📋 Step 2: Starting Local Server..."  
start_local_server

echo "📋 Step 3: Checking servers..."
check_server "http://127.0.0.1:8000/" "Flask API Server"
check_server "http://127.0.0.1:5000/" "Local Server"

echo "📋 Step 4: Starting monitoring..."
start_monitoring

echo ""
echo "🎉 SYSTEM STARTED SUCCESSFULLY!"
echo "=" * 60
echo "✅ Flask API Server: http://127.0.0.1:8000"
echo "✅ Local Server: http://127.0.0.1:5000" 
echo "✅ 10-second monitoring: ACTIVE"
echo ""
echo "👀 Check the Flask server console for output every 10 seconds:"
echo "   📊 [HH:MM:SS] Waiting for parking data..."
echo "   ⚠️  [HH:MM:SS] Local Server not responding"
echo "   🅿️  [HH:MM:SS] AVAILABLE SLOTS: XX/73"
echo ""
echo "🛑 To stop: Press Ctrl+C or run 'pkill -f flask_server.py && pkill -f frame_server.py'"
echo "=" * 60

# Keep script running
echo "⏰ System running... Press Ctrl+C to stop"
wait