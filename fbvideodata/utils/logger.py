"""
Logger module for the Facebook Video Data Tool application.
"""

import logging
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox


class Logger:
    """Logger with both file and UI functionality."""

    def __init__(self, log_widget=None):
        """
        Initialize logger.

        Args:
            log_widget: Optional ScrolledText widget for UI logging.
        """
        self.log_widget = log_widget

        # Setup file logger
        self.logger = logging.getLogger("fbvideodata")
        self.logger.setLevel(logging.INFO)

        # Create formatter
        self.formatter = logging.Formatter("[%(asctime)s] %(message)s", "%Y-%m-%d %H:%M:%S")

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)

    def set_log_widget(self, log_widget):
        """Set the UI widget for logging."""
        self.log_widget = log_widget

    def log(self, message, level=logging.INFO):
        """
        Log a message to file and UI if available.

        Args:
            message: Message to log
            level: Logging level
        """
        # Log to file
        self.logger.log(level, message)

        # Log to UI if available
        if self.log_widget:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message = f"[{timestamp}] {message}\n"

            # Enable editing, add message, auto-scroll, and disable editing
            self.log_widget.config(state=tk.NORMAL)
            self.log_widget.insert(tk.END, log_message)
            self.log_widget.see(tk.END)
            self.log_widget.config(state=tk.DISABLED)

    def clear_log_widget(self):
        """Clear the UI log widget."""
        if self.log_widget:
            self.log_widget.config(state=tk.NORMAL)
            self.log_widget.delete(1.0, tk.END)
            self.log_widget.config(state=tk.DISABLED)
            self.log("Log cleared")

    def save_log(self, parent_window=None):
        """
        Save the log to a text file.

        Args:
            parent_window: Parent window for dialogs

        Returns:
            bool: True if save was successful, False otherwise
        """
        if not self.log_widget:
            return False

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"fbv_log_{timestamp}.txt"

        file_path = filedialog.asksaveasfilename(
            parent=parent_window,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile=default_filename,
        )

        if not file_path:
            return False

        try:
            log_content = self.log_widget.get(1.0, tk.END)
            with open(file_path, "w") as f:
                f.write(log_content)

            self.log(f"Log saved to: {file_path}")
            return True
        except (IOError, OSError) as e:
            if parent_window:
                messagebox.showerror("Error", f"Failed to save log: {e}", parent=parent_window)
            self.log(f"Error saving log: {e}", level=logging.ERROR)
            return False


# Create a global logger instance
app_logger = Logger()


def get_logger():
    """Get the global logger instance."""
    return app_logger
