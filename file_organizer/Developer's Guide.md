# File Organizer - Developer's Guide

This document provides detailed information for developers who want to understand, modify, or extend the enhanced File Organizer script.

## Project Structure

The File Organizer project now follows a modular package structure to improve maintainability and readability:

```
file_organizer/
├── file_organizer.py          # Main entry point with main() function
├── utils/                     # Utils package
│   ├── __init__.py            # Package initialization
│   ├── file_operations.py     # File operations like move, copy, verify integrity
│   ├── path_utils.py          # Path-related utilities - safe path, secure filename
│   ├── categories.py          # Category-related functions and default definitions
│   ├── permissions.py         # Permission checking functions
│   ├── backup.py              # Backup creation functionality
│   └── logging_config.py      # Logging configuration
└── logs/                      # Log directory (created at runtime with timestamped logs)
```

## Module Functionality

### 1. `file_organizer.py`

The main entry point containing the `organize_files_by_category` function and the `main()` function that handles command-line arguments. This file imports functionality from the utils package.

```python
def organize_files_by_category(
    source_dir: Path,
    recursive: bool = True,
    max_workers: int = 4,
    dry_run: bool = False,
    verify_integrity: bool = False,
    create_backup_before: bool = False,
    zip_backup: bool = False,
    config_file: Path = None,
) -> None:
    """
    Organize files in the source directory by their file category.
    Uses parallel processing for better performance with large directories.
    """

def main():
    """Main entry point for the file organizer."""
    # Parse command-line arguments and call organize_files_by_category
```

### 2. `utils/__init__.py`

The initialization file for the utils package, which exports all the necessary functions for importing in the main file:

```python
from utils.file_operations import process_file, verify_file_integrity
from utils.path_utils import is_safe_path, get_secure_filename, should_skip_file
from utils.categories import get_file_category, load_category_config, build_extension_mapping, DEFAULT_EXTENSION_CATEGORIES
from utils.permissions import check_file_permissions, check_user_permissions
from utils.backup import create_backup
from utils.logging_config import setup_logging

__all__ = [
    'process_file',
    'verify_file_integrity',
    'is_safe_path',
    'get_secure_filename',
    'should_skip_file',
    'get_file_category',
    'load_category_config',
    'build_extension_mapping',
    'DEFAULT_EXTENSION_CATEGORIES',
    'check_file_permissions',
    'check_user_permissions',
    'create_backup',
    'setup_logging',
]
```

### 3. `utils/file_operations.py`

Handles core file operations including processing individual files and verifying file integrity:

```python
def verify_file_integrity(source_file: Path, dest_file: Path) -> Tuple[bool, str]:
    """Verify file integrity after moving by comparing file size and checksum."""

def process_file(args: Tuple[Path, Path, Path, Set[str], Dict[str, str], Dict]) -> Union[Tuple[str, str], Tuple[str, Path, str]]:
    """Process a single file (for parallel execution)."""
```

### 4. `utils/path_utils.py`

Provides utilities for path handling, safe path verification, and secure filename generation:

```python
def is_safe_path(base_dir: Union[str, Path], path: Union[str, Path]) -> bool:
    """Verify that a path is safe to access (within the base directory)."""

def get_secure_filename(base_path: Union[str, Path], filename: str) -> Path:
    """Generate a secure filename that doesn't exist at the destination."""

def should_skip_file(filename: str) -> Tuple[bool, str]:
    """Check if a file should be skipped based on patterns."""
```

### 5. `utils/categories.py`

Contains category-related functionality, including default categories and configuration loading:

```python
DEFAULT_EXTENSION_CATEGORIES = {
    "Documents": ["pdf", "doc", "docx", "txt", "rtf", "odt", "md", "csv", "xls", "xlsx", "ppt", "pptx"],
    # Other categories...
}

def get_file_category(extension: str, category_mapping: Dict[str, str]) -> str:
    """Determine the category of a file based on its extension."""

def load_category_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, List[str]]:
    """Load category configuration from a JSON file."""

def build_extension_mapping(categories: Dict[str, List[str]]) -> Dict[str, str]:
    """Build a lookup dictionary for fast extension to category mapping."""
```

### 6. `utils/permissions.py`

Handles permission checking for files and directories:

```python
def check_file_permissions(file_path: Path) -> Tuple[bool, str]:
    """Check if the user has read and write permissions for a specific file."""

def check_user_permissions(directory: Union[str, Path]) -> bool:
    """Check if the user has read and write permissions for the directory."""
```

### 7. `utils/backup.py`

Provides functionality for creating backups:

```python
def create_backup(source_dir: Union[str, Path], zip_backup: bool = False) -> Optional[Path]:
    """Create a backup of the files to be organized."""
```

### 8. `utils/logging_config.py`

Configures logging with timestamped log files in a dedicated directory:

```python
def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging for the file organizer application."""
```

## Code Flow

The high-level flow of the application remains the same, but now with improved modularity:

1. Parse command-line arguments in `main()`
2. Setup logging using `setup_logging()`
3. Call `organize_files_by_category()` with parsed arguments
4. If requested, create a backup using `create_backup()`
5. Load category configuration using `load_category_config()`
6. Create a mapping of extensions to categories using `build_extension_mapping()`
7. Scan for files to process (recursively or non-recursively)
8. Process files in parallel using `concurrent.futures.ThreadPoolExecutor`
9. For each file, call `process_file()` which:
   - Checks if the file should be skipped
   - Verifies path safety using `is_safe_path()`
   - Checks file permissions using `check_file_permissions()`
   - Determines the file category using `get_file_category()`
   - Generates a secure destination path using `get_secure_filename()`
   - Moves the file (with optional integrity verification via `verify_file_integrity()`)
10. Display a summary of the organization results

## Customization Points

The modular structure facilitates easy customization of the application:

### 1. Adding New File Categories

To add or modify file categories, you can:

1. Update the `DEFAULT_EXTENSION_CATEGORIES` dictionary in `utils/categories.py`
2. Create a custom JSON configuration file and use it with the `--config` option

### 2. Implementing New Skip Filters

To add new file skipping criteria:

1. Modify the `should_skip_file()` function in `utils/path_utils.py`

### 3. Enhancing Security Checks

To add additional security measures:

1. Modify `is_safe_path()` in `utils/path_utils.py`
2. Enhance `check_file_permissions()` or `check_user_permissions()` in `utils/permissions.py`

### 4. Adding New Backup Formats

To support additional backup formats:

1. Modify the `create_backup()` function in `utils/backup.py`

### 5. Extending Command-Line Options

To add new command-line options:

1. Modify the argument parser in the `main()` function in `file_organizer.py`
2. Update the `organize_files_by_category()` function to handle the new options

## Feature Implementation Details

### 1. Logging System

The logging system now creates timestamped log files in a dedicated `logs` directory:

```python
def setup_logging(verbose: bool = False) -> logging.Logger:
    # Create a logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create a timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"file_organizer_{timestamp}.log"
    
    # Configure logging
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure logger
    logger = logging.getLogger("file_organizer")
    logger.setLevel(level)
    
    # Add handlers for file and console output
    # ...
```

### 2. File Integrity Verification

The file verification system is implemented in `utils/file_operations.py` and uses a two-stage approach:

```python
def verify_file_integrity(source_file: Path, dest_file: Path) -> Tuple[bool, str]:
    try:
        # First check if file sizes match (fast)
        if source_file.stat().st_size != dest_file.stat().st_size:
            return False, "File sizes don't match"
            
        # Then calculate MD5 checksum for both files (more thorough)
        def calculate_checksum(file_path):
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
            
        source_checksum = calculate_checksum(source_file)
        dest_checksum = calculate_checksum(dest_file)
        
        if source_checksum != dest_checksum:
            return False, "File checksums don't match"
            
        return True, "Integrity check passed"
        
    except Exception as e:
        return False, f"Integrity check error: {str(e)}"
```

### 3. Backup System

The backup system in `utils/backup.py` supports both directory-based and zip-based backups:

```python
def create_backup(source_dir: Union[str, Path], zip_backup: bool = False) -> Optional[Path]:
    source_dir = Path(source_dir)
    timestamp = hashlib.md5(str(os.urandom(8)).encode()).hexdigest()[:8]
    
    if zip_backup:
        # Create a zip archive backup
        # ...
    else:
        # Create a directory backup
        # ...
```

## Testing

With the new modular structure, unit testing becomes easier. Here are some examples of how to test individual components:

### 1. Testing File Operations

```python
import unittest
from pathlib import Path
import tempfile
import shutil
from utils.file_operations import verify_file_integrity

class TestFileOperations(unittest.TestCase):
    def test_verify_file_integrity(self):
        # Setup test environment
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # Create test files
            source_file = temp_dir / "source.txt"
            with open(source_file, "w") as f:
                f.write("Test content")
                
            # Test case 1: Identical files
            dest_file = temp_dir / "dest_identical.txt"
            shutil.copy2(source_file, dest_file)
            result, _ = verify_file_integrity(source_file, dest_file)
            self.assertTrue(result)
            
            # Test case 2: Different content
            dest_file_modified = temp_dir / "dest_modified.txt"
            with open(dest_file_modified, "w") as f:
                f.write("Modified content")
            result, _ = verify_file_integrity(source_file, dest_file_modified)
            self.assertFalse(result)
        finally:
            # Cleanup
            shutil.rmtree(temp_dir)
```

### 2. Testing Category Configuration

```python
import unittest
import json
import tempfile
from utils.categories import load_category_config, build_extension_mapping

class TestCategories(unittest.TestCase):
    def test_category_config(self):
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp:
            config = {
                "TestDocs": ["doc", "pdf"],
                "TestImages": ["jpg", "png"]
            }
            json.dump(config, temp)
            temp_path = temp.name
            
        try:
            # Test loading custom config
            categories = load_category_config(temp_path)
            self.assertEqual(categories["TestDocs"], ["doc", "pdf"])
            self.assertEqual(categories["TestImages"], ["jpg", "png"])
            
            # Test extension mapping
            mapping = build_extension_mapping(categories)
            self.assertEqual(mapping["doc"], "TestDocs")
            self.assertEqual(mapping["jpg"], "TestImages")
        finally:
            # Clean up
            import os
            os.unlink(temp_path)
```

## Future Enhancements

The new modular structure makes it easier to implement future enhancements:

### 1. Implementing Content-Based Categorization

You could add a new module `utils/content_analyzer.py` to detect file types based on content rather than just extension:

```python
def get_file_type_by_content(file_path: Path) -> str:
    """Analyze file content to determine its type."""
    # Implementation using libraries like python-magic
    # ...
```

### 2. Adding File Deduplication

Create a new module `utils/deduplication.py` for handling duplicate files:

```python
def find_duplicates(directory: Path) -> Dict[str, List[Path]]:
    """Find duplicate files based on content hashing."""
    # Implementation
    # ...

def handle_duplicates(duplicates: Dict[str, List[Path]], strategy: str) -> None:
    """Handle duplicates using the specified strategy (keep newest, etc.)."""
    # Implementation
    # ...
```

### 3. Adding Support for Plugin System

Create a plugin architecture by adding a `plugins` directory and a manager module:

```python
def load_plugins(plugin_dir: Path) -> List[Any]:
    """Load and initialize plugins from the plugin directory."""
    # Implementation
    # ...

def run_plugin_hooks(hook_name: str, *args, **kwargs) -> None:
    """Run all plugin hooks with the given name."""
    # Implementation
    # ...
```

## Best Practices for Contributing

When modifying or extending the File Organizer, please follow these best practices:

1. **Maintain Modularity**: Keep related functionality in the appropriate modules.
2. **Follow Typing**: Use type hints for all function parameters and return values.
3. **Document Everything**: Add docstrings to all functions and classes.
4. **Error Handling**: Implement proper exception handling.
5. **Performance**: Consider performance implications, especially for operations on large directories.
6. **Testing**: Write unit tests for new functionality.
7. **Security**: Always validate paths and permissions.
8. **Line Length**: Keep all lines under 120 characters as per project standards.
9. **Logging**: Use the established logging framework with appropriate levels.
10. **PEP 8**: Follow PEP 8 style guidelines, especially for imports.

## Code Style Guidelines

The project follows these specific style guidelines:

1. **Imports**: Always organize imports according to PEP 8:
   - Standard library imports first
   - Related third-party imports second
   - Local application/library specific imports last
   - Alphabetical ordering within each group
   - Absolute imports are preferred over relative imports

   Example:
   ```python
   # Standard library imports
   import os
   import hashlib
   from pathlib import Path
   
   # Third-party imports (if any)
   # import third_party_library
   
   # Local application imports
   from utils.categories import get_file_category
   ```

2. **Line Length**: All lines must be kept under 120 characters.

3. **Type Hints**: Use type hints everywhere, with Union types when necessary:
   ```python
   def function_name(parameter: Type) -> ReturnType:
       """Docstring."""
       # Implementation
   ```

4. **Docstrings**: Use Google-style docstrings:
   ```python
   def function_name(parameter: Type) -> ReturnType:
       """Short description.
       
       Longer description if needed.
       
       Args:
           parameter: Description of parameter
           
       Returns:
           Description of return value
           
       Raises:
           ExceptionType: When this exception is raised
       """
   ```

5. **Exception Handling**: Use specific exception types, and handle each appropriately:
   ```python
   try:
       # Operation that might fail
   except SpecificException as e:
       # Handle specific exception
   except AnotherException as e:
       # Handle another exception
   ```

6. **Variable Naming**:
   - Use snake_case for variables and function names
   - Use PascalCase for class names
   - Use ALL_CAPS for constants

## Conclusion

The File Organizer script has been refactored to improve modularity, readability, and maintainability. The new structure separates functionality into logical modules, places logging in a dedicated directory with timestamped files, and maintains all PEP 8 standards including appropriate line lengths.

This enhanced structure makes the codebase easier to understand, modify, and extend, while preserving all the security, performance, and file management features of the original implementation.
