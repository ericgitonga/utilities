"""
Image Similarity Finder - Image Analysis

This module provides functionality for analyzing and comparing images.
It includes methods for extracting features from images and calculating similarity.

Classes:
    ImageAnalyzer: Class for analyzing and comparing images
"""

import numpy as np
import cv2
from pathlib import Path
from typing import Optional, Union
from sklearn.metrics.pairwise import cosine_similarity


class ImageAnalyzer:
    """
    Class for analyzing and comparing images.

    This class provides methods to extract features from images and
    calculate similarity between images based on their features.
    """

    @staticmethod
    def extract_features(image_path: Union[str, Path]) -> Optional[np.ndarray]:
        """
        Extract features from an image using Histogram of Oriented Gradients (HOG).

        This method loads an image, converts it to grayscale, extracts HOG features,
        and normalizes the feature vector.

        Args:
            image_path (Union[str, Path]): Path to the image file

        Returns:
            Optional[np.ndarray]: Normalized feature vector or None if extraction fails

        Raises:
            No exceptions, but prints error messages if processing fails
        """
        try:
            # Read the image
            img = cv2.imread(str(image_path))
            if img is None:
                print(f"Warning: Could not read image {image_path}")
                return None

            # Resize for consistency
            img = cv2.resize(img, (224, 224))

            # Convert to grayscale and extract HOG features
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Use HOG (Histogram of Oriented Gradients) for feature extraction
            win_size = (224, 224)
            block_size = (16, 16)
            block_stride = (8, 8)
            cell_size = (8, 8)
            nbins = 9
            hog = cv2.HOGDescriptor(win_size, block_size, block_stride, cell_size, nbins)
            features = hog.compute(gray)

            # Normalize the features
            if np.linalg.norm(features) > 0:
                features = features / np.linalg.norm(features)

            return features

        except Exception as e:
            print(f"Error processing {image_path}: {str(e)}")
            return None

    @staticmethod
    def calculate_similarity(features1: np.ndarray, features2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two feature vectors.

        This method compares two feature vectors using cosine similarity,
        which measures the cosine of the angle between them.

        Args:
            features1 (np.ndarray): First feature vector
            features2 (np.ndarray): Second feature vector

        Returns:
            float: Similarity score between 0 and 1, where 1 means identical

        Note:
            Returns 0 if either feature vector is None
        """
        if features1 is None or features2 is None:
            return 0

        # Reshape for cosine_similarity function
        f1 = features1.reshape(1, -1)
        f2 = features2.reshape(1, -1)

        return float(cosine_similarity(f1, f2)[0][0])
