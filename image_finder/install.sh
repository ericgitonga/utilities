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

# Clean any previous installation
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Removing previous installation...${NC}"
    rm -rf "$INSTALL_DIR"
fi

# Create directories
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

# Create package structure
echo -e "${YELLOW}Creating package structure...${NC}"

# Create __init__.py
cat > "$INSTALL_DIR/imagesim/__init__.py" << 'EOF'
"""
Image Similarity Finder

A tool that finds visually similar images across directories using computer vision techniques.
"""

__version__ = "1.0.0"
__author__ = "Eric Gitonga"
EOF

# Copy Python modules
echo -e "${YELLOW}Copying Python modules...${NC}"
cp "$SCRIPT_DIR/models.py" "$INSTALL_DIR/imagesim/"
cp "$SCRIPT_DIR/analyzer.py" "$INSTALL_DIR/imagesim/"
cp "$SCRIPT_DIR/finder.py" "$INSTALL_DIR/imagesim/"
cp "$SCRIPT_DIR/gui.py" "$INSTALL_DIR/imagesim/"

# Create __main__.py file
cat > "$INSTALL_DIR/imagesim/__main__.py" << 'EOF'
"""
Image Similarity Finder - Main Package Entry Point

This allows the package to be executed directly:
python -m imagesim

It directly contains the main functionality rather than importing
to avoid potential import issues.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# These imports will be relative to the installation directory
from imagesim.models import SearchConfig
from imagesim.finder import ImageSimilarityFinder
import imagesim.gui as gui_module


def parse_cli_args() -> Optional[SearchConfig]:
    """
    Parse command line arguments and create a SearchConfig.
    
    This function parses the command line arguments and creates a SearchConfig
    object if valid arguments are provided.
    
    Returns:
        Optional[SearchConfig]: SearchConfig object if valid CLI args, None otherwise
    """
    parser = argparse.ArgumentParser(
        description='Find similar images across directories',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('query_image', nargs='?', 
                        help='Path to the query image')
    parser.add_argument('search_dirs', nargs='*', 
                        help='Directories to search in')
    parser.add_argument('--threshold', type=float, default=0.7, 
                        help='Similarity threshold (0-1)')
    parser.add_argument('--max-results', type=int, default=10, 
                        help='Maximum number of results')
    parser.add_argument('--gui', '-g', action='store_true', 
                        help='Start in GUI mode')
    
    args = parser.parse_args()
    
    # Check if GUI mode is requested
    if args.gui or (not args.query_image and not args.search_dirs):
        return None
        
    # Validate and create config if CLI mode
    if args.query_image and args.search_dirs:
        try:
            config = SearchConfig(
                query_image=args.query_image,
                search_dirs=args.search_dirs,
                threshold=args.threshold,
                max_results=args.max_results
            )
            return config
        except Exception as e:
            print(f"Error in configuration: {str(e)}")
            parser.print_help()
            sys.exit(1)
    else:
        # Print help if not enough arguments for CLI mode
        parser.print_help()
        sys.exit(1)


def run_cli(config: SearchConfig) -> None:
    """
    Run the finder in CLI mode with the provided config.
    
    This function creates an ImageSimilarityFinder with the provided config,
    runs the search, and prints the results to the console.
    
    Args:
        config (SearchConfig): Configuration for the search
    """
    print(f"Searching for images similar to: {config.query_image}")
    print(f"Search directories: {', '.join(str(d) for d in config.search_dirs)}")
    print(f"Similarity threshold: {config.threshold}")
    print(f"Maximum results: {config.max_results}")
    print("\nSearching...")
    
    # Create finder and run search
    finder = ImageSimilarityFinder(config)
    results = finder.find_similar_images()
    
    # Print results
    if not results:
        print("\nNo similar images found.")
    else:
        print(f"\nFound {len(results)} similar images:")
        print("-" * 80)
        print(f"{'Similarity':^12} | {'Image Path'}")
        print("-" * 80)
        
        for result in results:
            print(f"{result.similarity:^12.4f} | {result.path}")


def main():
    """Main entry point for the application."""
    config = parse_cli_args()
    
    if config is None:
        # Start GUI
        gui_module.launch_gui()
    else:
        # Run CLI mode
        run_cli(config)


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

# Copy readme to installation directory
cp "$SCRIPT_DIR/readme.md" "$INSTALL_DIR/"

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
