"""
Image Similarity Finder - Data Models

This module defines the data models used throughout the application.
It provides type-safe models with validation using Pydantic.

Classes:
    FilePath: Custom path type for file paths with validation
    DirectoryPath: Custom path type for directory paths with validation
    SimilarityResult: Result of an image similarity comparison
    SearchConfig: Configuration settings for image similarity search
"""

from pydantic import BaseModel, Field, validator
from typing import List
from pathlib import Path


class FilePath(Path):
    """Custom path type for file paths."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field=None, values=None):
        """
        Validate that the path exists and is a file.

        Args:
            v: The value to validate
            field: The field being validated (added to match Pydantic's expected signature)
            values: Values validated so far (added to match Pydantic's expected signature)

        Returns:
            Path: Validated path

        Raises:
            TypeError: If the path is not a string or Path object
            ValueError: If the path does not exist or is not a file
        """
        if not isinstance(v, (str, Path)):
            raise TypeError("Path must be a string or Path object")
        path = Path(v)
        if not path.exists():
            raise ValueError(f"File '{path}' does not exist")
        if not path.is_file():
            raise ValueError(f"'{path}' is not a file")
        return path


class DirectoryPath(Path):
    """Custom path type for directory paths."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field=None, values=None):
        """
        Validate that the path exists and is a directory.

        Args:
            v: The value to validate
            field: The field being validated (added to match Pydantic's expected signature)
            values: Values validated so far (added to match Pydantic's expected signature)

        Returns:
            Path: Validated path

        Raises:
            TypeError: If the path is not a string or Path object
            ValueError: If the path does not exist or is not a directory
        """
        if not isinstance(v, (str, Path)):
            raise TypeError("Path must be a string or Path object")
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Directory '{path}' does not exist")
        if not path.is_dir():
            raise ValueError(f"'{path}' is not a directory")
        return path


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
    similarity: float = Field(..., ge=0)

    @validator("similarity")
    def clamp_similarity_to_valid_range(cls, v, values=None):
        """
        Ensure similarity value is in the valid range [0, 1].

        This handles floating-point precision issues that might produce
        values slightly larger than 1.0.

        Args:
            v (float): Similarity value
            values: Values validated so far (added to match Pydantic's expected signature)

        Returns:
            float: Value clamped to range [0, 1]
        """
        return min(max(v, 0.0), 1.0)

    class Config:
        """
        Pydantic configuration for the SimilarityResult model.

        This allows the model to handle arbitrary types.
        """

        arbitrary_types_allowed = True


class SearchConfig(BaseModel):
    """
    Configuration settings for image similarity search.

    This model validates and stores the parameters needed for an image similarity search,
    ensuring that all values are within acceptable ranges and that paths exist.

    Attributes:
        query_image (FilePath): Path to the reference image to search for
        search_dirs (List[str]): List of directories to search in
        threshold (float): Similarity threshold (0-1) where 1 means identical
        max_results (int): Maximum number of results to return
    """

    query_image: FilePath
    search_dirs: List[str]
    threshold: float = Field(0.7, ge=0.1, le=1.0)
    max_results: int = Field(10, ge=1)

    @validator("search_dirs")
    def validate_search_dirs(cls, dirs, values=None):
        """
        Validate that all search directories exist.

        Args:
            dirs (List[str]): List of directory paths
            values: Values validated so far (added to match Pydantic's expected signature)

        Returns:
            List[str]: Validated directory paths

        Raises:
            ValueError: If any directory does not exist
        """
        for dir_path in dirs:
            path = Path(dir_path)
            if not path.exists():
                raise ValueError(f"Directory '{path}' does not exist")
            if not path.is_dir():
                raise ValueError(f"'{path}' is not a directory")
        return dirs

    class Config:
        """
        Pydantic configuration for the SearchConfig model.
        """

        arbitrary_types_allowed = True
