"""File copier with directory structure preservation."""

import shutil
from pathlib import Path
from typing import Dict, List
from src.registry.models import RegistryItem


class CopyError(Exception):
    """Exception raised when file copy operation fails."""
    pass


class FileCopier:
    """Copier for registry item files."""

    @staticmethod
    def copy_item_files(
        item: RegistryItem,
        registry_path: Path,
        dest_root: Path,
        dry_run: bool = False
    ) -> List[str]:
        """Copy files for a single registry item.

        Args:
            item: RegistryItem to copy files from
            registry_path: Root path to registry
            dest_root: Root destination directory
            dry_run: If True, don't actually copy files

        Returns:
            List of destination file paths that were (or would be) created

        Raises:
            CopyError: If copy operation fails
        """
        from src.validation.integrity import validate_safe_path, PathTraversalError

        copied_files = []

        # Determine item directory in registry
        # Structure: registry/{namespace}/{item-name}/
        item_dir = registry_path / item.type.value + "s" / item.name

        if not dry_run and not item_dir.exists():
            raise CopyError(
                f"Item directory not found: {item_dir}"
            )

        # Copy each file according to file mappings
        for dest_path, source_path in item.files.items():
            # Validate paths for security
            try:
                validate_safe_path(dest_path, allow_absolute=False)
                validate_safe_path(source_path, allow_absolute=False)
            except PathTraversalError as e:
                raise CopyError(f"Security: {e}") from e
            full_source = item_dir / source_path
            full_dest = dest_root / dest_path

            if not dry_run:
                if not full_source.exists():
                    raise CopyError(
                        f"Source file not found: {full_source}"
                    )

                # Create parent directories
                full_dest.parent.mkdir(parents=True, exist_ok=True)

                # Copy file preserving metadata
                try:
                    shutil.copy2(full_source, full_dest)
                except Exception as e:
                    raise CopyError(
                        f"Failed to copy {source_path} to {dest_path}: {e}"
                    ) from e

            copied_files.append(str(dest_path))

        return copied_files

    @staticmethod
    def copy_all_items(
        items: List[RegistryItem],
        registry_path: Path,
        dest_root: Path,
        dry_run: bool = False
    ) -> Dict[str, List[str]]:
        """Copy files for multiple registry items.

        Args:
            items: List of RegistryItem instances to copy
            registry_path: Root path to registry
            dest_root: Root destination directory
            dry_run: If True, don't actually copy files

        Returns:
            Dictionary mapping item names to list of copied file paths

        Raises:
            CopyError: If any copy operation fails
        """
        results = {}

        for item in items:
            try:
                copied = FileCopier.copy_item_files(
                    item, registry_path, dest_root, dry_run
                )
                results[item.name] = copied
            except CopyError as e:
                raise CopyError(
                    f"Failed to copy files for '{item.name}': {e}"
                ) from e

        return results

    @staticmethod
    def get_total_size(
        items: List[RegistryItem],
        registry_path: Path
    ) -> int:
        """Calculate total size of files to be copied.

        Args:
            items: List of RegistryItem instances
            registry_path: Root path to registry

        Returns:
            Total size in bytes
        """
        total_size = 0

        for item in items:
            item_dir = registry_path / item.type.value + "s" / item.name

            for dest_path, source_path in item.files.items():
                full_source = item_dir / source_path
                if full_source.exists() and full_source.is_file():
                    total_size += full_source.stat().st_size

        return total_size

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format size in bytes to human-readable string.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string (e.g., "1.5 KB", "2.3 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    @staticmethod
    def preview_copy_operations(
        items: List[RegistryItem],
        registry_path: Path,
        dest_root: Path
    ) -> List[Dict[str, str]]:
        """Preview copy operations without executing them.

        Args:
            items: List of RegistryItem instances
            registry_path: Root path to registry
            dest_root: Root destination directory

        Returns:
            List of dictionaries with 'item', 'source', 'dest', 'size' keys
        """
        operations = []

        for item in items:
            item_dir = registry_path / item.type.value + "s" / item.name

            for dest_path, source_path in item.files.items():
                full_source = item_dir / source_path
                full_dest = dest_root / dest_path

                size = 0
                if full_source.exists() and full_source.is_file():
                    size = full_source.stat().st_size

                operations.append({
                    'item': item.name,
                    'source': str(source_path),
                    'dest': str(dest_path),
                    'size': FileCopier.format_size(size),
                    'size_bytes': size
                })

        return operations

    @staticmethod
    def check_existing_files(
        items: List[RegistryItem],
        dest_root: Path
    ) -> List[str]:
        """Check which destination files already exist.

        Args:
            items: List of RegistryItem instances
            dest_root: Root destination directory

        Returns:
            List of existing file paths
        """
        existing = []

        for item in items:
            for dest_path in item.files.keys():
                full_dest = dest_root / dest_path
                if full_dest.exists():
                    existing.append(str(dest_path))

        return existing

    @staticmethod
    def remove_copied_files(
        items: List[RegistryItem],
        dest_root: Path
    ):
        """Remove files that were copied (for rollback).

        Args:
            items: List of RegistryItem instances
            dest_root: Root destination directory
        """
        for item in items:
            for dest_path in item.files.keys():
                full_dest = dest_root / dest_path
                if full_dest.exists() and full_dest.is_file():
                    try:
                        full_dest.unlink()
                    except Exception:
                        pass  # Ignore errors during cleanup

        # Remove empty directories
        FileCopier._remove_empty_dirs(dest_root)

    @staticmethod
    def _remove_empty_dirs(path: Path):
        """Recursively remove empty directories.

        Args:
            path: Directory path to clean
        """
        try:
            for item in path.iterdir():
                if item.is_dir():
                    FileCopier._remove_empty_dirs(item)
                    if not any(item.iterdir()):
                        item.rmdir()
        except Exception:
            pass  # Ignore errors during cleanup
