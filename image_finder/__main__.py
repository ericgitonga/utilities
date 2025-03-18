"""
Image Similarity Finder - Main Package Entry Point

This allows the package to be executed directly:
python -m imagesim

It directly contains the main functionality rather than importing
to avoid potential import issues.
"""

import sys
import argparse
from typing import Optional

# These imports will be relative to the installation directory
from imagesim.models import SearchConfig
from imagesim.finder import ImageSimilarityFinder
import imagesim.gui as gui_module


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
    results = finder.find_similar_images()

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
    config = parse_cli_args()

    if config is None:
        # Start GUI
        gui_module.launch_gui()
    else:
        # Run CLI mode
        run_cli(config)


if __name__ == "__main__":
    main()
