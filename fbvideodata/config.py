"""
Configuration module for the Facebook Video Data Tool application.
"""

import os
import json
from pydantic import BaseModel, Field, validator

from .constants import SETTINGS_FILENAME, DEFAULT_MAX_VIDEOS, DEFAULT_EXPORT_FORMAT
from .constants import DEFAULT_SPREADSHEET_NAME, DEFAULT_WORKSHEET_NAME, DEFAULT_OUTPUT_PATH


class AppConfig(BaseModel):
    """Pydantic model for application configuration."""

    page_id: str = Field(default="", description="Facebook page ID")
    token_from_file: bool = Field(default=False, description="Load token from file instead of direct input")
    token_path: str = Field(default="", description="Path to file containing access token")
    access_token: str = Field(default="", description="Facebook API access token")
    max_videos: int = Field(default=DEFAULT_MAX_VIDEOS, description="Maximum number of videos to fetch")
    export_format: str = Field(default=DEFAULT_EXPORT_FORMAT, description="Export format (CSV or Google)")
    spreadsheet_name: str = Field(default=DEFAULT_SPREADSHEET_NAME, description="Google Sheets spreadsheet name")
    worksheet_name: str = Field(default=DEFAULT_WORKSHEET_NAME, description="Google Sheets worksheet name")
    output_path: str = Field(default=DEFAULT_OUTPUT_PATH, description="Output directory for exports")
    credentials_path: str = Field(default="", description="Path to Google API credentials file")

    @validator("max_videos")
    def validate_max_videos(cls, v):
        """Validate max_videos is within reasonable range."""
        if v < 1:
            return DEFAULT_MAX_VIDEOS
        if v > 1000:
            return 1000
        return v

    @validator("export_format")
    def validate_export_format(cls, v):
        """Validate export format is supported."""
        if v not in ["CSV", "Google"]:
            return DEFAULT_EXPORT_FORMAT
        return v

    @validator("output_path")
    def validate_output_path(cls, v):
        """Expand user directory in output path."""
        if v:
            return os.path.expanduser(v)
        return os.path.expanduser(DEFAULT_OUTPUT_PATH)

    class Config:
        """Configuration for the Pydantic model."""

        # Allow extra fields for future compatibility
        extra = "ignore"


class Config:
    """Application configuration manager using Pydantic for validation."""

    def __init__(self):
        """Initialize configuration with default values."""
        self.settings_path = os.path.join(os.path.expanduser("~"), SETTINGS_FILENAME)
        self.config = AppConfig()
        self.load_settings()

    def load_settings(self):
        """Load settings from file."""
        if os.path.isfile(self.settings_path):
            try:
                with open(self.settings_path, "r") as f:
                    settings = json.load(f)

                # Create a new Pydantic model instance with loaded settings
                self.config = AppConfig(**settings)

                # Handle special cases
                if self.config.output_path and not os.path.isdir(self.config.output_path):
                    self.config.output_path = os.path.expanduser(DEFAULT_OUTPUT_PATH)

                if self.config.credentials_path and not os.path.isfile(self.config.credentials_path):
                    self.config.credentials_path = ""
                else:
                    # Set environment variable for Google API
                    if self.config.credentials_path:
                        os.environ["GOOGLE_CREDENTIALS_PATH"] = self.config.credentials_path

                return True
            except (IOError, json.JSONDecodeError):
                # Fall back to default settings
                self.config = AppConfig()
                return False
        return False

    def save_settings(self):
        """Save settings to file."""
        try:
            # Convert Pydantic model to dict and save
            with open(self.settings_path, "w") as f:
                json.dump(self.config.dict(exclude={"access_token"}), f, indent=2)
            return True
        except (IOError, OSError):
            return False

    def get_access_token(self):
        """Get the current access token from file or direct entry."""
        if self.config.token_from_file and self.config.token_path and os.path.isfile(self.config.token_path):
            try:
                with open(self.config.token_path, "r") as f:
                    token = f.read().strip()
                    if token:
                        return token
            except (IOError, OSError):
                return None
        return self.config.access_token if self.config.access_token else None

    # Add property accessors for common properties to maintain backward compatibility
    @property
    def page_id(self):
        return self.config.page_id

    @page_id.setter
    def page_id(self, value):
        self.config.page_id = value

    @property
    def token_from_file(self):
        return self.config.token_from_file

    @token_from_file.setter
    def token_from_file(self, value):
        self.config.token_from_file = value

    @property
    def token_path(self):
        return self.config.token_path

    @token_path.setter
    def token_path(self, value):
        self.config.token_path = value

    @property
    def access_token(self):
        return self.config.access_token

    @access_token.setter
    def access_token(self, value):
        self.config.access_token = value

    @property
    def max_videos(self):
        return self.config.max_videos

    @max_videos.setter
    def max_videos(self, value):
        try:
            # Validate through the Pydantic model
            self.config.max_videos = int(value)
        except (ValueError, TypeError):
            self.config.max_videos = DEFAULT_MAX_VIDEOS

    @property
    def export_format(self):
        return self.config.export_format

    @export_format.setter
    def export_format(self, value):
        self.config.export_format = value

    @property
    def spreadsheet_name(self):
        return self.config.spreadsheet_name

    @spreadsheet_name.setter
    def spreadsheet_name(self, value):
        self.config.spreadsheet_name = value

    @property
    def worksheet_name(self):
        return self.config.worksheet_name

    @worksheet_name.setter
    def worksheet_name(self, value):
        self.config.worksheet_name = value

    @property
    def output_path(self):
        return self.config.output_path

    @output_path.setter
    def output_path(self, value):
        self.config.output_path = os.path.expanduser(value) if value else os.path.expanduser(DEFAULT_OUTPUT_PATH)

    @property
    def credentials_path(self):
        return self.config.credentials_path

    @credentials_path.setter
    def credentials_path(self, value):
        self.config.credentials_path = value
        if value and os.path.isfile(value):
            os.environ["GOOGLE_CREDENTIALS_PATH"] = value
