#!/bin/bash
# Deploy raspi folder to Raspberry Pi

# Configuration
RASPI_USER="${RASPI_USER:-pi}"
RASPI_HOST="${RASPI_HOST}"
RASPI_PORT="${RASPI_PORT:-22}"
RASPI_PATH="${RASPI_PATH:-~/YoloParklot}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}🍓 Raspberry Pi Deployment Script${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""

# Check if RASPI_HOST is set
if [ -z "$RASPI_HOST" ]; then
    echo -e "${YELLOW}Please enter Raspberry Pi details:${NC}"
    read -p "Raspberry Pi IP address: " RASPI_HOST
    read -p "Username [pi]: " input_user
    RASPI_USER=${input_user:-pi}
    read -p "SSH Port [22]: " input_port
    RASPI_PORT=${input_port:-22}
    read -p "Destination path [~/YoloParklot]: " input_path
    RASPI_PATH=${input_path:-~/YoloParklot}
fi

echo ""
echo -e "${BLUE}Deployment Configuration:${NC}"
echo -e "  Host: ${GREEN}${RASPI_USER}@${RASPI_HOST}:${RASPI_PORT}${NC}"
echo -e "  Path: ${GREEN}${RASPI_PATH}${NC}"
echo ""

# Test SSH connection
echo -e "${YELLOW}Testing SSH connection...${NC}"
if ssh -p "$RASPI_PORT" -o ConnectTimeout=5 "${RASPI_USER}@${RASPI_HOST}" "echo 'Connection successful'" 2>/dev/null; then
    echo -e "${GREEN}✅ SSH connection successful${NC}"
else
    echo -e "${RED}❌ Failed to connect to Raspberry Pi${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check if SSH is enabled on Raspberry Pi: sudo raspi-config"
    echo "2. Verify IP address: ping ${RASPI_HOST}"
    echo "3. Check firewall settings"
    echo "4. Ensure SSH key is set up or password is correct"
    exit 1
fi

echo ""
echo -e "${YELLOW}Creating destination directory...${NC}"
# Use quotes to handle paths with spaces and ~ expansion
ssh -p "$RASPI_PORT" "${RASPI_USER}@${RASPI_HOST}" "mkdir -p \"${RASPI_PATH}/raspi\""
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Directory created${NC}"
else
    echo -e "${RED}❌ Failed to create directory${NC}"
    echo -e "${YELLOW}Trying with sudo...${NC}"
    ssh -p "$RASPI_PORT" "${RASPI_USER}@${RASPI_HOST}" "sudo mkdir -p \"${RASPI_PATH}/raspi\" && sudo chown -R ${RASPI_USER}:${RASPI_USER} \"${RASPI_PATH}\""
    if [ $? -ne 0 ]; then
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}Copying raspi folder to Raspberry Pi...${NC}"
echo -e "${BLUE}This may take a few moments...${NC}"

# Copy the entire raspi folder using rsync or scp
if command -v rsync &> /dev/null; then
    echo -e "${BLUE}Using rsync for better performance...${NC}"
    if rsync -avz -e "ssh -p ${RASPI_PORT}" ./raspi/ "${RASPI_USER}@${RASPI_HOST}:${RASPI_PATH}/raspi/"; then
        echo -e "${GREEN}✅ Files copied successfully${NC}"
    else
        echo -e "${RED}❌ Failed to copy files${NC}"
        exit 1
    fi
else
    # Fallback to scp
    if scp -P "$RASPI_PORT" -r ./raspi "${RASPI_USER}@${RASPI_HOST}:${RASPI_PATH}/"; then
        echo -e "${GREEN}✅ Files copied successfully${NC}"
    else
        echo -e "${RED}❌ Failed to copy files${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}Setting permissions...${NC}"
ssh -p "$RASPI_PORT" "${RASPI_USER}@${RASPI_HOST}" "cd \"${RASPI_PATH}/raspi\" && chmod +x *.py *.sh 2>/dev/null || true"
echo -e "${GREEN}✅ Permissions set${NC}"

echo ""
echo -e "${YELLOW}Creating required directories...${NC}"
ssh -p "$RASPI_PORT" "${RASPI_USER}@${RASPI_HOST}" "cd \"${RASPI_PATH}/raspi\" && mkdir -p logs captured_frames test_captures"
echo -e "${GREEN}✅ Directories created${NC}"

echo ""
echo -e "${GREEN}=================================================${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${GREEN}=================================================${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. SSH into your Raspberry Pi:"
echo -e "   ${YELLOW}ssh -p ${RASPI_PORT} ${RASPI_USER}@${RASPI_HOST}${NC}"
echo ""
echo "2. Navigate to the raspi folder:"
echo -e "   ${YELLOW}cd ${RASPI_PATH}/raspi${NC}"
echo ""
echo "3. Edit configuration:"
echo -e "   ${YELLOW}nano config.json${NC}"
echo "   Update: api_endpoint, api_key, device_id, and camera settings"
echo ""
echo "4. Run setup (optional - installs dependencies):"
echo -e "   ${YELLOW}./setup.sh${NC}"
echo ""
echo "5. Test cameras:"
echo -e "   ${YELLOW}python3 test_camera.py${NC}"
echo ""
echo "6. Start edge server:"
echo -e "   ${YELLOW}python3 edge_server.py${NC}"
echo ""
echo "7. Or setup as service (runs automatically on boot):"
echo -e "   ${YELLOW}sudo cp edge_server.service /etc/systemd/system/${NC}"
echo -e "   ${YELLOW}sudo systemctl enable edge_server${NC}"
echo -e "   ${YELLOW}sudo systemctl start edge_server${NC}"
echo ""
