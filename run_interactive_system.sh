#!/bin/bash
# Interactive Parking Detection System - See Live Console Output
# This version runs Flask server in foreground so you can see output directly

set -e

echo "🚀 INTERACTIVE PARKING DETECTION SYSTEM"
echo "============================================================"
echo "This version shows Flask server output directly in your terminal!"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m' 
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Cleanup function
cleanup() {
    echo ""
    print_warning "Stopping servers..."
    pkill -f flask_server.py 2>/dev/null || true
    pkill -f frame_server.py 2>/dev/null || true
    print_status "Servers stopped"
    exit 0
}

# Handle Ctrl+C gracefully
trap cleanup INT

# Start Local server in background first
start_local_server() {
    print_info "Starting Local Server (background)..."
    cd /home/giyu/Desktop/MajorProject/Local-Server-1
    source venv_local/bin/activate
    python3 frame_server.py > /tmp/local_live.log 2>&1 &
    LOCAL_PID=$!
    print_status "Local server started (PID: $LOCAL_PID)"
    sleep 5
}

# Start Flask server in foreground to show output
start_flask_server_interactive() {
    print_info "Starting Flask API Server (interactive mode)..."
    cd /home/giyu/Desktop/MajorProject/Flask-API-1
    source venv_flask/bin/activate
    
    echo ""
    echo "🎯 FLASK SERVER STARTING..."
    echo "============================================================"
    print_warning "You'll see 10-second parking updates below!"
    print_info "Press Ctrl+C to stop the entire system"
    echo "============================================================"
    echo ""
    
    # Start Flask server in foreground
    python3 flask_server.py &
    FLASK_PID=$!
    
    # Wait for Flask to start
    sleep 8
    
    # Start monitoring automatically
    print_info "Auto-starting 10-second monitoring..."
    curl -s -X POST http://127.0.0.1:8000/start_monitoring > /dev/null
    
    # Process first frame automatically
    print_info "Auto-processing first frame..."
    curl -s -X POST http://127.0.0.1:8000/process_frame -H "Content-Type: application/json" -d '{}' > /dev/null
    
    print_status "System fully started! Watch for 10-second updates below:"
    echo ""
    
    # Show live Flask output
    tail -f /dev/null & # Keep script running
    wait $FLASK_PID
}

# Main execution
main() {
    cd /home/giyu/Desktop/MajorProject
    
    # Cleanup any existing processes
    pkill -f flask_server.py 2>/dev/null || true
    pkill -f frame_server.py 2>/dev/null || true
    
    # Start Local server
    start_local_server
    
    # Check if Local server started
    sleep 2
    if curl -s http://127.0.0.1:5000/ > /dev/null 2>&1; then
        print_status "Local Server verified running"
    else
        print_error "Local Server failed to start"
        exit 1
    fi
    
    # Start Flask server in interactive mode
    start_flask_server_interactive
}

# Show instructions
echo "📋 INSTRUCTIONS:"
echo "• This script shows live Flask server output"
echo "• You'll see 10-second parking updates directly"
echo "• Press Ctrl+C to stop everything"
echo ""
read -p "Press Enter to start the interactive system..."

# Run main function
main