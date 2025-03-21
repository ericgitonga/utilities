"""
Export tab UI for the Facebook Video Data Tool application.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from datetime import datetime

from ..utils import get_logger
from ..api.facebook_api import FacebookAPI
from ..api.google_api import export_to_google_sheet, GoogleSheetsConfig
from .dialogs import GoogleExportSuccessDialog, show_file_export_success


class ExportTab:
    """Export tab with export options."""

    def __init__(self, parent, notebook, config, status_var, get_data_callback):
        """
        Initialize export tab.

        Args:
            parent: Parent frame
            notebook: Parent notebook
            config: Application configuration
            status_var: Status bar variable
            get_data_callback: Callback to get the current video data
        """
        self.parent = parent
        self.notebook = notebook
        self.config = config
        self.status_var = status_var
        self.get_data_callback = get_data_callback
        self.logger = get_logger()

        # Create tab frame
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Export")

        # Build UI
        self._build_ui()

        # Bind events
        self.tab.bind("<FocusOut>", self.on_focus_out)

    def _build_ui(self):
        """Build the tab UI."""
        # Export options frame
        export_frame = ttk.LabelFrame(self.tab, text="Export Options", padding=10)
        export_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Export format
        ttk.Label(export_frame, text="Export Format:").grid(row=0, column=0, sticky=tk.W, pady=5)

        format_frame = ttk.Frame(export_frame)
        format_frame.grid(row=0, column=1, sticky=tk.W, pady=5)

        self.export_format_var = tk.StringVar(value=self.config.export_format)
        ttk.Radiobutton(
            format_frame, text="CSV", variable=self.export_format_var, value="CSV", command=self._toggle_export_options
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            format_frame,
            text="Google Sheet",
            variable=self.export_format_var,
            value="Google",
            command=self._toggle_export_options,
        ).pack(side=tk.LEFT, padx=5)

        # Google Sheets options (conditionally enabled)
        self.google_frame = ttk.Frame(export_frame)
        self.google_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W + tk.E, pady=5)

        ttk.Label(self.google_frame, text="Spreadsheet Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.spreadsheet_name_var = tk.StringVar(value=self.config.spreadsheet_name)
        ttk.Entry(self.google_frame, textvariable=self.spreadsheet_name_var, width=40).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=5
        )

        ttk.Label(self.google_frame, text="Worksheet Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.worksheet_name_var = tk.StringVar(value=self.config.worksheet_name)
        ttk.Entry(self.google_frame, textvariable=self.worksheet_name_var, width=40).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=5
        )

        # Output path for CSV
        self.csv_frame = ttk.Frame(export_frame)
        self.csv_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W + tk.E, pady=5)

        ttk.Label(self.csv_frame, text="Output Directory:").grid(row=0, column=0, sticky=tk.W, pady=5)

        path_frame = ttk.Frame(self.csv_frame)
        path_frame.grid(row=0, column=1, sticky=tk.W + tk.E, pady=5)

        self.output_path_var = tk.StringVar(value=self.config.output_path)
        ttk.Entry(path_frame, textvariable=self.output_path_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="Browse...", command=self._browse_output_path).pack(side=tk.LEFT, padx=5)

        # Initial toggle state
        self._toggle_export_options()

        # Export button
        ttk.Button(self.tab, text="Export Data", command=self._export_data).pack(pady=10)

    def _toggle_export_options(self):
        """Toggle between CSV and Google Sheet export options."""
        if self.export_format_var.get() == "CSV":
            # Disable Google Sheet options
            for child in self.google_frame.winfo_children():
                child.config(state=tk.DISABLED)

            # Enable CSV options
            for child in self.csv_frame.winfo_children():
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        subchild.config(state=tk.NORMAL)
                else:
                    child.config(state=tk.NORMAL)
        else:  # Google
            # Enable Google Sheet options
            for child in self.google_frame.winfo_children():
                child.config(state=tk.NORMAL)

            # Disable CSV options
            for child in self.csv_frame.winfo_children():
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        subchild.config(state=tk.DISABLED)
                else:
                    child.config(state=tk.DISABLED)

    def _browse_output_path(self):
        """Browse for output directory."""
        dir_path = filedialog.askdirectory(title="Select Output Directory")
        if dir_path:
            self.output_path_var.set(dir_path)

    def _export_data(self):
        """Export data using the selected format."""
        # Get video data from data tab
        video_collection = self.get_data_callback()

        if not video_collection or len(video_collection) == 0:
            messagebox.showerror("Error", "No data to export")
            return

        export_format = self.export_format_var.get()

        if export_format == "CSV":
            self._export_to_csv(video_collection)
        else:  # Google Sheets
            self._export_to_google_sheet(video_collection)

    def _export_to_csv(self, video_collection):
        """Export data to CSV file."""
        output_dir = self.output_path_var.get()

        if not os.path.isdir(output_dir):
            messagebox.showerror("Error", "Invalid output directory")
            return

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"facebook_video_data_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)

        self.status_var.set("Exporting to CSV...")
        self.logger.log(f"Exporting data to CSV: {filepath}")

        try:
            # Get access token
            access_token = self.config.get_access_token()
            if not access_token:
                messagebox.showerror("Error", "Please provide an Access Token in the Setup tab")
                self.notebook.select(0)  # Switch to setup tab
                return

            # Initialize API and export
            fb_api = FacebookAPI(access_token)

            # Get raw data from the Pydantic model collection
            raw_data = video_collection.get_raw_data()
            result = fb_api.export_to_csv(raw_data, filepath)

            self.logger.log(f"Export successful: {result}")
            self.status_var.set("Export complete")

            # Show success dialog
            show_file_export_success(self.parent, filepath)

        except Exception as e:
            self.logger.log(f"Error exporting to CSV: {e}")
            messagebox.showerror("Export Error", f"Failed to export to CSV: {e}")
            self.status_var.set("Export failed")

    def _export_to_google_sheet(self, video_collection):
        """Export data to Google Sheets."""
        spreadsheet_name = self.spreadsheet_name_var.get()
        worksheet_name = self.worksheet_name_var.get()

        # Check for credentials
        credentials_path = self.config.credentials_path
        if not credentials_path or not os.path.isfile(credentials_path):
            messagebox.showerror("Error", "Google API credentials file not found")
            return

        # Set environment variable
        os.environ["GOOGLE_CREDENTIALS_PATH"] = credentials_path

        # Validate Google Sheets configuration using Pydantic
        try:
            # This will validate the credentials_path exists
            # We don't need to store the result, just validate inputs
            GoogleSheetsConfig(
                credentials_path=credentials_path,
                spreadsheet_name=spreadsheet_name,
                worksheet_name=worksheet_name,
            )
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid Google Sheets configuration: {e}")
            return

        self.status_var.set("Exporting to Google Sheets...")
        self.logger.log(f"Exporting data to Google Sheets: {spreadsheet_name}/{worksheet_name}")

        # Run in a thread to avoid freezing UI
        threading.Thread(
            target=self._export_to_google_thread,
            args=(video_collection, spreadsheet_name, worksheet_name, credentials_path),
        ).start()

    def _export_to_google_thread(self, video_collection, spreadsheet_name, worksheet_name, credentials_path):
        """Thread for Google Sheets export."""
        try:
            # Get raw data from the Pydantic model collection
            raw_data = video_collection.get_raw_data()

            # Export
            sheet_url = export_to_google_sheet(
                raw_data,
                credentials_path=credentials_path,
                spreadsheet_name=spreadsheet_name,
                worksheet_name=worksheet_name,
            )

            self.logger.log(f"Export successful: {sheet_url}")

            # Show success message with link
            self.parent.after(0, lambda: self._show_google_export_success(sheet_url))

        except Exception as error:
            self.logger.log(f"Error exporting to Google Sheets: {error}")
            error_message = str(error)
            self.parent.after(
                0, lambda: messagebox.showerror("Export Error", f"Failed to export to Google Sheets: {error_message}")
            )
            self.parent.after(0, lambda: self.status_var.set("Export failed"))

    def _show_google_export_success(self, sheet_url):
        """Show success dialog with Google Sheet link."""
        self.status_var.set("Export complete")
        GoogleExportSuccessDialog(self.parent, sheet_url)

    def update_config(self):
        """Update configuration from UI values."""
        # Update Pydantic config through property accessors
        self.config.export_format = self.export_format_var.get()
        self.config.spreadsheet_name = self.spreadsheet_name_var.get()
        self.config.worksheet_name = self.worksheet_name_var.get()
        self.config.output_path = self.output_path_var.get()

    def on_focus_out(self, event=None):
        """Handle focus out event to update config."""
        self.update_config()
        self.config.save_settings()
