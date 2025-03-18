"""
Image Similarity Finder - Data Models

This module defines the data models used by the Image Similarity Finder application.
These models provide validation and structure for the application's data.

Classes:
    SearchConfig: Configuration settings for image similarity search
    ImageFeatures: Container for image features extracted from an image
    SimilarityResult: Result of an image similarity comparison
"""

import numpy as np
from typing import List, Optional
from pydantic import BaseModel, Field, validator, DirectoryPath, FilePath


class SearchConfig(BaseModel):
    """
    Configuration settings for image similarity search.

    This model validates and stores the parameters needed for an image similarity search,
    ensuring that all values are within acceptable ranges and that paths exist.

    Attributes:
        query_image (FilePath): Path to the reference image to search for
        search_dirs (List[DirectoryPath]): List of directories to search in
        threshold (float): Similarity threshold (0-1) where 1 means identical
        max_results (int): Maximum number of results to return
    """

    query_image: FilePath = Field(..., description="Path to the query image")
    search_dirs: List[DirectoryPath] = Field(..., min_items=1, description="Directories to search in")
    threshold: float = Field(0.7, ge=0.1, le=1.0, description="Similarity threshold (0-1)")
    max_results: int = Field(10, ge=1, description="Maximum number of results to return")

    @validator("threshold")
    def validate_threshold(cls, v):
        """
        Validate that the threshold is between 0.1 and 1.0.

        Args:
            v (float): The threshold value to validate

        Returns:
            float: The validated threshold

        Raises:
            ValueError: If threshold is outside the valid range
        """
        if v < 0.1 or v > 1.0:
            raise ValueError("Threshold must be between 0.1 and 1.0")
        return v

    @validator("max_results")
    def validate_max_results(cls, v):
        """
        Validate that max_results is at least 1.

        Args:
            v (int): The max_results value to validate

        Returns:
            int: The validated max_results

        Raises:
            ValueError: If max_results is less than 1
        """
        if v < 1:
            raise ValueError("Max results must be at least 1")
        return v


class ImageFeatures(BaseModel):
    """
    Container for image features extracted from an image.

    This model stores the feature vector extracted from an image along with its path.

    Attributes:
        features (Optional[np.ndarray]): Feature vector extracted from the image
        path (FilePath): Path to the image file
    """

    features: Optional[np.ndarray] = None
    path: FilePath

    class Config:
        """
        Pydantic configuration for the ImageFeatures model.

        This allows the model to handle arbitrary types like numpy arrays.
        """

        arbitrary_types_allowed = True


class SimilarityResult(BaseModel):
    """
    Result of an image similarity comparison.

    This model represents a single result from a similarity search,
    including the path to the matched image and its similarity score.

    Attributes:
        path (FilePath): Path to the similar image
        similarity (float): Similarity score between 0 and 1
    """

    path: FilePath
    similarity: float = Field(..., ge=0, le=1)

    class Config:
        """
        Pydantic configuration for the SimilarityResult model.

        This allows the model to handle arbitrary types.
        """

        arbitrary_types_allowed = True
