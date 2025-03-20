"""
Setup script for the Facebook Video Data Tool application.
"""

import sys
from cx_Freeze import setup, Executable

from fbvideodata import __version__
from fbvideodata.constants import APP_NAME, APP_DESCRIPTION, APP_ICON

# Dependencies are automatically detected, but might need adjustments
build_exe_options = {
    "packages": [
        "tkinter",
        "requests",
        "pandas",
        "gspread",
        "oauth2client",
        "gspread_dataframe",
        "json",
        "threading",
        "datetime",
        "fbvideodata",
    ],
    "excludes": [],
    "include_files": [
        "README.md",
        "LICENSE",
        APP_ICON,
    ],
    "include_msvcr": True,
}

# Base for GUI applications
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name=APP_NAME,
    version=__version__,
    description=APP_DESCRIPTION,
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "fbvideodata/main.py",
            base=base,
            target_name="FBVideoDataTool.exe",
            icon=APP_ICON,
            shortcut_name=APP_NAME,
            shortcut_dir="DesktopFolder",
        )
    ],
)
