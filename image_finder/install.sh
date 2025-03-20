#!/bin/bash

set -e

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Installing Image Similarity Finder...${NC}"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use pip to install the package
echo -e "${YELLOW}Installing package with pip...${NC}"
pip install -e "$SCRIPT_DIR"

echo -e "${GREEN}Installation complete!${NC}"
echo -e "${YELLOW}Usage: imagesim path/to/reference_image.jpg path/to/search/directory${NC}"
echo -e "${YELLOW}       imagesim --gui (or just imagesim with no arguments for GUI mode)${NC}"
echo -e "${YELLOW}See README.md for more information${NC}"

# Check if the Python scripts directory is in PATH
PYTHON_BIN_DIR=$(python -c "import sys; print(sys.prefix + '/bin')")
if [[ ":$PATH:" != *":$PYTHON_BIN_DIR:"* ]]; then
    echo -e "${YELLOW}Note: $PYTHON_BIN_DIR is not in your PATH.${NC}"
    echo -e "${YELLOW}Add it to your PATH or use the full path to the executable.${NC}"
    echo -e "${YELLOW}You can add it to your PATH by adding this line to your ~/.bashrc or ~/.zshrc:${NC}"
    echo -e "${YELLOW}export PATH=\"\$PATH:$PYTHON_BIN_DIR\"${NC}"
fi
