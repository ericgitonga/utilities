import os
from PIL import Image
from dotenv import load_dotenv


def process_images_in_directory(input_directory, output_directory, output_ext):
    """
    Scans a directory for common image types, converts them to a specified
    output format, resizes them to 1800x1200, and saves them in a new directory.

    Args:
        input_directory (str): The path to the folder with source images.
        output_directory (str): The path to the folder for processed images.
        output_ext (str): The desired file extension for all output images (e.g., "jpg").
    """
    # Define the supported input file extensions
    SUPPORTED_INPUT_FORMATS = (".png", ".jpg", ".jpeg", ".tiff", ".tif", ".webp")

    # Normalize the output extension to be lowercase and without a dot
    output_ext = output_ext.lower().lstrip(".")

    # Check if the source directory exists
    if not os.path.isdir(input_directory):
        print(f"Error: The source directory '{input_directory}' does not exist.")
        return

    # Create the output directory if it doesn't already exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        print(f"Created directory: {output_directory}")

    # List all files in the input directory
    for file_name in os.listdir(input_directory):
        # Check if the file is one of the supported image types
        if file_name.lower().endswith(SUPPORTED_INPUT_FORMATS):
            input_path = os.path.join(input_directory, file_name)

            try:
                with Image.open(input_path) as img:
                    # --- Image Mode Conversion ---
                    # Handle transparency correctly based on the desired output format
                    if output_ext == "png":
                        # Convert to RGBA to preserve transparency if it exists
                        img_converted = img.convert("RGBA")
                    else:
                        # For non-PNG outputs, convert to RGB to remove any alpha channel
                        if img.mode in ("RGBA", "P", "LA"):
                            img_converted = img.convert("RGB")
                        else:
                            img_converted = img

                    # Resize the image
                    resized_img = img_converted.resize((1800, 1200))

                    # Create the new file name with the desired extension
                    base_name = os.path.splitext(file_name)[0]
                    output_path = os.path.join(output_directory, f"{base_name}.{output_ext}")

                    # --- Save with the correct format ---
                    # Use an explicit format name for JPEG to avoid ambiguity
                    save_format = "jpeg" if output_ext in ["jpg", "jpeg"] else output_ext
                    resized_img.save(output_path, format=save_format)

                    print(f"Successfully processed {file_name} -> {os.path.basename(output_path)}")

            except Exception as e:
                print(f"Could not process {file_name}. Reason: {e}")

    print("\nImage processing complete.")


if __name__ == "__main__":
    # Load environment variables from the .env file in the script's directory
    load_dotenv()

    # Retrieve configuration from environment variables
    source_folder = os.getenv("SOURCE_FOLDER")
    destination_folder = os.getenv("DESTINATION_FOLDER")
    output_type = os.getenv("OUTPUT_TYPE")

    # Check if all required variables were loaded correctly
    if not all([source_folder, destination_folder, output_type]):
        print("Error: Please ensure your .env file is in the script's directory and contains:")
        print("SOURCE_FOLDER, DESTINATION_FOLDER, and OUTPUT_TYPE.")
    else:
        process_images_in_directory(source_folder, destination_folder, output_type)
