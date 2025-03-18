"""
Image Similarity Finder - Main Module

This is the main entry point for the Image Similarity Finder application.
It parses command line arguments and starts either the GUI or CLI interface.

Usage:
    python main.py                      # Starts the GUI
    python main.py --gui                # Explicitly starts the GUI
    python main.py image.jpg dir1 dir2  # Runs in CLI mode with the specified arguments
"""

import sys
import os
import argparse

# Use try-except to handle both direct execution and package import
try:
    # Try importing as a package first (when installed)
    from imagesim.cli import parse_cli_args, run_cli
    from imagesim.gui import launch_gui
except ImportError:
    # Fall back to direct import (when running from source)
    from cli import parse_cli_args, run_cli
    from gui import launch_gui


def main() -> None:
    """
    Main entry point for the application.

    This function parses command line arguments and starts either the GUI or
    the command-line interface based on the arguments.
    """
    # Add a simple --no-detach flag to the argument parser to handle it specially
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--no-detach", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--gui", "-g", action="store_true")
    args, remaining = parser.parse_known_args()

    # Check if detach is needed (GUI mode, not already detached)
    if not args.no_detach and (args.gui or len(sys.argv) == 1):
        # Simple detach using nohup-like behavior
        try:
            print("Starting application in background...")

            # Create a simple script to launch the app
            launch_script = f"""#!/bin/bash
python3 {__file__} --no-detach {'--gui' if args.gui else ''} {' '.join(remaining)}
"""
            script_path = os.path.expanduser("~/.image_finder_launch.sh")
            with open(script_path, "w") as f:
                f.write(launch_script)
            os.chmod(script_path, 0o755)

            # Launch it with bash detached
            os.system(f"bash {script_path} > /dev/null 2>&1 &")
            print("Application launched in background.")
            sys.exit(0)
        except Exception as e:
            print(f"Note: Could not detach process: {e}")
            print("Continuing in foreground mode...")
            # Continue with regular execution if detaching fails

    # Now parse the real command line arguments and run the application
    config = parse_cli_args()

    # Start GUI if requested or if no valid CLI args
    if config is None:
        # We're starting the GUI
        try:
            launch_gui()
        except Exception as e:
            print(f"Error launching GUI: {e}")
            import traceback

            traceback.print_exc()
    else:
        # Run in CLI mode with the provided config
        run_cli(config)


if __name__ == "__main__":
    main()
