"""
Image Similarity Finder - Core Functionality

This module implements the core functionality for finding similar images
across multiple directories.

Classes:
    ImageSimilarityFinder: Main class for finding similar images
"""

import os
from pathlib import Path
from typing import List, Optional, Callable, Union

# Use try-except to handle both direct execution and package import
try:
    # Try importing as a package first (when installed)
    from imagesim.models import SearchConfig, SimilarityResult
    from imagesim.analyzer import ImageAnalyzer
except ImportError:
    # Fall back to direct import (when running from source)
    from models import SearchConfig, SimilarityResult
    from analyzer import ImageAnalyzer


class ImageSimilarityFinder:
    """
    Main class for finding similar images.

    This class implements the core functionality for finding images similar to a
    reference image across multiple directories.

    Attributes:
        config (SearchConfig): Configuration for the search
        analyzer (ImageAnalyzer): Image analyzer used for feature extraction and comparison
        supported_extensions (set): Set of supported image file extensions
    """

    def __init__(self, config: SearchConfig):
        """
        Initialize the ImageSimilarityFinder with a search configuration.

        Args:
            config (SearchConfig): Configuration for the search
        """
        self.config = config
        self.analyzer = ImageAnalyzer()
        self.supported_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp", ".gif"}

    def find_similar_images(
        self, progress_callback: Optional[Callable[[int, int], Union[None, bool]]] = None
    ) -> List[SimilarityResult]:
        """
        Find images similar to the query image in the search directories.

        This method extracts features from the query image, then searches through
        the specified directories for similar images based on feature comparison.

        Args:
            progress_callback: Optional callback function for progress updates
                Takes two parameters: current progress and total items
                Can return True to signal cancellation

        Returns:
            List[SimilarityResult]: List of SimilarityResult objects sorted by similarity

        Note:
            The search can be time-consuming for large directories with many images
            If the progress_callback returns True, the search will be cancelled
        """
        # Extract features from the query image
        query_features = self.analyzer.extract_features(self.config.query_image)
        if query_features is None:
            print(f"Could not process query image: {self.config.query_image}")
            return []

        # List to store results
        results: List[SimilarityResult] = []

        # Get all image files from search directories
        image_files = self._get_image_files()
        total_files = len(image_files)

        # Process each image
        for i, file_path in enumerate(image_files):
            # Update progress and check for cancellation
            if progress_callback:
                cancel_requested = progress_callback(i, total_files)
                # If the callback returns True, cancel the operation
                if cancel_requested:
                    print("Search cancelled by user")
                    return results  # Return partial results

            # Extract features from the current image
            current_features = self.analyzer.extract_features(file_path)

            if current_features is not None:
                # Calculate similarity
                similarity = self.analyzer.calculate_similarity(query_features, current_features)

                # Add to results if above threshold
                if similarity >= self.config.threshold:
                    results.append(SimilarityResult(path=file_path, similarity=similarity))

        # Final progress update
        if progress_callback:
            cancel_requested = progress_callback(total_files, total_files)
            if cancel_requested:
                print("Search cancelled by user")
                return results  # Return partial results

        # Sort results by similarity (highest first)
        results.sort(key=lambda x: x.similarity, reverse=True)

        # Return top results
        return results[: self.config.max_results]

    def _get_image_files(self) -> List[Path]:
        """
        Get all image files from the search directories.

        This method recursively walks through all search directories and collects
        paths to image files with supported extensions.

        Returns:
            List[Path]: List of paths to image files

        Note:
            Skips the query image itself to avoid self-matches
        """
        image_files: List[Path] = []

        for search_dir in self.config.search_dirs:
            search_path = Path(search_dir)

            for root, _, files in os.walk(search_path):
                for file in files:
                    file_path = Path(root) / file

                    # Skip the query image itself
                    if file_path == Path(self.config.query_image).absolute():
                        continue

                    # Check if the file is an image
                    if file_path.suffix.lower() in self.supported_extensions:
                        image_files.append(file_path)

        return image_files
