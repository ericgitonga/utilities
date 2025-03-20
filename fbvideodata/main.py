"""
Entry point for the Facebook Video Data Tool application.
"""

import tkinter as tk
import os
from fbvideodata.ui import FacebookVideoDataApp


# Get the root directory of the package
def get_package_root():
    """Get the root directory of the package."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    return parent_dir if os.path.exists(os.path.join(parent_dir, "fbvideodata")) else current_dir


# Add package root to path if needed
# package_root = get_package_root()
# if package_root not in sys.path:
#    sys.path.insert(0, package_root)

# Import the app class


def main():
    """Main function to run the application."""
    # Create the root window
    root = tk.Tk()

    # Create and run the application
    FacebookVideoDataApp(root)

    # Start the main loop
    root.mainloop()


if __name__ == "__main__":
    main()
