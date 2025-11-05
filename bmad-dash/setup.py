"""
Setup script for BMAD Dashboard
"""
from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="bmad-dash",
    version="0.1.0",
    author="BMAD Team",
    description="Terminal-based MVP dashboard for managing BMAD projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bmad/bmad-dash",
    py_modules=["bmad_dash"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Project Management",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "bmad-dash=bmad_dash:main",
        ],
    },
)
