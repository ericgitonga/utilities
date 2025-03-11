#!/usr/bin/env python3
# Standard library imports
import os
from datetime import datetime
from typing import List, Optional

# Local imports
from models import RenameOptions


class FileOperations:
    """Service class for file operations and renaming logic"""

    @staticmethod
    def get_files_from_directory(directory: str, extensions: Optional[List[str]] = None) -> List[str]:
        """
        Get list of files from directory with optional extension filtering

        Args:
            directory: Directory path to scan
            extensions: Optional list of extensions to filter by (without dots)

        Returns:
            List of filenames in the directory
        """
        if not directory or not os.path.isdir(directory):
            return []

        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

        # Filter by extension if specified
        if extensions:
            files = [f for f in files if os.path.splitext(f)[1].lower().lstrip(".") in extensions]

        return files

    @staticmethod
    def determine_padding_digits(count: int) -> int:
        """
        Determine the number of digits needed for padding based on file count

        Args:
            count: Number of files

        Returns:
            Number of digits for padding
        """
        if count < 10:
            return 1
        elif count < 100:
            return 2
        elif count < 1000:
            return 3
        else:
            return len(str(count))

    @staticmethod
    def normalize_extension(filename: str) -> str:
        """
        Normalize file extensions to their more common forms and ensure lowercase

        Args:
            filename: Original filename

        Returns:
            Filename with normalized extension
        """
        name, ext = os.path.splitext(filename)
        ext = ext.lower()  # Always convert extension to lowercase

        # Dictionary of less common extensions and their normalized forms
        extension_map = {
            ".jpeg": ".jpg",
            ".tiff": ".tif",
            ".htm": ".html",
            ".mpeg": ".mpg",
            ".mov": ".mp4",
            ".text": ".txt",
            ".midi": ".mid",
            ".markdown": ".md",
            ".png2": ".png",
        }

        # Return normalized filename if extension is in our map
        if ext in extension_map:
            return name + extension_map[ext]
        return name + ext  # Return with lowercase extension even if not in map

    @classmethod
    def generate_new_filename(cls, filename: str, options: RenameOptions, index: int = 0, total_files: int = 0) -> str:
        """
        Generate new filename based on renaming options

        Args:
            filename: Original filename
            options: Renaming options
            index: Index of file in sequence
            total_files: Total number of files (for padding)

        Returns:
            New filename according to pattern
        """
        # First normalize the extension if enabled (which also ensures lowercase)
        if options.normalize_extensions:
            normalized = cls.normalize_extension(filename)
            file_name, file_ext = os.path.splitext(normalized)
        else:
            # Even if not normalizing, still ensure lowercase extension
            file_name, file_ext = os.path.splitext(filename)
            file_ext = file_ext.lower()

        # Get current date if needed
        date_prefix = ""
        if options.include_date:
            date_prefix = datetime.now().strftime("%Y%m%d_")

        # Get base name from user input
        base_name = options.pattern_text

        # Determine padding digits based on total file count
        padding = cls.determine_padding_digits(total_files)

        # Create new filename with sequential pattern
        new_name = f"{date_prefix}{base_name}_{index+1:0{padding}d}{file_ext}"

        return new_name
