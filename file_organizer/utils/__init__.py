"""Utility functions for file organizer."""

from utils.file_operations import process_file, verify_file_integrity
from utils.path_utils import is_safe_path, get_secure_filename, should_skip_file
from utils.categories import (
    get_file_category,
    load_category_config,
    build_extension_mapping,
    DEFAULT_EXTENSION_CATEGORIES,
)
from utils.permissions import check_file_permissions, check_user_permissions
from utils.backup import create_backup
from utils.logging_config import setup_logging

__all__ = [
    "process_file",
    "verify_file_integrity",
    "is_safe_path",
    "get_secure_filename",
    "should_skip_file",
    "get_file_category",
    "load_category_config",
    "build_extension_mapping",
    "DEFAULT_EXTENSION_CATEGORIES",
    "check_file_permissions",
    "check_user_permissions",
    "create_backup",
    "setup_logging",
]
