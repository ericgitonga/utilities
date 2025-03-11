#!/usr/bin/env python3
# Standard library imports
import tkinter as tk
from tkinter import ttk
from typing import Callable

# Local imports


class DirectorySelectionFrame:
    """Component for directory and file selection"""

    def __init__(
        self,
        parent: ttk.Frame,
        browse_dir_callback: Callable,
        browse_files_callback: Callable,
        selection_mode_callback: Callable,
        dir_path_var: tk.StringVar,
        selected_files_var: tk.StringVar,
        selection_mode_var: tk.StringVar,
    ):
        """
        Initialize directory selection frame

        Args:
            parent: Parent frame
            browse_dir_callback: Callback for directory browsing
            browse_files_callback: Callback for file browsing
            selection_mode_callback: Callback for selection mode change
            dir_path_var: Variable for directory path
            selected_files_var: Variable for selected files display
            selection_mode_var: Variable for selection mode
        """
        self.frame = ttk.LabelFrame(parent, text="File Selection")
        self.frame.pack(fill=tk.X, padx=5, pady=5)

        # Directory path
        ttk.Label(self.frame, text="Directory:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(self.frame, textvariable=dir_path_var, width=50).grid(
            row=0, column=1, padx=5, pady=5, sticky=tk.W + tk.E
        )
        ttk.Button(self.frame, text="Browse Directory...", command=browse_dir_callback).grid(
            row=0, column=2, padx=5, pady=5
        )

        # File selection
        ttk.Label(self.frame, text="Selected Files:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(self.frame, textvariable=selected_files_var, width=50, state="readonly").grid(
            row=1, column=1, padx=5, pady=5, sticky=tk.W + tk.E
        )
        ttk.Button(self.frame, text="Select Files...", command=browse_files_callback).grid(
            row=1, column=2, padx=5, pady=5
        )

        # Radio buttons for file selection mode
        mode_frame = ttk.Frame(self.frame)
        mode_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)

        ttk.Radiobutton(
            mode_frame,
            text="Process entire directory",
            variable=selection_mode_var,
            value="directory",
            command=selection_mode_callback,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            mode_frame,
            text="Process selected files only",
            variable=selection_mode_var,
            value="selected",
            command=selection_mode_callback,
        ).pack(side=tk.LEFT, padx=5)


class OptionsFrame:
    """Component for renaming options"""

    def __init__(
        self,
        parent: ttk.Frame,
        pattern_text_var: tk.StringVar,
        include_date_var: tk.BooleanVar,
        normalize_extensions_var: tk.BooleanVar,
        extension_filter_var: tk.StringVar,
        include_date_callback: Callable,
        normalize_ext_callback: Callable,
    ):
        """
        Initialize options frame

        Args:
            parent: Parent frame
            pattern_text_var: Variable for pattern text
            include_date_var: Variable for include date option
            normalize_extensions_var: Variable for normalize extensions option
            extension_filter_var: Variable for extension filter
            include_date_callback: Callback for include date option
            normalize_ext_callback: Callback for normalize extensions option
        """
        self.frame = ttk.LabelFrame(parent, text="Renaming Options")
        self.frame.pack(fill=tk.X, padx=5, pady=5)

        # Text input for base name
        ttk.Label(self.frame, text="Base Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(self.frame, textvariable=pattern_text_var, width=30).grid(
            row=0, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W + tk.E
        )

        # Help text for sequential pattern
        ttk.Label(self.frame, text="(Files will be renamed to basename_1.ext, basename_2.ext, etc.)").grid(
            row=0, column=3, columnspan=2, padx=5, pady=5, sticky=tk.W
        )

        # Additional options
        ttk.Checkbutton(
            self.frame, text="Include Date (YYYYMMDD)", variable=include_date_var, command=include_date_callback
        ).grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

        # Normalize extensions option
        ttk.Checkbutton(
            self.frame,
            text="Normalize File Extensions (.jpeg → .jpg, etc.)",
            variable=normalize_extensions_var,
            command=normalize_ext_callback,
        ).grid(row=1, column=2, columnspan=2, padx=5, pady=5, sticky=tk.W)

        # Extension filter
        ttk.Label(self.frame, text="Filter by Extension:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(self.frame, textvariable=extension_filter_var, width=10).grid(
            row=2, column=1, padx=5, pady=5, sticky=tk.W
        )
        ttk.Label(self.frame, text="(e.g., jpg,png,txt)").grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)


class PreviewFrame:
    """Component for file rename preview"""

    def __init__(self, parent: ttk.Frame):
        """
        Initialize preview frame

        Args:
            parent: Parent frame
        """
        self.frame = ttk.LabelFrame(parent, text="Preview")
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create treeview for file preview
        columns = ("Original Name", "New Name")
        self.treeview = ttk.Treeview(self.frame, columns=columns, show="headings")

        # Set column headings
        for col in columns:
            self.treeview.heading(col, text=col)
            # Make columns wider to accommodate longer filenames
            self.treeview.column(col, width=400, minwidth=200)

        # Add scrollbar
        y_scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.treeview.yview)
        self.treeview.configure(yscroll=y_scrollbar.set)

        # Add horizontal scrollbar for wide content
        x_scrollbar = ttk.Scrollbar(self.frame, orient=tk.HORIZONTAL, command=self.treeview.xview)
        self.treeview.configure(xscroll=x_scrollbar.set)

        # Place treeview and scrollbars
        self.treeview.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    def update(self, preview_data):
        """
        Update preview with new data

        Args:
            preview_data: List of (original_name, new_name) tuples
        """
        # Clear existing items
        for item in self.treeview.get_children():
            self.treeview.delete(item)

        # Add new preview data
        for preview in preview_data:
            self.treeview.insert("", tk.END, values=(preview.original_name, preview.new_name))


class ButtonFrame:
    """Component for action buttons"""

    def __init__(
        self, parent: ttk.Frame, preview_callback: Callable, rename_callback: Callable, exit_callback: Callable
    ):
        """
        Initialize button frame

        Args:
            parent: Parent frame
            preview_callback: Callback for preview button
            rename_callback: Callback for rename button
            exit_callback: Callback for exit button
        """
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.X, padx=5, pady=10)

        # Use larger buttons with more padding for better visibility
        ttk.Button(self.frame, text="Generate Preview", command=preview_callback, padding=(10, 5)).pack(
            side=tk.LEFT, padx=10
        )

        ttk.Button(self.frame, text="Rename Files", command=rename_callback, padding=(10, 5)).pack(
            side=tk.LEFT, padx=10
        )

        ttk.Button(self.frame, text="Exit", command=exit_callback, padding=(10, 5)).pack(side=tk.RIGHT, padx=10)
