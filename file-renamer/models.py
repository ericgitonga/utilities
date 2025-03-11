#!/usr/bin/env python3
# Standard library imports
from enum import Enum
from typing import List, Literal

# Third-party imports
from pydantic import BaseModel, Field, validator


class PatternType(str, Enum):
    """Enum for file renaming pattern types"""

    SEQUENCE = "sequence"  # Sequential renaming pattern


class RenameOptions(BaseModel):
    """Configuration options for file renaming"""

    pattern_type: PatternType = Field(default=PatternType.SEQUENCE)
    pattern_text: str = Field(default="")
    include_date: bool = Field(default=False)
    extension_filter: str = Field(default="")
    normalize_extensions: bool = Field(default=True)  # Option to normalize extensions

    @validator("extension_filter")
    def validate_extension_filter(cls, v):
        """Validate the extension filter format"""
        if v.strip() and not all(ext.strip() for ext in v.split(",")):
            raise ValueError("Extension filter must be comma-separated values")
        return v.lower().strip()

    def get_extensions_list(self) -> List[str]:
        """Convert extension string to list"""
        if not self.extension_filter:
            return []
        return [ext.strip() for ext in self.extension_filter.split(",")]


class RenamePreview(BaseModel):
    """Preview of original and new filenames"""

    original_name: str
    new_name: str


class AppConfig(BaseModel):
    """Application configuration"""

    dir_path: str = Field(default="")
    selected_files: List[str] = Field(default_factory=list)
    options: RenameOptions = Field(default_factory=RenameOptions)


class StatusMessage(BaseModel):
    """Status message for thread communication"""

    message: str
    status_type: Literal["info", "warning", "error", "success", "preview_done", "rename_done", "rename_error"] = "info"
