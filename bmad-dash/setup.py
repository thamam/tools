"""
Setup script for BMAD Dashboard
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="bmad-dash",
    version="1.0.0-rc1",
    author="BMAD Team",
    description="Executive terminal dashboard for managing BMAD projects with multi-resolution views",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thamam/tools",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Project Management",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "bmad-dash=bmad_dash_v2:main",
        ],
    },
)
