# File Organizer

A Python utility that automatically organizes files by their category with enhanced security, performance, and file management capabilities.

## Overview

File Organizer is a robust Python script that helps you clean up directories with mixed file types. It scans a specified directory, identifies each file's extension, creates a "processed" directory with subdirectories for each file category (Documents, Images, Audio, etc.), and moves files to their corresponding category directories.

## Features

### Security Features
- **Path Traversal Protection**: Prevents unauthorized access outside target directories
- **Enhanced Error Handling**: Implements specific exception handling for different error types
- **Secure Filename Generation**: Creates unique filenames using two-stage conflict resolution
- **Comprehensive Logging**: Maintains detailed logs of all operations and skipped files
- **Skip Filters**: Automatically skips system files, temporary files, and hidden files

### Performance Features
- **Multi-threaded Processing**: Utilizes parallel processing for significantly faster performance
- **Path Object Migration**: Uses Python's pathlib for more efficient path operations
- **Efficient Category Lookup**: Pre-computes extension-to-category mapping for O(1) lookups
- **Progress Tracking**: Shows real-time progress with percentage completion
- **Optimized File Handling**: Balances memory usage and processing speed

### File Management Features
- **File Verification/Integrity Checks**: Verifies files are moved correctly using size and checksum comparison
- **User Permissions Check**: Confirms appropriate permissions before starting operations
- **Dry Run Mode**: Simulates organization without making actual changes
- **Backup Option**: Creates backups before organizing (directory or zip archive)
- **Configurable Categories**: Supports custom category definitions via JSON configuration files
- **Recursive Option**: Process subdirectories or just the top-level directory
- **Centralized Processed Folder**: Places all organized files in a "processed" directory
- **Duplicate Handling**: Prevents overwriting existing files with secure naming
- **Summary Report**: Provides a count of files organized by category and details on skipped files

## Supported Categories (Default)

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

### Dry Run Mode

To simulate organization without making actual changes:

```bash
python file_organizer.py --dry-run
```
or the shorter form:
```bash
python file_organizer.py -d
```

### File Integrity Verification

To verify file integrity (size and checksum) after moving:

```bash
python file_organizer.py --verify-integrity
```
or the shorter form:
```bash
python file_organizer.py -i
```

### Create Backup Before Organizing

To create a backup of files before organizing:

```bash
python file_organizer.py --backup
```
or the shorter form:
```bash
python file_organizer.py -b
```

To create a zip archive backup instead of a directory backup:

```bash
python file_organizer.py --backup --zip-backup
```
or the shorter form:
```bash
python file_organizer.py -b -z
```

### Custom Category Configuration

To use custom file categories defined in a JSON file:

```bash
python file_organizer.py --config category_config.json
```
or the shorter form:
```bash
python file_organizer.py -c category_config.json
```

Example content of `category_config.json`:
```json
{
  "Documents": ["pdf", "doc", "docx", "txt", "rtf"],
  "Images": ["jpg", "jpeg", "png", "gif"],
  "CustomCategory": ["xyz", "abc"]
}
```

### Combining Options

You can combine multiple options:

```bash
python file_organizer.py /path/to/directory -r -y -d -i -b -w 8 -v
```

This would perform a dry run with recursive processing, skip confirmation, enable integrity verification, create a backup, use 8 worker threads, and enable verbose logging.

## Example

```bash
$ python file_organizer.py ~/Downloads --backup --verify-integrity
This will organize all files in '/home/user/Downloads' with integrity verification after creating backup into category subdirectories.
Using 4 worker threads for parallel processing.
Continue? (y/n): y
Creating directory backup at /home/user/file_organizer_backup_a1b2c3d4
Directory backup created successfully
Backup created at: /home/user/file_organizer_backup_a1b2c3d4
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
- **User Permissions Verification**: Confirms read/write access before starting operations
- **File Ownership Check**: Skips files not owned by the current user (e.g., files owned by root)

## Performance Features

- **Parallel Processing**: Utilizes multi-threading to greatly speed up file organization
- **Efficient Path Handling**: Uses Python's pathlib for more efficient path operations
- **Optimized Category Lookup**: Pre-computes extension mappings for O(1) lookups
- **Balanced Progress Reporting**: Provides feedback without excessive logging overhead

## Caution

- **This script moves files**, not copies them. Always ensure you have backups of important data.
- Running the script multiple times might result in nested organization if you run it on a directory that already contains category-based subdirectories.
- Use the `--dry-run` option first if you're unsure about the outcome.
- For extra security, use the `--backup` option to create a backup before organizing.

## License

This project is released under the MIT License. See the LICENSE file for details.

Copyright © 2025 Eric Gitonga. All rights reserved.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please file an issue on the GitHub repository. --verbose
```
or the shorter form:
```bash
python file_organizer.py
