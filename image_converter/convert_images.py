import os
from PIL import Image
from dotenv import load_dotenv


def calculate_new_dimensions(original_width, original_height, longest_edge):
    """
    Calculates new dimensions for an image, preserving the aspect ratio.
    The longest edge of the new dimensions will match the specified `longest_edge` size.

    Args:
        original_width (int): The original width of the image.
        original_height (int): The original height of the image.
        longest_edge (int): The target size for the longest side.

    Returns:
        tuple: A tuple containing the new (width, height).
    """
    if original_width >= original_height:
        # Landscape or square image
        aspect_ratio = original_height / original_width
        new_width = longest_edge
        new_height = int(new_width * aspect_ratio)
    else:
        # Portrait image
        aspect_ratio = original_width / original_height
        new_height = longest_edge
        new_width = int(new_height * aspect_ratio)

    return (new_width, new_height)


def process_images_in_directory(input_dir, output_dir, output_ext, longest_edge):
    """
    Scans a directory for common image types, converts them to a specified
    output format, resizes them based on the longest edge, and saves them.

    Args:
        input_dir (str): The path to the folder with source images.
        output_dir (str): The path to the folder for processed images.
        output_ext (str): The desired file extension for all output images.
        longest_edge (int): The target size for the longest side of the images.
    """
    SUPPORTED_INPUT_FORMATS = (".png", ".jpg", ".jpeg", ".tiff", ".tif", ".webp")
    output_ext = output_ext.lower().lstrip(".")

    if not os.path.isdir(input_dir):
        print(f"Error: The source directory '{input_dir}' does not exist.")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    for file_name in os.listdir(input_dir):
        if file_name.lower().endswith(SUPPORTED_INPUT_FORMATS):
            input_path = os.path.join(input_dir, file_name)

            try:
                with Image.open(input_path) as img:
                    # Calculate new dimensions while preserving aspect ratio
                    new_size = calculate_new_dimensions(img.width, img.height, longest_edge)

                    # Convert image mode for compatibility
                    if output_ext == "png":
                        img_converted = img.convert("RGBA")
                    else:
                        img_converted = img.convert("RGB") if img.mode in ("RGBA", "P", "LA") else img

                    # Resize the image using the calculated dimensions
                    resized_img = img_converted.resize(new_size, Image.Resampling.LANCZOS)

                    # Construct the output path
                    base_name = os.path.splitext(file_name)[0]
                    output_path = os.path.join(output_dir, f"{base_name}.{output_ext}")

                    save_format = "jpeg" if output_ext in ["jpg", "jpeg"] else output_ext
                    resized_img.save(output_path, format=save_format)

                    print(
                        f"Processed {file_name} -> {os.path.basename(output_path)} (Size: {new_size[0]}x{new_size[1]})"
                    )

            except Exception as e:
                print(f"Could not process {file_name}. Reason: {e}")

    print("\nImage processing complete.")


if __name__ == "__main__":
    load_dotenv()

    source_folder = os.getenv("SOURCE_FOLDER")
    destination_folder = os.getenv("DESTINATION_FOLDER")
    output_type = os.getenv("OUTPUT_TYPE")
    longest_edge_str = os.getenv("LONGEST_EDGE_PIXELS")

    # --- Validation ---
    if not all([source_folder, destination_folder, output_type, longest_edge_str]):
        print("Error: Please ensure your .env file contains all required variables:")
        print("SOURCE_FOLDER, DESTINATION_FOLDER, OUTPUT_TYPE, and LONGEST_EDGE_PIXELS.")
    else:
        try:
            longest_edge_pixels = int(longest_edge_str)
            process_images_in_directory(source_folder, destination_folder, output_type, longest_edge_pixels)
        except (ValueError, TypeError):
            print(f"Error: LONGEST_EDGE_PIXELS in your .env file must be a valid number. Found: '{longest_edge_str}'")
