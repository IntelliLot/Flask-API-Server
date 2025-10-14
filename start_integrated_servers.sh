#!/bin/bash

# Start servers for Flask API integration with Local Server
# This script starts both Local Server and Flask API server

echo "🚀 Starting Flask API & Local Server Integration"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for server to be ready
wait_for_server() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $name to start..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s $url >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $name is ready!${NC}"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts - waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $name failed to start within timeout${NC}"
    return 1
}

# Check if Local Server is already running
if check_port 5000; then
    echo -e "${GREEN}✅ Local Server already running on port 5000${NC}"
else
    echo "🔄 Starting Local Server..."
    
    # Navigate to Local Server directory and start
    if [ -d "../Local-Server-1" ]; then
        cd ../Local-Server-1
        
        # Start Local Server in background
        if [ -f "realtime_server.py" ]; then
            python3 realtime_server.py &
            LOCAL_SERVER_PID=$!
            echo "Local Server started with PID: $LOCAL_SERVER_PID"
        elif [ -f "backend_server.py" ]; then
            python3 backend_server.py &
            LOCAL_SERVER_PID=$!
            echo "Backend Server started with PID: $LOCAL_SERVER_PID"
        else
            echo -e "${RED}❌ No server file found in Local-Server-1${NC}"
            exit 1
        fi
        
        cd - > /dev/null
        
        # Wait for Local Server to be ready
        if ! wait_for_server "http://127.0.0.1:5000/health" "Local Server"; then
            echo -e "${YELLOW}⚠️ Local Server health check failed, but continuing...${NC}"
        fi
    else
        echo -e "${RED}❌ Local-Server-1 directory not found${NC}"
        exit 1
    fi
fi

# Check if Flask API is already running
if check_port 8000; then
    echo -e "${YELLOW}⚠️ Flask API already running on port 8000${NC}"
    echo "Please stop the existing Flask API server first"
    exit 1
fi

# Create output directory structure
echo "📁 Creating output directories..."
mkdir -p output/processed_frames
mkdir -p output/raw_frames
echo -e "${GREEN}✅ Output directories created${NC}"

# Start Flask API Server
echo "🔄 Starting Flask API Server..."
python3 realtime_flask_server.py &
FLASK_API_PID=$!
echo "Flask API Server started with PID: $FLASK_API_PID"

# Wait for Flask API to be ready
if wait_for_server "http://127.0.0.1:8000/health" "Flask API Server"; then
    echo -e "${GREEN}🎉 Both servers are running successfully!${NC}"
    echo ""
    echo "🌐 Server URLs:"
    echo "  Local Server:  http://127.0.0.1:5000"
    echo "  Flask API:     http://127.0.0.1:8000"
    echo ""
    echo "📊 API Endpoints:"
    echo "  Health:        http://127.0.0.1:8000/health"
    echo "  Stats:         http://127.0.0.1:8000/stats"
    echo "  Results:       http://127.0.0.1:8000/results"
    echo "  Upload:        http://127.0.0.1:8000/upload"
    echo ""
    echo "🗂️ Output Directory: ./output/"
    echo "  Processed frames: ./output/processed_frames/"
    echo "  Raw frames:       ./output/raw_frames/"
    echo "  Results file:     ./output/realtime_results.json"
    echo ""
    echo "To test integration, run:"
    echo "  python3 test_local_server_integration.py"
    echo ""
    echo "Press Ctrl+C to stop all servers"
    
    # Create a cleanup function
    cleanup() {
        echo -e "\n🛑 Stopping servers..."
        
        if [ ! -z "$FLASK_API_PID" ]; then
            kill $FLASK_API_PID 2>/dev/null
            echo "Flask API Server stopped"
        fi
        
        if [ ! -z "$LOCAL_SERVER_PID" ]; then
            kill $LOCAL_SERVER_PID 2>/dev/null
            echo "Local Server stopped"
        fi
        
        echo -e "${GREEN}✅ All servers stopped${NC}"
        exit 0
    }
    
    # Set trap for cleanup
    trap cleanup SIGINT SIGTERM
    
    # Keep script running
    wait
    
else
    echo -e "${RED}❌ Flask API Server failed to start${NC}"
    
    # Cleanup
    if [ ! -z "$FLASK_API_PID" ]; then
        kill $FLASK_API_PID 2>/dev/null
    fi
    if [ ! -z "$LOCAL_SERVER_PID" ]; then
        kill $LOCAL_SERVER_PID 2>/dev/null
    fi
    
    exit 1
fi