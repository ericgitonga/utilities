"""Backup utilities for file organizer."""

import os
import hashlib
import shutil
import logging
import zipfile
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger("file_organizer")


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
