#!/usr/bin/env python3
"""
Warp Chat Archiver Setup Script
Professional setup configuration for distribution
"""

from setuptools import setup, find_packages
import os
import sys

# Ensure we're running on Python 3.7+
if sys.version_info < (3, 7):
    sys.exit("Python 3.7 or higher is required")

# Read long description from README
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Read version from main module
def get_version():
    version = {}
    with open("version.py", "r", encoding="utf-8") as fh:
        exec(fh.read(), version)
    return version.get("__version__", "1.0.0")

setup(
    name="warp-chat-archiver",
    version=get_version(),
    author="Warp Chat Archiver Contributors",
    author_email="",
    description="Professional desktop application for archiving Warp Terminal chat conversations",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/runlvl/warp-chat-archiver",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Communications :: Chat",
        "Topic :: System :: Archiving :: Backup",
        "Topic :: Desktop Environment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Environment :: X11 Applications",
        "Environment :: MacOS X",
        "Environment :: Win32 (MS Windows)",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.10",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "build": [
            "pyinstaller>=4.0",
            "cx-Freeze>=6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "warp-chat-archiver=warp_archiver_gui:main",
            "warp-archiver-cli=view_conversations:main",
        ],
        "gui_scripts": [
            "warp-chat-archiver-gui=warp_archiver_gui:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.svg", "*.png", "*.desktop", "*.txt", "*.md"],
    },
    data_files=[
        ("share/applications", ["warp-chat-archiver.desktop"]),
        ("share/icons/hicolor/scalable/apps", ["assets/warp-chat-archiver.svg"]),
        ("share/pixmaps", ["assets/warp-chat-archiver.png"]),
    ],
    project_urls={
        "Bug Reports": "https://github.com/runlvl/warp-chat-archiver/issues",
        "Source": "https://github.com/runlvl/warp-chat-archiver",
        "Documentation": "https://github.com/runlvl/warp-chat-archiver/wiki",
        "Funding": "https://github.com/sponsors/runlvl",
    },
    keywords="warp terminal chat archiver backup export gui desktop",
    platforms=["any"],
    zip_safe=False,
)