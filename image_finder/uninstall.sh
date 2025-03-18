#!/bin/bash

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Define installation directories
INSTALL_DIR="$HOME/.image-similarity-finder"
BIN_DIR="$HOME/.local/bin"
EXECUTABLE="$BIN_DIR/imagesim"

echo -e "${YELLOW}Uninstalling Image Similarity Finder...${NC}"

# Check if installed
if [ ! -d "$INSTALL_DIR" ] && [ ! -f "$EXECUTABLE" ]; then
    echo -e "${RED}Image Similarity Finder doesn't appear to be installed.${NC}"
    exit 1
fi

# Remove executable
if [ -f "$EXECUTABLE" ]; then
    rm "$EXECUTABLE"
    echo -e "${GREEN}Removed executable from $BIN_DIR${NC}"
fi

# Remove installation directory
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo -e "${GREEN}Removed installation directory $INSTALL_DIR${NC}"
fi

echo -e "${GREEN}Image Similarity Finder has been uninstalled successfully.${NC}"

# Optionally ask about Python packages
echo -e "${YELLOW}Note: The Python packages installed by this tool (numpy, pillow, opencv-python, scikit-learn) were not removed.${NC}"
echo -e "${YELLOW}These may be used by other applications. If you want to remove them, you can do so manually.${NC}"
