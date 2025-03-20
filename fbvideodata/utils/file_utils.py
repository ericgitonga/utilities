"""
File utility functions for the Facebook Video Data Tool application.
"""

import os
import platform
import subprocess
from pathlib import Path


def open_file(filepath):
    """
    Open a file with the default application.

    Args:
        filepath: Path to the file to open

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if platform.system() == "Windows":
            os.startfile(filepath)
        elif platform.system() == "Darwin":  # macOS
            subprocess.call(("open", filepath))
        else:  # Linux and other Unix-like
            subprocess.call(("xdg-open", filepath))
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def open_directory(filepath):
    """
    Open the directory containing a file.

    Args:
        filepath: Path to a file whose directory should be opened

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        directory = os.path.dirname(os.path.abspath(filepath))

        if platform.system() == "Windows":
            subprocess.call(f'explorer "{directory}"', shell=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.call(["open", directory])
        else:  # Linux and other Unix-like
            subprocess.call(["xdg-open", directory])
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def ensure_directory_exists(directory_path):
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory_path: Path to the directory

    Returns:
        bool: True if directory exists or was created, False otherwise
    """
    try:
        path = Path(directory_path)
        if not path.exists():
            path.mkdir(parents=True)
        return True
    except (OSError, PermissionError):
        return False
