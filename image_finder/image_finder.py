import os
import sys
import numpy as np
from PIL import Image, ImageTk
import argparse
from pathlib import Path
import cv2
from sklearn.metrics.pairwise import cosine_similarity
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
import queue


def extract_features(image_path):
    """
    Extract features from an image using a pre-trained CNN model.
    Returns a feature vector that represents the image.
    """
    try:
        # Read the image
        img = cv2.imread(str(image_path))
        if img is None:
            print(f"Warning: Could not read image {image_path}")
            return None

        # Resize for consistency
        img = cv2.resize(img, (224, 224))

        # Convert to grayscale and extract HOG features
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Use HOG (Histogram of Oriented Gradients) for feature extraction
        win_size = (224, 224)
        block_size = (16, 16)
        block_stride = (8, 8)
        cell_size = (8, 8)
        nbins = 9
        hog = cv2.HOGDescriptor(win_size, block_size, block_stride, cell_size, nbins)
        features = hog.compute(gray)

        # Normalize the features
        if np.linalg.norm(features) > 0:
            features = features / np.linalg.norm(features)

        return features

    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")
        return None


def calculate_similarity(features1, features2):
    """
    Calculate cosine similarity between two feature vectors.
    Returns a value between 0 and 1, where 1 means identical.
    """
    if features1 is None or features2 is None:
        return 0

    # Reshape for cosine_similarity function
    f1 = features1.reshape(1, -1)
    f2 = features2.reshape(1, -1)

    return cosine_similarity(f1, f2)[0][0]


def find_similar_images(query_image_path, search_dirs, threshold=0.7, max_results=10, progress_callback=None):
    """
    Find images similar to the query image in the search directories.

    Args:
        query_image_path: Path to the query image
        search_dirs: List of directories to search in
        threshold: Similarity threshold (0-1)
        max_results: Maximum number of results to return
        progress_callback: Optional callback function for progress updates

    Returns:
        List of tuples (image_path, similarity_score) sorted by similarity
    """
    # Extract features from the query image
    query_features = extract_features(query_image_path)
    if query_features is None:
        print(f"Could not process query image: {query_image_path}")
        return []

    # List to store results
    results = []

    # Supported image extensions
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp", ".gif"}

    # Count total files to process for progress reporting
    total_files = 0
    image_files = []

    for search_dir in search_dirs:
        search_path = Path(search_dir)

        for root, _, files in os.walk(search_path):
            for file in files:
                file_path = Path(root) / file

                # Skip the query image itself
                if file_path == Path(query_image_path).absolute():
                    continue

                # Check if the file is an image
                if file_path.suffix.lower() in image_extensions:
                    image_files.append(file_path)
                    total_files += 1

    # Process each image
    for i, file_path in enumerate(image_files):
        # Update progress
        if progress_callback:
            progress_callback(i, total_files)

        # Extract features from the current image
        current_features = extract_features(file_path)

        if current_features is not None:
            # Calculate similarity
            similarity = calculate_similarity(query_features, current_features)

            # Add to results if above threshold
            if similarity >= threshold:
                results.append((str(file_path), similarity))

    # Final progress update
    if progress_callback:
        progress_callback(total_files, total_files)

    # Sort results by similarity (highest first)
    results.sort(key=lambda x: x[1], reverse=True)

    # Return top results
    return results[:max_results]


class ImageSimilarityFinderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Similarity Finder")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)

        # Configure style
        self.style = ttk.Style()
        self.style.theme_use("clam")  # Use a modern theme if available

        # Variables
        self.query_image_path = tk.StringVar()
        self.search_dirs = []
        self.threshold = tk.DoubleVar(value=0.7)
        self.max_results = tk.IntVar(value=10)
        self.results = []
        self.current_image_index = 0

        # Create the main layout
        self.create_widgets()

        # Queue for thread communication
        self.queue = queue.Queue()

    def create_widgets(self):
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

        # Threshold and max results
        params_frame = ttk.Frame(input_frame)
        params_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W + tk.E, pady=5)

        ttk.Label(params_frame, text="Similarity Threshold:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Scale(params_frame, from_=0.1, to=1.0, orient=tk.HORIZONTAL, variable=self.threshold, length=200).grid(
            row=0, column=1, padx=5
        )
        ttk.Label(params_frame, textvariable=tk.StringVar(value=lambda: f"{self.threshold.get():.2f}")).grid(
            row=0, column=2, padx=5
        )

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

        # Bottom section - Image preview
        preview_frame = ttk.LabelFrame(main_frame, text="Image Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Image display area
        self.image_display = ttk.Label(preview_frame)
        self.image_display.pack(fill=tk.BOTH, expand=True)

    def browse_query_image(self):
        filename = filedialog.askopenfilename(
            title="Select Query Image",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp *.gif"), ("All files", "*.*")),
        )
        if filename:
            self.query_image_path.set(filename)
            self.show_image(filename)

    def add_search_dir(self):
        directory = filedialog.askdirectory(title="Select Directory to Search")
        if directory:
            self.search_dirs.append(directory)
            self.dirs_listbox.insert(tk.END, directory)

    def remove_search_dir(self):
        selection = self.dirs_listbox.curselection()
        if selection:
            index = selection[0]
            self.dirs_listbox.delete(index)
            self.search_dirs.pop(index)

    def update_progress(self, current, total):
        """Update the progress bar and status text"""
        progress_pct = (current / total) * 100 if total > 0 else 0
        self.queue.put(("progress", progress_pct, f"Processing image {current} of {total}"))

    def process_queue(self):
        """Handle messages from the search thread"""
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg[0] == "progress":
                    _, progress_pct, text = msg
                    self.progress_var.set(progress_pct)
                    self.progress_label.config(text=text)
                elif msg[0] == "results":
                    _, results = msg
                    self.display_results(results)
                    messagebox.showinfo("Search Complete", f"Found {len(results)} similar images.")
                    self.progress_label.config(text="Search complete")
                elif msg[0] == "error":
                    _, error_msg = msg
                    messagebox.showerror("Error", error_msg)
                    self.progress_label.config(text="")

                self.queue.task_done()
        except queue.Empty:
            pass
        finally:
            # Schedule to check queue again
            self.root.after(100, self.process_queue)

    def search_thread(self):
        """Perform the search in a background thread"""
        try:
            query_image = self.query_image_path.get()
            search_dirs = self.search_dirs
            threshold = self.threshold.get()
            max_results = self.max_results.get()

            # Validate inputs
            if not query_image:
                self.queue.put(("error", "Please select a query image"))
                return

            if not search_dirs:
                self.queue.put(("error", "Please add at least one search directory"))
                return

            # Do the search
            results = find_similar_images(query_image, search_dirs, threshold, max_results, self.update_progress)

            # Send results back to main thread
            self.queue.put(("results", results))

        except Exception as e:
            self.queue.put(("error", f"Error during search: {str(e)}"))

    def start_search(self):
        """Start the search process in a separate thread"""
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Reset progress
        self.progress_var.set(0)
        self.progress_label.config(text="Starting search...")

        # Start search thread
        thread = threading.Thread(target=self.search_thread)
        thread.daemon = True
        thread.start()

        # Setup queue processing
        self.process_queue()

    def display_results(self, results):
        """Display search results in the treeview"""
        self.results = results

        # Clear current items
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Add new results
        for i, (path, similarity) in enumerate(results):
            self.results_tree.insert("", tk.END, values=(f"{similarity:.4f}", path))

    def on_result_select(self, event):
        """Handle selection of a result from the treeview"""
        selection = self.results_tree.selection()
        if selection:
            item = selection[0]
            # Get the path from the second column
            path = self.results_tree.item(item, "values")[1]
            self.show_image(path)

    def show_image(self, path):
        """Display an image in the preview area"""
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


def main():
    # Check if running in GUI or CLI mode
    if len(sys.argv) > 1 and sys.argv[1] not in ["--gui", "-g"]:
        # CLI mode
        parser = argparse.ArgumentParser(description="Find similar images in directories")
        parser.add_argument("query_image", help="Path to the query image")
        parser.add_argument("search_dirs", nargs="+", help="Directories to search in")
        parser.add_argument("--threshold", type=float, default=0.7, help="Similarity threshold (0-1)")
        parser.add_argument("--max-results", type=int, default=10, help="Maximum number of results")
        parser.add_argument("--gui", "-g", action="store_true", help="Start in GUI mode")

        args = parser.parse_args()

        if args.gui:
            # Launch GUI even if other arguments are provided
            launch_gui()
        else:
            # Run in CLI mode
            results = find_similar_images(args.query_image, args.search_dirs, args.threshold, args.max_results)

            # Print results
            if not results:
                print("No similar images found.")
            else:
                print(f"Found {len(results)} similar images:")
                for path, score in results:
                    print(f"Similarity: {score:.4f} - {path}")
    else:
        # No arguments or explicitly requested GUI mode
        launch_gui()


def launch_gui():
    """Launch the GUI application"""
    root = tk.Tk()
    root.mainloop()


if __name__ == "__main__":
    main()
