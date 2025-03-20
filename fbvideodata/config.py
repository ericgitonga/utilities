"""
Configuration module for the Facebook Video Data Tool application.
"""

import os
import json

from .constants import SETTINGS_FILENAME, DEFAULT_MAX_VIDEOS, DEFAULT_EXPORT_FORMAT
from .constants import DEFAULT_SPREADSHEET_NAME, DEFAULT_WORKSHEET_NAME, DEFAULT_OUTPUT_PATH


class Config:
    """Application configuration manager."""

    def __init__(self):
        """Initialize configuration with default values."""
        self.page_id = ""
        self.token_from_file = False
        self.token_path = ""
        self.access_token = ""
        self.max_videos = DEFAULT_MAX_VIDEOS
        self.export_format = DEFAULT_EXPORT_FORMAT
        self.spreadsheet_name = DEFAULT_SPREADSHEET_NAME
        self.worksheet_name = DEFAULT_WORKSHEET_NAME
        self.output_path = os.path.expanduser(DEFAULT_OUTPUT_PATH)
        self.credentials_path = ""

        # Load saved settings if they exist
        self.settings_path = os.path.join(os.path.expanduser("~"), SETTINGS_FILENAME)
        self.load_settings()

    def load_settings(self):
        """Load settings from file."""
        if os.path.isfile(self.settings_path):
            try:
                with open(self.settings_path, "r") as f:
                    settings = json.load(f)

                # Apply settings
                for key, value in settings.items():
                    if hasattr(self, key):
                        setattr(self, key, value)

                # Handle special cases
                if self.output_path and not os.path.isdir(self.output_path):
                    self.output_path = os.path.expanduser(DEFAULT_OUTPUT_PATH)

                if self.credentials_path and not os.path.isfile(self.credentials_path):
                    self.credentials_path = ""
                else:
                    # Set environment variable for Google API
                    if self.credentials_path:
                        os.environ["GOOGLE_CREDENTIALS_PATH"] = self.credentials_path

                return True
            except (IOError, json.JSONDecodeError):
                return False
        return False

    def save_settings(self):
        """Save settings to file."""
        settings = {
            "page_id": self.page_id,
            "token_from_file": self.token_from_file,
            "token_path": self.token_path,
            "max_videos": self.max_videos,
            "export_format": self.export_format,
            "spreadsheet_name": self.spreadsheet_name,
            "worksheet_name": self.worksheet_name,
            "output_path": self.output_path,
            "credentials_path": self.credentials_path,
        }

        try:
            with open(self.settings_path, "w") as f:
                json.dump(settings, f, indent=2)
            return True
        except (IOError, OSError):
            return False

    def get_access_token(self):
        """Get the current access token from file or direct entry."""
        if self.token_from_file and self.token_path and os.path.isfile(self.token_path):
            try:
                with open(self.token_path, "r") as f:
                    token = f.read().strip()
                    if token:
                        return token
            except (IOError, OSError):
                return None
        return self.access_token if self.access_token else None
