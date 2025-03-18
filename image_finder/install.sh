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
python3 -m pip install numpy pillow opencv-python scikit-learn argparse pathlib

# Copy the main script
cat > "$INSTALL_DIR/image_similarity_finder.py" << 'EOF'
import os
import numpy as np
from PIL import Image
import argparse
from pathlib import Path
import cv2
from sklearn.metrics.pairwise import cosine_similarity


def extract_features(image_path):
    """
    Extract features from an image using a pre-trained CNN model.
    Returns a feature vector that represents the image.
    """
    try:
        # Read the image
        img = cv2.imread(str(image_path))
        if img is None:
            print(f"Warning: Could not read image {image_path}")
            return None
            
        # Resize for consistency
        img = cv2.resize(img, (224, 224))
        
        # Convert to grayscale and extract HOG features
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Use HOG (Histogram of Oriented Gradients) for feature extraction
        win_size = (224, 224)
        block_size = (16, 16)
        block_stride = (8, 8)
        cell_size = (8, 8)
        nbins = 9
        hog = cv2.HOGDescriptor(win_size, block_size, block_stride, cell_size, nbins)
        features = hog.compute(gray)
        
        # Normalize the features
        if np.linalg.norm(features) > 0:
            features = features / np.linalg.norm(features)
            
        return features
        
    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")
        return None


def calculate_similarity(features1, features2):
    """
    Calculate cosine similarity between two feature vectors.
    Returns a value between 0 and 1, where 1 means identical.
    """
    if features1 is None or features2 is None:
        return 0
        
    # Reshape for cosine_similarity function
    f1 = features1.reshape(1, -1)
    f2 = features2.reshape(1, -1)
    
    return cosine_similarity(f1, f2)[0][0]


def find_similar_images(query_image_path, search_dirs, threshold=0.7, max_results=10):
    """
    Find images similar to the query image in the search directories.
    
    Args:
        query_image_path: Path to the query image
        search_dirs: List of directories to search in
        threshold: Similarity threshold (0-1)
        max_results: Maximum number of results to return
        
    Returns:
        List of tuples (image_path, similarity_score) sorted by similarity
    """
    # Extract features from the query image
    query_features = extract_features(query_image_path)
    if query_features is None:
        print(f"Could not process query image: {query_image_path}")
        return []
    
    # List to store results
    results = []
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif'}
    
    # Search through all directories
    for search_dir in search_dirs:
        search_path = Path(search_dir)
        
        # Walk through all files recursively
        for root, _, files in os.walk(search_path):
            for file in files:
                file_path = Path(root) / file
                
                # Skip the query image itself
                if file_path == Path(query_image_path).absolute():
                    continue
                    
                # Check if the file is an image
                if file_path.suffix.lower() in image_extensions:
                    # Extract features from the current image
                    current_features = extract_features(file_path)
                    
                    if current_features is not None:
                        # Calculate similarity
                        similarity = calculate_similarity(query_features, current_features)
                        
                        # Add to results if above threshold
                        if similarity >= threshold:
                            results.append((str(file_path), similarity))
    
    # Sort results by similarity (highest first)
    results.sort(key=lambda x: x[1], reverse=True)
    
    # Return top results
    return results[:max_results]


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Find similar images in directories')
    parser.add_argument('query_image', help='Path to the query image')
    parser.add_argument('search_dirs', nargs='+', help='Directories to search in')
    parser.add_argument('--threshold', type=float, default=0.7, help='Similarity threshold (0-1)')
    parser.add_argument('--max-results', type=int, default=10, help='Maximum number of results')
    
    args = parser.parse_args()
    
    # Find similar images
    results = find_similar_images(
        args.query_image, 
        args.search_dirs,
        args.threshold,
        args.max_results
    )
    
    # Print results
    if not results:
        print("No similar images found.")
    else:
        print(f"Found {len(results)} similar images:")
        for path, score in results:
            print(f"Similarity: {score:.4f} - {path}")


if __name__ == "__main__":
    main()
EOF

# Create wrapper script
cat > "$BIN_DIR/imagesim" << EOF
#!/bin/bash
python3 "$INSTALL_DIR/image_similarity_finder.py" "\$@"
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
