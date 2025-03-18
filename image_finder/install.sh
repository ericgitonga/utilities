#!/bin/bash

set -e

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Define installation directory
INSTALL_DIR="$HOME/.image-similarity-finder"
BIN_DIR="$HOME/.local/bin"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${YELLOW}Installing Image Similarity Finder...${NC}"

# Create directories if they don't exist
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/imagesim"
mkdir -p "$BIN_DIR"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
    exit 1
fi

# Install required packages
echo -e "${YELLOW}Installing required Python packages...${NC}"
python3 -m pip install numpy pillow opencv-python scikit-learn pydantic

# Copy the Python modules
echo -e "${YELLOW}Copying Python modules...${NC}"
cp "$SCRIPT_DIR/models.py" "$INSTALL_DIR/imagesim/"
cp "$SCRIPT_DIR/analyzer.py" "$INSTALL_DIR/imagesim/"
cp "$SCRIPT_DIR/finder.py" "$INSTALL_DIR/imagesim/"
cp "$SCRIPT_DIR/gui.py" "$INSTALL_DIR/imagesim/"
cp "$SCRIPT_DIR/cli.py" "$INSTALL_DIR/imagesim/"
cp "$SCRIPT_DIR/main.py" "$INSTALL_DIR/imagesim/"
cp "$SCRIPT_DIR/__init__.py" "$INSTALL_DIR/imagesim/"

# Create __main__.py file
cat > "$INSTALL_DIR/imagesim/__main__.py" << 'EOF'
"""
Image Similarity Finder - Main Module

This allows the package to be executed directly:
python -m imagesim

It simply imports and calls the main function from the main module.
"""

from imagesim.main import main

if __name__ == "__main__":
    main()
EOF

# Create wrapper script
cat > "$BIN_DIR/imagesim" << EOF
#!/bin/bash
PYTHONPATH="$INSTALL_DIR" python3 -m imagesim "\$@"
EOF

# Make the wrapper script executable
chmod +x "$BIN_DIR/imagesim"

# Create uninstaller
cat > "$INSTALL_DIR/uninstall.sh" << EOF
#!/bin/bash

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "\${YELLOW}Uninstalling Image Similarity Finder...${NC}"

# Remove binary
if [ -f "$BIN_DIR/imagesim" ]; then
    rm "$BIN_DIR/imagesim"
    echo -e "\${GREEN}Removed executable from $BIN_DIR${NC}"
fi

# Remove installation directory
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo -e "\${GREEN}Removed installation directory $INSTALL_DIR${NC}"
fi

echo -e "\${GREEN}Image Similarity Finder has been uninstalled successfully.${NC}"
EOF

# Make uninstaller executable
chmod +x "$INSTALL_DIR/uninstall.sh"

# Copy README to installation directory
cp "$SCRIPT_DIR/README.md" "$INSTALL_DIR/"

echo -e "${GREEN}Installation complete!${NC}"
echo -e "${YELLOW}Usage: imagesim path/to/reference_image.jpg path/to/search/directory${NC}"
echo -e "${YELLOW}       imagesim --gui (or just imagesim with no arguments for GUI mode)${NC}"
echo -e "${YELLOW}See README.md for more information${NC}"

# Check if $BIN_DIR is in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "${YELLOW}Note: $BIN_DIR is not in your PATH.${NC}"
    echo -e "${YELLOW}Add it to your PATH or use the full path to the executable.${NC}"
    echo -e "${YELLOW}You can add it to your PATH by adding this line to your ~/.bashrc or ~/.zshrc:${NC}"
    echo -e "${YELLOW}export PATH=\"\$PATH:$BIN_DIR\"${NC}"
fi
