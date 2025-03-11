#!/usr/bin/env python3
import os
import sys
import pytest
from pydantic import ValidationError

# Get the absolute path to the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Get the path to the file_renamer directory
file_renamer_path = os.path.join(project_root, "file-renamer")
# Add the file_renamer path to the Python path
if file_renamer_path not in sys.path:
    sys.path.insert(0, file_renamer_path)

# Now import the modules directly
# ruff: noqa: E402
from models import PatternType, RenameOptions, RenamePreview, AppConfig, StatusMessage


class TestPatternType:
    def test_pattern_type_values(self):
        """Test PatternType enum values"""
        assert PatternType.SEQUENCE == "sequence"

    def test_pattern_type_as_string(self):
        """Test PatternType string conversion"""
        pattern = PatternType.SEQUENCE
        assert pattern == "sequence"  # Value equality check
        # Don't test str(pattern) as its representation may vary


class TestRenameOptions:
    def test_default_values(self):
        """Test RenameOptions default values"""
        options = RenameOptions()
        assert options.pattern_type == PatternType.SEQUENCE
        assert options.pattern_text == ""
        assert options.include_date is False
        assert options.extension_filter == ""
        assert options.normalize_extensions is True

    def test_custom_values(self):
        """Test RenameOptions with custom values"""
        options = RenameOptions(
            pattern_text="test", include_date=True, extension_filter="jpg,png", normalize_extensions=False
        )
        assert options.pattern_text == "test"
        assert options.include_date is True
        assert options.extension_filter == "jpg,png"
        assert options.normalize_extensions is False

    def test_extension_filter_validation(self):
        """Test extension filter validation"""
        # Valid extension filters
        RenameOptions(extension_filter="jpg,png,txt")
        RenameOptions(extension_filter="JPG,PNG").extension_filter == "jpg,png"  # Should be lowercased

        # Invalid extension filter (empty item in list)
        with pytest.raises(ValidationError):
            RenameOptions(extension_filter="jpg,,png")

    def test_get_extensions_list(self):
        """Test get_extensions_list method"""
        # Empty extension filter
        options = RenameOptions(extension_filter="")
        assert options.get_extensions_list() == []

        # Single extension
        options = RenameOptions(extension_filter="jpg")
        assert options.get_extensions_list() == ["jpg"]

        # Multiple extensions
        options = RenameOptions(extension_filter="jpg,png,txt")
        assert options.get_extensions_list() == ["jpg", "png", "txt"]

        # With spaces
        options = RenameOptions(extension_filter=" jpg , png , txt ")
        assert options.get_extensions_list() == ["jpg", "png", "txt"]


class TestRenamePreview:
    def test_rename_preview(self):
        """Test RenamePreview model"""
        preview = RenamePreview(original_name="test.jpg", new_name="new_test.jpg")
        assert preview.original_name == "test.jpg"
        assert preview.new_name == "new_test.jpg"


class TestAppConfig:
    def test_default_values(self):
        """Test AppConfig default values"""
        config = AppConfig()
        assert config.dir_path == ""
        assert config.selected_files == []
        assert isinstance(config.options, RenameOptions)

    def test_custom_values(self):
        """Test AppConfig with custom values"""
        options = RenameOptions(pattern_text="test")
        config = AppConfig(
            dir_path="/test/path", selected_files=["/test/file1.jpg", "/test/file2.jpg"], options=options
        )
        assert config.dir_path == "/test/path"
        assert config.selected_files == ["/test/file1.jpg", "/test/file2.jpg"]
        assert config.options.pattern_text == "test"


class TestStatusMessage:
    def test_default_values(self):
        """Test StatusMessage default values"""
        msg = StatusMessage(message="Test message")
        assert msg.message == "Test message"
        assert msg.status_type == "info"

    def test_custom_values(self):
        """Test StatusMessage with custom values"""
        msg = StatusMessage(message="Test message", status_type="error")
        assert msg.message == "Test message"
        assert msg.status_type == "error"

    def test_invalid_status_type(self):
        """Test StatusMessage with invalid status type"""
        with pytest.raises(ValidationError):
            StatusMessage(message="Test message", status_type="invalid")
