#!/usr/bin/env python3
"""
Build script to create all installers for Facebook Video Data Tool.
"""

import os
import sys
import shutil
import subprocess
import platform
import argparse
import zipfile

# Configuration
APP_NAME = "Facebook Video Data Tool"
VERSION = "1.0.0"
AUTHOR = "Eric Gitonga"
COPYRIGHT = f"Copyright © 2025 {AUTHOR}. All rights reserved."
REPO_URL = "https://github.com/user/fbvideodata"  # Update this with your actual repo


def clean_build_dir(build_dir):
    """Clean up the build directory."""
    print(f"Cleaning build directory: {build_dir}")
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir, exist_ok=True)


def build_source_dist(build_dir):
    """Build source distribution."""
    print("Building source distribution...")

    # Run setup.py to create source distribution
    subprocess.run([sys.executable, "setup.py", "sdist", "--formats=zip", f"--dist-dir={build_dir}"], check=True)

    # Copy the installer scripts
    for script in ["install.py", "windows_installer.nsi", "create_linux_package.sh"]:
        if os.path.exists(script):
            shutil.copy(script, build_dir)

    # Copy documentation
    for doc in ["README.md", "INSTALLATION.md", "LICENSE"]:
        if os.path.exists(doc):
            shutil.copy(doc, build_dir)

    # Create a complete source zip with all required files
    source_zip = os.path.join(build_dir, f"fbvideodata-{VERSION}-source.zip")
    with zipfile.ZipFile(source_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add main Python package
        for root, _, files in os.walk("fbvideodata"):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, file_path)

        # Add all required files
        for file in [
            "setup.py",
            "requirements.txt",
            "README.md",
            "LICENSE",
            "INSTALLATION.md",
            "install.py",
            "fbv_icon.ico",
        ]:
            if os.path.exists(file):
                zipf.write(file, file)

    print(f"Source distribution created: {source_zip}")
    return source_zip


def build_windows_executable(build_dir, source_zip):
    """Build Windows executable using cx_Freeze."""
    if platform.system() != "Windows" and not args.force:
        print("Skipping Windows executable build (not on Windows)")
        return None

    print("Building Windows executable...")

    # Run cx_Freeze to create Windows executable
    subprocess.run(
        [sys.executable, "setup.py", "build_exe", f"--build-exe={os.path.join(build_dir, 'win_build')}"], check=True
    )

    # Create a zip of the Windows build
    win_zip = os.path.join(build_dir, f"fbvideodata-{VERSION}-windows.zip")
    with zipfile.ZipFile(win_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(os.path.join(build_dir, "win_build")):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.join(build_dir, "win_build"))
                zipf.write(file_path, arcname)

    print(f"Windows executable created: {win_zip}")
    return win_zip


def build_windows_installer(build_dir, win_zip=None):
    """Build Windows installer using NSIS."""
    if platform.system() != "Windows" and not args.force:
        print("Skipping Windows installer build (not on Windows)")
        return None

    if not shutil.which("makensis") and not args.force:
        print("Skipping Windows installer build (NSIS not found)")
        return None

    print("Building Windows installer...")

    # Prepare directory for NSIS
    nsis_dir = os.path.join(build_dir, "nsis_build")
    os.makedirs(nsis_dir, exist_ok=True)

    # Extract Windows build if available
    if win_zip and os.path.exists(win_zip):
        with zipfile.ZipFile(win_zip, "r") as zipf:
            zipf.extractall(os.path.join(nsis_dir, "dist"))

    # Copy NSIS script and icon
    shutil.copy("windows_installer.nsi", nsis_dir)
    if os.path.exists("fbv_icon.ico"):
        shutil.copy("fbv_icon.ico", nsis_dir)

    # Copy license file
    if os.path.exists("LICENSE"):
        shutil.copy("LICENSE", nsis_dir)

    # Run NSIS to create installer
    subprocess.run(["makensis", os.path.join(nsis_dir, "windows_installer.nsi")], check=True, cwd=nsis_dir)

    # Move the installer to the build directory
    installer = os.path.join(nsis_dir, "FBVideoDataTool_Setup.exe")
    if os.path.exists(installer):
        shutil.move(installer, os.path.join(build_dir, f"FBVideoDataTool_{VERSION}_Setup.exe"))
        print(f"Windows installer created: {os.path.join(build_dir, f'FBVideoDataTool_{VERSION}_Setup.exe')}")
        return os.path.join(build_dir, f"FBVideoDataTool_{VERSION}_Setup.exe")

    print("Failed to create Windows installer")
    return None


def build_linux_package(build_dir):
    """Build Linux Debian package."""
    if platform.system() != "Linux" and not args.force:
        print("Skipping Linux package build (not on Linux)")
        return None

    if not shutil.which("dpkg-deb") and not args.force:
        print("Skipping Linux package build (dpkg-deb not found)")
        return None

    print("Building Linux Debian package...")

    # Make the script executable
    if os.path.exists("create_linux_package.sh"):
        os.chmod("create_linux_package.sh", 0o755)

    # Run the package creation script
    subprocess.run(["./create_linux_package.sh"], check=True)

    # Move the package to the build directory
    deb_file = f"facebook-video-data-tool_{VERSION}_all.deb"
    if os.path.exists(deb_file):
        shutil.move(deb_file, os.path.join(build_dir, deb_file))
        print(f"Linux package created: {os.path.join(build_dir, deb_file)}")
        return os.path.join(build_dir, deb_file)

    print("Failed to create Linux package")
    return None


def update_installer_script(build_dir, source_zip):
    """Update the universal installer script with the correct URL."""
    if not os.path.exists("install.py"):
        print("Skipping installer script update (not found)")
        return None

    print("Updating universal installer script...")

    # Read the installer script
    with open("install.py", "r") as f:
        content = f.read()

    # Update the GitHub repo URL and version
    content = content.replace(
        'GITHUB_REPO = "https://github.com/user/fbvideodata/archive/main.zip"',
        f'GITHUB_REPO = "{REPO_URL}/releases/download/v{VERSION}/fbvideodata-{VERSION}-source.zip"',
    )

    # Write the updated installer script
    installer_path = os.path.join(build_dir, "install.py")
    with open(installer_path, "w") as f:
        f.write(content)

    print(f"Universal installer updated: {installer_path}")
    return installer_path


def main():
    """Main build function."""
    parser = argparse.ArgumentParser(description=f"Build installers for {APP_NAME}")
    parser.add_argument("--build-dir", default="build/installers", help="Build directory for installers")
    parser.add_argument("--force", action="store_true", help="Force build all installers regardless of platform")
    parser.add_argument("--skip-windows", action="store_true", help="Skip Windows installer build")
    parser.add_argument("--skip-linux", action="store_true", help="Skip Linux package build")

    global args
    args = parser.parse_args()

    # Ensure the build directory exists
    build_dir = args.build_dir
    clean_build_dir(build_dir)

    # Build source distribution
    source_zip = build_source_dist(build_dir)

    # Update installer script
    update_installer_script(build_dir, source_zip)

    # Build platform-specific installers
    if not args.skip_windows:
        win_exe = build_windows_executable(build_dir, source_zip)
        build_windows_installer(build_dir, win_exe)

    if not args.skip_linux:
        build_linux_package(build_dir)

    print("\nBuild Summary:")
    print(f"Source ZIP: {source_zip}")
    print(f"Installer script: {os.path.join(build_dir, 'install.py')}")
    print(f"Windows installer: {os.path.join(build_dir, f'FBVideoDataTool_{VERSION}_Setup.exe')}")
    print(f"Linux package: {os.path.join(build_dir, f'facebook-video-data-tool_{VERSION}_all.deb')}")
    print("\nAll installers have been built successfully!")


if __name__ == "__main__":
    main()
