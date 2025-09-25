#!/bin/bash

# Two-Server Architecture Startup Script
# Starts Local Server (Server I) and Flask API Server (Server II)

echo "🚀 Starting Two-Server Architecture for YOLO Parking Detection"
echo "================================================================"

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port $port is already in use"
        return 1
    else
        echo "✅ Port $port is available"
        return 0
    fi
}

# Function to start server in new terminal
start_server() {
    local server_name=$1
    local directory=$2
    local command=$3
    local port=$4
    
    echo "🔄 Starting $server_name on port $port..."
    
    # Check if port is available
    if ! check_port $port; then
        echo "⚠️  $server_name may already be running"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi
    
    # Start server in new terminal
    gnome-terminal --title="$server_name" --working-directory="$directory" -- bash -c "$command; read -p 'Press Enter to close...'" &
    
    echo "✅ $server_name started in new terminal"
    return 0
}

# Check if we're in the right directory
if [[ ! -d "Local-Server-1" || ! -d "Flask-API-1" ]]; then
    echo "❌ Error: Please run this script from the MajorProject directory"
    echo "Expected structure:"
    echo "  MajorProject/"
    echo "  ├── Local-Server-1/"
    echo "  └── Flask-API-1/"
    exit 1
fi

echo "📁 Current directory: $(pwd)"
echo "🔍 Checking server directories..."

# Check Local Server
if [[ -f "Local-Server-1/frame_server.py" ]]; then
    echo "✅ Local Server found"
else
    echo "❌ Local Server not found (frame_server.py missing)"
    exit 1
fi

# Check Flask API Server  
if [[ -f "Flask-API-1/flask_server.py" ]]; then
    echo "✅ Flask API Server found"
else
    echo "❌ Flask API Server not found (flask_server.py missing)"
    exit 1
fi

echo
echo "🎬 Starting servers..."
echo "----------------------"

#!/bin/bash
# Startup script to run both servers for YOLO Parking Detection System

echo "🚀 Starting Two-Server YOLO Parking Detection System"
echo "=" "="*60

# Kill any existing servers
echo "🧹 Cleaning up any existing servers..."
pkill -f "frame_server.py" 2>/dev/null
pkill -f "flask_server.py" 2>/dev/null
sleep 2

# Start Local Frame Server (Server 1) in background
echo "🎥 Starting Local Frame Server (Server 1) on port 5000..."
cd /home/giyu/Desktop/MajorProject/Local-Server-1
export PYTHONPATH="/home/giyu/Desktop/MajorProject/Local-Server-1/venv_local/lib/python3.12/site-packages"
python3 frame_server.py > local_server.log 2>&1 &
LOCAL_SERVER_PID=$!
echo "   📡 Local Server PID: $LOCAL_SERVER_PID"

# Wait for Local Server to start
sleep 3

# Start Flask API Server (Server 2) in background
echo "🔄 Starting Flask API Server (Server 2) on port 8000..."
cd /home/giyu/Desktop/MajorProject/Flask-API-1
source venv_flask/bin/activate
python flask_server.py > flask_server.log 2>&1 &
FLASK_SERVER_PID=$!
echo "   🧠 Flask Server PID: $FLASK_SERVER_PID"

# Wait for both servers to fully start
sleep 5

echo ""
echo "✅ BOTH SERVERS STARTED SUCCESSFULLY!"
echo "="*60
echo "🎥 Local Frame Server (Server 1):"
echo "   URL: http://127.0.0.1:5000"
echo "   Endpoint: /latest_frame"
echo "   Log: Local-Server-1/local_server.log"
echo ""
echo "🧠 Flask API Server (Server 2):"
echo "   URL: http://127.0.0.1:8000"  
echo "   Endpoint: /process_frame"
echo "   Log: Flask-API-1/flask_server.log"
echo ""
echo "💡 Test the system:"
echo "   curl http://127.0.0.1:5000/"
echo "   curl http://127.0.0.1:8000/"
echo ""
echo "🛑 To stop both servers:"
echo "   kill $LOCAL_SERVER_PID $FLASK_SERVER_PID"
echo ""
echo "📊 Monitoring logs:"
echo "   tail -f Local-Server-1/local_server.log"
echo "   tail -f Flask-API-1/flask_server.log"
echo "="*60

# Keep script running to monitor
echo "🔍 Monitoring servers... Press Ctrl+C to stop all servers"
trap 'kill $LOCAL_SERVER_PID $FLASK_SERVER_PID; echo "🛑 All servers stopped"; exit 0' INT

# Monitor both processes
while true; do
    if ! kill -0 $LOCAL_SERVER_PID 2>/dev/null; then
        echo "❌ Local Server stopped unexpectedly"
        kill $FLASK_SERVER_PID 2>/dev/null
        exit 1
    fi
    if ! kill -0 $FLASK_SERVER_PID 2>/dev/null; then
        echo "❌ Flask Server stopped unexpectedly" 
        kill $LOCAL_SERVER_PID 2>/dev/null
        exit 1
    fi
    sleep 5
done

echo
echo "🎉 Both servers started successfully!"
echo "===================================="
echo
echo "📊 Server Information:"
echo "  📡 Local Server (Server I):     http://127.0.0.1:5000"
echo "      - Captures and serves video frames"
echo "      - Endpoints: /, /latest_frame, /stats"
echo
echo "  🤖 Flask API Server (Server II): http://127.0.0.1:8000"
echo "      - Processes frames with YoloParklot"  
echo "      - Endpoints: /, /process_frame, /start_auto_processing, /stats"
echo
echo "🧪 Testing:"
echo "  python test_integration.py"
echo
echo "📖 API Usage Examples:"
echo "  # Get frame from Local Server"
echo "  curl http://127.0.0.1:5000/latest_frame"
echo
echo "  # Process frame with Flask API Server"
echo "  curl -X POST http://127.0.0.1:8000/process_frame"
echo
echo "  # Start auto-processing"
echo "  curl -X POST http://127.0.0.1:8000/start_auto_processing -H 'Content-Type: application/json' -d '{\"interval\": 5}'"
echo
echo "  # Get processing stats"
echo "  curl http://127.0.0.1:8000/stats"
echo
echo "🛑 To stop servers: Close the terminal windows or press Ctrl+C in each terminal"
echo
echo "Press Enter to continue or Ctrl+C to exit..."
read