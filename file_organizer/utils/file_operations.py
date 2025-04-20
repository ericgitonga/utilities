"""File operations utilities for file organizer."""

import os
import shutil
import hashlib
import logging
from pathlib import Path
from typing import Dict, Set, Tuple, Union

from utils.path_utils import is_safe_path, get_secure_filename, should_skip_file
from utils.permissions import check_file_permissions
from utils.categories import get_file_category

logger = logging.getLogger("file_organizer")


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
