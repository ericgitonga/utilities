from setuptools import setup, find_packages

setup(
    name="imagesim",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "imagesim=imagesim.__main__:main",
        ],
    },
    install_requires=[
        "numpy",
        "pillow",
        "opencv-python",
        "scikit-learn",
        "pydantic",
    ],
    python_requires=">=3.7",
)
