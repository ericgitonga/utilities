import tkinter as tk
from tkinter import filedialog, ttk, messagebox, Menu
import threading
import queue
import sys
import os
import subprocess
import platform
from typing import List, Optional
from PIL import Image, ImageTk
from pathlib import Path

from models import SearchConfig, SimilarityResult
from finder import ImageSimilarityFinder


class ImageSimilarityFinderGUI:
    """
    GUI for the Image Similarity Finder.

    This class implements a graphical user interface for the image similarity finder,
    allowing users to select images, specify search directories, adjust parameters,
    and view results in a visual manner.

    Attributes:
        root (tk.Tk): Tkinter root window
        query_image_path (tk.StringVar): Path to the query image
        search_dirs (List[str]): List of directories to search in
        threshold (tk.DoubleVar): Similarity threshold
        max_results (tk.IntVar): Maximum number of results
        results (List[SimilarityResult]): List of search results
        queue (queue.Queue): Queue for thread communication
    """

    def __init__(self, root):
        """
        Initialize the GUI.

        Args:
            root (tk.Tk): Tkinter root window
        """
        self.root = root
        self.root.title("Image Similarity Finder")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)

        # Configure style
        self.style = ttk.Style()
        self.style.theme_use("clam")  # Use a modern theme if available

        # Variables
        self.query_image_path = tk.StringVar()
        self.search_dirs: List[str] = []
        self.threshold = tk.DoubleVar(value=0.7)
        self.max_results = tk.IntVar(value=10)
        self.results: List[SimilarityResult] = []

        # Create menu bar
        self.create_menu()

        # Create the main layout
        self.create_widgets()

        # Queue for thread communication
        self.queue: queue.Queue = queue.Queue()

    def create_menu(self) -> None:
        """
        Create the application menu bar.

        This method creates a menu bar with File and Help menus, providing options
        for file operations and application information.
        """
        # Create main menu bar
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select Query Image", command=self.browse_query_image)
        file_menu.add_command(label="Add Search Directory", command=self.add_search_dir)
        file_menu.add_command(label="Clear Search Directories", command=self.clear_search_dirs)
        file_menu.add_separator()
        file_menu.add_command(label="Start Search", command=self.start_search)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_program)

        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Instructions", command=self.show_instructions)

    def exit_program(self) -> None:
        """
        Exit the application after confirming with the user.

        This method shows a confirmation dialog and exits the application
        if the user confirms.
        """
        if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            self.root.destroy()
            sys.exit(0)

    def show_about(self) -> None:
        """
        Show information about the application.

        This method displays an about dialog with version and author information.
        """
        messagebox.showinfo(
            "About Image Similarity Finder",
            "Image Similarity Finder v1.0.0\n\n"
            "A tool that finds visually similar images across directories "
            "using computer vision techniques.\n\n"
            "Features:\n"
            "- Find similar images across multiple directories\n"
            "- Works with different image sizes and formats\n"
            "- Adjustable similarity threshold\n\n"
            "Created by Eric Gitonga\n"
            "© 2025 Example Organization",
        )

    def show_instructions(self) -> None:
        """
        Show usage instructions for the application.

        This method displays a dialog with instructions on how to use the application.
        """
        messagebox.showinfo(
            "Instructions",
            "How to use Image Similarity Finder:\n\n"
            "1. Select a query image using 'File > Select Query Image' or the Browse button\n"
            "2. Add directories to search in using 'File > Add Search Directory'\n"
            "3. Adjust the similarity threshold as needed (higher = more similar)\n"
            "4. Set the maximum number of results to display\n"
            "5. Click 'Find Similar Images' to start the search\n"
            "6. Results will appear in the list below, sorted by similarity\n"
            "7. Click on any result to preview the image",
        )

    def create_widgets(self) -> None:
        """
        Create and arrange all widgets for the GUI.

        This method creates the main layout of the GUI, including input fields,
        buttons, progress indicators, results list, and image preview area.
        """
        # Create a main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top section - Input settings
        input_frame = ttk.LabelFrame(main_frame, text="Search Settings", padding="10")
        input_frame.pack(fill=tk.X, pady=5)

        # Query image selection
        ttk.Label(input_frame, text="Query Image:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(input_frame, textvariable=self.query_image_path, width=50).grid(
            row=0, column=1, padx=5, pady=5, sticky=tk.W + tk.E
        )
        ttk.Button(input_frame, text="Browse...", command=self.browse_query_image).grid(row=0, column=2, padx=5, pady=5)

        # Directory selection
        ttk.Label(input_frame, text="Search Directories:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.dirs_listbox = tk.Listbox(input_frame, height=3)
        self.dirs_listbox.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
        dirs_buttons_frame = ttk.Frame(input_frame)
        dirs_buttons_frame.grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(dirs_buttons_frame, text="Add...", command=self.add_search_dir).pack(fill=tk.X, pady=2)
        ttk.Button(dirs_buttons_frame, text="Remove", command=self.remove_search_dir).pack(fill=tk.X, pady=2)
        ttk.Button(dirs_buttons_frame, text="Clear All", command=self.clear_search_dirs).pack(fill=tk.X, pady=2)

        # Threshold and max results
        params_frame = ttk.Frame(input_frame)
        params_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W + tk.E, pady=5)

        ttk.Label(params_frame, text="Similarity Threshold:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Scale(params_frame, from_=0.1, to=1.0, orient=tk.HORIZONTAL, variable=self.threshold, length=200).grid(
            row=0, column=1, padx=5
        )
        self.threshold_label = ttk.Label(params_frame, text=f"{self.threshold.get():.2f}")
        self.threshold_label.grid(row=0, column=2, padx=5)

        # Update threshold label when slider changes
        def update_threshold_label(*args):
            """
            Update the threshold label when the slider value changes.

            Args:
                *args: Variable arguments (required for trace_add callback)
            """
            self.threshold_label.config(text=f"{self.threshold.get():.2f}")

        self.threshold.trace_add("write", update_threshold_label)

        ttk.Label(params_frame, text="Max Results:").grid(row=0, column=3, sticky=tk.W, padx=5)
        ttk.Spinbox(params_frame, from_=1, to=100, textvariable=self.max_results, width=5).grid(row=0, column=4, padx=5)

        # Start search button
        ttk.Button(input_frame, text="Find Similar Images", command=self.start_search).grid(
            row=3, column=0, columnspan=3, pady=10
        )

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            input_frame, orient=tk.HORIZONTAL, length=100, mode="determinate", variable=self.progress_var
        )
        self.progress.grid(row=4, column=0, columnspan=3, sticky=tk.W + tk.E, pady=5)
        self.progress_label = ttk.Label(input_frame, text="")
        self.progress_label.grid(row=5, column=0, columnspan=3, sticky=tk.W)

        # Middle section - Results list
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Results treeview
        columns = ("similarity", "path")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        self.results_tree.heading("similarity", text="Similarity")
        self.results_tree.heading("path", text="Image Path")
        self.results_tree.column("similarity", width=100, anchor=tk.CENTER)
        self.results_tree.column("path", width=600)
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add scrollbar to treeview
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscrollcommand=scrollbar.set)

        # Bind selection event
        self.results_tree.bind("<<TreeviewSelect>>", self.on_result_select)

        # Bind right-click event for context menu
        self.results_tree.bind("<Button-3>", self.show_context_menu)

        # Create context menu
        self.context_menu = Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Open Image", command=self.open_selected_image)
        self.context_menu.add_command(label="Open Containing Folder", command=self.open_containing_folder)

        # Bottom section - Image preview
        preview_frame = ttk.LabelFrame(main_frame, text="Image Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Image display area
        self.image_display = ttk.Label(preview_frame)
        self.image_display.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def browse_query_image(self) -> None:
        """
        Open file browser to select a query image.

        This method displays a file dialog for the user to select an image file,
        updates the query_image_path variable, and shows a preview of the selected image.
        """
        filename = filedialog.askopenfilename(
            title="Select Query Image",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp *.gif"), ("All files", "*.*")),
        )
        if filename:
            self.query_image_path.set(filename)
            self.show_image(filename)
            self.status_var.set(f"Query image selected: {Path(filename).name}")

    def add_search_dir(self) -> None:
        """
        Open directory browser to add a search directory.

        This method displays a directory dialog for the user to select a directory
        to search in, and adds it to the search_dirs list and the listbox display.
        """
        directory = filedialog.askdirectory(title="Select Directory to Search")
        if directory:
            self.search_dirs.append(directory)
            self.dirs_listbox.insert(tk.END, directory)
            self.status_var.set(f"Added directory: {Path(directory).name}")

    def remove_search_dir(self) -> None:
        """
        Remove the selected directory from the search list.

        This method removes the currently selected directory from the search_dirs list
        and the listbox display.
        """
        selection = self.dirs_listbox.curselection()
        if selection:
            index = selection[0]
            dir_name = self.dirs_listbox.get(index)
            self.dirs_listbox.delete(index)
            self.search_dirs.pop(index)
            self.status_var.set(f"Removed directory: {Path(dir_name).name}")
        else:
            messagebox.showinfo("Remove Directory", "Please select a directory to remove")

    def clear_search_dirs(self) -> None:
        """
        Clear all search directories.

        This method removes all directories from the search_dirs list and
        clears the listbox display.
        """
        if self.search_dirs:
            self.search_dirs.clear()
            self.dirs_listbox.delete(0, tk.END)
            self.status_var.set("All search directories cleared")
        else:
            messagebox.showinfo("Clear Directories", "No directories to clear")

    def update_progress(self, current: int, total: int) -> None:
        """
        Update the progress bar and status text.

        This method is called by the search thread to report progress.
        It puts a progress update message in the queue for the main thread to process.

        Args:
            current (int): Current progress (number of images processed)
            total (int): Total items to process
        """
        progress_pct = (current / total) * 100 if total > 0 else 0
        self.queue.put(("progress", progress_pct, f"Processing image {current} of {total}"))

    def process_queue(self) -> None:
        """
        Handle messages from the search thread.

        This method processes messages from the queue, which includes progress updates,
        search results, and error messages. It updates the GUI accordingly.

        Note:
            This method is called repeatedly by the event loop to check for new messages
        """
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg[0] == "progress":
                    _, progress_pct, text = msg
                    self.progress_var.set(progress_pct)
                    self.progress_label.config(text=text)
                    self.status_var.set(text)
                elif msg[0] == "results":
                    _, results = msg
                    self.display_results(results)
                    result_text = f"Found {len(results)} similar images"
                    messagebox.showinfo("Search Complete", result_text)
                    self.progress_label.config(text="Search complete")
                    self.status_var.set(result_text)
                elif msg[0] == "error":
                    _, error_msg = msg
                    messagebox.showerror("Error", error_msg)
                    self.progress_label.config(text="")
                    self.status_var.set(f"Error: {error_msg}")

                self.queue.task_done()
        except queue.Empty:
            pass
        finally:
            # Schedule to check queue again
            self.root.after(100, self.process_queue)

    def create_search_config(self) -> Optional[SearchConfig]:
        """
        Create search configuration from GUI inputs.

        This method reads the current values from the GUI and creates a SearchConfig
        object with validation.

        Returns:
            Optional[SearchConfig]: Validated search configuration or None if validation fails

        Note:
            If validation fails, an error message is put in the queue
        """
        try:
            query_image = self.query_image_path.get()
            search_dirs = self.search_dirs
            threshold = self.threshold.get()
            max_results = self.max_results.get()

            # Validate inputs manually before Pydantic validation
            if not query_image:
                raise ValueError("Please select a query image")

            if not search_dirs:
                raise ValueError("Please add at least one search directory")

            # Create and validate the config
            config = SearchConfig(
                query_image=query_image, search_dirs=search_dirs, threshold=threshold, max_results=max_results
            )

            return config

        except Exception as e:
            self.queue.put(("error", str(e)))
            return None

    def search_thread(self) -> None:
        """
        Perform the search in a background thread.

        This method is run in a separate thread to keep the GUI responsive during
        potentially long-running search operations.

        Note:
            Results and errors are communicated back to the main thread via the queue
        """
        try:
            # Create search config
            config = self.create_search_config()
            if not config:
                return

            # Initialize the finder
            finder = ImageSimilarityFinder(config)

            # Do the search
            results = finder.find_similar_images(self.update_progress)

            # Send results back to main thread
            self.queue.put(("results", results))

        except Exception as e:
            self.queue.put(("error", f"Error during search: {str(e)}"))

    def start_search(self) -> None:
        """
        Start the search process in a separate thread.

        This method clears previous results, resets the progress bar,
        and starts a new thread to perform the search.
        """
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Reset progress
        self.progress_var.set(0)
        self.progress_label.config(text="Starting search...")
        self.status_var.set("Starting search...")

        # Start search thread
        thread = threading.Thread(target=self.search_thread)
        thread.daemon = True
        thread.start()

        # Setup queue processing
        self.process_queue()

    def display_results(self, results: List[SimilarityResult]) -> None:
        """
        Display search results in the treeview.

        This method clears the current results in the treeview and adds the new results.

        Args:
            results (List[SimilarityResult]): List of search results to display
        """
        self.results = results

        # Clear current items
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Add new results
        for result in results:
            self.results_tree.insert("", tk.END, values=(f"{result.similarity:.4f}", str(result.path)))

    def on_result_select(self, event) -> None:
        """
        Handle selection of a result from the treeview.

        This method is called when the user selects a result in the treeview.
        It displays the selected image in the preview area.

        Args:
            event: Tkinter event object (not used)
        """
        selection = self.results_tree.selection()
        if selection:
            item = selection[0]
            # Get the path from the second column
            path = self.results_tree.item(item, "values")[1]
            self.show_image(path)
            # Update status bar
            similarity = self.results_tree.item(item, "values")[0]
            file_name = Path(path).name
            self.status_var.set(f"Viewing: {file_name} (Similarity: {similarity})")
        """
        Image Similarity Finder - Graphical User Interface

        This module implements the graphical user interface for the Image Similarity Finder.
        It provides a user-friendly way to select images, specify search parameters, and view results.

        Classes:
        ImageSimilarityFinderGUI: GUI for the Image Similarity Finder
        """

    def show_context_menu(self, event) -> None:
        """
        Display context menu on right-click in the results treeview.

        This method shows a context menu with options to open the image
        or navigate to its containing folder.

        Args:
            event: Tkinter event object containing information about the click
        """
        # Select the item under the cursor
        item = self.results_tree.identify_row(event.y)
        if item:
            # Select the item and show context menu
            self.results_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def open_selected_image(self) -> None:
        """
        Open the selected image with the default system application.

        This method gets the selected image path and opens it with
        the default application for that file type.
        """
        selection = self.results_tree.selection()
        if selection:
            item = selection[0]
            # Get the path from the second column
            path = self.results_tree.item(item, "values")[1]

            try:
                # Open the file with the default application
                if platform.system() == "Windows":
                    os.startfile(path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.call(("open", path))
                else:  # Linux and other Unix-like
                    subprocess.call(("xdg-open", path))

                self.status_var.set(f"Opened image: {Path(path).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open image: {str(e)}")
                self.status_var.set(f"Error opening image: {str(e)}")

    def open_containing_folder(self) -> None:
        """
        Open the folder containing the selected image.

        This method gets the selected image path, finds its parent directory,
        and opens that directory with the system file explorer.
        """
        selection = self.results_tree.selection()
        if selection:
            item = selection[0]
            # Get the path from the second column
            path = self.results_tree.item(item, "values")[1]
            parent_folder = str(Path(path).parent)

            try:
                # Open the folder with the default file explorer
                if platform.system() == "Windows":
                    os.startfile(parent_folder)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.call(("open", parent_folder))
                else:  # Linux and other Unix-like
                    subprocess.call(("xdg-open", parent_folder))

                self.status_var.set(f"Opened folder: {Path(parent_folder).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder: {str(e)}")
                self.status_var.set(f"Error opening folder: {str(e)}")

    def show_image(self, path: str) -> None:
        """
        Display an image in the preview area.

        This method loads an image from the specified path, resizes it to fit
        the preview area while maintaining aspect ratio, and displays it.

        Args:
            path (str): Path to the image file to display
        """
        try:
            # Open and resize the image for display
            img = Image.open(path)

            # Calculate resize dimensions to fit display area while maintaining aspect ratio
            display_width = 400
            display_height = 300

            img_width, img_height = img.size
            aspect_ratio = img_width / img_height

            if img_width > img_height:
                new_width = display_width
                new_height = int(display_width / aspect_ratio)
            else:
                new_height = display_height
                new_width = int(display_height * aspect_ratio)

            # Resize the image
            img = img.resize((new_width, new_height), Image.LANCZOS)

            # Convert to Tkinter-compatible format
            tk_img = ImageTk.PhotoImage(img)

            # Display the image
            self.image_display.config(image=tk_img)
            self.image_display.image = tk_img  # Keep a reference to prevent garbage collection

        except Exception as e:
            print(f"Error displaying image: {str(e)}")
            self.image_display.config(image=None, text="Error displaying image")
            self.status_var.set(f"Error displaying image: {str(e)}")


def launch_gui() -> None:
    """
    Launch the GUI application.

    This function creates and initializes the Tkinter root window and
    the ImageSimilarityFinderGUI application.
    """
    root = tk.Tk()
    app = ImageSimilarityFinderGUI(root)

    # Handle window close event
    root.protocol("WM_DELETE_WINDOW", app.exit_program)

    root.mainloop()
