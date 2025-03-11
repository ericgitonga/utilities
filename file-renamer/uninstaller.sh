#!/bin/bash
#
# File Renamer Uninstallation Script
# This script removes the File Renamer application from the system
# 
# This script can be run directly from the installation directory
# or from the bin directory via the file-renamer-uninstall command
#

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Print banner
echo -e "${GREEN}"
echo "======================================================"
echo "          FILE RENAMER UNINSTALLER                    "
echo "======================================================"
echo -e "${NC}"

# Get the script path and directory
SCRIPT_PATH="$(readlink -f "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

# Check if running as root
if [ "$(id -u)" != "0" ]; then
    # Running as regular user
    echo -e "${YELLOW}Running as regular user. Will uninstall from user directories.${NC}"
    INSTALL_DIR="$HOME/.local/share/file-renamer"
    BIN_DIR="$HOME/.local/bin"
    DESKTOP_DIR="$HOME/.local/share/applications"
    CONFIG_DIR="$HOME/.config/file-renamer"
    INSTALL_MODE="user"
else
    # Running as root
    echo -e "${YELLOW}Running as root. Will uninstall from system directories.${NC}"
    INSTALL_DIR="/opt/file-renamer"
    BIN_DIR="/usr/local/bin"
    DESKTOP_DIR="/usr/share/applications"
    CONFIG_DIR="/etc/file-renamer"
    INSTALL_MODE="system"
fi

# Check if running from the installation directory
if [[ "$SCRIPT_DIR" == "$INSTALL_DIR" ]]; then
    echo "Running from installation directory: $INSTALL_DIR"
elif [[ "$SCRIPT_DIR" == "$BIN_DIR" ]]; then
    echo "Running from bin directory via file-renamer-uninstall command"
else
    echo -e "${YELLOW}Running from an unexpected location: $SCRIPT_DIR${NC}"
    echo "Will attempt to uninstall using default paths."
fi

# Display confirmation
echo "This will uninstall File Renamer from the following locations:"
echo "  - Application files: $INSTALL_DIR"
echo "  - Launcher script: $BIN_DIR/file-renamer"
echo "  - Desktop entry: $DESKTOP_DIR/file-renamer.desktop"
echo "  - Configuration: $CONFIG_DIR (if exists)"
echo ""
echo -n "Do you want to continue? (y/n): "
read -r CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo -e "${YELLOW}Uninstallation cancelled.${NC}"
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
    if [ -e "$1" ]; then
        echo "Removing: $1"
        rm -rf "$1" || {
            echo -e "${RED}Failed to remove $1${NC}"
            ERRORS=$((ERRORS + 1))
        }
    else
        echo -e "${YELLOW}Not found: $1${NC}"
    fi
}

# Remove launcher script
safe_remove "$BIN_DIR/file-renamer"
safe_remove "$BIN_DIR/file-renamer-uninstall"

# Remove desktop entry
safe_remove "$DESKTOP_DIR/file-renamer.desktop"

# Remove configuration if requested
if [ "$REMOVE_DATA" = "y" ] || [ "$REMOVE_DATA" = "Y" ]; then
    safe_remove "$CONFIG_DIR"
    
    # Remove any additional user data
    if [ "$INSTALL_MODE" = "user" ]; then
        # Remove from user's home directory
        safe_remove "$HOME/.cache/file-renamer"
    else
        # Remove from system locations
        safe_remove "/var/cache/file-renamer"
    fi
else
    echo -e "${YELLOW}User data and configuration preserved.${NC}"
fi

# Clean up PATH in .bashrc if it was a user installation
if [ "$INSTALL_MODE" = "user" ]; then
    if grep -q "# Added by file-renamer installer" "$HOME/.bashrc"; then
        echo "Cleaning up PATH in .bashrc"
        sed -i '/# Added by file-renamer installer/d' "$HOME/.bashrc"
        sed -i "/export PATH=\"\$PATH:$BIN_DIR\"/d" "$HOME/.bashrc"
    fi
fi

# Check if we're running from the installation directory
# If so, we need to be careful about removing it
if [[ "$SCRIPT_DIR" == "$INSTALL_DIR" ]]; then
    echo -e "${YELLOW}Running from installation directory.${NC}"
    echo "The installation directory will be removed after this script completes."
    
    # Create a temporary script to remove the installation directory
    TMP_SCRIPT=$(mktemp)
    cat > "$TMP_SCRIPT" << EOF
#!/bin/bash
# Wait for parent process to exit
sleep 1
# Remove the installation directory
rm -rf "$INSTALL_DIR"
# Remove this temporary script
rm -f "$TMP_SCRIPT"
EOF
    chmod +x "$TMP_SCRIPT"
    
    # Run the temporary script in the background
    nohup "$TMP_SCRIPT" >/dev/null 2>&1 &
else
    # We can safely remove the installation directory
    safe_remove "$INSTALL_DIR"
fi

# Report results
echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}File Renamer has been successfully uninstalled!${NC}"
else
    echo -e "${RED}Uninstallation completed with $ERRORS errors.${NC}"
    echo "Some components may not have been completely removed."
    echo "You may need to manually remove them with administrator privileges."
fi

echo ""
echo "Thank you for using File Renamer!"
echo "======================================================"
