"""
Image Similarity Finder - Command Line Interface

This module implements the command line interface for the Image Similarity Finder.
It provides functionality to parse command line arguments and run the finder in CLI mode.

Functions:
    parse_cli_args: Parse command line arguments and create a SearchConfig
    run_cli: Run the finder in CLI mode with the provided config
"""

import sys
import argparse
from typing import Optional

# Use try-except to handle both direct execution and package import
try:
    # Try importing as a package first (when installed)
    from imagesim.models import SearchConfig
    from imagesim.finder import ImageSimilarityFinder
except ImportError:
    # Fall back to direct import (when running from source)
    from models import SearchConfig
    from finder import ImageSimilarityFinder


def parse_cli_args() -> Optional[SearchConfig]:
    """
    Parse command line arguments and create a SearchConfig.

    This function parses the command line arguments and creates a SearchConfig
    object if valid arguments are provided.

    Returns:
        Optional[SearchConfig]: SearchConfig object if valid CLI args, None otherwise

    Note:
        Returns None if GUI mode is requested or if insufficient arguments are provided
    """
    parser = argparse.ArgumentParser(
        description="Find similar images across directories", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("query_image", nargs="?", help="Path to the query image")
    parser.add_argument("search_dirs", nargs="*", help="Directories to search in")
    parser.add_argument("--threshold", type=float, default=0.7, help="Similarity threshold (0-1)")
    parser.add_argument("--max-results", type=int, default=10, help="Maximum number of results")
    parser.add_argument("--gui", "-g", action="store_true", help="Start in GUI mode")
    parser.add_argument(
        "--no-detach", action="store_true", help=argparse.SUPPRESS
    )  # Hidden option for process detachment

    args = parser.parse_args()

    # Check if GUI mode is requested
    if args.gui:
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
        # If not enough arguments for CLI mode and not explicitly requesting GUI,
        # print help and exit
        if not args.gui:
            parser.print_help()
            sys.exit(1)
        return None


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
    def cli_progress_callback(current: int, total: int) -> None:
        """Simple progress callback that prints progress to stdout"""
        if total > 0:
            percent = (current / total) * 100
            sys.stdout.write(f"\rProgress: {current}/{total} ({percent:.1f}%)")
            sys.stdout.flush()
        return False  # Never cancel from CLI progress callback

    results = finder.find_similar_images(cli_progress_callback)

    # End progress line
    if results:
        print("\n")

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
