import os
from PIL import Image


def process_images(input_directory, output_directory):
    """
    Reads all PNG files from a directory, converts them to JPG,
    resizes them to 1800x1200 pixels, and saves them to a new folder.

    Args:
        input_directory (str): The path to the directory containing the PNG files.
        output_directory (str): The path to the directory where the processed JPG files will be saved.
    """
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        print(f"Created directory: {output_directory}")

    # Loop through all files in the input directory
    for filename in os.listdir(input_directory):
        if filename.endswith(".png"):
            try:
                # Construct the full file paths
                input_path = os.path.join(input_directory, filename)
                output_filename = os.path.splitext(filename)[0] + ".jpg"
                output_path = os.path.join(output_directory, output_filename)

                # Open the PNG image
                with Image.open(input_path) as img:
                    # Convert the image to RGB mode to handle transparency
                    rgb_img = img.convert("RGB")

                    # Resize the image
                    resized_img = rgb_img.resize((1800, 1200))

                    # Save the resized image as a JPG
                    resized_img.save(output_path, "jpeg")
                    print(f"Processed and saved: {output_path}")

            except Exception as e:
                print(f"Error processing {filename}: {e}")


if __name__ == "__main__":
    # --- Configuration ---
    # Set the path to the directory containing your PNG files
    input_folder = "test"
    # Set the path for the new directory to save the JPG files
    output_folder = "test/jpg"

    # --- Run the script ---
    # Create a dummy input directory and a sample PNG file for demonstration if they don't exist
    if not os.path.exists(input_folder):
        os.makedirs(input_folder)
        try:
            from PIL import Image

            dummy_image = Image.new("RGBA", (200, 200), (255, 0, 0, 255))
            dummy_image.save(os.path.join(input_folder, "sample.png"))
            print(f"Created a sample input directory and image at: {input_folder}")
        except ImportError:
            print("Pillow is not installed. Cannot create a dummy image.")

    process_images(input_folder, output_folder)
    print("\nImage processing complete.")
