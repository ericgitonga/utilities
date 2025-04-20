import os
import shutil
import argparse
import logging
import hashlib

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


def is_safe_path(base_dir, path):
    """
    Verify that a path is safe to access (within the base directory).
    Prevents directory traversal vulnerabilities.

    Args:
        base_dir (str): The base directory that shouldn't be escaped
        path (str): The path to check

    Returns:
        bool: True if the path is safe, False otherwise
    """
    try:
        # Convert to absolute paths
        base_dir = os.path.abspath(base_dir)
        path = os.path.abspath(path)

        # Check if the path is within the base directory
        return os.path.commonpath([base_dir]) == os.path.commonpath([base_dir, path])
    except ValueError:
        # Path resolution failed, consider unsafe
        return False


def get_secure_filename(base_path, filename):
    """
    Generate a secure filename that doesn't exist at the destination.
    Uses a more efficient algorithm for finding available filenames.

    Args:
        base_path (str): The base directory path
        filename (str): The original filename

    Returns:
        str: The full path to the secure filename
    """
    dest_path = os.path.join(base_path, filename)

    if not os.path.exists(dest_path):
        return dest_path

    # If file exists, create a new name based on the base name and extension
    base_name, ext = os.path.splitext(filename)

    # Try with a simple counter first for common cases
    for i in range(1, 5):  # Try simple approach first
        new_filename = f"{base_name}_{i}{ext}"
        new_path = os.path.join(base_path, new_filename)
        if not os.path.exists(new_path):
            return new_path

    # If still conflicting, use a more unique approach with partial hash
    file_hash = hashlib.md5(f"{base_name}{ext}{os.urandom(8)}".encode()).hexdigest()[:8]
    new_path = os.path.join(base_path, f"{base_name}_{file_hash}{ext}")
    return new_path


def get_file_category(extension):
    """
    Determine the category of a file based on its extension.
    Uses a pre-computed mapping for O(1) lookup.

    Args:
        extension (str): The file extension without the dot

    Returns:
        str: The category name to use as a directory name
    """
    return EXTENSION_TO_CATEGORY.get(extension.lower(), "Misc")


def should_skip_file(filename):
    """
    Check if a file should be skipped based on patterns.

    Args:
        filename (str): The filename to check

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


def process_files_in_directory(directory, files, processed_dir, file_counts, source_dir, skipped_files):
    """
    Process files in a given directory and move them to the appropriate category location.

    Args:
        directory (str): Directory containing the files to process
        files (list): List of filenames to process
        processed_dir (str): Path to the processed directory
        file_counts (dict): Dictionary to track file counts by category
        source_dir (str): Source directory path (for path safety checks)
        skipped_files (set): Set of filenames to skip

    Returns:
        list: List of skipped files with reasons
    """
    skipped_files_list = []

    for filename in files:
        # Skip files in the skip list
        if filename in skipped_files:
            logger.info(f"Skipping file: {filename} (in skip list)")
            skipped_files_list.append((os.path.join(directory, filename), "in skip list"))
            continue

        # Skip system/temporary files
        should_skip, reason = should_skip_file(filename)
        if should_skip:
            logger.info(f"Skipping file: {filename} ({reason})")
            skipped_files_list.append((os.path.join(directory, filename), reason))
            continue

        file_path = os.path.join(directory, filename)

        # Path safety check
        if not is_safe_path(source_dir, file_path):
            logger.warning(f"Skipping potentially unsafe file path: {file_path}")
            skipped_files_list.append((file_path, "security check failed"))
            continue

        # Get file extension (without the dot)
        _, extension = os.path.splitext(filename)
        extension = extension[1:].lower() if extension else "no_extension"

        # Get the category for this file
        if extension == "no_extension":
            category = "Misc"
        else:
            category = get_file_category(extension)

        # Create a directory for this file category if it doesn't exist
        category_dir = os.path.join(processed_dir, category)
        os.makedirs(category_dir, exist_ok=True)

        # Get secure destination path
        dest_path = get_secure_filename(category_dir, filename)

        # Move the file
        try:
            shutil.move(file_path, dest_path)

            # Update file counts
            if category in file_counts:
                file_counts[category] += 1
            else:
                file_counts[category] = 1

            logger.info(f"Moved: {filename} -> processed/{category}/{os.path.basename(dest_path)}")
        except PermissionError:
            logger.error(f"Error: Permission denied when moving {filename}")
            skipped_files_list.append((file_path, "permission denied"))
        except FileNotFoundError:
            logger.error(f"Error: File {filename} not found during move operation")
            skipped_files_list.append((file_path, "file not found"))
        except OSError as e:
            logger.error(f"Error moving {filename}: OS error - {e}")
            skipped_files_list.append((file_path, f"OS error: {str(e)[:50]}..."))
        except Exception as e:
            logger.error(f"Error moving {filename}: Unexpected error - {e}")
            skipped_files_list.append((file_path, f"unexpected error: {str(e)[:50]}..."))

    return skipped_files_list


def organize_files_by_category(source_dir, recursive=True):
    """
    Organize files in the source directory by their file category.
    Each file will be moved to a subdirectory named after its category
    within a 'processed' directory.

    Args:
        source_dir (str): Path to the source directory containing files to organize
        recursive (bool): Whether to process subdirectories recursively
    """
    # Convert to absolute path and check if directory exists
    source_dir = os.path.abspath(source_dir)
    if not os.path.exists(source_dir):
        logger.error(f"Error: The directory '{source_dir}' does not exist.")
        return

    # Create the main processed directory
    processed_dir = os.path.join(source_dir, "processed")
    os.makedirs(processed_dir, exist_ok=True)

    # Dictionary to store file counts by category
    file_counts = {}

    # Define files to skip
    skipped_files = {
        os.path.basename(__file__),  # The script itself
        "file_organizer.log",  # The log file
        "desktop.ini",  # Common system files
        "thumbs.db",
        ".DS_Store",  # Mac OS system file
    }

    # List to track all skipped files
    all_skipped_files = []

    # Process files based on recursion option
    if recursive:
        # Recursive processing (walk through all subdirectories)
        for root, _, files in os.walk(source_dir):
            # Skip the processed directory to avoid circular processing
            if os.path.normpath(root).startswith(os.path.normpath(processed_dir)):
                continue

            skipped = process_files_in_directory(root, files, processed_dir, file_counts, source_dir, skipped_files)
            all_skipped_files.extend(skipped)
    else:
        # Non-recursive processing (only process files in the specified directory)
        files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
        skipped = process_files_in_directory(source_dir, files, processed_dir, file_counts, source_dir, skipped_files)
        all_skipped_files.extend(skipped)

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
    parser = argparse.ArgumentParser(description="Organize files by their category into a 'processed' directory.")
    parser.add_argument(
        "directory", nargs="?", default=os.getcwd(), help="The directory to organize (default: current directory)"
    )
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Process subdirectories recursively (default: False)"
    )
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt (default: False)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")

    # Parse arguments
    args = parser.parse_args()

    # Set logging level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Display information about the operation
    recursive_str = "recursively " if args.recursive else ""
    logger.info(f"This will organize all files {recursive_str}in '{args.directory}' into category subdirectories.")

    # Confirm with user unless --yes flag is used
    if args.yes:
        confirmation = "y"
    else:
        confirmation = input("Continue? (y/n): ")

    if confirmation.lower() in ["y", "yes"]:
        organize_files_by_category(args.directory, args.recursive)
    else:
        logger.info("Operation cancelled.")
