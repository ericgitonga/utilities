"""
Main application window for the Facebook Video Data Tool.
"""

import tkinter as tk
from tkinter import ttk
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

        # Create tabs
        self.setup_tab = SetupTab(self.root, self.notebook, self.config, self.status_var)
        self.data_tab = DataTab(self.root, self.notebook, self.config, self.status_var)
        self.export_tab = ExportTab(
            self.root, self.notebook, self.config, self.status_var, self.data_tab.get_video_data
        )
        self.log_tab = LogTab(self.root, self.notebook, self.status_var)

        # Log startup information
        self.logger.log(f"Application initialized. Version: {self.config.__class__.__module__}")

    def _on_close(self):
        """Handle application close event."""
        # Save configuration
        self.config.save_settings()
        self.logger.log("Application closed")

        # Close the window
        self.root.destroy()
