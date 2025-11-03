#!/bin/bash
# Simple deployment script for Raspberry Pi

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}🍓 Simple Raspberry Pi Deployment${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""

# Get Raspberry Pi details
read -p "Raspberry Pi IP address: " RASPI_IP
read -p "Username: " RASPI_USER
read -p "Destination folder name [YoloParklot]: " DEST_FOLDER
DEST_FOLDER=${DEST_FOLDER:-YoloParklot}

echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  User: ${GREEN}${RASPI_USER}${NC}"
echo -e "  Host: ${GREEN}${RASPI_IP}${NC}"
echo -e "  Destination: ${GREEN}~/${DEST_FOLDER}/raspi${NC}"
echo ""

# Test connection
echo -e "${YELLOW}Testing connection...${NC}"
if ssh "${RASPI_USER}@${RASPI_IP}" "echo 'Connected'" 2>/dev/null; then
    echo -e "${GREEN}✅ Connection successful${NC}"
else
    echo -e "${RED}❌ Connection failed${NC}"
    exit 1
fi

# Create directory
echo ""
echo -e "${YELLOW}Creating directory...${NC}"
ssh "${RASPI_USER}@${RASPI_IP}" "mkdir -p ~/${DEST_FOLDER}/raspi"
echo -e "${GREEN}✅ Directory created${NC}"

# Copy files
echo ""
echo -e "${YELLOW}Copying files (this may take a moment)...${NC}"

if command -v rsync &> /dev/null; then
    # Use rsync if available
    echo -e "${BLUE}Using rsync...${NC}"
    rsync -avz --progress ./raspi/ "${RASPI_USER}@${RASPI_IP}:~/${DEST_FOLDER}/raspi/"
else
    # Use scp as fallback
    echo -e "${BLUE}Using scp...${NC}"
    scp -r ./raspi "${RASPI_USER}@${RASPI_IP}:~/${DEST_FOLDER}/"
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Files copied successfully${NC}"
else
    echo -e "${RED}❌ Failed to copy files${NC}"
    exit 1
fi

# Set permissions
echo ""
echo -e "${YELLOW}Setting permissions...${NC}"
ssh "${RASPI_USER}@${RASPI_IP}" "cd ~/${DEST_FOLDER}/raspi && chmod +x *.py *.sh 2>/dev/null; mkdir -p logs captured_frames test_captures"
echo -e "${GREEN}✅ Setup complete${NC}"

echo ""
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo "1. SSH into your Raspberry Pi:"
echo -e "   ${YELLOW}ssh ${RASPI_USER}@${RASPI_IP}${NC}"
echo ""
echo "2. Navigate to the folder:"
echo -e "   ${YELLOW}cd ~/${DEST_FOLDER}/raspi${NC}"
echo ""
echo "3. Edit configuration:"
echo -e "   ${YELLOW}nano config.json${NC}"
echo "   Update: api_endpoint, api_key, and camera settings"
echo ""
echo "4. Install dependencies:"
echo -e "   ${YELLOW}./setup.sh${NC}"
echo ""
echo "5. Test cameras:"
echo -e "   ${YELLOW}python3 test_camera.py${NC}"
echo ""
echo "6. Run edge server:"
echo -e "   ${YELLOW}python3 edge_server.py${NC}"
echo ""
