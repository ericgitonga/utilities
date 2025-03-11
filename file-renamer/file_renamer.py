#!/usr/bin/env python3
import os
import re
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import threading
import queue


class FileRenamer(tk.Tk):
    def __init__(self):
        super().__init__()

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

        # Create main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create directory selection frame
        dir_frame = ttk.LabelFrame(main_frame, text="Directory Selection")
        dir_frame.pack(fill=tk.X, padx=5, pady=5)

        self.dir_path = tk.StringVar()

        ttk.Label(dir_frame, text="Directory:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(dir_frame, textvariable=self.dir_path, width=50).grid(
            row=0, column=1, padx=5, pady=5, sticky=tk.W + tk.E
        )
        ttk.Button(dir_frame, text="Browse...", command=self.browse_directory).grid(row=0, column=2, padx=5, pady=5)

        # Create renaming options frame
        options_frame = ttk.LabelFrame(main_frame, text="Renaming Options")
        options_frame.pack(fill=tk.X, padx=5, pady=5)

        # Rename pattern options
        ttk.Label(options_frame, text="Rename Pattern:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.pattern_type = tk.StringVar(value="prefix")
        ttk.Radiobutton(options_frame, text="Add Prefix", variable=self.pattern_type, value="prefix").grid(
            row=0, column=1, padx=5, pady=5, sticky=tk.W
        )
        ttk.Radiobutton(options_frame, text="Add Suffix", variable=self.pattern_type, value="suffix").grid(
            row=0, column=2, padx=5, pady=5, sticky=tk.W
        )
        ttk.Radiobutton(options_frame, text="Replace Text", variable=self.pattern_type, value="replace").grid(
            row=0, column=3, padx=5, pady=5, sticky=tk.W
        )
        ttk.Radiobutton(options_frame, text="Regular Expression", variable=self.pattern_type, value="regex").grid(
            row=0, column=4, padx=5, pady=5, sticky=tk.W
        )

        # Text inputs for pattern
        ttk.Label(options_frame, text="Text:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.pattern_text = tk.StringVar()
        ttk.Entry(options_frame, textvariable=self.pattern_text, width=30).grid(
            row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W + tk.E
        )

        ttk.Label(options_frame, text="Replace With:").grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        self.replace_text = tk.StringVar()
        ttk.Entry(options_frame, textvariable=self.replace_text, width=30).grid(
            row=1, column=4, padx=5, pady=5, sticky=tk.W + tk.E
        )

        # Additional options
        self.include_date = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Include Date (YYYYMMDD)", variable=self.include_date).grid(
            row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W
        )

        self.include_numbers = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Include Numbering", variable=self.include_numbers).grid(
            row=2, column=2, columnspan=2, padx=5, pady=5, sticky=tk.W
        )

        self.extension_filter = tk.StringVar()
        ttk.Label(options_frame, text="Filter by Extension:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(options_frame, textvariable=self.extension_filter, width=10).grid(
            row=3, column=1, padx=5, pady=5, sticky=tk.W
        )
        ttk.Label(options_frame, text="(e.g., jpg,png,txt)").grid(row=3, column=2, padx=5, pady=5, sticky=tk.W)

        # Preview frame
        preview_frame = ttk.LabelFrame(main_frame, text="Preview")
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

        # Create buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)

        ttk.Button(button_frame, text="Generate Preview", command=self.generate_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Rename Files", command=self.rename_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.quit).pack(side=tk.RIGHT, padx=5)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # For threaded operations
        self.queue = queue.Queue()
        self.preview_data = []
        self.periodic_call()

    def browse_directory(self):
        """Open directory browser dialog"""
        directory = filedialog.askdirectory()
        if directory:
            self.dir_path.set(directory)

    def process_queue(self):
        """Handle completed background tasks"""
        try:
            msg, status = self.queue.get(0)
            self.status_var.set(msg)

            if status == "preview_done":
                self.update_preview_display()
            elif status == "rename_done":
                messagebox.showinfo("Success", "Files have been renamed successfully!")

        except queue.Empty:
            pass

    def periodic_call(self):
        """Check if there is something new in the queue"""
        self.process_queue()
        self.after(100, self.periodic_call)

    def get_file_list(self):
        """Get list of files in the selected directory"""
        directory = self.dir_path.get()
        if not directory or not os.path.isdir(directory):
            messagebox.showerror("Error", "Please select a valid directory.")
            return []

        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

        # Filter by extension if specified
        extensions = self.extension_filter.get().strip().lower()
        if extensions:
            ext_list = [ext.strip() for ext in extensions.split(",")]
            files = [f for f in files if os.path.splitext(f)[1].lower().lstrip(".") in ext_list]

        return files

    def generate_new_filename(self, filename, index=0):
        """Generate new filename based on selected options"""
        file_name, file_ext = os.path.splitext(filename)

        # Get current date if needed
        date_prefix = ""
        if self.include_date.get():
            date_prefix = datetime.now().strftime("%Y%m%d_")

        # Get numbering if needed
        number_str = ""
        if self.include_numbers.get():
            number_str = f"_{index+1:03d}"

        # Apply renaming pattern
        pattern_type = self.pattern_type.get()
        pattern_text = self.pattern_text.get()

        if pattern_type == "prefix":
            new_name = f"{date_prefix}{pattern_text}{file_name}{number_str}{file_ext}"
        elif pattern_type == "suffix":
            new_name = f"{date_prefix}{file_name}{pattern_text}{number_str}{file_ext}"
        elif pattern_type == "replace":
            new_name = f"{date_prefix}{file_name.replace(pattern_text, self.replace_text.get())}{number_str}{file_ext}"
        elif pattern_type == "regex":
            try:
                new_name = (
                    f"{date_prefix}{re.sub(pattern_text, self.replace_text.get(), file_name)}{number_str}{file_ext}"
                )
            except re.error as e:
                messagebox.showerror("Regex Error", f"Invalid regular expression: {str(e)}")
                new_name = filename

        return new_name

    def preview_task(self):
        """Background task for generating preview"""
        files = self.get_file_list()
        self.preview_data = []

        for i, filename in enumerate(files):
            new_name = self.generate_new_filename(filename, i)
            self.preview_data.append((filename, new_name))

        self.queue.put(("Preview generated", "preview_done"))

    def update_preview_display(self):
        """Update the preview treeview with generated data"""
        # Clear existing items
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        # Add new preview data
        for original, new_name in self.preview_data:
            self.preview_tree.insert("", tk.END, values=(original, new_name))

    def generate_preview(self):
        """Generate preview of renaming operations"""
        self.status_var.set("Generating preview...")

        # Run in background thread
        threading.Thread(target=self.preview_task, daemon=True).start()

    def rename_task(self):
        """Background task for renaming files"""
        files = self.get_file_list()
        renamed_count = 0
        errors = []

        for i, filename in enumerate(files):
            try:
                new_name = self.generate_new_filename(filename, i)

                # Skip if names are the same
                if filename == new_name:
                    continue

                # Check for file name conflicts
                if os.path.exists(os.path.join(self.dir_path.get(), new_name)):
                    errors.append(f"Cannot rename {filename}: {new_name} already exists")
                    continue

                # Rename the file
                os.rename(os.path.join(self.dir_path.get(), filename), os.path.join(self.dir_path.get(), new_name))
                renamed_count += 1

            except Exception as e:
                errors.append(f"Error renaming {filename}: {str(e)}")

        if errors:
            self.queue.put((f"Renamed {renamed_count} files with {len(errors)} errors", "rename_error"))
            messagebox.showerror("Rename Errors", "\n".join(errors))
        else:
            self.queue.put((f"Renamed {renamed_count} files successfully", "rename_done"))

    def rename_files(self):
        """Rename files based on selected options"""
        if not self.dir_path.get() or not os.path.isdir(self.dir_path.get()):
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
