import os
import shutil
import argparse
import logging
import hashlib
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Set, Tuple, Union

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("file_organizer.log")],
)
logger = logging.getLogger("file_organizer")

# Pre-compute extension to category mapping for O(1) lookups
EXTENSION_TO_CATEGORY = {}
EXTENSION_CATEGORIES = {
    "Documents": ["pdf", "doc", "docx", "txt", "rtf", "odt", "md", "csv", "xls", "xlsx", "ppt", "pptx"],
    "Images": ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp", "svg", "ico", "heic", "psd", "dng", "nef"],
    "Audio": ["mp3", "wav", "ogg", "flac", "aac", "m4a"],
    "Video": ["mp4", "avi", "mkv", "mov", "wmv", "flv", "webm", "m4v"],
    "Archives": ["zip", "rar", "tar", "gz", "7z"],
    "Code": ["py", "js", "html", "css", "java", "c", "cpp", "go", "rs", "php", "rb", "ipynb", "jar"],
}

# Build the lookup dictionary once
for category, extensions in EXTENSION_CATEGORIES.items():
    for ext in extensions:
        EXTENSION_TO_CATEGORY[ext] = category


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


def get_file_category(extension: str) -> str:
    """
    Determine the category of a file based on its extension.
    Uses a pre-computed mapping for O(1) lookup.

    Args:
        extension: The file extension without the dot

    Returns:
        str: The category name to use as a directory name
    """
    return EXTENSION_TO_CATEGORY.get(extension.lower(), "Misc")


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


def process_file(args: Tuple[Path, Path, Path, Set[str]]) -> Union[Tuple[str, str], Tuple[str, Path, str]]:
    """
    Process a single file (for parallel execution).

    Args:
        args: Tuple containing:
            - file_path: Path to the file
            - processed_dir: Path to the processed directory
            - source_dir: Source directory path
            - skipped_files: Set of filenames to skip

    Returns:
        Union[Tuple[str, str], Tuple[str, Path, str]]:
            - On success: ("success", category)
            - On skip/error: ("skipped", file_path, reason)
    """
    file_path, processed_dir, source_dir, skipped_files = args

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

        # Get file extension (without the dot)
        extension = file_path.suffix[1:].lower() if file_path.suffix else "no_extension"

        # Get the category for this file
        category = "Misc" if extension == "no_extension" else get_file_category(extension)

        # Create a directory for this file category if it doesn't exist
        category_dir = processed_dir / category
        category_dir.mkdir(exist_ok=True)

        # Get secure destination path
        dest_path = get_secure_filename(category_dir, file_path.name)

        # Move the file
        shutil.move(str(file_path), str(dest_path))

        # Return success with category for counting
        return ("success", category)

    except PermissionError:
        return ("skipped", file_path, "permission denied")
    except FileNotFoundError:
        return ("skipped", file_path, "file not found")
    except OSError as e:
        return ("skipped", file_path, f"OS error: {str(e)[:50]}")
    except Exception as e:
        return ("skipped", file_path, f"unexpected error: {str(e)[:50]}")


def organize_files_by_category(source_dir: Union[str, Path], recursive: bool = True, max_workers: int = 4) -> None:
    """
    Organize files in the source directory by their file category.
    Uses parallel processing for better performance with large directories.

    Args:
        source_dir: Path to the source directory containing files to organize
        recursive: Whether to process subdirectories recursively
        max_workers: Maximum number of worker threads for parallel processing
    """
    # Convert to Path object
    source_dir = Path(source_dir).resolve()

    # Check if directory exists
    if not source_dir.exists():
        logger.error(f"Error: The directory '{source_dir}' does not exist.")
        return

    # Create the main processed directory
    processed_dir = source_dir / "processed"
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
                files_to_process.append((file_path, processed_dir, source_dir, skipped_files))
    else:
        # Non-recursive approach - just process files in the top directory
        logger.info(f"Finding files to process in '{source_dir}'...")

        for item in source_dir.iterdir():
            if item.is_file():
                files_to_process.append((item, processed_dir, source_dir, skipped_files))

    total_files = len(files_to_process)
    logger.info(f"Found {total_files} files to process")

    if total_files == 0:
        logger.info("No files to organize.")
        return

    # Process files in parallel for better performance
    logger.info(f"Processing files using {max_workers} worker threads...")

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
                logger.info(f"Progress: {completed}/{total_files} files processed ({percent_done}%)")

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
    logger.info("\nOrganization complete!")
    logger.info("Summary of files organized:")
    for category, count in sorted(file_counts.items()):
        logger.info(f"  {category}: {count} file(s)")

    # Print skipped files summary
    if all_skipped_files:
        logger.info("\nSkipped files:")
        for file_path, reason in all_skipped_files:
            logger.info(f"  {file_path} - Reason: {reason}")
    else:
        logger.info("\nNo files were skipped.")


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

    # Parse arguments
    args = parser.parse_args()

    # Set logging level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Display information about the operation
    recursive_str = "recursively " if args.recursive else ""
    logger.info(f"This will organize all files {recursive_str}in '{args.directory}' into category subdirectories.")
    logger.info(f"Using {args.workers} worker threads for parallel processing.")

    # Confirm with user unless --yes flag is used
    if args.yes:
        confirmation = "y"
    else:
        confirmation = input("Continue? (y/n): ")

    if confirmation.lower() in ["y", "yes"]:
        organize_files_by_category(args.directory, args.recursive, args.workers)
    else:
        logger.info("Operation cancelled.")
