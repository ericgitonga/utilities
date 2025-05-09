# MPEG Sorter

A Python utility that identifies and sorts media files based on their actual file signatures rather than extensions.

Copyright © 2025 Eric Gitonga. MIT License.

## Description

MPEG Sorter analyzes files using their binary signatures ("magic bytes") to identify their true file types, regardless of the file extension. It specifically targets MP3 and MP4 files that may have incorrect extensions and organizes them into appropriate directories based on their actual content.

## Features

- **Content-based identification**: Uses file signatures to detect actual file types regardless of extension
- **Automatic correction**: Renames files to match their actual content type
- **Efficient organization**: Sorts files into appropriate audio and video directories
- **Parallel processing**: Uses asynchronous multi-threading for fast processing of large directories
- **Sequential mode option**: Provides single-threaded processing for benchmarking or troubleshooting
- **Unknown file handling**: Automatically moves unrecognized files to a separate directory
- **Verbose logging**: Detailed output of actions performed on each file

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/mpeg-sorter.git
   cd mpeg-sorter
   ```

2. No additional dependencies required beyond Python 3.6+ standard library.

## Usage

```
python mpeg_sorter.py [source_folder] [options]
```

### Options

- `--sequential`: Run in single-threaded mode (slower but useful for debugging)
- `--no-unknown`: Do not create an "unknown" directory for unrecognized files
- `--workers N`: Specify the number of worker threads (default: number of CPU cores)

### Examples

Process all files in the current directory:
```
python mpeg_sorter.py .
```

Process files in a specific directory with parallel processing (default):
```
python mpeg_sorter.py /path/to/media/files
```

Process files sequentially (single-threaded):
```
python mpeg_sorter.py /path/to/media/files --sequential
```

Process files with a specific number of worker threads:
```
python mpeg_sorter.py /path/to/media/files --workers 4
```

## Output

The script creates the following directory structure within the source directory:

```
source_directory/
├── audio/         # All files with audio signatures (.mp3, etc.)
├── video/         # All files with video signatures (.mp4, etc.)
└── unknown/       # Files with unrecognized signatures (optional)
```

Each file is moved to the appropriate directory and renamed if its extension doesn't match its content.

## Testing

The project includes a comprehensive test suite that verifies all functionality:

```
# Run all tests
pytest

# Run specific test in parallel mode
pytest -xvs test_mpeg_sorter_pytest.py::test_parallel_processing

# Run specific test in sequential mode
pytest -xvs test_mpeg_sorter_pytest.py::test_sequential_processing
```

The test framework automatically:
1. Creates a test environment with sample files
2. Runs the sorter in both parallel and sequential modes
3. Verifies correct file sorting and renaming
4. Restores the original file structure for easy re-testing
