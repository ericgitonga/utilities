#!/usr/bin/env python3
"""
File sorter that identifies audio and video files based on file signatures,
moves them to appropriate folders, and corrects file extensions in both directions
(MP3 → MP4 and MP4 → MP3). Uses asynchronous processing for improved performance
with large directories.
"""

import asyncio
import shutil
import argparse
from pathlib import Path
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_file_signature(file_path):
    """
    Read the file signature (magic bytes) to identify the actual file type.

    Args:
        file_path: Path to the file

    Returns:
        String indicating file type ('mp3', 'mp4', or 'unknown')
    """
    signatures = {
        # MP3 signatures
        b"\xff\xfb": "mp3",  # MPEG-1 Layer 3
        b"\xff\xf3": "mp3",  # MPEG-2 Layer 3
        b"\xff\xf2": "mp3",  # MPEG-2.5 Layer 3
        b"\x49\x44\x33": "mp3",  # ID3 tag (common in MP3)
        # MP4 signatures
        b"\x00\x00\x00\x18\x66\x74\x79\x70": "mp4",  # ISO Base Media file (MPEG-4)
        b"\x00\x00\x00\x20\x66\x74\x79\x70": "mp4",  # ISO Base Media file (MPEG-4)
        b"\x66\x74\x79\x70\x4d\x53\x4e\x56": "mp4",  # MPEG-4 video
        b"\x66\x74\x79\x70\x69\x73\x6f\x6d": "mp4",  # ISO Base Media file (MPEG-4)
    }

    try:
        with open(file_path, "rb") as f:
            file_start = f.read(12)  # Read first 12 bytes for signature detection

            for signature, file_type in signatures.items():
                if file_start.startswith(signature):
                    return file_type

            # Additional check for MP4 container format (checking for 'ftyp' after the initial 4 bytes)
            if b"ftyp" in file_start[4:8]:
                return "mp4"

        return "unknown"
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return "unknown"


def process_file(item, audio_folder, video_folder, unknown_folder=None, create_unknown_folder=False):
    """
    Process a single file - identify its type, determine destination, and move it.
    This function is designed to be called in parallel.

    Args:
        item: Path object to the file
        audio_folder: Path to audio destination folder
        video_folder: Path to video destination folder
        unknown_folder: Path to unknown files folder (optional)
        create_unknown_folder: Whether to create and use a folder for unknown file types

    Returns:
        Dict with results of processing including success status and operation details
    """
    result = {
        "filename": item.name,
        "success": False,
        "operation": None,
        "destination": None,
        "new_name": None,
        "error": None,
    }

    try:
        # Skip files that are already in our destination folders
        if any(str(item).startswith(str(folder)) for folder in [audio_folder, video_folder]):
            result["operation"] = "skipped_in_dest"
            return result

        file_type = get_file_signature(item)

        # Determine destination based on file type
        if file_type == "mp3":
            dest_folder = audio_folder
            correct_extension = ".mp3"
        elif file_type == "mp4":
            dest_folder = video_folder
            correct_extension = ".mp4"
        else:
            if create_unknown_folder and unknown_folder:
                dest_folder = unknown_folder
                correct_extension = item.suffix  # Keep original extension for unknown types
            else:
                result["operation"] = "skipped_unknown"
                return result

        # Check if we have a mismatch between file extension and actual content type
        current_extension = item.suffix.lower()
        extension_mismatch = current_extension != correct_extension

        # Common mislabeling patterns to check
        mp3_as_mp4 = file_type == "mp3" and current_extension == ".mp4"
        mp4_as_mp3 = file_type == "mp4" and current_extension == ".mp3"

        if extension_mismatch:
            new_filename = f"{item.stem}{correct_extension}"
            mismatch_type = "MP3 saved as MP4" if mp3_as_mp4 else "MP4 saved as MP3" if mp4_as_mp3 else "extension"
            result["operation"] = f"rename_{mismatch_type}"
        else:
            new_filename = item.name
            result["operation"] = "move_only"

        # Move the file with possibly corrected name
        dest_file = dest_folder / new_filename

        # Handle filename conflicts
        if dest_file.exists():
            base_name = dest_file.stem
            extension = dest_file.suffix
            count = 1
            while dest_file.exists():
                new_name = f"{base_name}_{count}{extension}"
                dest_file = dest_folder / new_name
                count += 1
            result["operation"] += "_renamed_due_to_conflict"

        # Use shutil.move which actually moves the file (not copies)
        shutil.move(str(item), str(dest_file))

        result["success"] = True
        result["destination"] = str(dest_folder)
        result["new_name"] = dest_file.name

    except Exception as e:
        result["success"] = False
        result["error"] = str(e)

    return result


async def sort_files_async(source_folder, create_unknown_folder=False, max_workers=None):
    """
    Sort files asynchronously from source folder into video and audio subdirectories
    based on file signatures. Uses a thread pool to process files in parallel.

    Args:
        source_folder: Path to the folder containing files to be sorted
        create_unknown_folder: Whether to create a folder for files of unknown type
        max_workers: Maximum number of concurrent workers (default: None, uses CPU count)

    Returns:
        Dict with summary statistics of the operation
    """
    # If max_workers is not specified, use CPU count
    if max_workers is None:
        max_workers = os.cpu_count()

    start_time = time.time()
    source_path = Path(source_folder).resolve()
    print(f"Processing files in: {source_path} using {max_workers} workers")

    # Verify the source directory exists
    if not source_path.exists():
        print(f"Error: Source directory '{source_path}' does not exist.")
        return {"error": "Source directory does not exist"}

    if not source_path.is_dir():
        print(f"Error: '{source_path}' is not a directory.")
        return {"error": "Source path is not a directory"}

    # Create destination folders WITHIN the source directory
    audio_folder = source_path / "audio"
    video_folder = source_path / "video"
    unknown_folder = None

    # Create folders with parents=True to handle missing parent directories
    audio_folder.mkdir(exist_ok=True, parents=True)
    video_folder.mkdir(exist_ok=True, parents=True)

    print(f"Created audio directory: {audio_folder}")
    print(f"Created video directory: {video_folder}")

    if create_unknown_folder:
        unknown_folder = source_path / "unknown"
        unknown_folder.mkdir(exist_ok=True, parents=True)
        print(f"Created unknown directory: {unknown_folder}")

    # Get list of files to process
    files_to_process = [
        item
        for item in source_path.iterdir()
        if item.is_file()
        and not item.name.startswith(".")
        and not any(str(item).startswith(str(folder)) for folder in [audio_folder, video_folder, unknown_folder])
    ]

    total_files = len(files_to_process)
    print(f"Found {total_files} files to process")

    # Stats to track results
    stats = {
        "total_files": total_files,
        "processed": 0,
        "success": 0,
        "errors": 0,
        "skipped": 0,
        "mp3_files": 0,
        "mp4_files": 0,
        "unknown_files": 0,
        "renamed_extensions": 0,
    }

    # Process files concurrently using ThreadPoolExecutor
    processed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all files for processing
        future_to_file = {
            executor.submit(process_file, item, audio_folder, video_folder, unknown_folder, create_unknown_folder): item
            for item in files_to_process
        }

        # Process results as they complete
        for future in as_completed(future_to_file):
            processed += 1
            result = future.result()

            # Update progress periodically
            if processed % 10 == 0 or processed == total_files:
                print(f"Progress: {processed}/{total_files} files ({processed/total_files*100:.1f}%)")

            # Skip printing detailed output for better performance with large sets
            if total_files <= 100 or processed % 20 == 0 or "error" in result:
                if result["success"]:
                    operation = "Moved and renamed" if result["new_name"] != result["filename"] else "Moved"
                    dest_folder_name = os.path.basename(result["destination"])
                    print(f"{operation} '{result['filename']}' to {dest_folder_name}/{result['new_name']}")
                elif result.get("error"):
                    print(f"Error processing {result['filename']}: {result['error']}")
                elif "skipped" in result.get("operation", ""):
                    reason = "already in destination" if "in_dest" in result["operation"] else "unknown type"
                    print(f"Skipped {result['filename']} ({reason})")

            # Update stats
            stats["processed"] += 1

            if result["success"]:
                stats["success"] += 1
                if "audio" in result.get("destination", ""):
                    stats["mp3_files"] += 1
                elif "video" in result.get("destination", ""):
                    stats["mp4_files"] += 1
                elif "unknown" in result.get("destination", ""):
                    stats["unknown_files"] += 1

                if "rename" in result.get("operation", ""):
                    stats["renamed_extensions"] += 1
            elif "skipped" in result.get("operation", ""):
                stats["skipped"] += 1
            else:
                stats["errors"] += 1

    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    stats["elapsed_time"] = elapsed_time
    stats["files_per_second"] = stats["processed"] / elapsed_time if elapsed_time > 0 else 0

    print(f"\nSummary: {stats['processed']} files processed in {elapsed_time:.2f} seconds")
    print(f"  - {stats['mp3_files']} MP3 files moved to audio folder")
    print(f"  - {stats['mp4_files']} MP4 files moved to video folder")
    print(f"  - {stats['unknown_files']} files of unknown type")
    print(f"  - {stats['renamed_extensions']} files had extensions corrected")
    print(f"  - {stats['skipped']} files skipped")
    print(f"  - {stats['errors']} errors encountered")
    print(f"Performance: {stats['files_per_second']:.2f} files/second")

    return stats


def sort_files(source_folder, create_unknown_folder=False, max_workers=None):
    """
    Wrapper function to call the async version from synchronous code.

    Args:
        source_folder: Path to the folder containing files to be sorted
        create_unknown_folder: Whether to create a folder for files of unknown type
        max_workers: Maximum number of concurrent workers
    """
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(sort_files_async(source_folder, create_unknown_folder, max_workers))


def sort_files_sequential(source_folder, create_unknown_folder=False):
    """
    Sort files sequentially (single-threaded) from source folder into video and audio subdirectories.
    This function uses the original non-parallel implementation for benchmark comparison.

    Args:
        source_folder: Path to the folder containing files to be sorted
        create_unknown_folder: Whether to create a folder for files of unknown type

    Returns:
        Dict with summary statistics of the operation
    """
    start_time = time.time()
    source_path = Path(source_folder).resolve()
    print(f"Processing files sequentially in: {source_path}")

    # Verify the source directory exists
    if not source_path.exists():
        print(f"Error: Source directory '{source_path}' does not exist.")
        return {"error": "Source directory does not exist"}

    if not source_path.is_dir():
        print(f"Error: '{source_path}' is not a directory.")
        return {"error": "Source path is not a directory"}

    # Create destination folders WITHIN the source directory
    audio_folder = source_path / "audio"
    video_folder = source_path / "video"
    unknown_folder = None

    # Create folders with parents=True to handle missing parent directories
    audio_folder.mkdir(exist_ok=True, parents=True)
    video_folder.mkdir(exist_ok=True, parents=True)

    print(f"Created audio directory: {audio_folder}")
    print(f"Created video directory: {video_folder}")

    if create_unknown_folder:
        unknown_folder = source_path / "unknown"
        unknown_folder.mkdir(exist_ok=True, parents=True)
        print(f"Created unknown directory: {unknown_folder}")

    # Stats to track results
    stats = {
        "total_files": 0,
        "processed": 0,
        "success": 0,
        "errors": 0,
        "skipped": 0,
        "mp3_files": 0,
        "mp4_files": 0,
        "unknown_files": 0,
        "renamed_extensions": 0,
    }

    # Process all files in the source folder (not recursively)
    for item in source_path.iterdir():
        if not item.is_file():
            continue

        if item.name.startswith("."):  # Skip hidden files
            continue

        # Skip files that are already in our destination folders
        if any(str(item).startswith(str(folder)) for folder in [audio_folder, video_folder, unknown_folder]):
            continue

        stats["total_files"] += 1
        print(f"Analyzing {item.name}...")
        file_type = get_file_signature(item)

        # Determine destination based on file type
        if file_type == "mp3":
            dest_folder = audio_folder
            correct_extension = ".mp3"
            stats["mp3_files"] += 1
        elif file_type == "mp4":
            dest_folder = video_folder
            correct_extension = ".mp4"
            stats["mp4_files"] += 1
        else:
            if create_unknown_folder:
                dest_folder = unknown_folder
                correct_extension = item.suffix  # Keep original extension for unknown types
                stats["unknown_files"] += 1
            else:
                print(f"Skipping file of unknown type: {item.name}")
                stats["skipped"] += 1
                continue

        # Check if we have a mismatch between file extension and actual content type
        current_extension = item.suffix.lower()
        extension_mismatch = current_extension != correct_extension

        # Common mislabeling patterns to check
        mp3_as_mp4 = file_type == "mp3" and current_extension == ".mp4"
        mp4_as_mp3 = file_type == "mp4" and current_extension == ".mp3"

        if extension_mismatch:
            new_filename = f"{item.stem}{correct_extension}"
            mismatch_type = "MP3 saved as MP4" if mp3_as_mp4 else "MP4 saved as MP3" if mp4_as_mp3 else "extension"
            print(f"Detected {mismatch_type} mismatch: Renaming {item.name} to {new_filename}")
            stats["renamed_extensions"] += 1
        else:
            new_filename = item.name

        # Move the file with possibly corrected name
        dest_file = dest_folder / new_filename

        # Handle filename conflicts
        if dest_file.exists():
            base_name = dest_file.stem
            extension = dest_file.suffix
            count = 1
            while dest_file.exists():
                new_name = f"{base_name}_{count}{extension}"
                dest_file = dest_folder / new_name
                count += 1

        try:
            # Use shutil.move which actually moves the file (not copies)
            shutil.move(str(item), str(dest_file))
            stats["success"] += 1
            stats["processed"] += 1

            # Provide clear feedback about the operation
            operation = "Moved and renamed" if item.name != dest_file.name else "Moved"
            print(f"{operation} '{item.name}' to {dest_folder.name}/{dest_file.name}")
        except Exception as e:
            print(f"Error moving {item.name}: {e}")
            stats["errors"] += 1
            stats["processed"] += 1

    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    stats["elapsed_time"] = elapsed_time
    stats["files_per_second"] = stats["processed"] / elapsed_time if elapsed_time > 0 else 0

    print(f"\nSummary: {stats['processed']} files processed in {elapsed_time:.2f} seconds")
    print(f"  - {stats['mp3_files']} MP3 files moved to audio folder")
    print(f"  - {stats['mp4_files']} MP4 files moved to video folder")
    print(f"  - {stats['unknown_files']} files of unknown type")
    print(f"  - {stats['renamed_extensions']} files had extensions corrected")
    print(f"  - {stats['skipped']} files skipped")
    print(f"  - {stats['errors']} errors encountered")
    print(f"Performance: {stats['files_per_second']:.2f} files/second")

    return stats


def main():
    """Process command line arguments and initiate file sorting."""
    parser = argparse.ArgumentParser(
        description="Sort media files based on content signature and correct extensions in both directions."
    )
    parser.add_argument("folder", help="Folder containing files to be sorted")
    parser.add_argument("--unknown", action="store_true", help="Create folder for unknown file types")
    parser.add_argument(
        "--workers", type=int, default=None, help="Maximum number of concurrent workers (default: CPU count)"
    )
    parser.add_argument(
        "--sequential", action="store_true", help="Use single-threaded sequential processing (for benchmarking)"
    )
    args = parser.parse_args()

    if args.sequential:
        # Use the sequential (single-threaded) processing method
        print("Using sequential processing mode for benchmarking")
        sort_files_sequential(args.folder, args.unknown)
    else:
        # Use the parallel processing method
        workers = args.workers
        print(f"Using parallel processing mode with {'auto-detected' if workers is None else workers} workers")
        sort_files(args.folder, args.unknown, workers)

    print("File sorting complete!")


if __name__ == "__main__":
    main()
