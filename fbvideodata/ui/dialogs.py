"""
Common dialogs for the Facebook Video Data Tool application.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import webbrowser

from ..utils import file_utils


class VideoDetailsDialog:
    """Dialog window for displaying detailed video information."""

    def __init__(self, parent, video_data):
        """
        Initialize video details dialog.

        Args:
            parent: Parent window
            video_data: VideoData Pydantic model or dictionary with video data
        """
        self.parent = parent
        self.video_data = video_data

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Video Details")
        self.dialog.geometry("600x500")
        self.dialog.minsize(500, 400)

        # Make it modal
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Build the UI
        self._build_ui()

        # Center the window
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self):
        """Build the dialog UI."""
        # Create frame with padding
        detail_frame = ttk.Frame(self.dialog, padding=10)
        detail_frame.pack(fill=tk.BOTH, expand=True)

        # Convert to dict if not already
        if hasattr(self.video_data, "to_dict"):
            video = self.video_data.to_dict()
        else:
            video = self.video_data

        # Title
        title_text = video.get("title", video.get("display_title", "Untitled"))
        title_label = ttk.Label(detail_frame, text=title_text, font=("", 14, "bold"), wraplength=550)
        title_label.pack(fill=tk.X, pady=5)

        # Create a notebook for details
        detail_notebook = ttk.Notebook(detail_frame)
        detail_notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Basic info tab
        basic_tab = ttk.Frame(detail_notebook, padding=10)
        detail_notebook.add(basic_tab, text="Basic Info")

        # Format basic info text
        info_text = self._format_basic_info(video)

        # Display basic info
        info_display = scrolledtext.ScrolledText(basic_tab, wrap=tk.WORD, height=15)
        info_display.pack(fill=tk.BOTH, expand=True)
        info_display.insert(tk.END, info_text)
        info_display.config(state=tk.DISABLED)

        # URL button
        url = video.get("permalink_url")
        if url:
            ttk.Button(basic_tab, text="Open in Browser", command=lambda: webbrowser.open(url)).pack(pady=5)

        # Watch time tab
        watch_tab = ttk.Frame(detail_notebook, padding=10)
        detail_notebook.add(watch_tab, text="Watch Time")

        watch_text = self._format_watch_time_info(video)

        watch_display = scrolledtext.ScrolledText(watch_tab, wrap=tk.WORD, height=15)
        watch_display.pack(fill=tk.BOTH, expand=True)
        watch_display.insert(tk.END, watch_text)
        watch_display.config(state=tk.DISABLED)

        # Description tab
        desc_tab = ttk.Frame(detail_notebook, padding=10)
        detail_notebook.add(desc_tab, text="Description")

        desc_text = video.get("description", "No description available.")

        desc_display = scrolledtext.ScrolledText(desc_tab, wrap=tk.WORD, height=15)
        desc_display.pack(fill=tk.BOTH, expand=True)
        desc_display.insert(tk.END, desc_text)
        desc_display.config(state=tk.DISABLED)

        # Insights tab if available
        self._add_insights_tab(detail_notebook, video)

        # Raw Data tab
        raw_tab = ttk.Frame(detail_notebook, padding=10)
        detail_notebook.add(raw_tab, text="Raw Data")

        # Get raw data
        if hasattr(self.video_data, "get_raw_data"):
            raw_data = self.video_data.get_raw_data()
        else:
            raw_data = video

        # For Pydantic models, convert to dict for JSON serialization if needed
        if hasattr(raw_data, "dict"):
            raw_data = raw_data.dict(exclude={"_raw_data"})

        json_text = json.dumps(raw_data, indent=2)

        json_display = scrolledtext.ScrolledText(raw_tab, wrap=tk.WORD, height=15, font=("Courier", 10))
        json_display.pack(fill=tk.BOTH, expand=True)
        json_display.insert(tk.END, json_text)
        json_display.config(state=tk.DISABLED)

        # Close button
        ttk.Button(detail_frame, text="Close", command=self.dialog.destroy).pack(pady=10)

    def _format_basic_info(self, video):
        """Format the basic info text."""
        return (
            f"Video ID: {video.get('id', 'N/A')}\n\n"
            f"Created: {video.get('created_time', 'N/A')}\n"
            f"Updated: {video.get('updated_time', 'N/A')}\n\n"
            f"Duration: {video.get('duration', video.get('length', 0))} seconds\n\n"
            f"Views: {video.get('views', 0):,}\n"
            f"Reach: {video.get('reach', 0):,}\n"
            f"Comments: {video.get('comments_count', 0):,}\n"
            f"Likes: {video.get('likes_count', 0):,}\n"
            f"Shares: {video.get('shares_count', 0):,}\n"
            f"Saves: {video.get('saves_count', 0):,}\n"
            f"Link Clicks: {video.get('link_clicks', 'N/A')}\n\n"
            f"URL: {video.get('permalink_url', 'N/A')}"
        )

    def _format_watch_time_info(self, video):
        """Format the watch time tab information."""
        avg_watch = video.get("avg_watch_time", 0)
        total_watch = video.get("total_watch_time", 0)
        views_followers = video.get("views_from_followers", 0)
        views_non_followers = video.get("views_from_non_followers", 0)
        follower_pct = video.get("follower_percentage", 0)
        non_follower_pct = 100 - follower_pct

        return (
            f"Average Watch Time: {avg_watch:.1f} seconds\n"
            f"Total Watch Time: {total_watch:.1f} seconds\n\n"
            f"Audience Breakdown:\n"
            f"- From Followers: {views_followers:,} views ({follower_pct:.1f}%)\n"
            f"- From Non-Followers: {views_non_followers:,} views ({non_follower_pct:.1f}%)\n"
        )

    def _add_insights_tab(self, notebook, video):
        """Add insights tab if insights data is available."""
        # Check for insights in the Pydantic model or dict
        insights_keys = []
        if "insights" in video and isinstance(video["insights"], dict):
            insights_keys = list(video["insights"].keys())
        else:
            insights_keys = [key for key in video.keys() if key.startswith("total_")]

        if not insights_keys:
            return

        insights_tab = ttk.Frame(notebook, padding=10)
        notebook.add(insights_tab, text="Insights")

        insights_text = "Video Insights:\n\n"
        for key in sorted(insights_keys):
            # Format key for display
            display_key = key.replace("total_", "").replace("_", " ").title()

            # Get value from insights dict or directly from video dict
            if "insights" in video and isinstance(video["insights"], dict) and key in video["insights"]:
                value = video["insights"][key]
            else:
                value = video.get(key, 0)

            insights_text += f"{display_key}: {value:,}\n"

        insights_display = scrolledtext.ScrolledText(insights_tab, wrap=tk.WORD, height=15)
        insights_display.pack(fill=tk.BOTH, expand=True)
        insights_display.insert(tk.END, insights_text)
        insights_display.config(state=tk.DISABLED)


class GoogleExportSuccessDialog:
    """Dialog for successful Google Sheets export."""

    def __init__(self, parent, sheet_url):
        """
        Initialize export success dialog.

        Args:
            parent: Parent window
            sheet_url: URL of the exported Google Sheet
        """
        self.parent = parent
        self.sheet_url = sheet_url

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Export Successful")
        self.dialog.geometry("450x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Build the UI
        self._build_ui()

        # Center the window
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self):
        """Build the dialog UI."""
        # Message
        ttk.Label(self.dialog, text="Data successfully exported to Google Sheets!", font=("", 12, "bold")).pack(
            pady=(20, 10)
        )

        # URL display
        url_frame = ttk.Frame(self.dialog)
        url_frame.pack(fill=tk.X, padx=20, pady=10)

        url_entry = ttk.Entry(url_frame, width=50)
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        url_entry.insert(0, self.sheet_url)
        url_entry.config(state="readonly")

        # Copy button
        self.copy_btn = ttk.Button(url_frame, text="Copy", command=self._copy_url)
        self.copy_btn.pack(side=tk.LEFT, padx=5)

        # Open button
        ttk.Button(self.dialog, text="Open in Browser", command=lambda: webbrowser.open(self.sheet_url)).pack(pady=5)

        # Close button
        ttk.Button(self.dialog, text="Close", command=self.dialog.destroy).pack(pady=10)

    def _copy_url(self):
        """Copy sheet URL to clipboard."""
        self.dialog.clipboard_clear()
        self.dialog.clipboard_append(self.sheet_url)
        self.copy_btn.config(text="Copied!")
        self.dialog.after(1000, lambda: self.copy_btn.config(text="Copy"))


class HelpDialog:
    """Dialog for displaying help text."""

    def __init__(self, parent, title, help_text):
        """
        Initialize help dialog.

        Args:
            parent: Parent window
            title: Dialog title
            help_text: Help text to display
        """
        self.parent = parent

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Create text area with scrollbar
        text_frame = ttk.Frame(self.dialog, padding=10)
        text_frame.pack(fill=tk.BOTH, expand=True)

        text_area = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, help_text)
        text_area.config(state=tk.DISABLED)

        # Close button
        ttk.Button(self.dialog, text="Close", command=self.dialog.destroy).pack(pady=10)

        # Center the window
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")


def show_file_export_success(parent, filepath):
    """
    Show success dialog for file export.

    Args:
        parent: Parent window
        filepath: Path to the exported file
    """
    message = f"Data exported to:\n{filepath}\n\nOpen containing folder?"
    if messagebox.askyesno("Export Complete", message, parent=parent):
        file_utils.open_directory(filepath)
