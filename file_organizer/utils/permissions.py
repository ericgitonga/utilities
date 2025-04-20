"""Permission utilities for file organizer."""

import os
import pwd
import logging
from pathlib import Path
from typing import Tuple, Union

logger = logging.getLogger("file_organizer")


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
