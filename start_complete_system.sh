#!/bin/bash
# Complete Parking Detection System with Automatic Data Processing
# This script starts both servers, monitoring, and processes the first frame automatically

set -e  # Exit on any error

echo "🚀 PARKING DETECTION SYSTEM - COMPLETE STARTUP"
echo "============================================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to check if a process is running
check_server() {
    local url=$1
    local name=$2
    if curl -s "$url" > /dev/null 2>&1; then
        print_status "$name is running"
        return 0
    else
        print_error "$name is not responding"
        return 1
    fi
}

# Function to kill existing processes
cleanup_existing() {
    print_info "Cleaning up existing processes..."
    pkill -f flask_server.py 2>/dev/null || true
    pkill -f frame_server.py 2>/dev/null || true
    sleep 2
}

# Function to start Flask server
start_flask_server() {
    print_info "Starting Flask API Server..."
    cd /home/giyu/Desktop/MajorProject/Flask-API-1
    
    # Check if virtual environment exists
    if [ ! -d "venv_flask" ]; then
        print_error "Virtual environment venv_flask not found!"
        exit 1
    fi
    
    # Start Flask server in background
    source venv_flask/bin/activate
    nohup python flask_server.py > /tmp/flask_output.log 2>&1 &
    FLASK_PID=$!
    echo $FLASK_PID > /tmp/flask_pid.txt
    
    print_info "Flask server starting... (PID: $FLASK_PID)"
    sleep 8  # Give it time to initialize
}

# Function to start Local server  
start_local_server() {
    print_info "Starting Local Server..."
    cd /home/giyu/Desktop/MajorProject/Local-Server-1
    
    # Check if virtual environment exists
    if [ ! -d "venv_local" ]; then
        print_error "Virtual environment venv_local not found!"
        exit 1
    fi
    
    # Start Local server in background
    source venv_local/bin/activate
    nohup python frame_server.py > /tmp/local_output.log 2>&1 &
    LOCAL_PID=$!
    echo $LOCAL_PID > /tmp/local_pid.txt
    
    print_info "Local server starting... (PID: $LOCAL_PID)"
    sleep 5  # Give it time to initialize camera
}

# Function to start monitoring
start_monitoring() {
    print_info "Starting 10-second parking monitoring..."
    response=$(curl -s -X POST http://127.0.0.1:8000/start_monitoring)
    if echo "$response" | grep -q "started"; then
        print_status "10-second monitoring activated"
        return 0
    else
        print_error "Failed to start monitoring: $response"
        return 1
    fi
}

# Function to process first frame
process_first_frame() {
    print_info "Processing first frame to generate parking data..."
    response=$(curl -s -X POST http://127.0.0.1:8000/process_frame -H "Content-Type: application/json" -d '{}')
    
    if echo "$response" | grep -q "success"; then
        # Extract parking info
        available_slots=$(echo "$response" | grep -o '"available_slots":[0-9]*' | cut -d':' -f2)
        total_slots=$(echo "$response" | grep -o '"total_slots":[0-9]*' | cut -d':' -f2)
        processing_time=$(echo "$response" | grep -o '"processing_time_ms":[0-9.]*' | cut -d':' -f2)
        
        print_status "First frame processed successfully!"
        print_info "Available Slots: $available_slots/$total_slots"
        print_info "Processing Time: ${processing_time}ms"
        return 0
    else
        print_error "Failed to process frame: $response"
        return 1
    fi
}

# Function to show console output preview
show_console_preview() {
    echo ""
    echo "============================================================"
    echo "📺 CONSOLE OUTPUT PREVIEW - What you'll see every 10 seconds:"
    echo "============================================================"
    
    current_time=$(date '+%H:%M:%S')
    echo ""
    echo "================================================================================"
    echo "🅿️  [$current_time] AVAILABLE SLOTS: 73/73"
    echo "🔢 Available Slot Numbers: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10... (+63 more)"
    echo "🚗 Occupancy: 0.0%"
    echo "================================================================================"
    echo ""
}

# Function to show system status
show_final_status() {
    echo ""
    echo "🎉 SYSTEM SUCCESSFULLY STARTED!"
    echo "============================================================"
    print_status "Flask API Server: http://127.0.0.1:8000"
    print_status "Local Server: http://127.0.0.1:5000"
    print_status "10-second monitoring: ACTIVE"
    print_status "Parking data: GENERATED"
    echo ""
    echo "📊 API Endpoints Available:"
    echo "   GET  http://127.0.0.1:8000/        - Health check"
    echo "   GET  http://127.0.0.1:8000/stats   - System statistics"
    echo "   POST http://127.0.0.1:8000/process_frame - Process new frame"
    echo ""
    print_warning "Watch your Flask server terminal for 10-second updates!"
    echo ""
    echo "🛑 To stop the system:"
    echo "   pkill -f flask_server.py && pkill -f frame_server.py"
    echo ""
    echo "📊 To check system status anytime:"
    echo "   curl -s http://127.0.0.1:8000/stats | python3 -m json.tool"
    echo ""
    echo "============================================================"
}

# Main execution
main() {
    cd /home/giyu/Desktop/MajorProject
    
    # Step 1: Cleanup
    cleanup_existing
    
    # Step 2: Start Flask server
    start_flask_server
    
    # Step 3: Start Local server  
    start_local_server
    
    # Step 4: Check both servers are running
    print_info "Verifying servers are running..."
    sleep 3
    
    if ! check_server "http://127.0.0.1:8000/" "Flask API Server"; then
        print_error "Flask server failed to start. Check logs: tail /tmp/flask_output.log"
        exit 1
    fi
    
    if ! check_server "http://127.0.0.1:5000/" "Local Server"; then
        print_error "Local server failed to start. Check logs: tail /tmp/local_output.log"
        exit 1
    fi
    
    # Step 5: Start monitoring
    if ! start_monitoring; then
        exit 1
    fi
    
    # Step 6: Process first frame to get parking data
    sleep 2
    if ! process_first_frame; then
        print_warning "Frame processing failed, but monitoring will continue"
    fi
    
    # Step 7: Show preview and final status
    show_console_preview
    show_final_status
    
    # Step 8: Wait and show live monitoring
    print_info "Showing live monitoring for 30 seconds..."
    echo "============================================================"
    
    for i in {1..3}; do
        echo "⏰ Monitoring cycle $i/3 - Check your Flask server console now!"
        sleep 10
    done
    
    print_status "System is running! Check your Flask server terminal for continuous 10-second updates."
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n${YELLOW}⚠️  Script interrupted. Servers are still running.${NC}"; exit 130' INT

# Run main function
main

echo "🏁 Script completed. Servers continue running in background."