# File Organizer - Developer's Guide

This document provides detailed information for developers who want to understand, modify, or extend the enhanced File Organizer script.

## Code Structure

The File Organizer script follows a modular structure with enhanced security, performance, and file management features:

```
file_organizer.py
│
├─ organize_files_by_category(source_dir, recursive, max_workers, dry_run, verify_integrity, ...)  # Main function
│  │
│  ├─ Directory validation
│  ├─ User permissions check
│  ├─ Backup creation (optional)
│  ├─ Category configuration loading
│  ├─ "Processed" directory creation
│  ├─ File discovery (recursive or non-recursive)
│  ├─ Parallel file processing with ThreadPoolExecutor
│  ├─ Progress tracking
│  └─ Summary reporting
│
├─ process_file(args)  # Worker function for parallel processing
│  │
│  ├─ Skip checks (skip list, patterns, path safety)
│  ├─ Extension identification
│  ├─ Category determination
│  ├─ Category-specific directory creation
│  ├─ Secure filename generation
│  ├─ Dry run handling
│  ├─ File integrity verification (optional)
│  └─ File movement with error handling
│
├─ get_file_category(extension, category_mapping)  # O(1) category lookup
│  │
│  ├─ Maps extension to category using provided mapping
│  └─ Default "Misc" category for unknown extensions
│
├─ load_category_config(config_path)  # Configuration loading
│  │
│  ├─ JSON file parsing
│  ├─ Configuration validation
│  └─ Fallback to default categories on error
│
├─ build_extension_mapping(categories)  # Create lookup dictionary
│  │
│  └─ Builds extension to category mapping
│
├─ check_user_permissions(directory)  # Permission verification
│  │
│  ├─ Read permission test
│  └─ Write permission test
│
├─ create_backup(source_dir, zip_backup)  # Backup functionality
│  │
│  ├─ Directory-based backup
│  └─ Zip archive backup
│
├─ verify_file_integrity(source_file, dest_file)  # File verification
│  │
│  ├─ File size comparison
│  └─ Checksum verification
│
├─ is_safe_path(base_dir, path)  # Security function
│  │
│  └─ Path traversal protection
│
├─ get_secure_filename(base_path, filename)  # Filename conflict resolution
│  │
│  ├─ Simple counter-based resolution
│  └─ Hash-based resolution for complex conflicts
│
├─ should_skip_file(filename)  # Pattern-based file skipping
│  │
│  └─ Checks for system files, temp files, hidden files, etc.
│
└─ Command-line argument parsing with enhanced options
```

## Key Components

### 1. Main Function: `organize_files_by_category`

The core function has been updated to support additional features:

```python
def organize_files_by_category(
    source_dir: Union[str, Path], 
    recursive: bool = True,
    max_workers: int = 4,
    dry_run: bool = False,
    verify_integrity: bool = False,
    create_backup_before: bool = False,
    zip_backup: bool = False,
    config_file: Optional[Path] = None
) -> None:
    """
    Organize files in the source directory by their file category.
    Uses parallel processing for better performance with large directories.

    Args:
        source_dir: Path to the source directory containing files to organize
        recursive: Whether to process subdirectories recursively
        max_workers: Maximum number of worker threads for parallel processing
        dry_run: Whether to simulate operations without making changes
        verify_integrity: Whether to verify file integrity after moving
        create_backup_before: Whether to create a backup before organizing
        zip_backup: Whether to create a zip backup instead of directory backup
        config_file: Path to a JSON config file for custom categories
    """
```

### 2. Parallel Processing Worker: `process_file`

The worker function now handles additional options:

```python
def process_file(args: Tuple[Path, Path, Path, Set[str], Dict[str, str], Dict]) -> Union[Tuple[str, str], Tuple[str, Path, str]]:
    """
    Process a single file (for parallel execution).

    Args:
        args: Tuple containing:
            - file_path: Path to the file
            - processed_dir: Path to the processed directory
            - source_dir: Source directory path
            - skipped_files: Set of filenames to skip
            - category_mapping: Extension to category mapping
            - options: Additional options like dry_run and verify_integrity

    Returns:
        Union[Tuple[str, str], Tuple[str, Path, str]]:
            - On success: ("success", category)
            - On skip/error: ("skipped", file_path, reason)
    """
```

### 3. New Function: `check_user_permissions`

Verifies user permissions before starting operations:

```python
def check_user_permissions(directory: Union[str, Path]) -> bool:
    """
    Check if the user has read and write permissions for the directory.
    
    Args:
        directory: The directory to check permissions for
        
    Returns:
        bool: True if user has necessary permissions, False otherwise
    """
```

### 4. New Function: `create_backup`

Creates a backup of files before organizing:

```python
def create_backup(source_dir: Union[str, Path], zip_backup: bool = False) -> Optional[Path]:
    """
    Create a backup of the files to be organized.
    
    Args:
        source_dir: The source directory to back up
        zip_backup: Whether to create a zip archive
        
    Returns:
        Optional[Path]: Path to the backup directory or zip file, None if backup failed
    """
```

### 5. New Function: `verify_file_integrity`

Verifies file integrity after moving:

```python
def verify_file_integrity(source_file: Path, dest_file: Path) -> Tuple[bool, str]:
    """
    Verify file integrity after moving by comparing file size and checksum.
    
    Args:
        source_file: Path to source file
        dest_file: Path to destination file
        
    Returns:
        Tuple[bool, str]: Success status and message
    """
```

### 6. New Function: `load_category_config`

Loads custom category configuration from a JSON file:

```python
def load_category_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, List[str]]:
    """
    Load category configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dict: Dictionary of categories and their extensions
    """
```

### 7. New Function: `build_extension_mapping`

Builds the lookup dictionary for category mapping:

```python
def build_extension_mapping(categories: Dict[str, List[str]]) -> Dict[str, str]:
    """
    Build a lookup dictionary for fast extension to category mapping.
    
    Args:
        categories: Dictionary of categories and their extensions
        
    Returns:
        Dict: Mapping of each extension to its category
    """
```

## Phase 3 Feature Implementation Details

### 1. File Verification/Integrity Checks

The script now includes an option to verify file integrity after copying files:

```python
def verify_file_integrity(source_file: Path, dest_file: Path) -> Tuple[bool, str]:
    try:
        # First check if file sizes match
        if source_file.stat().st_size != dest_file.stat().st_size:
            return False, "File sizes don't match"
            
        # Calculate MD5 checksum for both files
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

When integrity verification is enabled, the process_file function operates differently:
1. First copies the file instead of moving it
2. Verifies the integrity of the copy
3. Removes the original file only if verification passes
4. Cleans up the copy if verification fails

```python
if verify_integrity:
    # First copy the file, then verify, then remove the original
    shutil.copy2(str(file_path), str(dest_path))
    
    # Verify integrity
    success, message = verify_file_integrity(file_path, dest_path)
    if success:
        # Remove original after verification
        os.remove(str(file_path))
        return ("success", category)
    else:
        # Remove failed copy and report error
        os.remove(str(dest_path))
        return ("skipped", file_path, f"integrity verification failed: {message}")
```

### 2. User Permissions Check

The script now verifies that the user has appropriate permissions before starting:

```python
def check_user_permissions(directory: Union[str, Path]) -> bool:
    try:
        directory = Path(directory)
        
        # Check if directory exists
        if not directory.exists():
            logger.error(f"Directory {directory} does not exist")
            return False
            
        # Check read permission by listing directory contents
        try:
            next(directory.iterdir(), None)
        except PermissionError:
            logger.error(f"No read permission for directory {directory}")
            return False
            
        # Check write permission by creating a temporary file
        try:
            test_file = directory / f".permission_test_{os.urandom(4).hex()}"
            test_file.touch()
            test_file.unlink()
        except PermissionError:
            logger.error(f"No write permission for directory {directory}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Permission check failed: {str(e)}")
        return False
```

This function performs two key checks:
1. Read permission - Attempts to list directory contents
2. Write permission - Creates and deletes a temporary file

### 3. Dry Run Mode

The script now includes a dry run mode that simulates operations without making actual changes:

```python
if dry_run:
    # If dry run, just log the action without actually moving
    logger.info(f"[DRY RUN] Would move: {file_path} -> {dest_path}")
    return ("success", category)
```

In dry run mode:
- No directories are created
- No files are moved
- All actions are logged as if they were performed
- Statistics are still collected

### 4. Backup Option

The script can now create backups before organizing files:

```python
def create_backup(source_dir: Union[str, Path], zip_backup: bool = False) -> Optional[Path]:
    source_dir = Path(source_dir)
    timestamp = hashlib.md5(str(os.urandom(8)).encode()).hexdigest()[:8]
    
    if zip_backup:
        # Create a zip archive backup
        backup_file = source_dir.parent / f"file_organizer_backup_{timestamp}.zip"
        try:
            logger.info(f"Creating zip backup at {backup_file}")
            
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for item in source_dir.rglob('*'):
                    if item.is_file():
                        zipf.write(item, item.relative_to(source_dir))
                        
            logger.info(f"Zip backup created successfully")
            return backup_file
            
        except Exception as e:
            logger.error(f"Failed to create zip backup: {str(e)}")
            return None
    else:
        # Create a directory backup
        backup_dir = source_dir.parent / f"file_organizer_backup_{timestamp}"
        try:
            logger.info(f"Creating directory backup at {backup_dir}")
            
            # Create backup directory
            backup_dir.mkdir(exist_ok=True)
            
            # Copy files to backup directory
            for item in source_dir.rglob('*'):
                if item.is_file():
                    # Create subdirectory structure in backup
                    rel_path = item.relative_to(source_dir)
                    dest_path = backup_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy the file
                    shutil.copy2(item, dest_path)
                    
            logger.info(f"Directory backup created successfully")
            return backup_dir
            
        except Exception as e:
            logger.error(f"Failed to create directory backup: {str(e)}")
            if backup_dir.exists():
                try:
                    shutil.rmtree(backup_dir)
                except Exception:
                    pass
            return None
```

The backup function supports two types of backups:
1. Directory backup - Creates a copy of the directory structure with all files
2. Zip backup - Creates a compressed archive of all files

### 5. Configurable Categories

The script now supports custom category definitions via JSON configuration files:

```python
def load_category_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, List[str]]:
    if not config_path:
        return DEFAULT_EXTENSION_CATEGORIES
        
    try:
        config_path = Path(config_path)
        if not config_path.exists():
            logger.warning(f"Config file {config_path} not found. Using default categories.")
            return DEFAULT_EXTENSION_CATEGORIES
            
        with open(config_path, 'r') as f:
            custom_categories = json.load(f)
            
        # Validate the config format
        if not isinstance(custom_categories, dict):
            logger.warning("Invalid config format. Using default categories.")
            return DEFAULT_EXTENSION_CATEGORIES
            
        for category, extensions in custom_categories.items():
            if not isinstance(extensions, list):
                logger.warning(f"Invalid extension list for {category}. Using default categories.")
                return DEFAULT_EXTENSION_CATEGORIES
                
        return custom_categories
        
    except (json.JSONDecodeError, PermissionError, OSError) as e:
        logger.warning(f"Error loading config file: {str(e)}. Using default categories.")
        return DEFAULT_EXTENSION_CATEGORIES
```

The category configuration system:
1. Loads custom categories from a JSON file
2. Validates the structure of the configuration
3. Falls back to default categories if any issues are found
4. Builds a lookup dictionary for efficient category mapping

## Security Enhancements

### 1. Path Traversal Protection

The script continues to validate that all file operations are confined to the authorized directory:

```python
def is_safe_path(base_dir: Union[str, Path], path: Union[str, Path]) -> bool:
    try:
        # Convert to Path objects and resolve to absolute paths
        base_dir_path = Path(base_dir).resolve()
        path_to_check = Path(path).resolve()
        
        # Check if the path is within the base directory
        return str(path_to_check).startswith(str(base_dir_path))
    except (ValueError, OSError):
        # Path resolution failed, consider unsafe
        return False
```

### 2. Enhanced Permission Checking

In addition to handling permission errors, the script now proactively checks for permissions:

```python
# Check user permissions
if not check_user_permissions(source_dir):
    logger.error(f"Insufficient permissions for directory '{source_dir}'. Aborting.")
    return
```

### 3. Secure File Operations

The file integrity verification adds another layer of security by ensuring files are transferred correctly:

```python
# Calculate MD5 checksum for both files
def calculate_checksum(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
```

## Performance Enhancements

The script maintains its performance optimizations while adding new features:

### 1. Efficient Backup Creation

The backup functionality uses efficient file operations:

```python
# Copy files to backup directory
for item in source_dir.rglob('*'):
    if item.is_file():
        # Create subdirectory structure in backup
        rel_path = item.relative_to(source_dir)
        dest_path = backup_dir / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the file
        shutil.copy2(item, dest_path)
```

### 2. Smart Integrity Verification

The integrity verification uses an efficient chunked approach for handling large files:

```python
# Calculate MD5 checksum for both files
def calculate_checksum(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
```

### 3. Optimized Category Configuration

The category configuration system uses a two-step approach for efficient lookup:

```python
# Load category configuration
extension_categories = load_category_config(config_file)
category_mapping = build_extension_mapping(extension_categories)
```

## Modifying the Script

### Adding New Features

Here are some advanced modifications developers might want to implement:

#### 1. Custom File Selection Filters

To implement more advanced file selection criteria:

```python
def matches_file_filter(file_path: Path, filters: List[str]) -> bool:
    """
    Check if a file matches any of the provided filters.
    Filters can be glob patterns, minimum/maximum size, or date ranges.
    
    Args:
        file_path: The file to check
        filters: List of filter strings
        
    Returns:
        bool: True if the file matches any filter
    """
    for filter_str in filters:
        # Check for size filters
        if filter_str.startswith("size>"):
            min_size = int(filter_str[5:])
            if file_path.stat().st_size > min_size:
                return True
                
        # Check for date filters
        elif filter_str.startswith("modified>"):
            date_str = filter_str[9:]
            # Parse date and compare to file modification time
            # ...
            
        # Check for glob pattern
        elif fnmatch.fnmatch(file_path.name, filter_str):
            return True
            
    return False
```

Add to the parser:

```python
parser.add_argument(
    "--filter", 
    action="append", 
    help="Add file filter (can be used multiple times)"
)
```

#### 2. Implementing an "Undo" Feature

Create a log of file movements for potential undoing:

```python
def log_file_movement(source_file: Path, dest_file: Path, log_file: Path):
    """Log file movement for potential undo operations."""
    with open(log_file, "a") as f:
        f.write(f"{source_file}|{dest_file}\n")

def undo_organization(log_file: Path):
    """Undo the last organization operation."""
    if not log_file.exists():
        logger.error("No organization log found to undo.")
        return
        
    with open(log_file, "r") as f:
        movements = f.readlines()
    
    # Reverse the movements (undo in reverse order)
    for movement in reversed(movements):
        source, dest = movement.strip().split("|")
        try:
            # Move the file back to its original location
            source_path = Path(source)
            dest_path = Path(dest)
            
            # Create parent directories if needed
            source_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move the file back
            shutil.move(str(dest_path), str(source_path))
            logger.info(f"Moved back: {dest_path} -> {source_path}")
        except Exception as e:
            logger.error(f"Failed to undo movement: {source} -> {dest}: {str(e)}")
```

#### 3. Implementing Content-Based Categorization

For more advanced categorization based on file content or metadata:

```python
def get_file_category_by_content(file_path: Path, extension: str, category_mapping: Dict[str, str]) -> str:
    """Determine category based on both extension and content/metadata."""
    # First try extension-based categorization
    category = get_file_category(extension, category_mapping)
    
    # If it's "Misc", try content-based categorization
    if category == "Misc":
        try:
            # Try to identify file type by its content
            mime_type = magic.from_file(str(file_path), mime=True)
            
            # Map MIME types to categories
            mime_categories = {
                "image/": "Images",
                "audio/": "Audio",
                "video/": "Video",
                "application/pdf": "Documents",
                # Add more mappings
            }
            
            # Check if the mime type matches any category
            for mime_prefix, mime_category in mime_categories.items():
                if mime_type.startswith(mime_prefix):
                    return mime_category
                    
            # Check metadata for documents
            if mime_type == "application/octet-stream":
                # Try to extract document metadata
                # ...
                
        except Exception:
            pass
            
    return category
```

Note: This requires the `python-magic` library to detect MIME types.

#### 4. Implementing File Deduplication

To detect and handle duplicate files:

```python
def find_duplicates(directory: Path) -> Dict[str, List[Path]]:
    """
    Find duplicate files in a directory.
    
    Args:
        directory: The directory to scan
        
    Returns:
        Dict: Mapping of file hashes to lists of paths
    """
    file_hashes = {}
    
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            try:
                # Calculate file hash
                file_hash = calculate_file_hash(file_path)
                
                # Add to hash dictionary
                if file_hash in file_hashes:
                    file_hashes[file_hash].append(file_path)
                else:
                    file_hashes[file_hash] = [file_path]
            except Exception:
                continue
    
    # Return only items with more than one file (duplicates)
    return {k: v for k, v in file_hashes.items() if len(v) > 1}
```

#### 5. Enhanced Reporting and Statistics

To generate more detailed reports:

```python
def generate_detailed_report(file_counts: Dict[str, int], 
                             skipped_files: List[Tuple[Path, str]], 
                             start_time: float, 
                             end_time: float,
                             report_file: Path) -> None:
    """
    Generate a detailed report of the organization operation.
    
    Args:
        file_counts: Mapping of categories to file counts
        skipped_files: List of skipped files and reasons
        start_time: Start time of the operation
        end_time: End time of the operation
        report_file: Path to save the report
    """
    with open(report_file, "w") as f:
        f.write("# File Organization Report\n\n")
        
        # Time information
        duration = end_time - start_time
        f.write(f"## Operation Details\n\n")
        f.write(f"- Start time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}\n")
        f.write(f"- End time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}\n")
        f.write(f"- Duration: {duration:.2f} seconds\n\n")
        
        # Category statistics
        f.write("## Files Organized\n\n")
        total_files = sum(file_counts.values())
        f.write(f"Total files processed: {total_files}\n\n")
        
        f.write("| Category | Count | Percentage |\n")
        f.write("|----------|-------|------------|\n")
        
        for category, count in sorted(file_counts.items()):
            percentage = (count / total_files * 100) if total_files > 0 else 0
            f.write(f"| {category} | {count} | {percentage:.1f}% |\n")
        
        # Skipped files
        if skipped_files:
            f.write("\n## Skipped Files\n\n")
            f.write("| File | Reason |\n")
            f.write("|------|--------|\n")
            
            for file_path, reason in skipped_files:
                f.write(f"| {file_path} | {reason} |\n")
```

## Testing

Here are additional test cases for the new features:

### 1. Testing File Integrity Verification

```python
def test_file_integrity_verification():
    """Test that file integrity verification works correctly."""
    # Setup test directory and files
    test_dir = Path(tempfile.mkdtemp())
    dest_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create a test file
        test_file = test_dir / "test.txt"
        with open(test_file, "w") as f:
            f.write("Test content for integrity verification")
        
        # Create a destination file with the same name
        dest_file = dest_dir / "test.txt"
        
        # Test correct copy - should verify successfully
        shutil.copy2(test_file, dest_file)
        success, message = verify_file_integrity(test_file, dest_file)
        assert success, f"Integrity verification failed on identical files: {message}"
        
        # Test corrupted file - should fail verification
        with open(dest_file, "w") as f:
            f.write("Modified content that breaks integrity")
        
        success, message = verify_file_integrity(test_file, dest_file)
        assert not success, "Integrity verification should have failed on modified file"
        
    finally:
        # Clean up
        shutil.rmtree(test_dir)
        shutil.rmtree(dest_dir)
```

### 2. Testing Permission Checks

```python
def test_permission_checks():
    """Test that permission checks work correctly."""
    # Setup test directory with normal permissions
    test_dir = Path(tempfile.mkdtemp())
    
    try:
        # Initially should have full permissions
        assert check_user_permissions(test_dir), "Should have permissions on newly created temp dir"
        
        if os.name != 'nt':  # Skip on Windows as permissions work differently
            # Remove write permission
            os.chmod(test_dir, 0o555)  # r-xr-xr-x
            assert not check_user_permissions(test_dir), "Should detect missing write permission"
            
            # Restore permissions for cleanup
            os.chmod(test_dir, 0o755)  # rwxr-xr-x
    finally:
        # Clean up
        shutil.rmtree(test_dir)
```

### 3. Testing Backup Functionality

```python
def test_backup_creation():
    """Test backup creation functionality."""
    # Setup test directory
    test_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create some test files
        (test_dir / "file1.txt").write_text("Test content 1")
        (test_dir / "file2.txt").write_text("Test content 2")
        
        # Create a subdirectory with files
        sub_dir = test_dir / "subdir"
        sub_dir.mkdir()
        (sub_dir / "file3.txt").write_text("Test content 3")
        
        # Test directory backup
        backup_path = create_backup(test_dir, zip_backup=False)
        assert backup_path is not None, "Backup creation failed"
        assert backup_path.is_dir(), "Backup should be a directory"
        assert (backup_path / "file1.txt").exists(), "file1.txt missing from backup"
        assert (backup_path / "file2.txt").exists(), "file2.txt missing from backup"
        assert (backup_path / "subdir" / "file3.txt").exists(), "subdir/file3.txt missing from backup"
        
        # Test zip backup
        zip_backup_path = create_backup(test_dir, zip_backup=True)
        assert zip_backup_path is not None, "Zip backup creation failed"
        assert zip_backup_path.is_file(), "Zip backup should be a file"
        assert zipfile.is_zipfile(zip_backup_path), "Should be a valid zip file"
        
        # Verify zip contents
        with zipfile.ZipFile(zip_backup_path) as zipf:
            file_list = zipf.namelist()
            assert "file1.txt" in file_list, "file1.txt missing from zip backup"
            assert "file2.txt" in file_list, "file2.txt missing from zip backup"
            assert "subdir/file3.txt" in file_list, "subdir/file3.txt missing from zip backup"
            
    finally:
        # Clean up
        shutil.rmtree(test_dir)
        if 'backup_path' in locals() and backup_path.exists():
            shutil.rmtree(backup_path)
        if 'zip_backup_path' in locals() and zip_backup_path.exists():
            zip_backup_path.unlink()
```

### 4. Testing Custom Category Configuration

```python
def test_category_config_loading():
    """Test loading custom category configuration."""
    # Create a temporary config file
    fd, config_file = tempfile.mkstemp(suffix='.json')
    try:
        # Write custom config
        custom_config = {
            "Documents": ["pdf", "doc", "docx"],
            "CustomCategory": ["xyz", "abc"]
        }
        
        with os.fdopen(fd, 'w') as f:
            json.dump(custom_config, f)
        
        # Test loading valid config
        categories = load_category_config(config_file)
        assert "CustomCategory" in categories, "Custom category not loaded"
        assert "xyz" in categories["CustomCategory"], "Custom extension not loaded"
        
        # Test mapping creation
        mapping = build_extension_mapping(categories)
        assert mapping["xyz"] == "CustomCategory", "Extension mapping incorrect"
        assert mapping["pdf"] == "Documents", "Standard extension mapping incorrect"
        
        # Test invalid config
        with open(config_file, 'w') as f:
            f.write("This is not valid JSON")
        
        categories = load_category_config(config_file)
        assert categories == DEFAULT_EXTENSION_CATEGORIES, "Should fall back to defaults for invalid config"
        
    finally:
        # Clean up
        os.unlink(config_file)
```

### 5. Testing Dry Run Mode

```python
def test_dry_run_mode():
    """Test that dry run mode doesn't make actual changes."""
    # Setup test directory
    test_dir = Path(tempfile.mkdtemp())
    
    try:
        # Create test files
        (test_dir / "document.pdf").write_text("PDF test content")
        (test_dir / "image.jpg").write_text("JPG test content")
        
        # Get initial state
        initial_files = set(f.name for f in test_dir.iterdir())
        
        # Run in dry run mode
        organize_files_by_category(test_dir, recursive=False, dry_run=True)
        
        # Check that no files were moved
        after_dry_run = set(f.name for f in test_dir.iterdir())
        assert initial_files == after_dry_run, "Dry run should not move any files"
        assert not (test_dir / "processed").exists(), "Processed dir should not be created in dry run"
        
        # Run for real to compare
        organize_files_by_category(test_dir, recursive=False, dry_run=False)
        
        # Check that files were moved
        after_real_run = set(f.name for f in test_dir.iterdir())
        assert "processed" in after_real_run, "Processed directory should be created in real run"
        assert len(after_real_run) < len(initial_files), "Files should be moved in real run"
        
    finally:
        # Clean up
        shutil.rmtree(test_dir)
```

## Future Enhancements

Here are some potential enhancements for future versions beyond Phase 3:

1. **Web Interface**: Create a web-based GUI for easier interaction
2. **Machine Learning Classification**: Use ML to categorize files by content rather than just extension
3. **File Deduplication**: Identify and handle duplicate files
4. **Cloud Storage Integration**: Add support for organizing files on cloud storage platforms
5. **Rule-Based Organization**: Support complex rules with conditions (e.g., "if filename contains 'invoice' and extension is PDF, put in Finances")
6. **Scheduled Organization**: Add ability to run the organizer on a schedule
7. **History and Analytics**: Track organization history and provide statistics over time
8. **Presets and Templates**: Save and load organization configurations as presets
9. **Multi-Stage Organization**: Support sequential organization with different rules for each stage
10. **Plugin System**: Create a plugin architecture for extending functionality

## Implementation Notes for Phase 3 Features

### 1. File Verification Implementation Considerations

The file verification system uses a two-stage approach:
1. First checks file sizes, which is very fast
2. Only computes checksums (which is more expensive) if file sizes match

This approach balances thoroughness with performance. For extremely large files, you might want to implement a sampling approach that only checks parts of the file.

### 2. Backup Performance Considerations

For very large directories, creating a full backup might be time-consuming and storage-intensive. Consider:

1. Implementing a selective backup that only backs up files that will be moved
2. Adding a progress indicator during backup
3. Implementing an incremental backup system for frequent organizers

### 3. Custom Category Configuration Design

The JSON-based configuration system provides flexibility while maintaining a simple interface. When extending this system, consider:

1. Supporting fallbacks within the config (e.g., try custom categories first, then default)
2. Adding category hierarchies (subcategories)
3. Supporting pattern-based extension matching with wildcards

### 4. Dry Run Implementation Details

The dry run implementation uses a flag that's passed through the entire processing chain. Key considerations:

1. Ensure all file system operations check the flag
2. Maintain consistent logging prefixes ("[DRY RUN]")
3. Pre-validate all operations that would be performed

### 5. Permission Checking Implementation

The permission checking is proactive rather than reactive. It:

1. Tests actual operations rather than just checking permission bits
2. Handles both read and write permissions separately
3. Works cross-platform (Windows, Unix)

## Best Practices

When working with the enhanced script, consider these best practices:

1. **Test First**: Always use dry run mode before making actual changes
2. **Backup Regularly**: Enable the backup option for important directories
3. **Custom Categories**: Create custom category configurations for specific use cases
4. **Performance Tuning**: Adjust worker count based on your system's capabilities
5. **Security**: Always verify file integrity for critical data
6. **Documentation**: Keep notes about your organization scheme
7. **Incremental Organization**: Organize files in stages for complex hierarchies
8. **Regular Maintenance**: Run the organizer regularly rather than only when directories become unmanageable

## Conclusion

The File Organizer script has been significantly enhanced with Phase 3 features, building on the solid foundation of security and performance established in earlier phases. The new features provide greater safety (file integrity verification, permission checks, backups), flexibility (custom categories), and usability (dry run mode).

Together, these features transform the script from a simple utility into a robust file management tool suitable for both casual users and professionals who need to maintain organized file systems with reliable, safe operations. The modular design continues to make it easy to extend and customize for specific needs and workflows.
