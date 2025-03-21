"""
Main application window for the Facebook Video Data Tool.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os

from ..config import Config
from ..utils import get_logger
from ..constants import APP_NAME

from .setup_tab import SetupTab
from .data_tab import DataTab
from .export_tab import ExportTab
from .log_tab import LogTab


class FacebookVideoDataApp:
    """Main application window."""

    def __init__(self, root):
        """
        Initialize the application.

        Args:
            root: Root Tkinter window
        """
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("800x700")
        self.root.minsize(700, 600)

        # Set icon if available
        try:
            if os.path.exists("fbv_icon.ico"):
                self.root.iconbitmap("fbv_icon.ico")
        except tk.TclError:
            pass  # Icon file not found, use default

        # Load configuration
        self.config = Config()

        # Initialize the logger
        self.logger = get_logger()
        self.logger.log("Application started")

        # Set up the UI
        self._setup_ui()

        # Set up clean exit
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_ui(self):
        """Set up the main UI components."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create a notebook (tabbed interface)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Create menu bar
        self._create_menu_bar()

        # Create tabs
        self.setup_tab = SetupTab(self.root, self.notebook, self.config, self.status_var)
        self.data_tab = DataTab(self.root, self.notebook, self.config, self.status_var)
        self.export_tab = ExportTab(
            self.root, self.notebook, self.config, self.status_var, self.data_tab.get_video_data
        )
        self.log_tab = LogTab(self.root, self.notebook, self.status_var)

        # Log startup information
        from .. import __version__

        self.logger.log(f"Application initialized. Version: {__version__}")

        # Check for updates silently at startup
        self.root.after(3000, self._check_for_updates_silent)

    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self._on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Check for Updates", command=self._check_for_updates)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _check_for_updates(self):
        """Check for updates with user notification."""
        from ..utils.update_checker import check_for_updates

        check_for_updates(self.root, silent=False)

    def _check_for_updates_silent(self):
        """Check for updates silently."""
        from ..utils.update_checker import check_for_updates

        check_for_updates(self.root, silent=True)

    def _show_about(self):
        """Show about dialog."""
        from .. import __version__

        about_text = f"""Facebook Video Data Tool v{__version__}
        
A GUI application for non-programmers to easily retrieve, analyze, and export Facebook video data.

Copyright © 2025 Eric Gitonga. All rights reserved.

This software is released under the MIT License.
"""

        messagebox.showinfo("About", about_text, parent=self.root)

    def _on_close(self):
        """Handle application close event."""
        # Save configuration
        self.config.save_settings()
        self.logger.log("Application closed")

        # Close the window
        self.root.destroy()
