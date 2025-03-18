import os
import numpy as np
import argparse
from pathlib import Path
import cv2
from sklearn.metrics.pairwise import cosine_similarity


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


def find_similar_images(query_image_path, search_dirs, threshold=0.7, max_results=10):
    """
    Find images similar to the query image in the search directories.

    Args:
        query_image_path: Path to the query image
        search_dirs: List of directories to search in
        threshold: Similarity threshold (0-1)
        max_results: Maximum number of results to return

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

    # Search through all directories
    for search_dir in search_dirs:
        search_path = Path(search_dir)

        # Walk through all files recursively
        for root, _, files in os.walk(search_path):
            for file in files:
                file_path = Path(root) / file

                # Skip the query image itself
                if file_path == Path(query_image_path).absolute():
                    continue

                # Check if the file is an image
                if file_path.suffix.lower() in image_extensions:
                    # Extract features from the current image
                    current_features = extract_features(file_path)

                    if current_features is not None:
                        # Calculate similarity
                        similarity = calculate_similarity(query_features, current_features)

                        # Add to results if above threshold
                        if similarity >= threshold:
                            results.append((str(file_path), similarity))

    # Sort results by similarity (highest first)
    results.sort(key=lambda x: x[1], reverse=True)

    # Return top results
    return results[:max_results]


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Find similar images in directories")
    parser.add_argument("query_image", help="Path to the query image")
    parser.add_argument("search_dirs", nargs="+", help="Directories to search in")
    parser.add_argument("--threshold", type=float, default=0.7, help="Similarity threshold (0-1)")
    parser.add_argument("--max-results", type=int, default=10, help="Maximum number of results")

    args = parser.parse_args()

    # Find similar images
    results = find_similar_images(args.query_image, args.search_dirs, args.threshold, args.max_results)

    # Print results
    if not results:
        print("No similar images found.")
    else:
        print(f"Found {len(results)} similar images:")
        for path, score in results:
            print(f"Similarity: {score:.4f} - {path}")


if __name__ == "__main__":
    main()
