import os
import shutil
import argparse


def organize_files_by_category(source_dir, recursive=True):
    """
    Organize files in the source directory by their file category.
    Each file will be moved to a subdirectory named after its category
    within a 'processed' directory.

    Args:
        source_dir (str): Path to the source directory containing files to organize
        recursive (bool): Whether to process subdirectories recursively
    """
    # Convert to absolute path and check if directory exists
    source_dir = os.path.abspath(source_dir)
    if not os.path.exists(source_dir):
        print(f"Error: The directory '{source_dir}' does not exist.")
        return

    # Create the main processed directory
    processed_dir = os.path.join(source_dir, "processed")
    os.makedirs(processed_dir, exist_ok=True)

    # Dictionary to store file counts by category
    file_counts = {}

    # Process files based on recursion option
    if recursive:
        # Recursive processing (walk through all subdirectories)
        for root, _, files in os.walk(source_dir):
            # Skip the processed directory to avoid circular processing
            if os.path.normpath(root).startswith(os.path.normpath(processed_dir)):
                continue

            process_files_in_directory(root, files, processed_dir, file_counts)
    else:
        # Non-recursive processing (only process files in the specified directory)
        files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
        process_files_in_directory(source_dir, files, processed_dir, file_counts)

    # Print summary
    print("\nOrganization complete!")
    print("Summary of files organized:")
    for category, count in sorted(file_counts.items()):
        print(f"  {category}: {count} file(s)")


def get_file_category(extension):
    """
    Determine the category of a file based on its extension.

    Args:
        extension (str): The file extension without the dot

    Returns:
        str: The category name to use as a directory name
    """
    # Define extension categories
    extension_categories = {
        "Documents": ["pdf", "doc", "docx", "txt", "rtf", "odt", "md", "csv", "xls", "xlsx", "ppt", "pptx"],
        "Images": [
            "jpg",
            "jpeg",
            "png",
            "gif",
            "bmp",
            "tiff",
            "tif",
            "webp",
            "svg",
            "ico",
            "heic",
            "psd",
            "dng",
            "nef",
        ],
        "Audio": ["mp3", "wav", "ogg", "flac", "aac", "m4a"],
        "Video": ["mp4", "avi", "mkv", "mov", "wmv", "flv", "webm", "m4v"],
        "Archives": ["zip", "rar", "tar", "gz", "7z"],
        "Code": ["py", "js", "html", "css", "java", "c", "cpp", "go", "rs", "php", "rb", "ipynb", "jar"],
    }

    # Find which category the extension belongs to
    for category, extensions in extension_categories.items():
        if extension in extensions:
            return category

    # If no category matches, return "Misc"
    return "Misc"


def process_files_in_directory(directory, files, processed_dir, file_counts):
    """
    Process files in a given directory and move them to the appropriate category location.

    Args:
        directory (str): Directory containing the files to process
        files (list): List of filenames to process
        processed_dir (str): Path to the processed directory
        file_counts (dict): Dictionary to track file counts by category
    """
    for filename in files:
        # Skip the script itself if it's in the directory
        if filename == os.path.basename(__file__):
            continue

        file_path = os.path.join(directory, filename)

        # Get file extension (without the dot)
        _, extension = os.path.splitext(filename)
        extension = extension[1:].lower() if extension else "no_extension"

        # Get the category for this file
        if extension == "no_extension":
            category = "Misc"
        else:
            category = get_file_category(extension)

        # Create a directory for this file category if it doesn't exist
        category_dir = os.path.join(processed_dir, category)
        os.makedirs(category_dir, exist_ok=True)

        # Destination path
        dest_path = os.path.join(category_dir, filename)

        # If the file already exists in the destination, add a suffix
        if os.path.exists(dest_path):
            base_name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest_path):
                new_filename = f"{base_name}_{counter}{ext}"
                dest_path = os.path.join(category_dir, new_filename)
                counter += 1

        # Move the file
        try:
            shutil.move(file_path, dest_path)

            # Update file counts
            if category in file_counts:
                file_counts[category] += 1
            else:
                file_counts[category] = 1

            print(f"Moved: {filename} -> processed/{category}/{os.path.basename(dest_path)}")
        except Exception as e:
            print(f"Error moving {filename}: {e}")


if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(description="Organize files by their category into a 'processed' directory.")
    parser.add_argument(
        "directory", nargs="?", default=os.getcwd(), help="The directory to organize (default: current directory)"
    )
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Process subdirectories recursively (default: False)"
    )
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt (default: False)")

    # Parse arguments
    args = parser.parse_args()

    # Display information about the operation
    recursive_str = "recursively " if args.recursive else ""
    print(f"This will organize all files {recursive_str}in '{args.directory}' into category subdirectories.")

    # Confirm with user unless --yes flag is used
    if args.yes:
        confirmation = "y"
    else:
        confirmation = input("Continue? (y/n): ")

    if confirmation.lower() in ["y", "yes"]:
        organize_files_by_category(args.directory, args.recursive)
    else:
        print("Operation cancelled.")
