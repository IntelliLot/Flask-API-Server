#!/bin/bash
# Live Output Viewer for Parking Detection System

echo "🎯 PARKING DETECTION SYSTEM - LIVE OUTPUT VIEWER"
echo "============================================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if servers are running
check_system() {
    if curl -s http://127.0.0.1:8000/ > /dev/null 2>&1; then
        print_status "Flask API Server (port 8000) is running"
    else
        print_warning "Flask API Server is not running"
        echo "Run: ./start_complete_system.sh first"
        exit 1
    fi
    
    if curl -s http://127.0.0.1:5000/ > /dev/null 2>&1; then
        print_status "Local Server (port 5000) is running"
    else
        print_warning "Local Server is not running"
    fi
}

# Show where outputs are located
show_output_locations() {
    echo ""
    echo "📂 OUTPUT LOCATIONS:"
    echo "============================================================="
    echo "🔹 Flask Server Output:  /tmp/flask_output.log"
    echo "🔹 Local Server Output:  /tmp/local_output.log"
    echo ""
}

# Show live console commands
show_commands() {
    echo "📋 COMMANDS TO VIEW LIVE OUTPUT:"
    echo "============================================================="
    echo "1️⃣  View Flask Server Console (10-second parking updates):"
    echo "   tail -f /tmp/flask_output.log"
    echo ""
    echo "2️⃣  View Local Server Console:"
    echo "   tail -f /tmp/local_output.log"
    echo ""
    echo "3️⃣  View Both Outputs Side by Side:"
    echo "   # Terminal 1: tail -f /tmp/flask_output.log"
    echo "   # Terminal 2: tail -f /tmp/local_output.log"
    echo ""
    echo "4️⃣  Check System Status:"
    echo "   curl -s http://127.0.0.1:8000/stats | python3 -m json.tool"
    echo ""
}

# Show current parking status
show_current_status() {
    echo "📊 CURRENT PARKING STATUS:"
    echo "============================================================="
    status=$(curl -s http://127.0.0.1:8000/stats)
    if echo "$status" | grep -q "available_slots"; then
        available=$(echo "$status" | grep -o '"available_slots":[0-9]*' | cut -d':' -f2)
        monitoring=$(echo "$status" | grep -o '"status_monitoring_active":[a-z]*' | cut -d':' -f2)
        
        print_status "Available Slots: $available/73"
        print_status "Monitoring Active: $monitoring"
        print_info "All parking slots are currently available"
    else
        print_warning "Could not retrieve parking status"
    fi
    echo ""
}

# Main function
main() {
    check_system
    show_output_locations
    show_current_status
    show_commands
    
    echo "🎬 STARTING LIVE OUTPUT VIEWER..."
    echo "============================================================="
    print_info "Press Ctrl+C to stop viewing"
    print_warning "This will show Flask server output with 10-second parking updates"
    echo ""
    
    # Show live Flask output
    if [ -f "/tmp/flask_output.log" ]; then
        tail -f /tmp/flask_output.log
    else
        echo "❌ Flask output log not found. Run ./start_complete_system.sh first"
        exit 1
    fi
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n${YELLOW}👋 Live output viewer stopped. Servers continue running.${NC}"; exit 0' INT

# Run main function
main