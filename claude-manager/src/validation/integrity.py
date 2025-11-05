"""Atomic file operations with rollback capability."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Callable
from contextlib import contextmanager


class AtomicOperationError(Exception):
    """Exception raised when atomic operation fails."""
    pass


class PathTraversalError(Exception):
    """Exception raised when path traversal attempt detected."""
    pass


def validate_safe_path(path: str, allow_absolute: bool = False):
    """Validate path is safe (no path traversal).

    Args:
        path: Path string to validate
        allow_absolute: If True, allow absolute paths

    Raises:
        PathTraversalError: If path contains ".." or other unsafe patterns
    """
    from pathlib import Path as PathlibPath

    # Check for path traversal patterns
    if ".." in path:
        raise PathTraversalError(
            f"Path traversal detected: {path} contains '..'"
        )

    # Check for absolute paths if not allowed
    if not allow_absolute and PathlibPath(path).is_absolute():
        raise PathTraversalError(
            f"Absolute path not allowed: {path}"
        )

    # Additional safety checks
    normalized = PathlibPath(path).as_posix()
    if normalized.startswith("../") or "/../" in normalized:
        raise PathTraversalError(
            f"Path traversal detected in normalized path: {path}"
        )


@contextmanager
def atomic_operation(target_dir: str):
    """Context manager for atomic file operations.

    Uses temporary directory pattern:
    1. Create temp directory
    2. Perform all operations in temp dir
    3. On success: atomic rename to target
    4. On error: delete temp dir (automatic rollback)

    Args:
        target_dir: Target directory for final operation

    Yields:
        Path to temporary directory for operations

    Raises:
        AtomicOperationError: If operation fails

    Example:
        with atomic_operation('.claude') as temp_dir:
            # Write files to temp_dir
            shutil.copy('source.md', temp_dir / 'target.md')
            # On success, temp_dir atomically replaces .claude
            # On error, temp_dir is automatically deleted
    """
    target_path = Path(target_dir).resolve()
    temp_dir = None
    backup_dir = None

    try:
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix="claude-seed-"))

        # Yield temp directory for operations
        yield temp_dir

        # Success - prepare for atomic replacement
        if target_path.exists():
            # Create backup with unique name
            backup_dir = Path(tempfile.mkdtemp(prefix="claude-seed-backup-"))
            shutil.move(str(target_path), str(backup_dir / target_path.name))

        # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic move: rename is atomic on POSIX systems
        shutil.move(str(temp_dir), str(target_path))
        temp_dir = None  # Prevent cleanup

        # Remove backup on success
        if backup_dir and backup_dir.exists():
            shutil.rmtree(backup_dir)
            backup_dir = None

    except Exception as e:
        # Rollback: restore from backup if it exists
        if backup_dir and backup_dir.exists():
            if target_path.exists():
                shutil.rmtree(target_path, ignore_errors=True)
            shutil.move(str(backup_dir / target_path.name), str(target_path))

        raise AtomicOperationError(
            f"Atomic operation failed: {e}"
        ) from e

    finally:
        # Cleanup temporary directories
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        if backup_dir and backup_dir.exists():
            shutil.rmtree(backup_dir, ignore_errors=True)


class FileOperation:
    """Safe file operation utilities."""

    @staticmethod
    def copy_with_structure(
        source_dir: Path,
        dest_dir: Path,
        file_mappings: dict
    ):
        """Copy files preserving directory structure.

        Args:
            source_dir: Source root directory
            dest_dir: Destination root directory
            file_mappings: Dict mapping destination paths to source paths

        Raises:
            AtomicOperationError: If copy fails
        """
        for dest_path, source_path in file_mappings.items():
            full_source = source_dir / source_path
            full_dest = dest_dir / dest_path

            if not full_source.exists():
                raise AtomicOperationError(
                    f"Source file not found: {full_source}"
                )

            # Create parent directories
            full_dest.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            try:
                shutil.copy2(full_source, full_dest)
            except Exception as e:
                raise AtomicOperationError(
                    f"Failed to copy {source_path} to {dest_path}: {e}"
                ) from e

    @staticmethod
    def write_json(file_path: Path, data: dict, sort_keys: bool = True):
        """Write JSON file with deterministic formatting.

        Args:
            file_path: Path to JSON file
            data: Dictionary to write
            sort_keys: Sort keys for reproducibility

        Raises:
            AtomicOperationError: If write fails
        """
        import json

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, sort_keys=sort_keys)
                f.write('\n')  # Ensure newline at end
        except Exception as e:
            raise AtomicOperationError(
                f"Failed to write JSON to {file_path}: {e}"
            ) from e

    @staticmethod
    def read_json(file_path: Path) -> dict:
        """Read JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON dictionary

        Raises:
            AtomicOperationError: If read fails
        """
        import json

        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise AtomicOperationError(
                f"Failed to read JSON from {file_path}: {e}"
            ) from e

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        """Compute SHA-256 hash of file.

        Args:
            file_path: Path to file

        Returns:
            Hash string with 'sha256:' prefix

        Raises:
            AtomicOperationError: If computation fails
        """
        import hashlib

        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(chunk)
            return f"sha256:{sha256_hash.hexdigest()}"
        except Exception as e:
            raise AtomicOperationError(
                f"Failed to compute hash for {file_path}: {e}"
            ) from e

    @staticmethod
    def verify_sha256(file_path: Path, expected_hash: str) -> bool:
        """Verify SHA-256 hash of file.

        Args:
            file_path: Path to file
            expected_hash: Expected hash with 'sha256:' prefix

        Returns:
            True if hash matches, False otherwise
        """
        try:
            actual_hash = FileOperation.compute_sha256(file_path)
            return actual_hash == expected_hash
        except AtomicOperationError:
            return False

    @staticmethod
    def safe_remove(path: Path):
        """Safely remove file or directory.

        Args:
            path: Path to remove
        """
        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
        except Exception:
            pass  # Ignore errors during cleanup
