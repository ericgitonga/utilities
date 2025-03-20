#!/usr/bin/env python3
"""
Installer script for Facebook Video Data Tool.
Works on both Windows and Linux platforms.
"""

import os
import sys
import platform
import subprocess
import shutil
import tempfile
import argparse
from pathlib import Path
import urllib.request
import zipfile
import stat

# Constants
APP_NAME = "Facebook Video Data Tool"
GITHUB_REPO = "https://github.com/user/fbvideodata/archive/main.zip"  # Replace with actual repo
DEPENDENCIES = [
    "requests>=2.25.0",
    "pandas>=1.1.5",
    "gspread>=3.6.0",
    "oauth2client>=4.1.3",
    "gspread-dataframe>=3.2.0",
]


def is_admin():
    """Check if running with admin/root privileges."""
    if platform.system() == "Windows":
        try:
            # Requires admin privileges
            return subprocess.run("net session", shell=True, capture_output=True, text=True).returncode == 0
        except Exception:
            return False
    else:  # Linux/Mac
        return os.geteuid() == 0


def check_python():
    """Check if Python 3.7+ is installed."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"⚠️ {APP_NAME} requires Python 3.7 or newer")
        print(f"Current Python version: {sys.version}")
        return False
    return True


def install_python_dependencies():
    """Install required Python packages."""
    print("📦 Installing Python dependencies...")

    # Create a temporary requirements file
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as temp:
        temp.write("\n".join(DEPENDENCIES))
        requirements_path = temp.name

    try:
        # Install dependencies
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_path], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(requirements_path):
            os.unlink(requirements_path)

    return True


def download_application(target_dir):
    """Download the application from GitHub."""
    print(f"⬇️ Downloading {APP_NAME}...")

    # Create temporary file for the download
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp:
        temp_path = temp.name

    try:
        # Download the ZIP file
        urllib.request.urlretrieve(GITHUB_REPO, temp_path)

        # Extract the ZIP file
        with zipfile.ZipFile(temp_path, "r") as zip_ref:
            # Get the root folder name in the zip
            root_folder = zip_ref.namelist()[0].split("/")[0]
            zip_ref.extractall(target_dir)

        # Move contents to the target directory
        source_dir = os.path.join(target_dir, root_folder)
        for item in os.listdir(source_dir):
            s = os.path.join(source_dir, item)
            d = os.path.join(target_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

        # Clean up the extracted root folder
        shutil.rmtree(source_dir)

        print(f"✅ {APP_NAME} downloaded and extracted to {target_dir}")
        return True
    except Exception as e:
        print(f"❌ Failed to download and extract application: {e}")
        return False
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def create_desktop_shortcut(install_dir):
    """Create desktop shortcut based on platform."""
    print("🔗 Creating desktop shortcut...")

    home_dir = Path.home()
    desktop_dir = home_dir / "Desktop"

    if not desktop_dir.exists():
        desktop_dir = home_dir / "Desktop"  # Try again with capital D
        if not desktop_dir.exists():
            print("❌ Could not locate Desktop directory")
            return False

    if platform.system() == "Windows":
        # Create Windows shortcut (.lnk file)
        try:
            import win32com.client

            shortcut_path = desktop_dir / f"{APP_NAME}.lnk"
            target_path = os.path.join(install_dir, "fbvideodata", "main.py")

            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.TargetPath = sys.executable
            shortcut.Arguments = f'"{target_path}"'
            shortcut.WorkingDirectory = install_dir
            shortcut.IconLocation = os.path.join(install_dir, "fbv_icon.ico")
            shortcut.save()

            print(f"✅ Shortcut created at {shortcut_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to create Windows shortcut: {e}")
            print("You can manually create a shortcut to run 'python -m fbvideodata.main'")
            return False
    else:
        # Create Linux desktop entry
        try:
            entry_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={APP_NAME}
Comment=Tool for retrieving and analyzing Facebook video data
Exec={sys.executable} "{os.path.join(install_dir, 'fbvideodata', 'main.py')}"
Icon={os.path.join(install_dir, 'fbv_icon.ico')}
Terminal=false
Categories=Utility;
"""
            desktop_file = desktop_dir / f"{APP_NAME}.desktop"
            with open(desktop_file, "w") as f:
                f.write(entry_content)

            # Make the desktop file executable
            os.chmod(desktop_file, os.stat(desktop_file).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

            print(f"✅ Desktop entry created at {desktop_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to create Linux desktop entry: {e}")
            print("You can manually create a launcher to run 'python -m fbvideodata.main'")
            return False


def create_start_script(install_dir):
    """Create a start script for easier launching."""
    script_path = os.path.join(install_dir, "start_fbvideodata")

    if platform.system() == "Windows":
        script_path += ".bat"
        script_content = f"""@echo off
"{sys.executable}" "{os.path.join(install_dir, 'fbvideodata', 'main.py')}"
"""
    else:  # Linux/Mac
        script_content = f"""#!/bin/bash
"{sys.executable}" "{os.path.join(install_dir, 'fbvideodata', 'main.py')}"
"""

    try:
        with open(script_path, "w") as f:
            f.write(script_content)

        # Make the script executable on Linux/Mac
        if platform.system() != "Windows":
            os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        print(f"✅ Start script created at {script_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create start script: {e}")
        return False


def install_extra_windows_dependencies():
    """Install Windows-specific dependencies."""
    if platform.system() != "Windows":
        return True

    try:
        # Install pywin32 for shortcuts
        subprocess.run([sys.executable, "-m", "pip", "install", "pywin32"], check=True)
        print("✅ Windows dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Windows dependencies: {e}")
        return False


def main():
    """Main installer function."""
    parser = argparse.ArgumentParser(description=f"Installer for {APP_NAME}")
    parser.add_argument("--dir", type=str, help="Installation directory")
    parser.add_argument("--no-shortcut", action="store_true", help="Skip desktop shortcut creation")
    args = parser.parse_args()

    print(f"=== {APP_NAME} Installer ===")

    # Check Python version
    if not check_python():
        sys.exit(1)

    # Determine installation directory
    if args.dir:
        install_dir = args.dir
    else:
        if platform.system() == "Windows":
            install_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME)
        else:  # Linux/Mac
            install_dir = os.path.join(os.path.expanduser("~"), ".local", "share", APP_NAME.lower().replace(" ", "_"))

    # Create installation directory
    os.makedirs(install_dir, exist_ok=True)
    print(f"📁 Installation directory: {install_dir}")

    # Install platform-specific dependencies
    if platform.system() == "Windows":
        install_extra_windows_dependencies()

    # Install Python dependencies
    if not install_python_dependencies():
        sys.exit(1)

    # Download application
    if not download_application(install_dir):
        sys.exit(1)

    # Create start script
    create_start_script(install_dir)

    # Create desktop shortcut
    if not args.no_shortcut:
        create_desktop_shortcut(install_dir)

    print(f"\n✨ {APP_NAME} has been successfully installed! ✨")
    print(f"You can run it using the desktop shortcut or from: {os.path.join(install_dir, 'start_fbvideodata')}")
    print("If you encounter any issues, please report them at: https://github.com/user/fbvideodata/issues")


if __name__ == "__main__":
    main()
