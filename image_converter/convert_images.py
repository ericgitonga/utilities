import os
from PIL import Image
from dotenv import load_dotenv


def process_images_in_directory(input_directory, output_directory):
    """
    Reads all PNG files from a given directory, converts them to JPG,
    resizes them to 1800x1200 pixels, and saves them in a new directory.

    Args:
        input_directory (str): The path to the folder containing the PNG images.
        output_directory (str): The path to the folder where the processed JPG images will be saved.
    """
    # Check if the source directory exists
    if not os.path.isdir(input_directory):
        print(f"Error: The source directory '{input_directory}' does not exist.")
        return

    # Create the output directory if it does not already exist.
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        print(f"Created directory: {output_directory}")

    # Get a list of all files in the input directory.
    files = os.listdir(input_directory)

    for file_name in files:
        # Check if the file is a PNG image.
        if file_name.lower().endswith(".png"):
            input_path = os.path.join(input_directory, file_name)

            # Open the image file.
            try:
                with Image.open(input_path) as img:
                    # Convert the image to RGB mode to ensure JPG compatibility.
                    rgb_img = img.convert("RGB")

                    # Resize the image to the desired dimensions.
                    resized_img = rgb_img.resize((1800, 1200))

                    # Create the new file name with a .jpg extension.
                    base_name = os.path.splitext(file_name)[0]
                    output_path = os.path.join(output_directory, f"{base_name}.jpg")

                    # Save the resized image as a JPG file.
                    resized_img.save(output_path, "jpeg")
                    print(f"Successfully processed {file_name}")

            except Exception as e:
                print(f"Could not process {file_name}. Reason: {e}")

    print("\nImage processing complete.")


if __name__ == "__main__":
    # Load environment variables from the .env file in the same directory
    load_dotenv()

    # Retrieve the folder paths from the environment variables
    source_folder = os.getenv("SOURCE_FOLDER")
    destination_folder = os.getenv("DESTINATION_FOLDER")

    # Check if the variables were loaded correctly
    if not source_folder or not destination_folder:
        print("Error: Please make sure you have created a .env file in the same directory as the script")
        print("and that it contains the SOURCE_FOLDER and DESTINATION_FOLDER variables.")
    else:
        process_images_in_directory(source_folder, destination_folder)
