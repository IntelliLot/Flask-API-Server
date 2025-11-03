#!/bin/bash
# Quick Start Script - Choose Development or Production

echo "=========================================="
echo "  YOLOv8 Parking Detection System"
echo "=========================================="
echo ""
echo "Select environment:"
echo "  1) Development (Port 5001)"
echo "  2) Production (Port 80)"
echo "  3) Exit"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo ""
        echo "Starting Development Environment..."
        ./docker-helper.sh dev-start
        ;;
    2)
        echo ""
        echo "Starting Production Environment..."
        ./docker-helper.sh prod-start
        ;;
    3)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice!"
        exit 1
        ;;
esac
