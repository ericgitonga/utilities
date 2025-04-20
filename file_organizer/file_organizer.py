import os
import pwd
import shutil
import argparse
import logging
import hashlib
import concurrent.futures
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Union, Optional
import zipfile

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("file_organizer.log")],
)
logger = logging.getLogger("file_organizer")

# Pre-compute extension to category mapping for O(1) lookups
EXTENSION_TO_CATEGORY = {}
DEFAULT_EXTENSION_CATEGORIES = {
    "Documents": ["pdf", "doc", "docx", "txt", "rtf", "odt", "md", "csv", "xls", "xlsx", "ppt", "pptx"],
    "Images": ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp", "svg", "ico", "heic", "psd", "dng", "nef"],
    "Audio": ["mp3", "wav", "ogg", "flac", "aac", "m4a"],
    "Video": ["mp4", "avi", "mkv", "mov", "wmv", "flv", "webm", "m4v"],
    "Archives": ["zip", "rar", "tar", "gz", "7z"],
    "Code": ["py", "js", "html", "css", "java", "c", "cpp", "go", "rs", "php", "rb", "ipynb", "jar"],
}


def verify_file_integrity(source_file: Path, dest_file: Path) -> Tuple[bool, str]:
    """
    Verify file integrity after moving by comparing file size and checksum.

    Args:
        source_file: Path to source file
        dest_file: Path to destination file

    Returns:
        Tuple[bool, str]: Success status and message
    """
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


def is_safe_path(base_dir: Union[str, Path], path: Union[str, Path]) -> bool:
    """
    Verify that a path is safe to access (within the base directory).
    Prevents directory traversal vulnerabilities.

    Args:
        base_dir: The base directory that shouldn't be escaped
        path: The path to check

    Returns:
        bool: True if the path is safe, False otherwise
    """
    try:
        # Convert to Path objects and resolve to absolute paths
        base_dir_path = Path(base_dir).resolve()
        path_to_check = Path(path).resolve()

        # Check if the path is within the base directory
        return str(path_to_check).startswith(str(base_dir_path))
    except (ValueError, OSError):
        # Path resolution failed, consider unsafe
        return False


def get_secure_filename(base_path: Union[str, Path], filename: str) -> Path:
    """
    Generate a secure filename that doesn't exist at the destination.
    Uses a more efficient algorithm for finding available filenames.

    Args:
        base_path: The base directory path
        filename: The original filename

    Returns:
        Path: The full path to the secure filename
    """
    base_path = Path(base_path)
    dest_path = base_path / filename

    if not dest_path.exists():
        return dest_path

    # If file exists, create a new name based on the base name and extension
    stem = dest_path.stem
    suffix = dest_path.suffix

    # Try with a simple counter first for common cases
    for i in range(1, 5):  # Try simple approach first
        new_path = base_path / f"{stem}_{i}{suffix}"
        if not new_path.exists():
            return new_path

    # If still conflicting, use a more unique approach with partial hash
    file_hash = hashlib.md5(f"{stem}{suffix}{os.urandom(8)}".encode()).hexdigest()[:8]
    return base_path / f"{stem}_{file_hash}{suffix}"


def get_file_category(extension: str, category_mapping: Dict[str, str]) -> str:
    """
    Determine the category of a file based on its extension.
    Uses a pre-computed mapping for O(1) lookup.

    Args:
        extension: The file extension without the dot
        category_mapping: Mapping from extension to category

    Returns:
        str: The category name to use as a directory name
    """
    return category_mapping.get(extension.lower(), "Misc")


def should_skip_file(filename: str) -> Tuple[bool, str]:
    """
    Check if a file should be skipped based on patterns.

    Args:
        filename: The filename to check

    Returns:
        tuple: (should_skip, reason)
    """
    if (
        filename.startswith(".")  # Hidden files
        or filename.startswith("~$")  # Office temp files
        or filename.startswith("._")  # Mac resource forks
        or filename.endswith("~")  # Temp files
        or filename.endswith(".tmp")  # Temp files
        or filename.endswith(".lock")
    ):  # Lock files
        return True, "system or temporary file"
    return False, ""


def check_file_permissions(file_path: Path) -> Tuple[bool, str]:
    """
    Check if the user has read and write permissions for a specific file.

    Args:
        file_path: The file to check permissions for

    Returns:
        Tuple[bool, str]: (has_permissions, reason if not)
    """
    try:
        # Check if file exists
        if not file_path.exists():
            return False, "file does not exist"

        # Try to open the file for reading
        try:
            with open(file_path, "rb") as f:
                f.read(1)  # Try to read 1 byte
        except PermissionError:
            return False, "no read permission"

        # Check if we can write to the file by opening in append mode
        try:
            with open(file_path, "a") as f:
                pass  # Just open and close
        except PermissionError:
            return False, "no write permission"

        # Check if we can delete/rename the file - more complicated
        # Instead of actually deleting, we'll check ownership on Unix systems
        if os.name != "nt":  # Unix-like systems
            # Get file's owner
            file_owner = file_path.stat().st_uid
            current_user = os.getuid()

            if file_owner != current_user:
                owner_name = pwd.getpwuid(file_owner).pw_name
                current_name = pwd.getpwuid(current_user).pw_name
                return False, f"owned by {owner_name}, not {current_name}"

        return True, ""

    except Exception as e:
        return False, f"permission check error: {str(e)}"


def load_category_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, List[str]]:
    """
    Load category configuration from a JSON file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Dict: Dictionary of categories and their extensions
    """
    if not config_path:
        return DEFAULT_EXTENSION_CATEGORIES

    try:
        config_path = Path(config_path)
        if not config_path.exists():
            logger.warning(f"Config file {config_path} not found. Using default categories.")
            return DEFAULT_EXTENSION_CATEGORIES

        with open(config_path, "r") as f:
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


def build_extension_mapping(categories: Dict[str, List[str]]) -> Dict[str, str]:
    """
    Build a lookup dictionary for fast extension to category mapping.

    Args:
        categories: Dictionary of categories and their extensions

    Returns:
        Dict: Mapping of each extension to its category
    """
    mapping = {}
    for category, extensions in categories.items():
        for ext in extensions:
            mapping[ext.lower()] = category
    return mapping


def check_user_permissions(directory: Union[str, Path]) -> bool:
    """
    Check if the user has read and write permissions for the directory.

    Args:
        directory: The directory to check permissions for

    Returns:
        bool: True if user has necessary permissions, False otherwise
    """
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


def create_backup(source_dir: Union[str, Path], zip_backup: bool = False) -> Optional[Path]:
    """
    Create a backup of the files to be organized.

    Args:
        source_dir: The source directory to back up
        zip_backup: Whether to create a zip archive

    Returns:
        Optional[Path]: Path to the backup directory or zip file, None if backup failed
    """
    source_dir = Path(source_dir)
    timestamp = hashlib.md5(str(os.urandom(8)).encode()).hexdigest()[:8]

    if zip_backup:
        # Create a zip archive backup
        backup_file = source_dir.parent / f"file_organizer_backup_{timestamp}.zip"
        try:
            logger.info(f"Creating zip backup at {backup_file}")

            with zipfile.ZipFile(backup_file, "w", zipfile.ZIP_DEFLATED) as zipf:
                for item in source_dir.rglob("*"):
                    if item.is_file():
                        zipf.write(item, item.relative_to(source_dir))

            logger.info("Zip backup created successfully")
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
            for item in source_dir.rglob("*"):
                if item.is_file():
                    # Create subdirectory structure in backup
                    rel_path = item.relative_to(source_dir)
                    dest_path = backup_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)

                    # Copy the file
                    shutil.copy2(item, dest_path)

            logger.info("Directory backup created successfully")
            return backup_dir

        except Exception as e:
            logger.error(f"Failed to create directory backup: {str(e)}")
            if backup_dir.exists():
                try:
                    shutil.rmtree(backup_dir)
                except Exception:
                    pass
            return None


def process_file(
    args: Tuple[Path, Path, Path, Set[str], Dict[str, str], Dict],
) -> Union[Tuple[str, str], Tuple[str, Path, str]]:
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
    file_path, processed_dir, source_dir, skipped_files, category_mapping, options = args
    dry_run = options.get("dry_run", False)
    verify_integrity = options.get("verify_integrity", False)

    try:
        # Skip files in the skip list
        if file_path.name in skipped_files:
            return ("skipped", file_path, "in skip list")

        # Skip system/temporary files
        should_skip, reason = should_skip_file(file_path.name)
        if should_skip:
            return ("skipped", file_path, reason)

        # Path safety check
        if not is_safe_path(source_dir, file_path):
            return ("skipped", file_path, "security check failed")

        # Skip non-files (shouldn't happen, but just in case)
        if not file_path.is_file():
            return ("skipped", file_path, "not a file")

        # Check file permissions (skip files not owned by the user)
        has_permissions, permission_reason = check_file_permissions(file_path)
        if not has_permissions:
            return ("skipped", file_path, f"insufficient permissions: {permission_reason}")

        # Get file extension (without the dot)
        extension = file_path.suffix[1:].lower() if file_path.suffix else "no_extension"

        # Get the category for this file
        category = "Misc" if extension == "no_extension" else get_file_category(extension, category_mapping)

        # Create a directory for this file category if it doesn't exist
        category_dir = processed_dir / category
        if not dry_run:
            category_dir.mkdir(exist_ok=True)

        # Get secure destination path
        dest_path = get_secure_filename(category_dir, file_path.name)

        if dry_run:
            # If dry run, just log the action without actually moving
            logger.info(f"[DRY RUN] Would move: {file_path} -> {dest_path}")
            return ("success", category)
        else:
            # Actually move the file
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
            else:
                # Direct move without verification
                shutil.move(str(file_path), str(dest_path))
                return ("success", category)

    except PermissionError:
        return ("skipped", file_path, "permission denied")
    except FileNotFoundError:
        return ("skipped", file_path, "file not found")
    except OSError as e:
        return ("skipped", file_path, f"OS error: {str(e)[:50]}")
    except Exception as e:
        return ("skipped", file_path, f"unexpected error: {str(e)[:50]}")


def organize_files_by_category(
    source_dir: Union[str, Path],
    recursive: bool = True,
    max_workers: int = 4,
    dry_run: bool = False,
    verify_integrity: bool = False,
    create_backup_before: bool = False,
    zip_backup: bool = False,
    config_file: Optional[Path] = None,
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
    # Convert to Path object
    source_dir = Path(source_dir).resolve()

    # Check if directory exists
    if not source_dir.exists():
        logger.error(f"Error: The directory '{source_dir}' does not exist.")
        return

    # Check user permissions
    if not check_user_permissions(source_dir):
        logger.error(f"Insufficient permissions for directory '{source_dir}'. Aborting.")
        return

    # Create backup if requested
    if create_backup_before:
        backup_path = create_backup(source_dir, zip_backup)
        if not backup_path:
            logger.error("Backup creation failed. Aborting for safety.")
            return
        logger.info(f"Backup created at: {backup_path}")

    # Load category configuration
    extension_categories = load_category_config(config_file)
    category_mapping = build_extension_mapping(extension_categories)

    # Create the main processed directory (unless dry run)
    processed_dir = source_dir / "processed"
    if not dry_run:
        processed_dir.mkdir(exist_ok=True)

    # Dictionary to store file counts by category
    file_counts: Dict[str, int] = {}

    # Define files to skip
    skipped_files = {
        os.path.basename(__file__),  # The script itself
        "file_organizer.log",  # The log file
        "desktop.ini",  # Common system files
        "thumbs.db",
        ".DS_Store",  # Mac OS system file
    }

    # List to track all skipped files
    all_skipped_files: List[Tuple[Path, str]] = []

    # Create list of files to process
    files_to_process = []

    # Process options
    options = {"dry_run": dry_run, "verify_integrity": verify_integrity}

    # Find all files to process
    if recursive:
        # Recursive approach - walk through directory tree
        logger.info(f"Finding files to process recursively in '{source_dir}'...")

        for root, _, files in os.walk(source_dir):
            root_path = Path(root)

            # Skip the processed directory to avoid circular processing
            if str(root_path).startswith(str(processed_dir)):
                continue

            for filename in files:
                file_path = root_path / filename
                files_to_process.append(
                    (file_path, processed_dir, source_dir, skipped_files, category_mapping, options)
                )
    else:
        # Non-recursive approach - just process files in the top directory
        logger.info(f"Finding files to process in '{source_dir}'...")

        for item in source_dir.iterdir():
            if item.is_file():
                files_to_process.append((item, processed_dir, source_dir, skipped_files, category_mapping, options))

    total_files = len(files_to_process)
    logger.info(f"Found {total_files} files to process")

    if total_files == 0:
        logger.info("No files to organize.")
        return

    # Process files in parallel for better performance
    mode_str = "[DRY RUN] " if dry_run else ""
    logger.info(f"{mode_str}Processing files using {max_workers} worker threads...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Process files and gather results
        futures = [executor.submit(process_file, args) for args in files_to_process]

        # Track progress
        completed = 0

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            completed += 1

            # Show progress periodically
            if completed % 10 == 0 or completed == total_files:
                percent_done = int(completed / total_files * 100)
                logger.info(f"{mode_str}Progress: {completed}/{total_files} files processed ({percent_done}%)")

            # Process the result
            if result[0] == "success":
                # Update file counts for success
                category = result[1]
                file_counts[category] = file_counts.get(category, 0) + 1
            elif result[0] == "skipped":
                # Add to skipped files list
                file_path, reason = result[1], result[2]
                all_skipped_files.append((file_path, reason))

                # Log skipped files with appropriate level
                if "security check failed" in reason:
                    logger.warning(f"Skipping file: {file_path} - Reason: {reason}")
                else:
                    logger.info(f"Skipping file: {file_path} - Reason: {reason}")

    # Print summary
    logger.info(f"\n{mode_str}Organization complete!")
    logger.info(f"{mode_str}Summary of files organized:")
    for category, count in sorted(file_counts.items()):
        logger.info(f"{mode_str}  {category}: {count} file(s)")

    # Print skipped files summary
    if all_skipped_files:
        logger.info(f"\n{mode_str}Skipped files:")
        for file_path, reason in all_skipped_files:
            logger.info(f"{mode_str}  {file_path} - Reason: {reason}")
    else:
        logger.info(f"\n{mode_str}No files were skipped.")


if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Organize files by their category into a 'processed' directory.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("directory", nargs="?", default=os.getcwd(), help="The directory to organize")
    parser.add_argument("-r", "--recursive", action="store_true", help="Process subdirectories recursively")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("-w", "--workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")

    # Phase 3 features
    parser.add_argument("-d", "--dry-run", action="store_true", help="Simulate organization without making changes")
    parser.add_argument("-i", "--verify-integrity", action="store_true", help="Verify file integrity after moving")
    parser.add_argument("-b", "--backup", action="store_true", help="Create backup before organizing")
    parser.add_argument("-z", "--zip-backup", action="store_true", help="Create backup as zip archive")
    parser.add_argument("-c", "--config", type=str, help="Path to JSON file with custom category mappings")

    # Parse arguments
    args = parser.parse_args()

    # Set logging level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Display information about the operation
    recursive_str = "recursively " if args.recursive else ""
    dry_run_str = "[DRY RUN] " if args.dry_run else ""

    # Build operation description in parts to keep line length manageable
    op_desc = f"This will organize all files {recursive_str}in '{args.directory}'"
    if args.verify_integrity:
        op_desc += " with integrity verification"
    if args.backup:
        op_desc += " after creating backup"
    op_desc += " into category subdirectories."

    logger.info(f"{dry_run_str}{op_desc}")
    logger.info(f"{dry_run_str}Using {args.workers} worker threads for parallel processing.")

    if args.config:
        logger.info(f"{dry_run_str}Using custom category config from: {args.config}")

    # Confirm with user unless --yes flag is used
    if args.yes:
        confirmation = "y"
    else:
        confirmation = input(f"{dry_run_str}Continue? (y/n): ")

    if confirmation.lower() in ["y", "yes"]:
        organize_files_by_category(
            args.directory,
            args.recursive,
            args.workers,
            args.dry_run,
            args.verify_integrity,
            args.backup,
            args.zip_backup,
            args.config,
        )
    else:
        logger.info("Operation cancelled.")
