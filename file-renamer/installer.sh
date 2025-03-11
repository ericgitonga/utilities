#!/bin/bash
#
# File Renamer Installation Script
# This script installs the File Renamer application on Linux systems
# 
# This script assumes it is already located inside the file-renamer directory
#

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Get the absolute path of the current directory (file-renamer)
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Print banner
echo -e "${GREEN}"
echo "======================================================"
echo "             FILE RENAMER INSTALLER                   "
echo "======================================================"
echo -e "${NC}"
echo "Source directory: $SOURCE_DIR"
echo ""

# Check if running as root (for system-wide installation)
if [ "$(id -u)" != "0" ]; then
    echo -e "${YELLOW}Not running as root. Installation will be user-local only.${NC}"
    INSTALL_MODE="user"
else
    INSTALL_MODE="system"
fi

# Determine installation directory
if [ "$INSTALL_MODE" = "system" ]; then
    INSTALL_DIR="/opt/file-renamer"
    BIN_DIR="/usr/local/bin"
    DESKTOP_DIR="/usr/share/applications"
else
    INSTALL_DIR="$HOME/.local/share/file-renamer"
    BIN_DIR="$HOME/.local/bin"
    DESKTOP_DIR="$HOME/.local/share/applications"
fi

# Create directories if they don't exist
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"

# Check if PATH includes the bin directory (only for user installation)
if [ "$INSTALL_MODE" = "user" ]; then
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo -e "${YELLOW}Adding $BIN_DIR to your PATH in .bashrc${NC}"
        echo "# Added by file-renamer installer" >> "$HOME/.bashrc"
        echo "export PATH=\"\$PATH:$BIN_DIR\"" >> "$HOME/.bashrc"
        echo "Please restart your terminal or run 'source ~/.bashrc' after installation."
    fi
fi

# Check for Python
echo "Checking for Python..."
if command -v python3 &>/dev/null; then
    PYTHON="python3"
    echo -e "${GREEN}Python 3 found!${NC}"
else
    echo -e "${RED}Python 3 is not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

# Check for pip
echo "Checking for pip..."
if command -v pip3 &>/dev/null; then
    PIP="pip3"
    echo -e "${GREEN}pip found!${NC}"
else
    echo -e "${YELLOW}pip not found. Attempting to install pip...${NC}"
    if [ "$INSTALL_MODE" = "system" ]; then
        apt-get update && apt-get install -y python3-pip || yum install -y python3-pip || pacman -S python-pip
    else
        $PYTHON -m ensurepip --upgrade || {
            echo -e "${RED}Failed to install pip. Please install pip manually and try again.${NC}"
            exit 1
        }
    fi
    PIP="pip3"
fi

# Check for Tkinter
echo "Checking for Tkinter..."
if $PYTHON -c "import tkinter" &>/dev/null; then
    echo -e "${GREEN}Tkinter found!${NC}"
else
    echo -e "${YELLOW}Tkinter not found. Attempting to install Tkinter...${NC}"
    if [ "$INSTALL_MODE" = "system" ]; then
        apt-get update && apt-get install -y python3-tk || yum install -y python3-tkinter || pacman -S tk
    else
        echo -e "${RED}Tkinter not found and cannot be installed in user mode."
        echo -e "Please install Tkinter using your system package manager and try again."
        echo -e "For example: sudo apt-get install python3-tk${NC}"
        exit 1
    fi
fi

# Check for required Python packages
echo "Checking for required Python packages..."

# Function to check if a Python package is installed
check_package() {
  $PYTHON -c "import $1" 2>/dev/null
  return $?
}

# Check for Pydantic
if check_package "pydantic"; then
  echo -e "${GREEN}Pydantic found!${NC}"
else
  echo -e "${YELLOW}Pydantic not found. Will install it...${NC}"
fi

# Check for other required packages
REQUIRED_PACKAGES=("pydantic" "enum" "typing")
MISSING_PACKAGES=()

for pkg in "${REQUIRED_PACKAGES[@]}"; do
  if ! check_package "$pkg"; then
    MISSING_PACKAGES+=("$pkg")
  fi
done

# Install required Python packages
if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
  echo "Installing required Python packages: ${MISSING_PACKAGES[*]}"
  $PIP install --upgrade pip
  $PIP install "${MISSING_PACKAGES[@]}" PyInstaller
else
  echo -e "${GREEN}All required packages are installed!${NC}"
  # Still make sure PyInstaller is available for optional step
  $PIP install --upgrade pip
  $PIP install PyInstaller
fi

# Ensure we're in the right directory
if [ ! -f "$SOURCE_DIR/file_renamer.py" ]; then
    echo -e "${RED}Error: file_renamer.py not found in $SOURCE_DIR.${NC}"
    echo "This script must be run from within the file-renamer directory."
    exit 1
fi

# Copy files to installation directory
echo "Copying files to $INSTALL_DIR..."
cp -r "$SOURCE_DIR"/* "$INSTALL_DIR/"

# Make sure the main script is executable
chmod +x "$INSTALL_DIR/file_renamer.py"

# Create a launch script in the bin directory
echo "Creating launcher script..."
cat > "$BIN_DIR/file-renamer" << EOF
#!/bin/bash
cd "$INSTALL_DIR" && $PYTHON file_renamer.py "\$@"
EOF
chmod +x "$BIN_DIR/file-renamer"

# Create desktop entry
echo "Creating desktop entry..."
cat > "$DESKTOP_DIR/file-renamer.desktop" << EOF
[Desktop Entry]
Name=File Renamer
Comment=Rename files easily
Exec=$BIN_DIR/file-renamer
Terminal=false
Type=Application
Categories=Utility;FileTools;
EOF

# Add icon if available
if [ -f "$INSTALL_DIR/icon.png" ]; then
    echo "Icon=$INSTALL_DIR/icon.png" >> "$DESKTOP_DIR/file-renamer.desktop"
fi

# Create uninstall script
echo "Creating uninstaller..."
cat > "$INSTALL_DIR/uninstall.sh" << EOF
#!/bin/bash
#
# File Renamer Uninstallation Script
# This script removes the File Renamer application from the system
#

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Print banner
echo -e "\${GREEN}"
echo "======================================================"
echo "          FILE RENAMER UNINSTALLER                    "
echo "======================================================"
echo -e "\${NC}"

# Check if running as root
if [ "\$(id -u)" != "0" ]; then
    # Running as regular user
    echo -e "\${YELLOW}Running as regular user. Will uninstall from user directories.\${NC}"
    INSTALL_DIR="$HOME/.local/share/file-renamer"
    BIN_DIR="$HOME/.local/bin"
    DESKTOP_DIR="$HOME/.local/share/applications"
    CONFIG_DIR="$HOME/.config/file-renamer"
    INSTALL_MODE="user"
else
    # Running as root
    echo -e "\${YELLOW}Running as root. Will uninstall from system directories.\${NC}"
    INSTALL_DIR="/opt/file-renamer"
    BIN_DIR="/usr/local/bin"
    DESKTOP_DIR="/usr/share/applications"
    CONFIG_DIR="/etc/file-renamer"
    INSTALL_MODE="system"
fi

# Display confirmation
echo "This will uninstall File Renamer from the following locations:"
echo "  - Application files: \$INSTALL_DIR"
echo "  - Launcher script: \$BIN_DIR/file-renamer"
echo "  - Desktop entry: \$DESKTOP_DIR/file-renamer.desktop"
echo "  - Configuration: \$CONFIG_DIR (if exists)"
echo ""
echo -n "Do you want to continue? (y/n): "
read -r CONFIRM

if [ "\$CONFIRM" != "y" ] && [ "\$CONFIRM" != "Y" ]; then
    echo -e "\${YELLOW}Uninstallation cancelled.\${NC}"
    exit 0
fi

# Ask if user data should be removed
echo ""
echo -n "Do you want to remove user settings and data? (y/n): "
read -r REMOVE_DATA

# Track uninstallation status
ERRORS=0

# Function to safely remove a file or directory
safe_remove() {
    if [ -e "\$1" ]; then
        echo "Removing: \$1"
        rm -rf "\$1" || {
            echo -e "\${RED}Failed to remove \$1\${NC}"
            ERRORS=\$((ERRORS + 1))
        }
    else
        echo -e "\${YELLOW}Not found: \$1\${NC}"
    fi
}

# Remove launcher script
safe_remove "\$BIN_DIR/file-renamer"
safe_remove "\$BIN_DIR/file-renamer-uninstall"

# Remove desktop entry
safe_remove "\$DESKTOP_DIR/file-renamer.desktop"

# Remove application files
safe_remove "\$INSTALL_DIR"

# Remove configuration if requested
if [ "\$REMOVE_DATA" = "y" ] || [ "\$REMOVE_DATA" = "Y" ]; then
    safe_remove "\$CONFIG_DIR"
    
    # Remove any additional user data
    if [ "\$INSTALL_MODE" = "user" ]; then
        # Remove from user's home directory
        safe_remove "\$HOME/.cache/file-renamer"
    else
        # Remove from system locations
        safe_remove "/var/cache/file-renamer"
    fi
else
    echo -e "\${YELLOW}User data and configuration preserved.\${NC}"
fi

# Clean up PATH in .bashrc if it was a user installation
if [ "\$INSTALL_MODE" = "user" ]; then
    if grep -q "# Added by file-renamer installer" "\$HOME/.bashrc"; then
        echo "Cleaning up PATH in .bashrc"
        sed -i '/# Added by file-renamer installer/d' "\$HOME/.bashrc"
        sed -i "/export PATH=\"\\\$PATH:$BIN_DIR\"/d" "\$HOME/.bashrc"
    fi
fi

# Report results
echo ""
if [ \$ERRORS -eq 0 ]; then
    echo -e "\${GREEN}File Renamer has been successfully uninstalled!\${NC}"
else
    echo -e "\${RED}Uninstallation completed with \$ERRORS errors.\${NC}"
    echo "Some components may not have been completely removed."
    echo "You may need to manually remove them with administrator privileges."
fi

echo ""
echo "Thank you for using File Renamer!"
echo "======================================================"
EOF

# Make the uninstaller executable
chmod +x "$INSTALL_DIR/uninstall.sh"

# Create a symlink to the uninstaller in bin directory
ln -sf "$INSTALL_DIR/uninstall.sh" "$BIN_DIR/file-renamer-uninstall"

# Build with PyInstaller (optional)
echo "Do you want to create a standalone executable with PyInstaller? (y/n)"
read -r BUILD_CHOICE

if [ "$BUILD_CHOICE" = "y" ] || [ "$BUILD_CHOICE" = "Y" ]; then
    echo "Building standalone executable with PyInstaller..."
    cd "$INSTALL_DIR"
    
    if [ -f "icon.ico" ]; then
        ICON_OPTION="--icon=icon.ico"
    elif [ -f "icon.png" ]; then
        # Convert PNG to ICO if needed
        if command -v convert &>/dev/null; then
            convert icon.png icon.ico
            ICON_OPTION="--icon=icon.ico"
        else
            ICON_OPTION=""
        fi
    else
        ICON_OPTION=""
    fi
    
    PyInstaller --name FileRenamer --windowed --onefile $ICON_OPTION --hidden-import=pydantic file_renamer.py
    
    # Update the launcher to use the executable instead
    if [ -f "$INSTALL_DIR/dist/FileRenamer" ]; then
        echo "Updating launcher to use the executable..."
        cat > "$BIN_DIR/file-renamer" << EOF
#!/bin/bash
"$INSTALL_DIR/dist/FileRenamer" "\$@"
EOF
        chmod +x "$BIN_DIR/file-renamer"
        
        # Update desktop entry
        sed -i "s|Exec=$BIN_DIR/file-renamer|Exec=$INSTALL_DIR/dist/FileRenamer|" "$DESKTOP_DIR/file-renamer.desktop"
    else
        echo -e "${RED}Failed to build executable. Will use Python script instead.${NC}"
    fi
fi

echo -e "${GREEN}"
echo "======================================================"
echo "       FILE RENAMER INSTALLATION COMPLETE!           "
echo "======================================================"
echo -e "${NC}"
echo "You can now run File Renamer by typing 'file-renamer' in your terminal"
echo "or by finding it in your application menu."
echo ""
echo "To uninstall, run 'file-renamer-uninstall' or execute the uninstall.sh"
echo "script in the installation directory."
echo ""
if [ "$INSTALL_MODE" = "user" ]; then
    echo "You may need to restart your terminal or run 'source ~/.bashrc'"
    echo "before the 'file-renamer' command is available."
fi
