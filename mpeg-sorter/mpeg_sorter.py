#!/usr/bin/env python3
"""
File sorter that identifies audio and video files based on file signatures,
moves them to appropriate folders, and corrects file extensions in both directions
(MP3 → MP4 and MP4 → MP3).
"""

import shutil
import argparse
from pathlib import Path


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


def sort_files(source_folder, create_unknown_folder=False):
    """
    Sort files from source folder into video and audio subdirectories based on file signatures.
    Corrects file extensions to match the actual file type in both directions.

    Args:
        source_folder: Path to the folder containing files to be sorted
        create_unknown_folder: Whether to create a folder for files of unknown type
    """
    source_path = Path(source_folder).resolve()
    print(f"Processing files in: {source_path}")

    # Verify the source directory exists
    if not source_path.exists():
        print(f"Error: Source directory '{source_path}' does not exist.")
        return

    if not source_path.is_dir():
        print(f"Error: '{source_path}' is not a directory.")
        return

    # Create destination folders WITHIN the source directory
    audio_folder = source_path / "audio"
    video_folder = source_path / "video"

    # Create folders with parents=True to handle missing parent directories
    audio_folder.mkdir(exist_ok=True, parents=True)
    video_folder.mkdir(exist_ok=True, parents=True)

    print(f"Created audio directory: {audio_folder}")
    print(f"Created video directory: {video_folder}")

    if create_unknown_folder:
        unknown_folder = source_path / "unknown"
        unknown_folder.mkdir(exist_ok=True, parents=True)
        print(f"Created unknown directory: {unknown_folder}")

    # Keep track of processed files
    files_processed = 0

    # Process all files in the source folder (not recursively)
    for item in source_path.iterdir():
        if not item.is_file():
            continue

        if item.name.startswith("."):  # Skip hidden files
            continue

        # Skip files that are already in our destination folders
        if any(str(item).startswith(str(folder)) for folder in [audio_folder, video_folder]):
            continue

        print(f"Analyzing {item.name}...")
        file_type = get_file_signature(item)

        # Determine destination based on file type
        if file_type == "mp3":
            dest_folder = audio_folder
            correct_extension = ".mp3"
        elif file_type == "mp4":
            dest_folder = video_folder
            correct_extension = ".mp4"
        else:
            if create_unknown_folder:
                dest_folder = unknown_folder
                correct_extension = item.suffix  # Keep original extension for unknown types
            else:
                print(f"Skipping file of unknown type: {item.name}")
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
            files_processed += 1

            # Provide clear feedback about the operation
            operation = "Moved and renamed" if item.name != dest_file.name else "Moved"
            print(f"{operation} '{item.name}' to {dest_folder.name}/{dest_file.name}")
        except Exception as e:
            print(f"Error moving {item.name}: {e}")

    print(f"\nSummary: {files_processed} files processed and moved to subdirectories")


def main():
    """Process command line arguments and initiate file sorting."""
    parser = argparse.ArgumentParser(
        description="Sort media files based on content signature and correct extensions in both directions."
    )
    parser.add_argument("folder", help="Folder containing files to be sorted")
    parser.add_argument("--unknown", action="store_true", help="Create folder for unknown file types")
    args = parser.parse_args()

    sort_files(args.folder, args.unknown)
    print("File sorting complete!")


if __name__ == "__main__":
    main()
