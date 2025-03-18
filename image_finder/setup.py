"""
Image Similarity Finder - Setup Script

This module provides setup and installation instructions for the Image Similarity Finder.
It uses setuptools to create a Python package that can be installed with pip.
"""

from setuptools import setup, find_packages

setup(
    name="imagesim",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "imagesim=main:main",
        ],
    },
    install_requires=[
        "numpy",
        "pillow",
        "opencv-python",
        "scikit-learn",
        "pydantic",
    ],
    author="Claude AI",
    author_email="example@example.com",
    description="A tool that finds visually similar images across directories",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/example/imagesim",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
