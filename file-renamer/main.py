#!/usr/bin/env python3
# Standard library imports
import os
import sys
import threading
import queue
from typing import List

# Third-party imports
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Local imports
from models import AppConfig, RenamePreview, StatusMessage
from file_operations import FileOperations
from ui_components import DirectorySelectionFrame, OptionsFrame, PreviewFrame, ButtonFrame


class SequentialFileRenamer(tk.Tk):
    """Main application class for Sequential File Renamer"""

    def __init__(self):
        super().__init__()

        # Initialize app state
        self.config = AppConfig()
        self.preview_data: List[RenamePreview] = []

        # Setup UI
        self.title("Sequential File Renamer")
        self.geometry("900x650")
        self.minsize(800, 550)

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

        # Initialize variables
        self.initialize_variables()

        # Create GUI elements
        self.create_main_interface()

        # Start periodic check for queue
        self.periodic_call()

        # Center window on screen
        self.center_window()

    def initialize_variables(self):
        """Initialize all tkinter variables"""
        # Directory selection variables
        self.dir_path_var = tk.StringVar()
        self.dir_path_var.trace_add("write", self._on_dir_path_changed)

        self.selected_files_var = tk.StringVar()
        self.selected_files_var.set("No files selected")

        self.selection_mode_var = tk.StringVar(value="directory")

        # Options variables
        self.pattern_text_var = tk.StringVar()
        self.pattern_text_var.trace_add("write", self._on_pattern_text_changed)

        self.include_date_var = tk.BooleanVar(value=self.config.options.include_date)

        self.normalize_extensions_var = tk.BooleanVar(value=self.config.options.normalize_extensions)

        self.extension_filter_var = tk.StringVar(value=self.config.options.extension_filter)
        self.extension_filter_var.trace_add("write", self._on_extension_filter_changed)

    def create_main_interface(self):
        """Create the main UI elements"""
        # Create main frame with additional padding
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Create directory selection frame
        self.dir_frame = DirectorySelectionFrame(
            main_frame,
            self.browse_directory,
            self.browse_files,
            self._on_selection_mode_changed,
            self.dir_path_var,
            self.selected_files_var,
            self.selection_mode_var,
        )

        # Add some vertical spacing
        ttk.Frame(main_frame, height=10).pack(fill=tk.X)

        # Create renaming options frame
        self.options_frame = OptionsFrame(
            main_frame,
            self.pattern_text_var,
            self.include_date_var,
            self.normalize_extensions_var,
            self.extension_filter_var,
            self._on_include_date_changed,
            self._on_normalize_extensions_changed,
        )

        # Add some vertical spacing
        ttk.Frame(main_frame, height=10).pack(fill=tk.X)

        # Preview frame
        self.preview_frame = PreviewFrame(main_frame)

        # Add some vertical spacing
        ttk.Frame(main_frame, height=10).pack(fill=tk.X)

        # Create buttons frame
        self.button_frame = ButtonFrame(main_frame, self.generate_preview, self.rename_files, self.quit)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def center_window(self):
        """Center the window on the screen"""
        # Update the window to ensure it has processed size requests
        self.update_idletasks()

        # Get screen width and height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Calculate position coordinates
        x = (screen_width - self.winfo_width()) // 2
        y = (screen_height - self.winfo_height()) // 2

        # Set the position
        self.geometry(f"+{x}+{y}")

    # Event handlers
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

    # UI actions
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

    # Queue processing
    def process_queue(self):
        """Handle completed background tasks"""
        try:
            status_msg: StatusMessage = self.queue.get(0)
            self.status_var.set(status_msg.message)

            if status_msg.status_type == "preview_done":
                self.preview_frame.update(self.preview_data)
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

    # File operations
    def get_file_list(self) -> List[str]:
        """Get list of files to process based on selection mode"""
        # If in selected files mode and files are selected, use them
        if self.selection_mode_var.get() == "selected" and self.config.selected_files:
            return [os.path.basename(f) for f in self.config.selected_files]

        # Otherwise, get files from directory
        extensions = self.config.options.get_extensions_list()
        return FileOperations.get_files_from_directory(self.config.dir_path, extensions)

    def preview_task(self):
        """Background task for generating preview"""
        files = self.get_file_list()
        preview_data: List[RenamePreview] = []

        # Calculate total files for determining padding in sequence mode
        total_files = len(files)

        for i, filename in enumerate(files):
            new_name = FileOperations.generate_new_filename(filename, self.config.options, i, total_files)
            preview_data.append(RenamePreview(original_name=filename, new_name=new_name))

        self.preview_data = preview_data
        self.queue.put(StatusMessage(message="Preview generated", status_type="preview_done"))

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
                new_name = FileOperations.generate_new_filename(filename, self.config.options, i, total_files)

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
    app = SequentialFileRenamer()
    app.mainloop()
