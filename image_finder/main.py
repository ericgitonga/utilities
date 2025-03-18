"""
Image Similarity Finder - Main Module

This is the main entry point for the Image Similarity Finder application.
It parses command line arguments and starts either the GUI or CLI interface.

Usage:
    python main.py                      # Starts the GUI
    python main.py --gui                # Explicitly starts the GUI
    python main.py image.jpg dir1 dir2  # Runs in CLI mode with the specified arguments
"""

from cli import parse_cli_args, run_cli
from gui import launch_gui


def main() -> None:
    """
    Main entry point for the application.

    This function parses command line arguments and starts either the GUI or
    the command-line interface based on the arguments.
    """
    config = parse_cli_args()

    # Start GUI if requested or if no valid CLI args
    if config is None:
        launch_gui()
    else:
        # Run in CLI mode with the provided config
        run_cli(config)


if __name__ == "__main__":
    main()
