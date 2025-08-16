"""
Setup script for development environment
Installs dependencies and sets up the development environment
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="wellness-at-work-eye-tracker",
    version="1.0.0",
    author="Wellness at Work",
    author_email="support@wellnessatwork.com",
    description="Desktop eye tracking application for workplace wellness",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wellnessatwork/eye-tracker",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "wellness-eye-tracker=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["assets/*", "*.ui"],
    },
)