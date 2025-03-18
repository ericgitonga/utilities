"""
Image Similarity Finder

A tool that finds visually similar images across directories using computer vision techniques.
Supports both GUI and command-line interfaces.

This module provides functionality to:
1. Extract features from images using Histogram of Oriented Gradients (HOG)
2. Compare images based on feature similarity
3. Search directories for images similar to a reference image
4. Present results through a GUI or command line

Author: Claude AI
License: MIT
"""

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
from typing import List, Optional, Callable, Union
from pydantic import BaseModel, Field, validator, DirectoryPath, FilePath


class SearchConfig(BaseModel):
    """
    Configuration settings for image similarity search.

    This model validates and stores the parameters needed for an image similarity search,
    ensuring that all values are within acceptable ranges and that paths exist.

    Attributes:
        query_image (FilePath): Path to the reference image to search for
        search_dirs (List[DirectoryPath]): List of directories to search in
        threshold (float): Similarity threshold (0-1) where 1 means identical
        max_results (int): Maximum number of results to return
    """

    query_image: FilePath = Field(..., description="Path to the query image")
    search_dirs: List[DirectoryPath] = Field(..., min_items=1, description="Directories to search in")
    threshold: float = Field(0.7, ge=0.1, le=1.0, description="Similarity threshold (0-1)")
    max_results: int = Field(10, ge=1, description="Maximum number of results to return")

    @validator("threshold")
    def validate_threshold(cls, v):
        """
        Validate that the threshold is between 0.1 and 1.0.

        Args:
            v (float): The threshold value to validate

        Returns:
            float: The validated threshold

        Raises:
            ValueError: If threshold is outside the valid range
        """
        if v < 0.1 or v > 1.0:
            raise ValueError("Threshold must be between 0.1 and 1.0")
        return v

    @validator("max_results")
    def validate_max_results(cls, v):
        """
        Validate that max_results is at least 1.

        Args:
            v (int): The max_results value to validate

        Returns:
            int: The validated max_results

        Raises:
            ValueError: If max_results is less than 1
        """
        if v < 1:
            raise ValueError("Max results must be at least 1")
        return v


class ImageFeatures(BaseModel):
    """
    Container for image features extracted from an image.

    This model stores the feature vector extracted from an image along with its path.

    Attributes:
        features (Optional[np.ndarray]): Feature vector extracted from the image
        path (FilePath): Path to the image file
    """

    features: Optional[np.ndarray] = None
    path: FilePath

    class Config:
        """
        Pydantic configuration for the ImageFeatures model.

        This allows the model to handle arbitrary types like numpy arrays.
        """

        arbitrary_types_allowed = True


class SimilarityResult(BaseModel):
    """
    Result of an image similarity comparison.

    This model represents a single result from a similarity search,
    including the path to the matched image and its similarity score.

    Attributes:
        path (FilePath): Path to the similar image
        similarity (float): Similarity score between 0 and 1
    """

    path: FilePath
    similarity: float = Field(..., ge=0, le=1)

    class Config:
        """
        Pydantic configuration for the SimilarityResult model.

        This allows the model to handle arbitrary types.
        """

        arbitrary_types_allowed = True


class ImageAnalyzer:
    """
    Class for analyzing and comparing images.

    This class provides methods to extract features from images and
    calculate similarity between images based on their features.
    """

    @staticmethod
    def extract_features(image_path: Union[str, Path]) -> Optional[np.ndarray]:
        """
        Extract features from an image using Histogram of Oriented Gradients (HOG).

        This method loads an image, converts it to grayscale, extracts HOG features,
        and normalizes the feature vector.

        Args:
            image_path (Union[str, Path]): Path to the image file

        Returns:
            Optional[np.ndarray]: Normalized feature vector or None if extraction fails

        Raises:
            No exceptions, but prints error messages if processing fails
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

    @staticmethod
    def calculate_similarity(features1: np.ndarray, features2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two feature vectors.

        This method compares two feature vectors using cosine similarity,
        which measures the cosine of the angle between them.

        Args:
            features1 (np.ndarray): First feature vector
            features2 (np.ndarray): Second feature vector

        Returns:
            float: Similarity score between 0 and 1, where 1 means identical

        Note:
            Returns 0 if either feature vector is None
        """
        if features1 is None or features2 is None:
            return 0

        # Reshape for cosine_similarity function
        f1 = features1.reshape(1, -1)
        f2 = features2.reshape(1, -1)

        return float(cosine_similarity(f1, f2)[0][0])


class ImageSimilarityFinder:
    """
    Main class for finding similar images.

    This class implements the core functionality for finding images similar to a
    reference image across multiple directories.

    Attributes:
        config (SearchConfig): Configuration for the search
        analyzer (ImageAnalyzer): Image analyzer used for feature extraction and comparison
        supported_extensions (set): Set of supported image file extensions
    """

    def __init__(self, config: SearchConfig):
        """
        Initialize the ImageSimilarityFinder with a search configuration.

        Args:
            config (SearchConfig): Configuration for the search
        """
        self.config = config
        self.analyzer = ImageAnalyzer()
        self.supported_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp", ".gif"}

    def find_similar_images(
        self, progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[SimilarityResult]:
        """
        Find images similar to the query image in the search directories.

        This method extracts features from the query image, then searches through
        the specified directories for similar images based on feature comparison.

        Args:
            progress_callback: Optional callback function for progress updates
                Takes two parameters: current progress and total items

        Returns:
            List[SimilarityResult]: List of SimilarityResult objects sorted by similarity

        Note:
            The search can be time-consuming for large directories with many images
        """
        # Extract features from the query image
        query_features = self.analyzer.extract_features(self.config.query_image)
        if query_features is None:
            print(f"Could not process query image: {self.config.query_image}")
            return []

        # List to store results
        results: List[SimilarityResult] = []

        # Get all image files from search directories
        image_files = self._get_image_files()
        total_files = len(image_files)

        # Process each image
        for i, file_path in enumerate(image_files):
            # Update progress
            if progress_callback:
                progress_callback(i, total_files)

            # Extract features from the current image
            current_features = self.analyzer.extract_features(file_path)

            if current_features is not None:
                # Calculate similarity
                similarity = self.analyzer.calculate_similarity(query_features, current_features)

                # Add to results if above threshold
                if similarity >= self.config.threshold:
                    results.append(SimilarityResult(path=file_path, similarity=similarity))

        # Final progress update
        if progress_callback:
            progress_callback(total_files, total_files)

        # Sort results by similarity (highest first)
        results.sort(key=lambda x: x.similarity, reverse=True)

        # Return top results
        return results[: self.config.max_results]

    def _get_image_files(self) -> List[Path]:
        """
        Get all image files from the search directories.

        This method recursively walks through all search directories and collects
        paths to image files with supported extensions.

        Returns:
            List[Path]: List of paths to image files

        Note:
            Skips the query image itself to avoid self-matches
        """
        image_files: List[Path] = []

        for search_dir in self.config.search_dirs:
            search_path = Path(search_dir)

            for root, _, files in os.walk(search_path):
                for file in files:
                    file_path = Path(root) / file

                    # Skip the query image itself
                    if file_path == Path(self.config.query_image).absolute():
                        continue

                    # Check if the file is an image
                    if file_path.suffix.lower() in self.supported_extensions:
                        image_files.append(file_path)

        return image_files


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

        # Create the main layout
        self.create_widgets()

        # Queue for thread communication
        self.queue: queue.Queue = queue.Queue()

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

        # Bottom section - Image preview
        preview_frame = ttk.LabelFrame(main_frame, text="Image Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Image display area
        self.image_display = ttk.Label(preview_frame)
        self.image_display.pack(fill=tk.BOTH, expand=True)

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

    def remove_search_dir(self) -> None:
        """
        Remove the selected directory from the search list.

        This method removes the currently selected directory from the search_dirs list
        and the listbox display.
        """
        selection = self.dirs_listbox.curselection()
        if selection:
            index = selection[0]
            self.dirs_listbox.delete(index)
            self.search_dirs.pop(index)

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


def parse_cli_args() -> Optional[SearchConfig]:
    """
    Parse command line arguments and create a SearchConfig.

    This function parses the command line arguments and creates a SearchConfig
    object if valid arguments are provided.

    Returns:
        Optional[SearchConfig]: SearchConfig object if valid CLI args, None otherwise

    Note:
        Returns None if GUI mode is requested or if insufficient arguments are provided
    """
    parser = argparse.ArgumentParser(description="Find similar images in directories")
    parser.add_argument("query_image", nargs="?", help="Path to the query image")
    parser.add_argument("search_dirs", nargs="*", help="Directories to search in")
    parser.add_argument("--threshold", type=float, default=0.7, help="Similarity threshold (0-1)")
    parser.add_argument("--max-results", type=int, default=10, help="Maximum number of results")
    parser.add_argument("--gui", "-g", action="store_true", help="Start in GUI mode")

    args = parser.parse_args()

    # Check if GUI mode is requested
    if args.gui:
        return None

    # Validate and create config if CLI mode
    if args.query_image and args.search_dirs:
        try:
            config = SearchConfig(
                query_image=args.query_image,
                search_dirs=args.search_dirs,
                threshold=args.threshold,
                max_results=args.max_results,
            )
            return config
        except Exception as e:
            print(f"Error in configuration: {str(e)}")
            parser.print_help()
            sys.exit(1)
    else:
        # If not enough arguments for CLI mode and not explicitly requesting GUI,
        # print help and exit
        if not args.gui:
            parser.print_help()
            sys.exit(1)
        return None


def launch_gui() -> None:
    """
    Launch the GUI application.

    This function creates and initializes the Tkinter root window and
    the ImageSimilarityFinderGUI application.
    """
    root = tk.Tk()
    root.mainloop()


def main() -> None:
    """
    Main entry point for the application.

    This function parses command line arguments and starts either the GUI or
    the command-line interface based on the arguments.
    """
    config = parse_cli_args()

    # Start GUI if requested or if no valid CLI args
    if config is None:
        launch_gui()
    else:
        # Run in CLI mode with the provided config
        finder = ImageSimilarityFinder(config)
        results = finder.find_similar_images()

        # Print results
        if not results:
            print("No similar images found.")
        else:
            print(f"Found {len(results)} similar images:")
            for result in results:
                print(f"Similarity: {result.similarity:.4f} - {result.path}")


if __name__ == "__main__":
    main()
