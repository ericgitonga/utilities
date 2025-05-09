# README

Copyright © 2025 Eric Gitonga. All rights reserved.  
This document is licensed under the MIT License.

## Description

MPEG Sorter analyzes files using their binary signatures ("magic bytes") to identify their true file types, regardless of their file extensions. It then sorts the files into appropriate subdirectories and corrects any mismatched extensions.

Specifically designed to handle:
- MP3 files incorrectly saved with `.mp4` extensions
- MP4 files incorrectly saved with `.mp3` extensions
- Properly labeled media files that just need organization

## Features

- **Signature-based identification**: Uses file headers rather than extensions to determine file types
- **Automatic sorting**: Moves files to appropriate subdirectories (`audio/` or `video/`)
- **Extension correction**: Renames files to match their actual content type (`.mp3` or `.mp4`)
- **Conflict resolution**: Handles duplicate filenames automatically
- **Detailed logging**: Provides clear feedback about each operation

## Installation

No additional dependencies are required beyond the Python standard library.

```bash
# Clone the repository (or download the script)
git clone https://github.com/yourusername/mpeg-sorter.git
cd mpeg-sorter

# Make the script executable
chmod +x mpeg_sorter.py
```

## Usage

```bash
python mpeg_sorter.py /path/to/your/media/folder [--unknown]
```

### Options

- `folder`: Path to the directory containing the media files to sort (required)
- `--unknown`: Creates an "unknown" subdirectory for files that can't be identified (optional)

## Examples

```bash
# Sort all files in the current directory
python mpeg_sorter.py .

# Sort files in a specific directory and handle unknown file types
python mpeg_sorter.py ~/Music/unsorted --unknown
```

## Output

The script will:
1. Create `audio/` and `video/` subdirectories in the specified folder
2. Analyze each file to determine its actual type
3. Move files to the appropriate subdirectory
4. Correct file extensions if they don't match the content
5. Print a summary of the operations performed
