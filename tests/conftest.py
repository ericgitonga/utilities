#!/usr/bin/env python3
"""
Test script for MPEG Sorter that:
1. Sets up a test environment with test files
2. Runs the sorter in both sequential and parallel modes
3. Validates the sorting operation
4. Restores the original file structure for re-testing
"""

import os
import sys
import shutil
import time
import argparse
import subprocess
from pathlib import Path


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

# Add the module directory to the Python path
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

# Try to import the MPEG sorter module
try:
    from mpeg_sorter import sort_files, sort_files_sequential
except ImportError:
    # If import fails, define placeholder functions
    print("Warning: Could not import mpeg_sorter module directly.")
    print("Will use command-line execution for testing.")

    def sort_files(source_folder, create_unknown_folder=True, max_workers=None):
        """Placeholder for direct testing - will use command-line instead."""
        raise NotImplementedError("Direct function testing not available - use --command-line option")

    def sort_files_sequential(source_folder, create_unknown_folder=True):
        """Placeholder for direct testing - will use command-line instead."""
        raise NotImplementedError("Direct function testing not available - use --command-line option")


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

    def run_tests(self):
        """Run sorting tests in both sequential and parallel modes."""
        if not self.setup():
            print("Error: Failed to set up test environment.")
            return False

        print("\n" + "=" * 60)
        print("RUNNING MPEG SORTER TESTS")
        print("=" * 60)

        test_results = []

        # Run sequential mode test
        print("\n[TEST] Running in sequential mode...")
        sequential_start = time.time()
        try:
            sort_files_sequential(self.temp_dir)
            sequential_time = time.time() - sequential_start
            self.log(f"Sequential processing completed in {sequential_time:.4f} seconds")

            # Validate sorting results
            result = self._validate_sorting()
            if result:
                print("[PASS] Sequential mode sorting completed successfully")
                test_results.append(("sequential", True, sequential_time))
            else:
                print("[FAIL] Sequential mode sorting validation failed")
                test_results.append(("sequential", False, sequential_time))
        except Exception as e:
            print(f"[ERROR] Sequential mode test failed: {e}")
            test_results.append(("sequential", False, 0))

        # Restore original state
        self._restore_original_state()

        # Run parallel mode test
        print("\n[TEST] Running in parallel mode...")
        parallel_start = time.time()
        try:
            sort_files(self.temp_dir)
            parallel_time = time.time() - parallel_start
            self.log(f"Parallel processing completed in {parallel_time:.4f} seconds")

            # Validate sorting results
            result = self._validate_sorting()
            if result:
                print("[PASS] Parallel mode sorting completed successfully")
                test_results.append(("parallel", True, parallel_time))
            else:
                print("[FAIL] Parallel mode sorting validation failed")
                test_results.append(("parallel", False, parallel_time))
        except Exception as e:
            print(f"[ERROR] Parallel mode test failed: {e}")
            test_results.append(("parallel", False, 0))

        # Display test summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        all_passed = True
        for mode, passed, duration in test_results:
            status = "PASSED" if passed else "FAILED"
            print(f"{mode.capitalize()} Mode: {status} ({duration:.4f} seconds)")
            all_passed = all_passed and passed

        # Compare performance if both tests passed
        if len(test_results) == 2 and all(result[1] for result in test_results):
            sequential_time = test_results[0][2]
            parallel_time = test_results[1][2]

            if sequential_time > 0 and parallel_time > 0:
                speedup = sequential_time / parallel_time
                print(f"\nPerformance Speedup: {speedup:.2f}x faster in parallel mode")

        return all_passed

    def _validate_sorting(self):
        """Validate that files were correctly sorted and renamed."""
        # Check for expected directories
        audio_dir = self.temp_dir / "audio"
        video_dir = self.temp_dir / "video"
        unknown_dir = self.temp_dir / "unknown"

        if not (audio_dir.exists() and video_dir.exists() and unknown_dir.exists()):
            print("[FAIL] One or more expected directories were not created")
            return False

        # Expected files after sorting (path, original_filename)
        expected_files = [
            (video_dir / "video1.mp4", "video1.mp4"),
            (video_dir / "video2_as_audio.mp4", "video2_as_audio.mp3"),  # Extension corrected
            (audio_dir / "audio1.mp3", "audio1.mp3"),
            (audio_dir / "audio2_as_video.mp3", "audio2_as_video.mp4"),  # Extension corrected
            (unknown_dir / "unknown.bin", "unknown.bin"),
        ]

        # Check if all expected files exist
        all_found = True
        for expected_path, original_name in expected_files:
            if expected_path.exists():
                self.log(f"Found correctly sorted file: {expected_path}")

                # Update the current path in original state for restoration
                for item in self.original_state:
                    if item["original_name"] == original_name:
                        item["current_path"] = str(expected_path)
                        break
            else:
                print(f"[FAIL] Expected file not found: {expected_path}")
                all_found = False

        return all_found

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


def run_command_line_test():
    """Run tests using the command-line script instead of imported functions."""
    test_dir = Path(__file__).parent
    temp_dir = test_dir / "temp_test_data"

    # Ensure the temp directory exists and is populated
    tester = MPEGSorterTest(verbose=True)
    if not tester.setup():
        print("Error: Failed to set up test environment.")
        return False

    # Verify the script path
    script_path = Path(SCRIPT_PATH)

    # If script not found at expected location, search common locations
    if not script_path.exists():
        # Define possible alternative paths
        alt_paths = [
            os.path.join(project_root, "mpeg_sorter.py"),
            os.path.join(project_root, "mpeg-sorter", "mpeg_sorter.py"),
            os.path.join(os.getcwd(), "mpeg_sorter.py"),
            os.path.join(os.getcwd(), "mpeg-sorter", "mpeg_sorter.py"),
        ]

        # Try alternative paths
        for path in alt_paths:
            if os.path.exists(path):
                script_path = Path(path)
                break

    if not script_path.exists():
        print("Error: Could not find mpeg_sorter.py script in any expected location.")
        print(f"Main path checked: {SCRIPT_PATH}")
        print("Also searched in:")
        for path in alt_paths:
            print(f"  - {path}")
        return False

    print(f"Found script at: {script_path}")

    print("\n" + "=" * 60)
    print("RUNNING COMMAND-LINE TESTS")
    print("=" * 60)

    # Test sequential mode
    print("\n[TEST] Running command-line sequential mode...")
    seq_cmd = [sys.executable, str(script_path), str(temp_dir), "--sequential"]
    seq_start = time.time()
    seq_result = subprocess.run(seq_cmd, capture_output=True, text=True)
    seq_time = time.time() - seq_start

    if seq_result.returncode == 0:
        print(f"[PASS] Command-line sequential mode completed in {seq_time:.4f} seconds")
    else:
        print("[FAIL] Command-line sequential mode failed:")
        print(seq_result.stderr)

    # Restore original state
    tester._restore_original_state()

    # Test parallel mode
    print("\n[TEST] Running command-line parallel mode...")
    par_cmd = [sys.executable, str(script_path), str(temp_dir)]
    par_start = time.time()
    par_result = subprocess.run(par_cmd, capture_output=True, text=True)
    par_time = time.time() - par_start

    if par_result.returncode == 0:
        print(f"[PASS] Command-line parallel mode completed in {par_time:.4f} seconds")
        if seq_time > 0 and par_time > 0:
            speedup = seq_time / par_time
            print(f"\nPerformance Speedup: {speedup:.2f}x faster in parallel mode")
    else:
        print("[FAIL] Command-line parallel mode failed:")
        print(par_result.stderr)

    # Clean up
    tester.cleanup()

    return seq_result.returncode == 0 and par_result.returncode == 0


def main():
    """Main entry point for the test script."""
    parser = argparse.ArgumentParser(description="Test script for MPEG Sorter")
    parser.add_argument(
        "--command-line", action="store_true", help="Test using command-line script instead of imported functions"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    # If module import failed, force command-line mode
    if "sort_files" in globals() and sort_files.__doc__.startswith("Placeholder"):
        if not args.command_line:
            print("Module import failed. Switching to command-line testing mode.")
            args.command_line = True

    if args.command_line:
        # Run tests using command-line script
        success = run_command_line_test()
    else:
        # Run tests using imported functions
        tester = MPEGSorterTest(verbose=args.verbose)
        success = tester.run_tests()
        tester.cleanup()

    # Exit with appropriate status code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
