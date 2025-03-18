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
mkdir -p "$BIN_DIR"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
    exit 1
fi

# Install required packages
echo -e "${YELLOW}Installing required Python packages...${NC}"
python3 -m pip install numpy pillow opencv-python scikit-learn argparse pathlib tk pydantic

# Copy the main script from the same directory
if [ -f "$SCRIPT_DIR/image_finder.py" ]; then
    cp "$SCRIPT_DIR/image_finder.py" "$INSTALL_DIR/"
    echo -e "${GREEN}Copied image_finder.py to $INSTALL_DIR${NC}"
else
    echo -e "${RED}Error: image_finder.py not found in the current directory.${NC}"
    exit 1
fi

# Create wrapper script
cat > "$BIN_DIR/imagesim" << EOF
#!/bin/bash
if [ "$1" == "--gui" ] || [ "$1" == "-g" ]; then
  python3 "$INSTALL_DIR/image_finder.py" --gui
else
  python3 "$INSTALL_DIR/image_finder.py" "\$@"
fi
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

# Create README file
cat > "$INSTALL_DIR/README.md" << 'EOF'
# Image Similarity Finder

A command-line tool to find visually similar images across directories, regardless of size or format.

## Features

- Find images similar to a reference image across multiple directories
- Supports various image formats (JPG, PNG, BMP, TIFF, WebP, GIF)
- Adjustable similarity threshold for more or fewer matches
- Works with different image sizes and aspect ratios

## Installation

Run the installer script:

```bash
./install.sh
```

This will install:
- The required Python packages
- The main script in ~/.image-similarity-finder/
- A command-line executable at ~/.local/bin/imagesim

## Usage

Basic usage:

```bash
imagesim path/to/reference_image.jpg path/to/search/directory
```

Search multiple directories:

```bash
imagesim reference_image.jpg dir1 dir2 dir3
```

Adjust similarity threshold (0-1, where 1 is identical):

```bash
imagesim reference_image.jpg directory --threshold 0.6
```

Limit number of results:

```bash
imagesim reference_image.jpg directory --max-results 5
```

## How It Works

The tool uses computer vision techniques to find similar images:

1. **Feature Extraction**: Converts each image into a numerical representation using Histogram of Oriented Gradients (HOG)
2. **Similarity Comparison**: Uses cosine similarity to compare feature vectors
3. **Result Ranking**: Returns the most similar images sorted by similarity score

## Uninstallation

To uninstall:

```bash
~/.image-similarity-finder/uninstall.sh
```

## Requirements

- Python 3
- Required packages (automatically installed): numpy, pillow, opencv-python, scikit-learn
EOF

# Copy README to current directory as well
cp "$INSTALL_DIR/README.md" "./README.md"

echo -e "${GREEN}Installation complete!${NC}"
echo -e "${YELLOW}Usage: imagesim path/to/reference_image.jpg path/to/search/directory${NC}"
echo -e "${YELLOW}See README.md for more information${NC}"

# Check if $BIN_DIR is in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "${YELLOW}Note: $BIN_DIR is not in your PATH.${NC}"
    echo -e "${YELLOW}Add it to your PATH or use the full path to the executable.${NC}"
    echo -e "${YELLOW}You can add it to your PATH by adding this line to your ~/.bashrc or ~/.zshrc:${NC}"
    echo -e "${YELLOW}export PATH=\"\$PATH:$BIN_DIR\"${NC}"
fi
