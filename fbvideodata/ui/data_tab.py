"""
Data tab UI for the Facebook Video Data Tool application.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading

from ..utils import get_logger
from .dialogs import VideoDetailsDialog
from ..api import facebook_api
from ..models.video_data import VideoDataCollection


class DataTab:
    """Data tab with video data display."""

    def __init__(self, parent, notebook, config, status_var):
        """
        Initialize data tab.

        Args:
            parent: Parent frame
            notebook: Parent notebook
            config: Application configuration
            status_var: Status bar variable
        """
        self.parent = parent
        self.notebook = notebook
        self.config = config
        self.status_var = status_var
        self.logger = get_logger()

        # Data storage - initialize with empty Pydantic model
        self.video_collection = VideoDataCollection(videos=[])

        # Create tab frame
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Video Data")

        # Build UI
        self._build_ui()

        # Bind events
        self.tab.bind("<FocusOut>", self.on_focus_out)

    def _build_ui(self):
        """Build the tab UI."""
        # Control frame
        control_frame = ttk.Frame(self.tab, padding=5)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(control_frame, text="Fetch Video Data", command=self._fetch_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear Data", command=self._clear_data).pack(side=tk.LEFT, padx=5)

        # Create Treeview with scrollbars
        tree_frame = ttk.Frame(self.tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create vertical scrollbar
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Create horizontal scrollbar
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        # Create Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("title", "created", "views", "reach", "comments", "likes", "shares", "avg_watch"),
            show="headings",
            selectmode="browse",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
        )

        # Configure scrollbars
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        # Define columns
        self.tree.heading("title", text="Title")
        self.tree.heading("created", text="Created Date")
        self.tree.heading("views", text="Views")
        self.tree.heading("reach", text="Reach")
        self.tree.heading("comments", text="Comments")
        self.tree.heading("likes", text="Likes")
        self.tree.heading("shares", text="Shares")
        self.tree.heading("avg_watch", text="Avg Watch")

        # Set column widths
        self.tree.column("title", width=200, minwidth=100)
        self.tree.column("created", width=150, minwidth=100)
        self.tree.column("views", width=70, minwidth=50)
        self.tree.column("reach", width=70, minwidth=50)
        self.tree.column("comments", width=70, minwidth=50)
        self.tree.column("likes", width=70, minwidth=50)
        self.tree.column("shares", width=70, minwidth=50)
        self.tree.column("avg_watch", width=80, minwidth=70)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Double-click to view details
        self.tree.bind("<Double-1>", self._show_video_details)

        # Stats frame
        stats_frame = ttk.LabelFrame(self.tab, text="Statistics", padding=5)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)

        self.stats_label = ttk.Label(stats_frame, text="No data loaded")
        self.stats_label.pack(pady=5)

    def _fetch_data(self):
        """Fetch video data from Facebook."""
        # Check if we need to update config first
        if hasattr(self.notebook, "select"):
            setup_tab = self.notebook.tab(0, option="text")
            if setup_tab == "Setup":
                # Get setup tab widget and update config
                setup_widget = self.notebook.children["!frame"]
                if hasattr(setup_widget, "update_config"):
                    setup_widget.update_config()

        page_id = self.config.page_id
        max_videos = self.config.max_videos

        if not page_id:
            messagebox.showerror("Error", "Please enter a Page ID in the Setup tab")
            self.notebook.select(0)  # Switch to setup tab
            return

        # Get access token
        access_token = self.config.get_access_token()
        if not access_token:
            messagebox.showerror("Error", "Please provide an Access Token in the Setup tab")
            self.notebook.select(0)  # Switch to setup tab
            return

        self.status_var.set("Fetching data...")
        self.logger.log(f"Fetching video data for Page ID: {page_id} (max: {max_videos} videos)...")

        # Clear previous data
        self._clear_data()

        # Run in a thread to avoid freezing UI
        threading.Thread(target=self._fetch_data_thread, args=(page_id, access_token, max_videos)).start()

    def _fetch_data_thread(self, page_id, access_token, max_videos):
        """Thread for fetching video data."""
        try:
            # Get video data
            video_data = facebook_api.get_all_facebook_video_data(page_id, access_token, max_videos)

            # Updated: Use VideoDataCollection.from_api_response for Pydantic validation
            self.video_collection = VideoDataCollection.from_api_response(video_data)

            # Update UI with results
            self.parent.after(0, self._update_data_display)

        except Exception as error:
            self.logger.log(f"Error fetching data: {error}")
            error_message = str(error)
            self.parent.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch data: {error_message}"))
            self.parent.after(0, lambda: self.status_var.set("Error fetching data"))
            return

        self.parent.after(0, lambda: self.status_var.set(f"Fetched {len(self.video_collection)} videos"))

    def _update_data_display(self):
        """Update the treeview with fetched data."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        if len(self.video_collection) == 0:
            self.logger.log("No videos found.")
            self.stats_label.configure(text="No videos found")
            return

        # Add data to treeview
        for i, video in enumerate(self.video_collection.videos):
            title = video.display_title
            created_time = video.created_time_formatted

            # Format watch time to 1 decimal place if available
            avg_watch = f"{video.avg_watch_time:.1f}s" if video.avg_watch_time else "N/A"

            # Insert data into tree
            self.tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    title,
                    created_time,
                    f"{video.views:,}",
                    f"{video.reach:,}" if video.reach else "N/A",
                    f"{video.comments_count:,}",
                    f"{video.likes_count:,}",
                    f"{video.shares_count:,}",
                    avg_watch,
                ),
            )

        # Calculate and display statistics
        stats = self.video_collection.get_statistics()

        stats_text = (
            f"Total Videos: {stats['total_videos']} | "
            f"Total Views: {stats['total_views']:,} | "
            f"Average Views: {stats['average_views']:,.1f} | "
            f"Average Watch Time: {stats.get('average_watch_time', 0):,.1f}s | "
            f"Total Engagements: {stats['total_engagement']:,}"
        )

        self.stats_label.configure(text=stats_text)

        # Log
        self.logger.log(f"Fetched {stats['total_videos']} videos with {stats['total_views']:,} total views")

        # Switch to data tab
        self.notebook.select(self.tab)

    def _show_video_details(self, event):
        """Show detailed information about a selected video."""
        selected_item = self.tree.selection()
        if not selected_item:
            return

        # Get the video data
        idx = int(selected_item[0])
        video = self.video_collection.get_video(idx)

        if video:
            VideoDetailsDialog(self.parent, video)

    def _clear_data(self):
        """Clear all loaded data."""
        # Clear treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Clear data using Pydantic model's clear method
        self.video_collection.clear()

        # Update stats
        self.stats_label.configure(text="No data loaded")

        self.logger.log("Data cleared")

    def get_video_data(self):
        """Get the current video data collection."""
        return self.video_collection

    def on_focus_out(self, event=None):
        """Handle focus out event to update config."""
        # Nothing to update for this tab
        pass
