#!/usr/bin/env python3
"""
File Organizer - A utility that organizes files by category.

This script scans a directory, categorizes files by extension, and moves them
to appropriate subdirectories within a 'processed' directory.
"""

import os
import argparse
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Tuple

from utils.logging_config import setup_logging
from utils.file_operations import process_file
from utils.categories import load_category_config, build_extension_mapping
from utils.permissions import check_user_permissions
from utils.backup import create_backup


def organize_files_by_category(
    source_dir: Path,
    recursive: bool = True,
    max_workers: int = 4,
    dry_run: bool = False,
    verify_integrity: bool = False,
    create_backup_before: bool = False,
    zip_backup: bool = False,
    config_file: Path = None,
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
    # Get logger
    logger = setup_logging()

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


def main():
    """Main entry point for the file organizer."""
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
    parser.add_argument("-d", "--dry-run", action="store_true", help="Simulate organization without making changes")
    parser.add_argument("-i", "--verify-integrity", action="store_true", help="Verify file integrity after moving")
    parser.add_argument("-b", "--backup", action="store_true", help="Create backup before organizing")
    parser.add_argument("-z", "--zip-backup", action="store_true", help="Create backup as zip archive")
    parser.add_argument("-c", "--config", type=str, help="Path to JSON file with custom category mappings")

    # Parse arguments
    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.verbose)

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


if __name__ == "__main__":
    main()
