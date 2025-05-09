#!/usr/bin/env python3
"""
File sorter that identifies audio and video files based on file signatures and moves them to appropriate folders.
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

    Args:
        source_folder: Path to the folder containing files to be sorted
        create_unknown_folder: Whether to create a folder for files of unknown type
    """
    source_path = Path(source_folder)

    # Create destination folders if they don't exist
    audio_folder = source_path / "audio"
    video_folder = source_path / "video"
    audio_folder.mkdir(exist_ok=True)
    video_folder.mkdir(exist_ok=True)

    if create_unknown_folder:
        unknown_folder = source_path / "unknown"
        unknown_folder.mkdir(exist_ok=True)

    # Process all files in the source folder (not recursively)
    for item in source_path.iterdir():
        if not item.is_file():
            continue

        if item.name.startswith("."):  # Skip hidden files
            continue

        # Skip files that are already in our destination folders
        if item.parent in (audio_folder, video_folder):
            continue

        print(f"Analyzing {item.name}...")
        file_type = get_file_signature(item)

        # Determine destination based on file type
        if file_type == "mp3":
            dest_folder = audio_folder
        elif file_type == "mp4":
            dest_folder = video_folder
        else:
            if create_unknown_folder:
                dest_folder = unknown_folder
            else:
                print(f"Skipping file of unknown type: {item.name}")
                continue

        # Move the file
        dest_file = dest_folder / item.name

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
            shutil.move(item, dest_file)
            print(f"Moved '{item.name}' to {dest_folder.name}/ folder")
        except Exception as e:
            print(f"Error moving {item.name}: {e}")


def main():
    """Process command line arguments and initiate file sorting."""
    parser = argparse.ArgumentParser(description="Sort media files based on their actual content signature.")
    parser.add_argument("folder", help="Folder containing files to be sorted")
    parser.add_argument("--unknown", action="store_true", help="Create folder for unknown file types")
    args = parser.parse_args()

    sort_files(args.folder, args.unknown)
    print("File sorting complete!")


if __name__ == "__main__":
    main()
