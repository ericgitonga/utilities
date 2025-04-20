"""Path utilities for file organizer."""

import os
import hashlib
from pathlib import Path
from typing import Tuple, Union


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
        or filename.endswith(".lock")  # Lock files
    ):
        return True, "system or temporary file"
    return False, ""
