#!/bin/bash
# Script to create a Debian package for Facebook Video Data Tool
# Copyright © 2025 Eric Gitonga. All rights reserved.

set -e  # Exit on error

# Configuration
APP_NAME="fbvideodata"
PACKAGE_NAME="facebook-video-data-tool"
VERSION="1.0.0"
MAINTAINER="Eric Gitonga <gitonga@ericgitonga.com>"
DESCRIPTION="Tool for retrieving and analyzing Facebook video data"
ARCHITECTURE="all"  # Python apps are architecture-independent
DEPENDS="python3 (>= 3.7), python3-pip, python3-tk, python3-requests, python3-pandas"

# Working directories
WORK_DIR="$(mktemp -d)"
BUILD_DIR="${WORK_DIR}/${PACKAGE_NAME}-${VERSION}"
DEBIAN_DIR="${BUILD_DIR}/DEBIAN"
INSTALL_DIR="${BUILD_DIR}/usr/local/lib/${APP_NAME}"
BIN_DIR="${BUILD_DIR}/usr/local/bin"
DESKTOP_DIR="${BUILD_DIR}/usr/share/applications"
PIXMAPS_DIR="${BUILD_DIR}/usr/share/pixmaps"
DOC_DIR="${BUILD_DIR}/usr/share/doc/${PACKAGE_NAME}"

# Create directory structure
mkdir -p "${DEBIAN_DIR}" "${INSTALL_DIR}" "${BIN_DIR}" "${DESKTOP_DIR}" "${PIXMAPS_DIR}" "${DOC_DIR}"

# Create control file
cat > "${DEBIAN_DIR}/control" << EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCHITECTURE}
Depends: ${DEPENDS}
Maintainer: ${MAINTAINER}
Description: ${DESCRIPTION}
 Facebook Video Data Tool is a GUI application for
 non-programmers to easily retrieve, analyze, and export
 Facebook video data.
 .
 Features:
  * Simple Interface: Easy-to-use GUI requiring no programming knowledge
  * Data Retrieval: Fetch video metrics from any Facebook page
  * Data Visualization: View and sort video data in a clean tabular format
  * Detailed Video Analysis: See in-depth metrics for each video
  * Export Options: Save data to CSV or Google Sheets
EOF

# Create postinst script to install Python dependencies
cat > "${DEBIAN_DIR}/postinst" << EOF
#!/bin/bash
set -e

# Install Python dependencies
pip3 install requests>=2.25.0 pandas>=1.1.5 gspread>=3.6.0 oauth2client>=4.1.3 gspread-dataframe>=3.2.0

# Update desktop database
if [ -x /usr/bin/update-desktop-database ]; then
    /usr/bin/update-desktop-database
fi

exit 0
EOF
chmod 755 "${DEBIAN_DIR}/postinst"

# Create postrm script (cleanup after uninstall)
cat > "${DEBIAN_DIR}/postrm" << EOF
#!/bin/bash
set -e

# Update desktop database
if [ -x /usr/bin/update-desktop-database ]; then
    /usr/bin/update-desktop-database
fi

exit 0
EOF
chmod 755 "${DEBIAN_DIR}/postrm"

# Copy application files
echo "Copying application files..."
cp -r fbvideodata "${INSTALL_DIR}/"
cp README.md LICENSE setup.py requirements.txt "${INSTALL_DIR}/"

# Copy icon for the application
cp fbv_icon.ico "${INSTALL_DIR}/"
# Convert icon to png for Linux
convert fbv_icon.ico "${PIXMAPS_DIR}/${PACKAGE_NAME}.png"

# Create executable script
cat > "${BIN_DIR}/${PACKAGE_NAME}" << EOF
#!/bin/bash
exec python3 -m fbvideodata.main "\$@"
EOF
chmod 755 "${BIN_DIR}/${PACKAGE_NAME}"

# Create desktop file
cat > "${DESKTOP_DIR}/${PACKAGE_NAME}.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Facebook Video Data Tool
Comment=${DESCRIPTION}
Exec=${PACKAGE_NAME}
Icon=${PACKAGE_NAME}
Terminal=false
Categories=Utility;Network;
Keywords=facebook;video;data;analysis;
EOF

# Copy documentation
cp README.md "${DOC_DIR}/"
cp LICENSE "${DOC_DIR}/copyright"

# Build the package
echo "Building Debian package..."
dpkg-deb --build "${BUILD_DIR}" "${PACKAGE_NAME}_${VERSION}_${ARCHITECTURE}.deb"

# Clean up
echo "Cleaning up temporary files..."
rm -rf "${WORK_DIR}"

echo "Package created: ${PACKAGE_NAME}_${VERSION}_${ARCHITECTURE}.deb"
echo "You can install it with: sudo dpkg -i ${PACKAGE_NAME}_${VERSION}_${ARCHITECTURE}.deb"
echo "If there are dependency errors, run: sudo apt-get install -f"
