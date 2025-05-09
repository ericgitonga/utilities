## Testing

The MPEG Sorter includes a comprehensive test suite that validates functionality and provides performance benchmarking:

```bash
# Run the standard test script (from project root)
python tests/test_mpeg_sorter.py

# Force command-line script testing (useful if import fails)
python tests/test_mpeg_sorter.py --command-line

# For detailed output
python tests/test_mpeg_sorter.py --verbose
```

### Integration with pytest

For pytest integration, the project includes a dedicated pytest-compatible test file:

```bash
# Run the pytest-specific tests (recommended)
pytest tests/test_mpeg_sorter_pytest.py -v

# Run specific tests only
pytest tests/test_mpeg_sorter_pytest.py::test_command_line_sequential -v

# Run with test selection by keyword
pytest tests/test_mpeg_sorter_pytest.py -v -k "command"
```

The test suite automatically:
- Creates sample media files with various signatures
- Tests both sequential and parallel processing modes
- Validates correct file sorting and extension correction
- Reports performance metrics and speedup comparison
- Restores the test environment after completion

See the Technical Documentation for detailed testing information.

The test suite automatically:
- Creates sample media files with various signatures
- Tests both sequential and parallel processing modes
- Validates correct file sorting and extension correction
- Reports performance metrics and speedup comparison
- Restores the test environment after completion

See the Technical Documentation for detailed testing information.# README

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
- **Parallel processing**: Uses asynchronous execution for significantly faster performance
- **Progress tracking**: Shows real-time progress during file processing
- **Performance metrics**: Reports processing speed and operation statistics
- **Benchmarking mode**: Includes sequential processing option for performance comparison

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
- `--no-unknown`: Do not create an "unknown" subdirectory (by default, unknown files are moved to an "unknown" folder)
- `--workers`: Maximum number of concurrent workers to use (default: uses CPU count)
- `--sequential`: Use single-threaded sequential processing (for benchmarking)

## Examples

```bash
# Sort all files in the current directory
python mpeg_sorter.py .

# Sort files in a specific directory but skip unknown file types
python mpeg_sorter.py ~/Music/unsorted --no-unknown

# Process files with a specific number of worker threads
python mpeg_sorter.py ~/Music/large_collection --workers 8

# Run in single-threaded mode for benchmarking
python mpeg_sorter.py ~/Music/benchmark_folder --sequential
```

## Output

The script will:
1. Create `audio/`, `video/`, and `unknown/` subdirectories in the specified folder
2. Analyze each file to determine its actual type
3. Move files to the appropriate subdirectory using parallel processing
4. Correct file extensions if they don't match the content
5. Show real-time progress for large operations
6. Print a detailed summary with performance metrics
7. Report statistics including processing speed (files per second)
