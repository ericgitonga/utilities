import sys
from cx_Freeze import setup, Executable

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
    ],
    "excludes": [],
    "include_files": [
        "README.md",
        "LICENSE",
    ],
    "include_msvcr": True,
}

# Base for GUI applications
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="Facebook Video Data Tool",
    version="1.0.0",
    description="Tool for retrieving and analyzing Facebook video data",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "fb_video_gui.py",
            base=base,
            target_name="FBVideoDataTool.exe",
            icon="fbv_icon.ico",
            shortcut_name="Facebook Video Data Tool",
            shortcut_dir="DesktopFolder",
        )
    ],
)
