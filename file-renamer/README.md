# File Renamer

A cross-platform utility for batch renaming files with sequential numbering and adaptive padding.

## Overview

Sequential File Renamer allows you to easily rename multiple files with a consistent naming pattern. It's perfect for organizing photos, documents, or any collection of files that need sequential naming.

## Features

- **Simple Sequential Renaming**: Rename files to `basename_1.jpg`, `basename_2.jpg`, etc.
- **Adaptive Digit Padding**: Automatically adjusts padding based on file count
  - For 1-9 files: Single digit (e.g., photo_1.jpg)
  - For 10-99 files: Double digits (e.g., photo_01.jpg)
  - For 100-999 files: Triple digits (e.g., photo_001.jpg)
- **Multiple Selection Methods**: 
  - Process an entire directory at once
  - Select specific files to rename
  - Mix files from different folders
- **Additional Options**:
  - Include date stamps (YYYYMMDD format)
  - Filter files by extension

## Installation

### Prerequisites

- Python 3.6 or higher
- Tkinter (usually included with Python)
- Pydantic (automatically installed by the installer)

### Linux

1. Download the installation package
2. Extract the package contents
3. Navigate to the file-renamer directory:
   ```bash
   cd file-renamer
   ```
4. Run the installer script:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

For system-wide installation (requires administrator privileges):
```bash
chmod +x install.sh
sudo ./install.sh
```

To uninstall:
```bash
file-renamer-uninstall
```

Or for system-wide installations:
```bash
sudo file-renamer-uninstall
```

### Windows

1. Download the Windows executable (.exe file)
2. Run the executable to start the application

### Manual Installation Steps

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/file-renamer.git
   ```

2. Navigate to the directory:
   ```bash
   cd file-renamer
   ```

3. Install required dependencies:
   ```bash
   pip install pydantic
   ```

4. Run the application:
   ```bash
   python3 file_renamer.py
   ```

## Usage Guide

### File Selection Methods

1. **Process an Entire Directory**:
   - Click "Browse Directory..." to select a folder
   - All files in the directory will be processed (filtered by extension if specified)
   - Select the "Process entire directory" radio button

2. **Select Specific Files**:
   - Click "Select Files..." to open a file browser
   - Choose one or more files (use Ctrl/Shift for multiple selections)
   - Files will be listed as "X files selected"
   - Select the "Process selected files only" radio button

### Renaming Options

1. **Enter a Base Name**:
   - Type the text you want to use as the base name for all files
   - Example: "photo" will result in "photo_1.jpg", "photo_2.jpg", etc.

2. **Optional Settings**:
   - Include Date: Adds the current date in YYYYMMDD format
   - Filter by Extension: Enter comma-separated extensions (e.g., jpg,png,txt)
     Note: Extension filter only applies in directory mode

3. **Preview changes**: Click "Generate Preview" to see how files will be renamed

4. **Apply changes**: When satisfied, click "Rename Files" to apply the changes

## Examples

```
Original files:          After Sequential Renaming (base name "pic"):
IMG_1234.jpg  →         pic_1.jpg
DSC_9876.jpg  →         pic_2.jpg
photo-123.jpg →         pic_3.jpg
```

With date option enabled:
```
Original files:          After Sequential Renaming (base name "photo"):
IMG_1234.jpg  →         20240311_photo_1.jpg
DSC_9876.jpg  →         20240311_photo_2.jpg
photo-123.jpg →         20240311_photo_3.jpg
```

## Working with Files from Different Folders

You can select files from different folders:

1. Click "Select Files..." and browse to your first folder
2. Select the files you want to rename
3. With the file selection dialog still open, navigate to a different folder
4. Hold Ctrl (or Command on Mac) and select additional files
5. Click "Open" to confirm your selection
6. All selected files will be shown and can be renamed together

Note: When renaming files from different folders, each file will remain in its original folder but will be renamed according to your pattern.

## Troubleshooting

### Common Installation Issues

- **Command not found**: If you get "command not found" errors, make sure your PATH includes the bin directory
- **Missing Python/Tkinter**: Ensure Python 3 and Tkinter are installed on your system
- **Permission errors**: Check if you need to run with sudo for system-wide installation
- **Application doesn't appear in menu**: Try logging out and back in to refresh the application menu

### Runtime Issues

- **File access errors**: Ensure the application has read/write permissions for the selected directory and files
- **No files found**: Make sure you've either selected files or chosen a directory with files in it
- **Cannot rename file**: Check if another application has the file open or locked

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
