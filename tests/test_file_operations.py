#!/usr/bin/env python3
import os
import sys
import tempfile

# Get the absolute path to the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Get the path to the file_renamer directory
file_renamer_path = os.path.join(project_root, "file-renamer")
# Add the file_renamer path to the Python path
if file_renamer_path not in sys.path:
    sys.path.insert(0, file_renamer_path)

# Now import the modules directly
# ruff: noqa: E402
from models import RenameOptions, PatternType

# ruff: noqa: E402
from file_operations import FileOperations


class TestFileOperations:
    def setup_method(self):
        """Set up test directory with sample files"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = self.temp_dir.name

        # Create sample files
        sample_files = ["test1.jpg", "test2.png", "test3.txt", "TEST4.JPG", "test5.jpeg", "test6.tiff"]
        for filename in sample_files:
            with open(os.path.join(self.dir_path, filename), "w") as f:
                f.write("test content")

    def teardown_method(self):
        """Clean up test directory"""
        self.temp_dir.cleanup()

    def test_get_files_from_directory(self):
        """Test get_files_from_directory method"""
        # Get all files
        files = FileOperations.get_files_from_directory(self.dir_path)
        assert len(files) == 6

        # Check with extension filter
        files = FileOperations.get_files_from_directory(self.dir_path, ["jpg", "jpeg"])
        assert len(files) == 3
        for file in files:
            assert file.lower().endswith((".jpg", ".jpeg"))

        # Invalid directory
        files = FileOperations.get_files_from_directory("/nonexistent/dir")
        assert files == []

    def test_determine_padding_digits(self):
        """Test determine_padding_digits method"""
        assert FileOperations.determine_padding_digits(1) == 1
        assert FileOperations.determine_padding_digits(9) == 1
        assert FileOperations.determine_padding_digits(10) == 2
        assert FileOperations.determine_padding_digits(99) == 2
        assert FileOperations.determine_padding_digits(100) == 3
        assert FileOperations.determine_padding_digits(999) == 3
        assert FileOperations.determine_padding_digits(1000) == 4

        # Edge cases
        assert FileOperations.determine_padding_digits(0) == 1
        assert FileOperations.determine_padding_digits(-10) == 1  # Should handle negative numbers gracefully

    def test_normalize_extension(self):
        """Test normalize_extension method"""
        # Basic normalization
        assert FileOperations.normalize_extension("test.jpg") == "test.jpg"
        assert FileOperations.normalize_extension("test.JPG") == "test.jpg"
        assert FileOperations.normalize_extension("test.jpeg") == "test.jpg"
        assert FileOperations.normalize_extension("test.JPEG") == "test.jpg"
        assert FileOperations.normalize_extension("test.tiff") == "test.tif"
        assert FileOperations.normalize_extension("test.htm") == "test.html"

        # No extension
        assert FileOperations.normalize_extension("test") == "test"

        # Dot only
        assert FileOperations.normalize_extension(".") == "."

        # Unknown extension
        assert FileOperations.normalize_extension("test.xyz") == "test.xyz"

    def test_generate_new_filename(self):
        """Test generate_new_filename method"""
        options = RenameOptions(pattern_type=PatternType.SEQUENCE, pattern_text="photo")

        # Basic renaming
        new_name = FileOperations.generate_new_filename("test.jpg", options, 0, 5)
        assert new_name == "photo_1.jpg"

        # With different index
        new_name = FileOperations.generate_new_filename("test.jpg", options, 9, 20)
        assert new_name == "photo_10.jpg"

        # With date
        options.include_date = True
        new_name = FileOperations.generate_new_filename("test.jpg", options, 0, 5)
        # Date format is YYYYMMDD, but we can't assert the exact value since it changes
        assert new_name.startswith("20")  # Start of year
        assert "_photo_1.jpg" in new_name

        # With normalize extensions
        options.include_date = False
        new_name = FileOperations.generate_new_filename("test.JPG", options, 0, 5)
        assert new_name == "photo_1.jpg"

        new_name = FileOperations.generate_new_filename("test.jpeg", options, 0, 5)
        assert new_name == "photo_1.jpg"

        # Without normalize extensions
        options.normalize_extensions = False
        new_name = FileOperations.generate_new_filename("test.JPEG", options, 0, 5)
        assert new_name == "photo_1.jpeg"  # Still lowercase but not normalized to jpg
