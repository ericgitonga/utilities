#!/usr/bin/env python3
import os
import re
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import threading
import queue
from typing import List, Literal
from enum import Enum
from pydantic import BaseModel, Field, validator


# Define enums and models
class PatternType(str, Enum):
    PREFIX = "prefix"
    SUFFIX = "suffix"
    REPLACE = "replace"
    REGEX = "regex"


class RenameOptions(BaseModel):
    pattern_type: PatternType = Field(default=PatternType.PREFIX)
    pattern_text: str = Field(default="")
    replace_text: str = Field(default="")
    include_date: bool = Field(default=False)
    include_numbers: bool = Field(default=False)
    extension_filter: str = Field(default="")

    @validator("extension_filter")
    def validate_extension_filter(cls, v):
        """Validate the extension filter format"""
        if v.strip() and not all(ext.strip() for ext in v.split(",")):
            raise ValueError("Extension filter must be comma-separated values")
        return v.lower().strip()

    def get_extensions_list(self) -> List[str]:
        """Convert extension string to list"""
        if not self.extension_filter:
            return []
        return [ext.strip() for ext in self.extension_filter.split(",")]


class RenamePreview(BaseModel):
    original_name: str
    new_name: str


class AppConfig(BaseModel):
    dir_path: str = Field(default="")
    options: RenameOptions = Field(default_factory=RenameOptions)


class StatusMessage(BaseModel):
    message: str
    status_type: Literal["info", "warning", "error", "success", "preview_done", "rename_done", "rename_error"] = "info"


class FileRenamer(tk.Tk):
    def __init__(self):
        super().__init__()

        # Initialize app state
        self.config = AppConfig()
        self.preview_data: List[RenamePreview] = []

        # Setup UI
        self.title("File Renamer")
        self.geometry("800x600")
        self.minsize(600, 400)

        # Set application icon (you would need to replace with actual icon path)
        if sys.platform.startswith("win"):
            try:
                self.iconbitmap(default="icon.ico")
            except tk.TclError:
                pass  # Icon file not found, continue without icon

        # Configure style
        self.style = ttk.Style()
        self.style.theme_use("clam")  # Use a cross-platform theme

        # Create GUI elements
        self._create_main_interface()

        # For threaded operations
        self.queue: queue.Queue = queue.Queue()
        self.periodic_call()

    def _create_main_interface(self):
        """Create the main UI elements"""
        # Create main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create directory selection frame
        self._create_directory_frame(main_frame)

        # Create renaming options frame
        self._create_options_frame(main_frame)

        # Preview frame
        self._create_preview_frame(main_frame)

        # Create buttons frame
        self._create_button_frame(main_frame)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_directory_frame(self, parent):
        """Create the directory selection UI"""
        dir_frame = ttk.LabelFrame(parent, text="Directory Selection")
        dir_frame.pack(fill=tk.X, padx=5, pady=5)

        self.dir_path_var = tk.StringVar()
        self.dir_path_var.trace_add("write", self._on_dir_path_changed)

        ttk.Label(dir_frame, text="Directory:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(dir_frame, textvariable=self.dir_path_var, width=50).grid(
            row=0, column=1, padx=5, pady=5, sticky=tk.W + tk.E
        )
        ttk.Button(dir_frame, text="Browse...", command=self.browse_directory).grid(row=0, column=2, padx=5, pady=5)

    def _on_dir_path_changed(self, *args):
        """Update config when directory path changes"""
        self.config.dir_path = self.dir_path_var.get()

    def _create_options_frame(self, parent):
        """Create the renaming options UI"""
        options_frame = ttk.LabelFrame(parent, text="Renaming Options")
        options_frame.pack(fill=tk.X, padx=5, pady=5)

        # Rename pattern options
        ttk.Label(options_frame, text="Rename Pattern:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.pattern_type_var = tk.StringVar(value=self.config.options.pattern_type)
        self.pattern_type_var.trace_add("write", self._on_pattern_type_changed)

        ttk.Radiobutton(
            options_frame, text="Add Prefix", variable=self.pattern_type_var, value=PatternType.PREFIX
        ).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Radiobutton(
            options_frame, text="Add Suffix", variable=self.pattern_type_var, value=PatternType.SUFFIX
        ).grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        ttk.Radiobutton(
            options_frame, text="Replace Text", variable=self.pattern_type_var, value=PatternType.REPLACE
        ).grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        ttk.Radiobutton(
            options_frame, text="Regular Expression", variable=self.pattern_type_var, value=PatternType.REGEX
        ).grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)

        # Text inputs for pattern
        ttk.Label(options_frame, text="Text:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.pattern_text_var = tk.StringVar()
        self.pattern_text_var.trace_add("write", self._on_pattern_text_changed)
        ttk.Entry(options_frame, textvariable=self.pattern_text_var, width=30).grid(
            row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W + tk.E
        )

        ttk.Label(options_frame, text="Replace With:").grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        self.replace_text_var = tk.StringVar()
        self.replace_text_var.trace_add("write", self._on_replace_text_changed)
        ttk.Entry(options_frame, textvariable=self.replace_text_var, width=30).grid(
            row=1, column=4, padx=5, pady=5, sticky=tk.W + tk.E
        )

        # Additional options
        self.include_date_var = tk.BooleanVar(value=self.config.options.include_date)
        self.include_date_var.trace_add("write", self._on_include_date_changed)
        ttk.Checkbutton(options_frame, text="Include Date (YYYYMMDD)", variable=self.include_date_var).grid(
            row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W
        )

        self.include_numbers_var = tk.BooleanVar(value=self.config.options.include_numbers)
        self.include_numbers_var.trace_add("write", self._on_include_numbers_changed)
        ttk.Checkbutton(options_frame, text="Include Numbering", variable=self.include_numbers_var).grid(
            row=2, column=2, columnspan=2, padx=5, pady=5, sticky=tk.W
        )

        self.extension_filter_var = tk.StringVar(value=self.config.options.extension_filter)
        self.extension_filter_var.trace_add("write", self._on_extension_filter_changed)
        ttk.Label(options_frame, text="Filter by Extension:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(options_frame, textvariable=self.extension_filter_var, width=10).grid(
            row=3, column=1, padx=5, pady=5, sticky=tk.W
        )
        ttk.Label(options_frame, text="(e.g., jpg,png,txt)").grid(row=3, column=2, padx=5, pady=5, sticky=tk.W)

    def _on_pattern_type_changed(self, *args):
        """Update config when pattern type changes"""
        try:
            self.config.options.pattern_type = PatternType(self.pattern_type_var.get())
        except (ValueError, KeyError):
            self.config.options.pattern_type = PatternType.PREFIX
            self.pattern_type_var.set(PatternType.PREFIX)

    def _on_pattern_text_changed(self, *args):
        """Update config when pattern text changes"""
        self.config.options.pattern_text = self.pattern_text_var.get()

    def _on_replace_text_changed(self, *args):
        """Update config when replace text changes"""
        self.config.options.replace_text = self.replace_text_var.get()

    def _on_include_date_changed(self, *args):
        """Update config when include date changes"""
        self.config.options.include_date = self.include_date_var.get()

    def _on_include_numbers_changed(self, *args):
        """Update config when include numbers changes"""
        self.config.options.include_numbers = self.include_numbers_var.get()

    def _on_extension_filter_changed(self, *args):
        """Update config when extension filter changes"""
        try:
            self.config.options.extension_filter = self.extension_filter_var.get()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            self.extension_filter_var.set("")

    def _create_preview_frame(self, parent):
        """Create the preview UI"""
        preview_frame = ttk.LabelFrame(parent, text="Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create treeview for file preview
        columns = ("Original Name", "New Name")
        self.preview_tree = ttk.Treeview(preview_frame, columns=columns, show="headings")

        # Set column headings
        for col in columns:
            self.preview_tree.heading(col, text=col)
            self.preview_tree.column(col, width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        self.preview_tree.configure(yscroll=scrollbar.set)

        # Place treeview and scrollbar
        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_button_frame(self, parent):
        """Create the button UI"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=10)

        ttk.Button(button_frame, text="Generate Preview", command=self.generate_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Rename Files", command=self.rename_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.quit).pack(side=tk.RIGHT, padx=5)

    def browse_directory(self):
        """Open directory browser dialog"""
        directory = filedialog.askdirectory()
        if directory:
            self.dir_path_var.set(directory)

    def process_queue(self):
        """Handle completed background tasks"""
        try:
            status_msg: StatusMessage = self.queue.get(0)
            self.status_var.set(status_msg.message)

            if status_msg.status_type == "preview_done":
                self.update_preview_display()
            elif status_msg.status_type == "rename_done":
                messagebox.showinfo("Success", "Files have been renamed successfully!")
            elif status_msg.status_type == "rename_error":
                pass  # Error message already displayed in rename_task

        except queue.Empty:
            pass

    def periodic_call(self):
        """Check if there is something new in the queue"""
        self.process_queue()
        self.after(100, self.periodic_call)

    def get_file_list(self) -> List[str]:
        """Get list of files in the selected directory"""
        directory = self.config.dir_path
        if not directory or not os.path.isdir(directory):
            messagebox.showerror("Error", "Please select a valid directory.")
            return []

        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

        # Filter by extension if specified
        extensions = self.config.options.get_extensions_list()
        if extensions:
            files = [f for f in files if os.path.splitext(f)[1].lower().lstrip(".") in extensions]

        return files

    def generate_new_filename(self, filename: str, index: int = 0) -> str:
        """Generate new filename based on selected options"""
        file_name, file_ext = os.path.splitext(filename)

        # Get current date if needed
        date_prefix = ""
        if self.config.options.include_date:
            date_prefix = datetime.now().strftime("%Y%m%d_")

        # Get numbering if needed
        number_str = ""
        if self.config.options.include_numbers:
            number_str = f"_{index+1:03d}"

        # Apply renaming pattern
        pattern_type = self.config.options.pattern_type
        pattern_text = self.config.options.pattern_text

        if pattern_type == PatternType.PREFIX:
            new_name = f"{date_prefix}{pattern_text}{file_name}{number_str}{file_ext}"
        elif pattern_type == PatternType.SUFFIX:
            new_name = f"{date_prefix}{file_name}{pattern_text}{number_str}{file_ext}"
        elif pattern_type == PatternType.REPLACE:
            replaced_name = file_name.replace(pattern_text, self.config.options.replace_text)
            new_name = f"{date_prefix}{replaced_name}{number_str}{file_ext}"
        elif pattern_type == PatternType.REGEX:
            try:
                replaced_name = re.sub(pattern_text, self.config.options.replace_text, file_name)
                new_name = f"{date_prefix}{replaced_name}{number_str}{file_ext}"
            except re.error as e:
                messagebox.showerror("Regex Error", f"Invalid regular expression: {str(e)}")
                new_name = filename

        return new_name

    def preview_task(self):
        """Background task for generating preview"""
        files = self.get_file_list()
        preview_data: List[RenamePreview] = []

        for i, filename in enumerate(files):
            new_name = self.generate_new_filename(filename, i)
            preview_data.append(RenamePreview(original_name=filename, new_name=new_name))

        self.preview_data = preview_data
        self.queue.put(StatusMessage(message="Preview generated", status_type="preview_done"))

    def update_preview_display(self):
        """Update the preview treeview with generated data"""
        # Clear existing items
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        # Add new preview data
        for preview in self.preview_data:
            self.preview_tree.insert("", tk.END, values=(preview.original_name, preview.new_name))

    def generate_preview(self):
        """Generate preview of renaming operations"""
        self.status_var.set("Generating preview...")

        # Run in background thread
        threading.Thread(target=self.preview_task, daemon=True).start()

    def rename_task(self):
        """Background task for renaming files"""
        files = self.get_file_list()
        renamed_count = 0
        errors: List[str] = []

        for i, filename in enumerate(files):
            try:
                new_name = self.generate_new_filename(filename, i)

                # Skip if names are the same
                if filename == new_name:
                    continue

                # Check for file name conflicts
                if os.path.exists(os.path.join(self.config.dir_path, new_name)):
                    errors.append(f"Cannot rename {filename}: {new_name} already exists")
                    continue

                # Rename the file
                os.rename(os.path.join(self.config.dir_path, filename), os.path.join(self.config.dir_path, new_name))
                renamed_count += 1

            except Exception as e:
                errors.append(f"Error renaming {filename}: {str(e)}")

        if errors:
            self.queue.put(
                StatusMessage(
                    message=f"Renamed {renamed_count} files with {len(errors)} errors", status_type="rename_error"
                )
            )
            messagebox.showerror("Rename Errors", "\n".join(errors))
        else:
            self.queue.put(
                StatusMessage(message=f"Renamed {renamed_count} files successfully", status_type="rename_done")
            )

    def rename_files(self):
        """Rename files based on selected options"""
        if not self.config.dir_path or not os.path.isdir(self.config.dir_path):
            messagebox.showerror("Error", "Please select a valid directory.")
            return

        # Confirm before renaming
        if not messagebox.askyesno("Confirm", "Are you sure you want to rename these files?"):
            return

        self.status_var.set("Renaming files...")

        # Run in background thread
        threading.Thread(target=self.rename_task, daemon=True).start()


if __name__ == "__main__":
    app = FileRenamer()
    app.mainloop()
