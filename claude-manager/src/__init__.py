"""Claude Code Project Seeder - CLI tool for initializing Claude Code projects.

This package provides tools for selecting and installing sub-agents, commands,
and MCP servers from a private registry with dependency resolution and conflict
detection.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

# Expose key classes for easier imports
from src.registry.models import RegistryItem, ItemType, EnvVar
from src.registry.loader import RegistryLoader
from src.registry.resolver import DependencyResolver, DependencyGraph
from src.operations.lockfile import LockFile, LockItem
from src.operations.merger import JSONMerger
from src.operations.copier import FileCopier
from src.validation.integrity import atomic_operation, FileOperation

__all__ = [
    # Version info
    "__version__",
    "__author__",

    # Registry models
    "RegistryItem",
    "ItemType",
    "EnvVar",

    # Registry operations
    "RegistryLoader",
    "DependencyResolver",
    "DependencyGraph",

    # Lock file operations
    "LockFile",
    "LockItem",

    # File operations
    "FileCopier",
    "JSONMerger",
    "FileOperation",
    "atomic_operation",
]
