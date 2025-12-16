"""Setup script for Digital Humain.

Installation:
    # Basic installation
    pip install .
    
    # Development installation with test tools
    pip install -e .[dev]
    
    # With GUI dependencies
    pip install -e .[gui]
    
    # Everything (dev + gui)
    pip install -e .[all]
"""

import re
from setuptools import setup, find_packages
from pathlib import Path


def read_file(filepath: str) -> str:
    """Read file contents safely."""
    file_path = Path(__file__).parent / filepath
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return ""


def parse_requirements(filename: str) -> list:
    """Parse requirements.txt handling comments and environment markers."""
    requirements = []
    for line in read_file(filename).splitlines():
        line = line.strip()
        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue
        # Handle lines with ; (environment markers)
        if ";" in line:
            requirements.append(line)
        else:
            requirements.append(line)
    return requirements


# Read metadata
readme = read_file("README.md")
version = "0.1.0"
author = "Digital Humain Team"
author_email = "contact@digitalhumain.dev"
description = "Self-hosted Agentic AI for Enterprise Desktop Automation"
url = "https://github.com/curiousbrutus/digital-humain"

# Parse requirements
base_requirements = parse_requirements("requirements.txt")

# Extra dependencies for different use cases
extras_require = {
    "gui": [
        "tkinter",  # Usually included with Python
    ],
    "dev": [
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.1.0",
        "black>=23.0.0",
        "flake8>=6.0.0",
        "mypy>=1.0.0",
        "pre-commit>=3.0.0",
    ],
    "build": [
        "pyinstaller>=6.0.0",
        "wheel>=0.41.0",
        "build>=0.11.0",
    ],
}

# all = all optional dependencies
extras_require["all"] = (
    extras_require["gui"] +
    extras_require["dev"] +
    extras_require["build"]
)

setup(
    name="digital-humain",
    version=version,
    author=author,
    author_email=author_email,
    description=description,
    long_description=readme,
    long_description_content_type="text/markdown",
    url=url,
    project_urls={
        "Bug Tracker": f"{url}/issues",
        "Documentation": f"{url}/wiki",
        "Source Code": url,
    },
    packages=find_packages(
        exclude=[
            "tests",
            "tests.*",
            "examples",
            "docs",
            "scripts",
            "apps",
            "data",
        ]
    ),
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.9",
    install_requires=base_requirements,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "digital-humain=digital_humain.__main__:main",
        ],
        "gui_scripts": [
            # Can be used for GUI applications on Windows
        ],
    },
    package_data={
        "digital_humain": [
            "py.typed",
        ],
    },
    zip_safe=False,
    options={
        "build_scripts": {
            "executable": "/usr/bin/python3",
        },
    },
)
