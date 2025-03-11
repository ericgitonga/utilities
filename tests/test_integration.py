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
from models import AppConfig, RenameOptions, PatternType

# ruff: noqa: E402
from file_operations import FileOperations


class TestIntegration:
    def setup_method(self):
        """Set up test directory with sample files"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = self.temp_dir.name

        # Create sample files
        self.sample_files = ["image1.jpg", "image2.png", "document.txt", "PHOTO.JPG", "snapshot.jpeg", "scan.tiff"]
        for filename in self.sample_files:
            with open(os.path.join(self.dir_path, filename), "w") as f:
                f.write("test content")

    def teardown_method(self):
        """Clean up test directory"""
        self.temp_dir.cleanup()

    def test_complete_rename_workflow(self):
        """Test the complete file renaming workflow"""
        # Set up the application configuration
        config = AppConfig(
            dir_path=self.dir_path,
            options=RenameOptions(pattern_type=PatternType.SEQUENCE, pattern_text="file", normalize_extensions=True),
        )

        # Get files from directory
        files = FileOperations.get_files_from_directory(config.dir_path)
        assert len(files) == 6

        # Calculate total files for padding
        total_files = len(files)
        assert total_files == 6

        # Generate new filenames
        original_paths = []
        new_paths = []
        errors = []

        for i, filename in enumerate(files):
            try:
                new_name = FileOperations.generate_new_filename(filename, config.options, i, total_files)

                original_path = os.path.join(config.dir_path, filename)
                new_path = os.path.join(config.dir_path, new_name)

                # Store paths for later
                original_paths.append(original_path)
                new_paths.append(new_path)

            except Exception as e:
                errors.append(f"Error processing {filename}: {str(e)}")

        assert len(errors) == 0

        # Verify new names follow expected pattern
        assert "file_1" in new_paths[0]
        assert "file_6" in new_paths[5]

        # Check extension normalization
        normalized_extensions = [os.path.splitext(path)[1] for path in new_paths]
        assert ".jpg" in normalized_extensions
        assert ".tif" in normalized_extensions
        assert ".jpg" in normalized_extensions  # From .jpeg

        # Actually rename files
        renamed = 0
        for i, (original_path, new_path) in enumerate(zip(original_paths, new_paths)):
            # Skip if paths are the same
            if original_path == new_path:
                continue

            # Skip if target already exists
            if os.path.exists(new_path):
                continue

            # Rename file
            os.rename(original_path, new_path)
            renamed += 1

        # Verify all files were renamed
        assert renamed == 6

        # Check that original files don't exist anymore
        for path in original_paths:
            assert not os.path.exists(path)

        # Check that new files exist
        for path in new_paths:
            assert os.path.exists(path)

    def test_filter_by_extension(self):
        """Test filtering files by extension"""
        # Set up the application configuration with extension filter
        config = AppConfig(
            dir_path=self.dir_path,
            options=RenameOptions(
                pattern_type=PatternType.SEQUENCE, pattern_text="image", extension_filter="jpg,jpeg,png"
            ),
        )

        # Get files with filter
        extensions = config.options.get_extensions_list()
        files = FileOperations.get_files_from_directory(config.dir_path, extensions)

        # Should only include image files
        assert len(files) == 4  # image1.jpg, image2.png, PHOTO.JPG, snapshot.jpeg

        # Check if txt and tiff files are excluded
        for file in files:
            assert not file.lower().endswith((".txt", ".tiff"))
