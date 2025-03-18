"""
Image Similarity Finder - Main Package Entry Point

This allows the package to be executed directly:
python -m imagesim

It directly contains the main functionality rather than importing
to avoid potential import issues.
"""

import sys
import os
import platform
import subprocess
import argparse
import tempfile
from typing import Optional

# These imports will be relative to the installation directory
from imagesim.models import SearchConfig
from imagesim.finder import ImageSimilarityFinder
import imagesim.gui as gui_module


def detach_terminal_linux():
    """
    Detach from terminal on Linux using nohup.

    This launches a new, detached instance of the application and exits the original process.
    """
    # Prepare the command
    args = ["nohup", sys.executable, "-m", "imagesim"] + sys.argv[1:] + ["--no-detach"]

    # Redirect standard file descriptors
    with open(os.devnull, "w") as devnull:
        # Start the detached process
        subprocess.Popen(
            args,
            stdout=devnull,
            stderr=devnull,
            stdin=devnull,
            preexec_fn=os.setpgrp,  # This is the key for detaching
            close_fds=True,
            start_new_session=True,
        )

    # Exit the original process
    sys.exit(0)


def detach_terminal_macos():
    """
    Detach from terminal on macOS.

    This launches a new, detached instance of the application and exits the original process.
    """
    # Prepare the command
    args = [sys.executable, "-m", "imagesim"] + sys.argv[1:] + ["--no-detach"]

    # Create a launch script in a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".command", delete=False) as f:
        script_path = f.name
        f.write("#!/bin/bash\n")
        f.write(" ".join(args))
        f.write(" &\n")  # Run in background
        f.write("disown\n")  # Detach process

    # Make the script executable
    os.chmod(script_path, 0o755)

    # Use the 'open' command to run the script in a new Terminal window
    subprocess.Popen(["open", script_path])

    # Exit the original process
    sys.exit(0)


def detach_terminal_windows():
    """
    Detach from terminal on Windows.

    This launches a new, detached instance of the application and exits the original process.
    """
    # Prepare the command
    args = [sys.executable, "-m", "imagesim"] + sys.argv[1:] + ["--no-detach"]

    # Use pythonw.exe instead of python.exe if possible (prevents console window)
    python_path = sys.executable
    pythonw_path = python_path.replace("python.exe", "pythonw.exe")
    if os.path.exists(pythonw_path):
        args[0] = pythonw_path

    # Start the process detached
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0  # SW_HIDE

    subprocess.Popen(
        args,
        startupinfo=startupinfo,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
        close_fds=True,
        shell=False,
    )

    # Exit the original process
    sys.exit(0)


def parse_cli_args() -> Optional[SearchConfig]:
    """
    Parse command line arguments and create a SearchConfig.

    This function parses the command line arguments and creates a SearchConfig
    object if valid arguments are provided.

    Returns:
        Optional[SearchConfig]: SearchConfig object if valid CLI args, None otherwise
    """
    parser = argparse.ArgumentParser(
        description="Find similar images across directories", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("query_image", nargs="?", help="Path to the query image")
    parser.add_argument("search_dirs", nargs="*", help="Directories to search in")
    parser.add_argument("--threshold", type=float, default=0.7, help="Similarity threshold (0-1)")
    parser.add_argument("--max-results", type=int, default=10, help="Maximum number of results")
    parser.add_argument("--gui", "-g", action="store_true", help="Start in GUI mode")
    parser.add_argument("--no-detach", action="store_true", help=argparse.SUPPRESS)  # Hidden option

    args = parser.parse_args()

    # Check if GUI mode is requested
    if args.gui or (not args.query_image and not args.search_dirs):
        return None

    # Validate and create config if CLI mode
    if args.query_image and args.search_dirs:
        try:
            config = SearchConfig(
                query_image=args.query_image,
                search_dirs=args.search_dirs,
                threshold=args.threshold,
                max_results=args.max_results,
            )
            return config
        except Exception as e:
            print(f"Error in configuration: {str(e)}")
            parser.print_help()
            sys.exit(1)
    else:
        # Print help if not enough arguments for CLI mode
        parser.print_help()
        sys.exit(1)


def run_cli(config: SearchConfig) -> None:
    """
    Run the finder in CLI mode with the provided config.

    This function creates an ImageSimilarityFinder with the provided config,
    runs the search, and prints the results to the console.

    Args:
        config (SearchConfig): Configuration for the search
    """
    print(f"Searching for images similar to: {config.query_image}")
    print(f"Search directories: {', '.join(str(d) for d in config.search_dirs)}")
    print(f"Similarity threshold: {config.threshold}")
    print(f"Maximum results: {config.max_results}")
    print("\nSearching...")

    # Create finder and run search
    finder = ImageSimilarityFinder(config)

    # Define a simple progress callback for CLI
    def cli_progress_callback(current: int, total: int) -> bool:
        """Simple progress callback that prints progress to stdout"""
        if total > 0:
            percent = (current / total) * 100
            sys.stdout.write(f"\rProgress: {current}/{total} ({percent:.1f}%)")
            sys.stdout.flush()
        return False  # Never cancel from CLI progress callback

    results = finder.find_similar_images(cli_progress_callback)

    # Print results
    if not results:
        print("\nNo similar images found.")
    else:
        print(f"\nFound {len(results)} similar images:")
        print("-" * 80)
        print(f"{'Similarity':^12} | {'Image Path'}")
        print("-" * 80)

        for result in results:
            print(f"{result.similarity:^12.4f} | {result.path}")


def main():
    """Main entry point for the application."""
    # Check if this is a detached process (has --no-detach flag)
    if "--no-detach" in sys.argv:
        # Remove the flag to prevent parsing issues
        sys.argv.remove("--no-detach")
    else:
        # Check if GUI mode is explicitly requested or implied
        if len(sys.argv) > 1 and (sys.argv[1] == "--gui" or sys.argv[1] == "-g"):
            # Detach for GUI mode based on platform
            if platform.system() == "Linux":
                detach_terminal_linux()
            elif platform.system() == "Darwin":  # macOS
                detach_terminal_macos()
            elif platform.system() == "Windows":
                detach_terminal_windows()
        # Also detach if no arguments (implicit GUI mode)
        elif len(sys.argv) == 1:
            # Detach based on platform
            if platform.system() == "Linux":
                detach_terminal_linux()
            elif platform.system() == "Darwin":  # macOS
                detach_terminal_macos()
            elif platform.system() == "Windows":
                detach_terminal_windows()

    # Regular execution continues here for either:
    # 1. CLI mode
    # 2. Detached GUI process
    # 3. Already detached process (--no-detach flag present)
    config = parse_cli_args()

    if config is None:
        # Start GUI
        gui_module.launch_gui()
    else:
        # Run CLI mode
        run_cli(config)


if __name__ == "__main__":
    main()
