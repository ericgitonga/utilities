import os
import shutil
import sys


def organize_files_by_type(source_dir):
    """
    Organize files in the source directory by their file type.
    Each file will be moved to a subdirectory named after its extension
    within a 'processed' directory.

    Args:
        source_dir (str): Path to the source directory containing files to organize
    """
    # Convert to absolute path and check if directory exists
    source_dir = os.path.abspath(source_dir)
    if not os.path.exists(source_dir):
        print(f"Error: The directory '{source_dir}' does not exist.")
        return

    # Create the main processed directory
    processed_dir = os.path.join(source_dir, "processed")
    os.makedirs(processed_dir, exist_ok=True)

    # Dictionary to store file counts by extension
    file_counts = {}

    # Walk through the source directory
    for root, _, files in os.walk(source_dir):
        # Skip the processed directory to avoid circular processing
        if os.path.normpath(root).startswith(os.path.normpath(processed_dir)):
            continue

        for filename in files:
            # Skip the script itself if it's in the directory
            if filename == os.path.basename(__file__):
                continue

            file_path = os.path.join(root, filename)

            # Get file extension (without the dot)
            _, extension = os.path.splitext(filename)
            extension = extension[1:].lower() if extension else "no_extension"

            # Create a directory for this extension if it doesn't exist
            extension_dir = os.path.join(processed_dir, extension)
            os.makedirs(extension_dir, exist_ok=True)

            # Destination path
            dest_path = os.path.join(extension_dir, filename)

            # If the file already exists in the destination, add a suffix
            if os.path.exists(dest_path):
                base_name, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dest_path):
                    new_filename = f"{base_name}_{counter}{ext}"
                    dest_path = os.path.join(extension_dir, new_filename)
                    counter += 1

            # Move the file
            try:
                shutil.move(file_path, dest_path)

                # Update file counts
                if extension in file_counts:
                    file_counts[extension] += 1
                else:
                    file_counts[extension] = 1

                print(f"Moved: {filename} -> processed/{extension}/{os.path.basename(dest_path)}")
            except Exception as e:
                print(f"Error moving {filename}: {e}")

    # Print summary
    print("\nOrganization complete!")
    print("Summary of files organized:")
    for ext, count in sorted(file_counts.items()):
        print(f"  {ext}: {count} file(s)")


if __name__ == "__main__":
    # Use command line argument if provided, otherwise use current directory
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = os.getcwd()
        print(f"No directory specified, using current directory: {directory}")

    # Confirm with user
    print(f"This will organize all files in '{directory}' into subdirectories by file type.")
    confirmation = input("Continue? (y/n): ")

    if confirmation.lower() in ["y", "yes"]:
        organize_files_by_type(directory)
    else:
        print("Operation cancelled.")
