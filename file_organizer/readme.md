# File Organizer

A Python utility that automatically organizes files by their category with enhanced security and performance.

## Overview

File Organizer is a robust Python script that helps you clean up directories with mixed file types. It scans a specified directory, identifies each file's extension, creates a "processed" directory with subdirectories for each file category (Documents, Images, Audio, etc.), and moves files to their corresponding category directories.

## Features

- **Automatic Category Organization**: Organizes files into meaningful categories rather than by individual extensions
- **Multi-threaded Processing**: Utilizes parallel processing for significantly faster performance
- **Enhanced Security**: Protects against path traversal vulnerabilities and provides secure filename handling
- **Comprehensive Logging**: Maintains detailed logs of all operations and skipped files
- **Recursive Option**: Choose whether to process subdirectories or just the top-level directory
- **Centralized Processed Folder**: Places all organized files in a "processed" directory
- **Custom Directory Support**: Specify any directory to organize
- **Duplicate Handling**: Uses advanced algorithms to prevent overwriting existing files
- **Progress Tracking**: Shows real-time progress with percentage completion
- **Summary Report**: Provides a count of files organized by category and details on skipped files
- **User Confirmation**: Asks for confirmation before proceeding with file operations
- **Skip Filters**: Automatically skips system files, temporary files, and hidden files
- **Self-Preservation**: Skips the script itself to avoid disrupting execution
- **Circular Processing Prevention**: Avoids re-processing files in the "processed" directory
- **Enhanced Command-Line Arguments**: Supports various options through command-line flags including worker threads

## Supported Categories

Files are organized into the following categories:

- **Documents**: PDF, DOC, DOCX, TXT, RTF, ODT, MD, CSV, XLS, XLSX, PPT, PPTX
- **Images**: JPG, JPEG, PNG, GIF, BMP, TIFF, WEBP, SVG, ICO, HEIC, PSD, DNG, NEF
- **Audio**: MP3, WAV, OGG, FLAC, AAC, M4A
- **Video**: MP4, AVI, MKV, MOV, WMV, FLV, WEBM
- **Archives**: ZIP, RAR, TAR, GZ, 7Z
- **Code**: PY, JS, HTML, CSS, JAVA, C, CPP, GO, RS, PHP, RB, IPYNB, JAR
- **Misc**: Any other file type or files without an extension

## Installation

No installation required! Simply download the `file_organizer.py` script to your computer.

### Requirements

- Python 3.6 or higher
- Standard library modules only (no external dependencies)

## Usage

### Basic Usage

To organize files in your current directory (non-recursive, only processes files in the current directory):

```bash
python file_organizer.py
```

### Specifying a Directory

To organize files in a specific directory (non-recursive):

```bash
python file_organizer.py /path/to/directory
```

### Recursive Processing

To process files in a directory and all its subdirectories:

```bash
python file_organizer.py /path/to/directory --recursive
```
or the shorter form:
```bash
python file_organizer.py /path/to/directory -r
```

### Skip Confirmation

To skip the confirmation prompt and proceed immediately:

```bash
python file_organizer.py --yes
```
or the shorter form:
```bash
python file_organizer.py -y
```

### Control Parallel Processing

To specify the number of worker threads for parallel processing:

```bash
python file_organizer.py --workers 8
```
or the shorter form:
```bash
python file_organizer.py -w 8
```

### Verbose Logging

To get more detailed logs:

```bash
python file_organizer.py --verbose
```
or the shorter form:
```bash
python file_organizer.py -v
```

### Combining Options

You can combine options as needed:

```bash
python file_organizer.py /path/to/directory -r -y -w 8 -v
```

### Example

```bash
$ python file_organizer.py ~/Downloads
This will organize all files in '/home/user/Downloads' into category subdirectories.
Using 4 worker threads for parallel processing.
Continue? (y/n): y
Found 36 files to process
Progress: 10/36 files processed (27%)
Progress: 20/36 files processed (55%)
Progress: 30/36 files processed (83%)
Progress: 36/36 files processed (100%)

Organization complete!
Summary of files organized:
  Archives: 4 file(s)
  Documents: 12 file(s)
  Images: 15 file(s)
  Misc: 2 file(s)
  Video: 3 file(s)

Skipped files:
  /home/user/Downloads/.DS_Store - Reason: system or temporary file
  /home/user/Downloads/desktop.ini - Reason: in skip list
```

## Security Features

- **Path Traversal Protection**: Validates that all file operations remain within the intended directory
- **Permission Checking**: Detects and handles permission-related errors properly
- **Secure Filename Generation**: Uses advanced techniques to handle filename conflicts
- **Skip Filters**: Automatically skips potentially problematic system and temporary files

## Performance Features

- **Parallel Processing**: Utilizes multi-threading to greatly speed up file organization
- **Efficient Path Handling**: Uses Python's pathlib for more efficient path operations
- **Optimized Category Lookup**: Pre-computes extension mappings for O(1) lookups

## Caution

- **This script moves files**, not copies them. Always ensure you have backups of important data.
- Running the script multiple times might result in nested organization if you run it on a directory that already contains category-based subdirectories.

## License

This project is released under the MIT License. See the LICENSE file for details.

Copyright © 2025 Eric Gitonga. All rights reserved.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please file an issue on the GitHub repository.
