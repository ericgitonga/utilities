"""
Log tab UI for the Facebook Video Data Tool application.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext

from ..utils import get_logger


class LogTab:
    """Log tab with scrollable text area for log messages."""

    def __init__(self, parent, notebook, status_var):
        """
        Initialize log tab.

        Args:
            parent: Parent frame
            notebook: Parent notebook
            status_var: Status bar variable
        """
        self.parent = parent
        self.notebook = notebook
        self.status_var = status_var

        # Create tab frame
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Log")

        # Build UI
        self._build_ui()

        # Set up the logger
        self.logger = get_logger()
        self.logger.set_log_widget(self.log_text)

    def _build_ui(self):
        """Build the tab UI."""
        # Log frame
        log_frame = ttk.Frame(self.tab, padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create text area with scrollbar
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

        # Buttons
        button_frame = ttk.Frame(self.tab)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(button_frame, text="Clear Log", command=self._clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Log", command=self._save_log).pack(side=tk.LEFT, padx=5)

    def _clear_log(self):
        """Clear the log text."""
        self.logger.clear_log_widget()

    def _save_log(self):
        """Save the log to a file."""
        self.logger.save_log(parent_window=self.parent)
