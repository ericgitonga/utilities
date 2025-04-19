# File Organizer

A Python utility that automatically organizes files by their category.

## Overview

File Organizer is a simple yet powerful Python script that helps you clean up directories with mixed file types. It scans a specified directory, identifies each file's extension, creates a "processed" directory with subdirectories for each file category (Documents, Images, Audio, etc.), and moves files to their corresponding category directories.

## Features

- **Automatic Category Organization**: Organizes files into meaningful categories rather than by individual extensions
- **Recursive Option**: Choose whether to process subdirectories or just the top-level directory
- **Centralized Processed Folder**: Places all organized files in a "processed" directory
- **Custom Directory Support**: Specify any directory to organize
- **Duplicate Handling**: Automatically adds suffixes to prevent overwriting existing files
- **Progress Tracking**: Shows real-time feedback on files being moved
- **Summary Report**: Provides a count of files organized by category
- **User Confirmation**: Asks for confirmation before proceeding with file operations
- **No-Extension Handling**: Places files without extensions in the "Misc" directory
- **Self-Preservation**: Skips the script itself to avoid disrupting execution
- **Circular Processing Prevention**: Avoids re-processing files in the "processed" directory
- **Command-Line Arguments**: Supports various options through command-line flags

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

### Combining Options

You can combine options as needed:

```bash
python file_organizer.py /path/to/directory -r -y
```

### Example

```bash
$ python file_organizer.py ~/Downloads
This will organize all files in '/home/user/Downloads' into category subdirectories.
Continue? (y/n): y
Moved: document.pdf -> processed/Documents/document.pdf
Moved: image.jpg -> processed/Images/image.jpg
Moved: presentation.pptx -> processed/Documents/presentation.pptx
...

Organization complete!
Summary of files organized:
  Archives: 4 file(s)
  Documents: 12 file(s)
  Images: 15 file(s)
  Misc: 2 file(s)
  Video: 3 file(s)
```

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
