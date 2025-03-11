#!/usr/bin/env python3
import os
import sys

# Get the absolute path to the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Get the path to the file_renamer directory
file_renamer_path = os.path.join(project_root, "file-renamer")
# Add the file_renamer path to the Python path
if file_renamer_path not in sys.path:
    sys.path.insert(0, file_renamer_path)
