"""
Update checker for the Facebook Video Data Tool.
"""

import json
import tkinter as tk
from tkinter import messagebox
import webbrowser
import threading
import requests
from packaging import version

from .. import __version__
from ..utils import get_logger

# GitHub API URL for releases
GITHUB_API_URL = "https://github.com/user/fbvideodata/releases/latest"
GITHUB_RELEASES_URL = "https://github.com/user/fbvideodata/releases"


class UpdateChecker:
    """Check for updates to the application."""

    def __init__(self, parent=None):
        """
        Initialize the update checker.

        Args:
            parent: Parent window for dialogs (optional)
        """
        self.parent = parent
        self.logger = get_logger()
        self.current_version = __version__

    def check_for_updates(self, silent=False):
        """
        Check for updates in a background thread.

        Args:
            silent: If True, only show notification if update is available
        """
        threading.Thread(target=self._check_for_updates_thread, args=(silent,)).start()

    def _check_for_updates_thread(self, silent=False):
        """
        Background thread for checking updates.

        Args:
            silent: If True, only show notification if update is available
        """
        try:
            self.logger.log("Checking for updates...")

            # Get latest release info from GitHub API
            response = requests.get(
                "https://api.github.com/repos/user/fbvideodata/releases/latest",
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=5,
            )
            response.raise_for_status()

            # Parse response
            release_info = response.json()
            latest_version = release_info["tag_name"].lstrip("v")
            release_notes = release_info["body"]
            release_url = release_info["html_url"]

            # Compare versions
            if version.parse(latest_version) > version.parse(self.current_version):
                self.logger.log(f"New version available: {latest_version} (current: {self.current_version})")

                # Show update dialog in main thread
                if self.parent:
                    self.parent.after(0, lambda: self._show_update_dialog(latest_version, release_notes, release_url))
            else:
                self.logger.log(f"No updates available (current: {self.current_version})")

                # Show "no updates" message if not silent
                if not silent and self.parent:
                    self.parent.after(
                        0,
                        lambda: messagebox.showinfo(
                            "No Updates Available",
                            f"You are running the latest version ({self.current_version}).",
                            parent=self.parent,
                        ),
                    )

        except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
            self.logger.log(f"Error checking for updates: {e}")

            # Show error message if not silent
            if not silent and self.parent:
                self.parent.after(
                    0,
                    lambda: messagebox.showwarning(
                        "Update Check Failed",
                        "Could not check for updates. Please try again later or visit the website manually.",
                        parent=self.parent,
                    ),
                )

    def _show_update_dialog(self, latest_version, release_notes, release_url):
        """
        Show dialog with update information.

        Args:
            latest_version: Latest version string
            release_notes: Release notes text
            release_url: URL to the release page
        """
        # Create dialog window
        dialog = tk.Toplevel(self.parent)
        dialog.title("Update Available")
        dialog.geometry("500x400")
        dialog.minsize(400, 300)

        # Make it modal
        dialog.transient(self.parent)
        dialog.grab_set()

        # Dialog content
        tk.Label(dialog, text="A new version is available!", font=("", 12, "bold")).pack(pady=(20, 5))

        tk.Label(dialog, text=f"Current version: {self.current_version} → New version: {latest_version}").pack(
            pady=(0, 10)
        )

        # Frame for release notes
        notes_frame = tk.Frame(dialog)
        notes_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        tk.Label(notes_frame, text="Release Notes:", anchor="w", justify="left").pack(anchor="w")

        # Scrollable text area for release notes
        notes_text = tk.Text(notes_frame, wrap="word", height=10, width=60)
        notes_text.pack(fill=tk.BOTH, expand=True, pady=5)
        notes_text.insert("1.0", release_notes)
        notes_text.config(state="disabled")

        # Add scrollbar
        scrollbar = tk.Scrollbar(notes_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        notes_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=notes_text.yview)

        # Button frame
        button_frame = tk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        # Download button
        tk.Button(
            button_frame, text="Download Update", command=lambda: self._open_download_page(release_url, dialog)
        ).pack(side=tk.LEFT, padx=5)

        # Remind later button
        tk.Button(button_frame, text="Remind Me Later", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _open_download_page(self, url, dialog=None):
        """
        Open the download page in a web browser.

        Args:
            url: URL to open
            dialog: Dialog to close after opening the URL
        """
        try:
            webbrowser.open(url)
            self.logger.log(f"Opened download page: {url}")
        except Exception as e:
            self.logger.log(f"Error opening download page: {e}")
            if self.parent:
                messagebox.showerror(
                    "Error",
                    f"Could not open the download page. Please visit {GITHUB_RELEASES_URL} manually.",
                    parent=self.parent,
                )

        # Close the dialog if provided
        if dialog:
            dialog.destroy()


def check_for_updates(parent=None, silent=False):
    """
    Check for updates to the application.

    Args:
        parent: Parent window for dialogs
        silent: If True, only show notification if update is available
    """
    checker = UpdateChecker(parent)
    checker.check_for_updates(silent)
