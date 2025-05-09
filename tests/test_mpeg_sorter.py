#!/usr/bin/env python3
"""
Pytest-compatible test module for MPEG Sorter.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import pytest


# Get the absolute path to the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Set up paths to access the mpeg-sorter module
mpeg_sorter_dir = os.path.join(project_root, "mpeg-sorter")
if os.path.isdir(mpeg_sorter_dir):
    # If there's a mpeg-sorter subdirectory, use it
    SCRIPT_PATH = os.path.join(mpeg_sorter_dir, "mpeg_sorter.py")
    MODULE_DIR = mpeg_sorter_dir
else:
    # Otherwise, assume it's directly in the project root
    SCRIPT_PATH = os.path.join(project_root, "mpeg_sorter.py")
    MODULE_DIR = project_root


# Include MPEGSorterTest class directly instead of importing
class MPEGSorterTest:
    """Test class for MPEG Sorter functionality."""

    def __init__(self, verbose=False):
        """Initialize the test environment."""
        self.verbose = verbose

        # Set up paths
        self.test_dir = Path(__file__).parent
        self.data_dir = self.test_dir / "data"
        self.temp_dir = self.test_dir / "temp_test_data"

        # Define test files (filename, type)
        self.test_files = [
            ("video1.mp4", "video"),  # Correctly named MP4
            ("video2_as_audio.mp3", "video"),  # MP4 with incorrect .mp3 extension
            ("audio1.mp3", "audio"),  # Correctly named MP3
            ("audio2_as_video.mp4", "audio"),  # MP3 with incorrect .mp4 extension
            ("unknown.bin", "unknown"),  # Unknown file type
        ]

        # Track original file state for restoration
        self.original_state = []

    def log(self, message):
        """Print log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[TEST] {message}")

    def setup(self):
        """Set up the test environment with sample files."""
        self.log("Setting up test environment...")

        # Create temp test directory if it doesn't exist
        if not self.temp_dir.exists():
            self.temp_dir.mkdir(parents=True, exist_ok=True)

        # If data directory doesn't exist or is empty, create and populate with test data
        if not self.data_dir.exists() or not any(self.data_dir.iterdir()):
            print("Test data not found. Initializing test files...")
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self._create_test_files()

        # Copy test files from data dir to temp dir
        for filename, _ in self.test_files:
            source = self.data_dir / filename
            dest = self.temp_dir / filename

            if source.exists():
                shutil.copy2(source, dest)
                self.log(f"Copied {filename} to test directory")

                # Remember the original state (for restoration)
                self.original_state.append(
                    {"original_name": filename, "original_path": str(dest), "current_path": str(dest)}
                )
            else:
                print(f"Warning: Test file {filename} not found in data directory")

        return len(self.original_state) > 0

    def _create_test_files(self):
        """Create sample test files with correct signatures if they don't exist."""
        self.log("Creating sample test files...")

        # Ensure the data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Create an MP4 video file (minimal valid signature)
        video1_path = self.data_dir / "video1.mp4"
        if not video1_path.exists():
            with open(video1_path, "wb") as f:
                # ISO Base Media file signature (MP4)
                f.write(b"\x00\x00\x00\x18\x66\x74\x79\x70\x6d\x70\x34\x32")
                f.write(b"\x00" * 100)  # Padding
            self.log(f"Created test file: {video1_path}")

        # Create another MP4 but with .mp3 extension (to test extension correction)
        video2_path = self.data_dir / "video2_as_audio.mp3"
        if not video2_path.exists():
            with open(video2_path, "wb") as f:
                # Another valid MP4 signature
                f.write(b"\x00\x00\x00\x20\x66\x74\x79\x70\x69\x73\x6f\x6d")
                f.write(b"\x00" * 100)  # Padding
            self.log(f"Created test file: {video2_path}")

        # Create an MP3 audio file
        audio1_path = self.data_dir / "audio1.mp3"
        if not audio1_path.exists():
            with open(audio1_path, "wb") as f:
                # ID3 tag (common in MP3)
                f.write(b"\x49\x44\x33\x03\x00\x00\x00\x00\x00\x00")
                f.write(b"\x00" * 100)  # Padding
            self.log(f"Created test file: {audio1_path}")

        # Create another MP3 but with .mp4 extension (to test extension correction)
        audio2_path = self.data_dir / "audio2_as_video.mp4"
        if not audio2_path.exists():
            with open(audio2_path, "wb") as f:
                # MPEG-1 Layer 3 signature
                f.write(b"\xff\xfb\x90\x44\x00\x00\x00\x00\x00\x00")
                f.write(b"\x00" * 100)  # Padding
            self.log(f"Created test file: {audio2_path}")

        # Create an unknown file type
        unknown_path = self.data_dir / "unknown.bin"
        if not unknown_path.exists():
            with open(unknown_path, "wb") as f:
                # Some arbitrary bytes that don't match known signatures
                f.write(b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a")
                f.write(b"\x00" * 100)  # Padding
            self.log(f"Created test file: {unknown_path}")

        print(f"Test data initialized in {self.data_dir}")

    def _restore_original_state(self):
        """Restore files to their original state and remove created directories."""
        self.log("Restoring original file structure...")

        # Move all files back to their original locations
        for item in self.original_state:
            current_path = Path(item["current_path"])
            original_path = Path(item["original_path"])

            if current_path.exists() and current_path != original_path:
                # Create parent directory if it doesn't exist
                original_path.parent.mkdir(parents=True, exist_ok=True)

                try:
                    shutil.move(str(current_path), str(original_path))
                    self.log(f"Restored {current_path} to {original_path}")

                    # Update the current path
                    item["current_path"] = str(original_path)
                except Exception as e:
                    print(f"Warning: Failed to restore {current_path}: {e}")

        # Clean up directories
        for directory in ["audio", "video", "unknown"]:
            dir_path = self.temp_dir / directory
            if dir_path.exists():
                try:
                    # Only attempt to remove if empty
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        self.log(f"Removed directory: {dir_path}")
                except Exception as e:
                    print(f"Warning: Failed to remove directory {dir_path}: {e}")

    def cleanup(self):
        """Clean up the entire test environment."""
        self.log("Performing final cleanup...")

        # Restore original state first
        self._restore_original_state()

        try:
            # Remove the temp test directory if it's empty
            if self.temp_dir.exists():
                if not any(self.temp_dir.iterdir()):
                    self.temp_dir.rmdir()
                    self.log(f"Removed test directory: {self.temp_dir}")
                else:
                    self.log(f"Could not remove test directory as it's not empty: {self.temp_dir}")
        except Exception as e:
            print(f"Warning: Failed to clean up test directory: {e}")


# Import the MPEG sorter module if possible
try:
    if MODULE_DIR not in sys.path:
        sys.path.insert(0, MODULE_DIR)
    from mpeg_sorter import sort_files, sort_files_sequential

    DIRECT_IMPORT_AVAILABLE = True
except ImportError:
    DIRECT_IMPORT_AVAILABLE = False


@pytest.fixture
def test_environment():
    """Set up and tear down the test environment."""
    tester = MPEGSorterTest(verbose=True)
    tester.setup()
    yield tester
    tester.cleanup()


def test_script_exists():
    """Test that the script file exists at the expected location."""
    # Try to find the script in multiple possible locations
    script_paths = [
        SCRIPT_PATH,
        os.path.join(project_root, "mpeg_sorter.py"),
        os.path.join(project_root, "mpeg-sorter", "mpeg_sorter.py"),
    ]

    script_found = False
    for path in script_paths:
        if os.path.exists(path):
            script_found = True
            print(f"Found script at: {path}")
            break

    assert script_found, "mpeg_sorter.py not found in any expected location"


@pytest.mark.skipif(not os.path.exists(SCRIPT_PATH), reason="Script not found")
def test_command_line_sequential(test_environment):
    """Test the script in sequential mode using command-line execution."""
    temp_dir = test_environment.temp_dir

    # Run the script in sequential mode
    cmd = [sys.executable, SCRIPT_PATH, str(temp_dir), "--sequential"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Print output for debugging
    print(f"Command: {' '.join(cmd)}")
    print(f"Exit code: {result.returncode}")
    if result.stdout:
        print(f"Output:\n{result.stdout}")
    if result.stderr:
        print(f"Error output:\n{result.stderr}")

    # Verify that the script ran successfully
    assert result.returncode == 0, f"Command failed with exit code {result.returncode}"

    # Verify that directories were created
    audio_dir = temp_dir / "audio"
    video_dir = temp_dir / "video"
    unknown_dir = temp_dir / "unknown"

    assert audio_dir.exists(), "Audio directory was not created"
    assert video_dir.exists(), "Video directory was not created"
    assert unknown_dir.exists(), "Unknown directory was not created"


@pytest.mark.skipif(not os.path.exists(SCRIPT_PATH), reason="Script not found")
def test_command_line_parallel(test_environment):
    """Test the script in parallel mode using command-line execution."""
    temp_dir = test_environment.temp_dir

    # Run the script in parallel mode
    cmd = [sys.executable, SCRIPT_PATH, str(temp_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Verify that the script ran successfully
    assert result.returncode == 0, f"Command failed with exit code {result.returncode}"

    # Verify that directories were created
    audio_dir = temp_dir / "audio"
    video_dir = temp_dir / "video"
    unknown_dir = temp_dir / "unknown"

    assert audio_dir.exists(), "Audio directory was not created"
    assert video_dir.exists(), "Video directory was not created"
    assert unknown_dir.exists(), "Unknown directory was not created"


@pytest.mark.skipif(not DIRECT_IMPORT_AVAILABLE, reason="Module import not available")
def test_direct_sequential(test_environment):
    """Test the sequential processing function directly."""
    temp_dir = test_environment.temp_dir

    # Call the sequential function directly
    sort_files_sequential(temp_dir)

    # Verify that directories were created
    audio_dir = temp_dir / "audio"
    video_dir = temp_dir / "video"
    unknown_dir = temp_dir / "unknown"

    assert audio_dir.exists(), "Audio directory was not created"
    assert video_dir.exists(), "Video directory was not created"
    assert unknown_dir.exists(), "Unknown directory was not created"


@pytest.mark.skipif(not DIRECT_IMPORT_AVAILABLE, reason="Module import not available")
def test_direct_parallel(test_environment):
    """Test the parallel processing function directly."""
    temp_dir = test_environment.temp_dir

    # Call the parallel function directly
    sort_files(temp_dir)

    # Verify that directories were created
    audio_dir = temp_dir / "audio"
    video_dir = temp_dir / "video"
    unknown_dir = temp_dir / "unknown"

    assert audio_dir.exists(), "Audio directory was not created"
    assert video_dir.exists(), "Video directory was not created"
    assert unknown_dir.exists(), "Unknown directory was not created"


if __name__ == "__main__":
    # This allows running the tests directly (not using pytest)
    print("This module is designed to be run with pytest.")
    print("Please use: pytest test_mpeg_sorter_pytest.py")
