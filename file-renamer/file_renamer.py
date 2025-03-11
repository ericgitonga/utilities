#!/usr/bin/env python3
import os
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
    SEQUENCE = "sequence"  # Sequential renaming pattern


class RenameOptions(BaseModel):
    pattern_type: PatternType = Field(default=PatternType.SEQUENCE)
    pattern_text: str = Field(default="")
    include_date: bool = Field(default=False)
    extension_filter: str = Field(default="")
    normalize_extensions: bool = Field(default=True)  # New option to normalize extensions

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
    selected_files: List[str] = Field(default_factory=list)
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

        # For threaded operations
        self.queue: queue.Queue = queue.Queue()

        # Create GUI elements
        self._create_main_interface()

        # Start periodic check for queue
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
        """Create the directory and file selection UI"""
        dir_frame = ttk.LabelFrame(parent, text="File Selection")
        dir_frame.pack(fill=tk.X, padx=5, pady=5)

        # Directory path
        self.dir_path_var = tk.StringVar()

        ttk.Label(dir_frame, text="Directory:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(dir_frame, textvariable=self.dir_path_var, width=50).grid(
            row=0, column=1, padx=5, pady=5, sticky=tk.W + tk.E
        )
        ttk.Button(dir_frame, text="Browse Directory...", command=self.browse_directory).grid(
            row=0, column=2, padx=5, pady=5
        )

        # File selection
        ttk.Label(dir_frame, text="Selected Files:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.selected_files_var = tk.StringVar()
        self.selected_files_var.set("No files selected")
        ttk.Entry(dir_frame, textvariable=self.selected_files_var, width=50, state="readonly").grid(
            row=1, column=1, padx=5, pady=5, sticky=tk.W + tk.E
        )
        ttk.Button(dir_frame, text="Select Files...", command=self.browse_files).grid(row=1, column=2, padx=5, pady=5)

        # Radio buttons for file selection mode
        self.selection_mode_var = tk.StringVar(value="directory")

        mode_frame = ttk.Frame(dir_frame)
        mode_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)

        ttk.Radiobutton(
            mode_frame,
            text="Process entire directory",
            variable=self.selection_mode_var,
            value="directory",
            command=self._on_selection_mode_changed,
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            mode_frame,
            text="Process selected files only",
            variable=self.selection_mode_var,
            value="selected",
            command=self._on_selection_mode_changed,
        ).pack(side=tk.LEFT, padx=5)

        # Connect directory path change event
        self.dir_path_var.trace_add("write", self._on_dir_path_changed)

    def _on_dir_path_changed(self, *args):
        """Update config when directory path changes"""
        self.config.dir_path = self.dir_path_var.get()

    def _on_selection_mode_changed(self):
        """Handle changes to the file selection mode"""
        mode = self.selection_mode_var.get()
        if mode == "directory":
            # Clear selected files when switching to directory mode
            self.config.selected_files = []
            self.selected_files_var.set("No files selected")
        elif mode == "selected" and not self.config.selected_files:
            # If switching to selected mode but no files are selected
            self.selected_files_var.set("No files selected")
        self.generate_preview()

    def _update_selected_files_display(self):
        """Update the display of selected files"""
        if not self.config.selected_files:
            self.selected_files_var.set("No files selected")
        elif len(self.config.selected_files) == 1:
            self.selected_files_var.set(os.path.basename(self.config.selected_files[0]))
        else:
            self.selected_files_var.set(f"{len(self.config.selected_files)} files selected")

    def browse_files(self):
        """Open file browser dialog for selecting multiple files"""
        files = filedialog.askopenfilenames(
            title="Select Files to Rename",
            initialdir=self.config.dir_path if self.config.dir_path else os.path.expanduser("~"),
        )

        if files:
            # Get the directory of the first selected file
            self.config.dir_path = os.path.dirname(files[0])
            self.dir_path_var.set(self.config.dir_path)

            # Update selected files
            self.config.selected_files = list(files)
            self._update_selected_files_display()

            # Switch to selected files mode
            self.selection_mode_var.set("selected")

            # Generate preview with the selected files
            self.generate_preview()

    def _create_options_frame(self, parent):
        """Create the renaming options UI"""
        options_frame = ttk.LabelFrame(parent, text="Renaming Options")
        options_frame.pack(fill=tk.X, padx=5, pady=5)

        # Text input for base name
        ttk.Label(options_frame, text="Base Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.pattern_text_var = tk.StringVar()
        ttk.Entry(options_frame, textvariable=self.pattern_text_var, width=30).grid(
            row=0, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W + tk.E
        )

        # Help text for sequential pattern
        ttk.Label(options_frame, text="(Files will be renamed to basename_1.ext, basename_2.ext, etc.)").grid(
            row=0, column=3, columnspan=2, padx=5, pady=5, sticky=tk.W
        )

        # Additional options
        self.include_date_var = tk.BooleanVar(value=self.config.options.include_date)
        ttk.Checkbutton(
            options_frame,
            text="Include Date (YYYYMMDD)",
            variable=self.include_date_var,
            command=self._on_include_date_changed,
        ).grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

        # Normalize extensions option
        self.normalize_extensions_var = tk.BooleanVar(value=self.config.options.normalize_extensions)
        ttk.Checkbutton(
            options_frame,
            text="Normalize File Extensions (.jpeg → .jpg, etc.)",
            variable=self.normalize_extensions_var,
            command=self._on_normalize_extensions_changed,
        ).grid(row=1, column=2, columnspan=2, padx=5, pady=5, sticky=tk.W)

        # Extension filter
        self.extension_filter_var = tk.StringVar(value=self.config.options.extension_filter)
        ttk.Label(options_frame, text="Filter by Extension:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(options_frame, textvariable=self.extension_filter_var, width=10).grid(
            row=2, column=1, padx=5, pady=5, sticky=tk.W
        )
        ttk.Label(options_frame, text="(e.g., jpg,png,txt)").grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)

        # Connect text change events
        self.pattern_text_var.trace_add("write", self._on_pattern_text_changed)
        self.extension_filter_var.trace_add("write", self._on_extension_filter_changed)

    def _on_pattern_text_changed(self, *args):
        """Update config when pattern text changes"""
        self.config.options.pattern_text = self.pattern_text_var.get()

    def _on_include_date_changed(self):
        """Update config when include date changes"""
        self.config.options.include_date = self.include_date_var.get()

    def _on_normalize_extensions_changed(self):
        """Update config when normalize extensions option changes"""
        self.config.options.normalize_extensions = self.normalize_extensions_var.get()

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
            # Clear selected files when changing directory
            self.config.selected_files = []
            self._update_selected_files_display()
            # Switch to directory mode
            self.selection_mode_var.set("directory")
            # Generate preview with the new directory
            self.generate_preview()

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
        """Get list of files to process based on selection mode"""
        # If in selected files mode and files are selected, use them
        if self.selection_mode_var.get() == "selected" and self.config.selected_files:
            return [os.path.basename(f) for f in self.config.selected_files]

        # Otherwise, get files from directory
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

    def _determine_padding_digits(self, count: int) -> int:
        """Determine the number of digits needed for padding based on file count"""
        if count < 10:
            return 1
        elif count < 100:
            return 2
        elif count < 1000:
            return 3
        else:
            return len(str(count))

    def _normalize_extension(self, filename: str) -> str:
        """Normalize file extensions to their more common forms"""
        name, ext = os.path.splitext(filename)
        ext = ext.lower()

        # Dictionary of less common extensions and their normalized forms
        extension_map = {
            ".jpeg": ".jpg",
            ".tiff": ".tif",
            ".htm": ".html",
            ".mpeg": ".mpg",
            ".mov": ".mp4",
            ".text": ".txt",
            ".midi": ".mid",
            ".markdown": ".md",
            ".png2": ".png",
        }

        # Return normalized filename if extension is in our map
        if ext in extension_map:
            return name + extension_map[ext]
        return filename

    def generate_new_filename(self, filename: str, index: int = 0, total_files: int = 0) -> str:
        """Generate new filename based on sequential pattern"""
        # First normalize the extension if enabled
        if self.config.options.normalize_extensions:
            filename = self._normalize_extension(filename)

        file_name, file_ext = os.path.splitext(filename)

        # Get current date if needed
        date_prefix = ""
        if self.config.options.include_date:
            date_prefix = datetime.now().strftime("%Y%m%d_")

        # Get base name from user input
        base_name = self.config.options.pattern_text

        # Determine padding digits based on total file count
        padding = self._determine_padding_digits(total_files)

        # Create new filename with sequential pattern
        new_name = f"{date_prefix}{base_name}_{index+1:0{padding}d}{file_ext}"

        return new_name

    def preview_task(self):
        """Background task for generating preview"""
        files = self.get_file_list()
        preview_data: List[RenamePreview] = []

        # Calculate total files for determining padding in sequence mode
        total_files = len(files)

        for i, filename in enumerate(files):
            new_name = self.generate_new_filename(filename, i, total_files)
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

        # Calculate total files for determining padding in sequence mode
        total_files = len(files)

        is_selected_mode = self.selection_mode_var.get() == "selected" and self.config.selected_files

        for i, filename in enumerate(files):
            try:
                new_name = self.generate_new_filename(filename, i, total_files)

                # Skip if names are the same
                if filename == new_name:
                    continue

                # Determine file paths based on mode
                if is_selected_mode:
                    # For selected files mode, use the full paths from selected_files
                    original_path = self.config.selected_files[i]
                    new_path = os.path.join(os.path.dirname(original_path), new_name)
                else:
                    # For directory mode, use the directory and filenames
                    original_path = os.path.join(self.config.dir_path, filename)
                    new_path = os.path.join(self.config.dir_path, new_name)

                # Check for file name conflicts
                if os.path.exists(new_path):
                    errors.append(f"Cannot rename {filename}: {new_name} already exists")
                    continue

                # Rename the file
                os.rename(original_path, new_path)
                renamed_count += 1

                # Update the selected_files list if in selected mode
                if is_selected_mode:
                    self.config.selected_files[i] = new_path

            except Exception as e:
                errors.append(f"Error renaming {filename}: {str(e)}")

        # Update the selected files display if needed
        if is_selected_mode:
            self._update_selected_files_display()

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
        # Check if we have files to rename
        if self.selection_mode_var.get() == "selected" and not self.config.selected_files:
            messagebox.showerror("Error", "Please select files to rename.")
            return
        elif self.selection_mode_var.get() == "directory" and (
            not self.config.dir_path or not os.path.isdir(self.config.dir_path)
        ):
            messagebox.showerror("Error", "Please select a valid directory.")
            return

        # Get a count of files to be renamed
        files = self.get_file_list()
        if not files:
            messagebox.showerror("Error", "No files found to rename.")
            return

        # Confirm before renaming
        if not messagebox.askyesno("Confirm", f"Are you sure you want to rename {len(files)} files?"):
            return

        self.status_var.set("Renaming files...")

        # Run in background thread
        threading.Thread(target=self.rename_task, daemon=True).start()


if __name__ == "__main__":
    app = FileRenamer()
    app.mainloop()
