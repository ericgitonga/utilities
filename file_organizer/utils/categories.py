"""Category-related utilities for file organizer."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

# Default category mappings
DEFAULT_EXTENSION_CATEGORIES = {
    "Documents": ["pdf", "doc", "docx", "txt", "rtf", "odt", "md", "csv", "xls", "xlsx", "ppt", "pptx"],
    "Images": ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp", "svg", "ico", "heic", "psd", "dng", "nef"],
    "Audio": ["mp3", "wav", "ogg", "flac", "aac", "m4a"],
    "Video": ["mp4", "avi", "mkv", "mov", "wmv", "flv", "webm", "m4v"],
    "Archives": ["zip", "rar", "tar", "gz", "7z"],
    "Code": ["py", "js", "html", "css", "java", "c", "cpp", "go", "rs", "php", "rb", "ipynb", "jar"],
}

logger = logging.getLogger("file_organizer")


def get_file_category(extension: str, category_mapping: Dict[str, str]) -> str:
    """
    Determine the category of a file based on its extension.
    Uses a pre-computed mapping for O(1) lookup.

    Args:
        extension: The file extension without the dot
        category_mapping: Mapping from extension to category

    Returns:
        str: The category name to use as a directory name
    """
    return category_mapping.get(extension.lower(), "Misc")


def load_category_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, List[str]]:
    """
    Load category configuration from a JSON file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Dict: Dictionary of categories and their extensions
    """
    if not config_path:
        return DEFAULT_EXTENSION_CATEGORIES

    try:
        config_path = Path(config_path)
        if not config_path.exists():
            logger.warning(f"Config file {config_path} not found. Using default categories.")
            return DEFAULT_EXTENSION_CATEGORIES

        with open(config_path, "r") as f:
            custom_categories = json.load(f)

        # Validate the config format
        if not isinstance(custom_categories, dict):
            logger.warning("Invalid config format. Using default categories.")
            return DEFAULT_EXTENSION_CATEGORIES

        for category, extensions in custom_categories.items():
            if not isinstance(extensions, list):
                logger.warning(f"Invalid extension list for {category}. Using default categories.")
                return DEFAULT_EXTENSION_CATEGORIES

        return custom_categories

    except (json.JSONDecodeError, PermissionError, OSError) as e:
        logger.warning(f"Error loading config file: {str(e)}. Using default categories.")
        return DEFAULT_EXTENSION_CATEGORIES


def build_extension_mapping(categories: Dict[str, List[str]]) -> Dict[str, str]:
    """
    Build a lookup dictionary for fast extension to category mapping.

    Args:
        categories: Dictionary of categories and their extensions

    Returns:
        Dict: Mapping of each extension to its category
    """
    mapping = {}
    for category, extensions in categories.items():
        for ext in extensions:
            mapping[ext.lower()] = category
    return mapping
