"""Data models and operations for lock files."""

from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime
from enum import Enum
import re
import hashlib


class LockItemType(Enum):
    """Types of locked items."""
    SUBAGENT = "subagent"
    COMMAND = "command"
    MCP = "mcp"


@dataclass
class LockItem:
    """Individual item entry in lock file.

    Attributes:
        type: Item type (subagent, command, or mcp)
        version: Semver version installed
        files: Map of destination path to SHA-256 hash
    """
    type: LockItemType
    version: str
    files: Dict[str, str]

    def __post_init__(self):
        """Validate lock item constraints."""
        # Validate version is semver-like
        if not re.match(r'^\d+\.\d+\.\d+', self.version):
            raise ValueError(
                f"Invalid version '{self.version}'. "
                "Must be valid semver (e.g., '2.1.0')"
            )

        # Validate hash format
        for path, hash_value in self.files.items():
            if not re.match(r'^sha256:[0-9a-f]{64}$', hash_value):
                raise ValueError(
                    f"Invalid hash format for '{path}': {hash_value}. "
                    "Must be 'sha256:' prefix + 64 hex chars"
                )

        # Convert string type to enum if needed
        if isinstance(self.type, str):
            self.type = LockItemType(self.type)

    def verify_file_hash(self, file_path: str, expected_hash: str) -> bool:
        """Compute the file's SHA-256 and compare to expected 'sha256:<hex>'."""
        try:
            h = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
            actual = f"sha256:{h.hexdigest()}"
            # Normalize expected to lowercase for robustness
            return actual == expected_hash.lower()
        except FileNotFoundError:
            return False


@dataclass
class LockFile:
    """Lock file recording exact versions and hashes of installed items.

    Attributes:
        version: Lock file format version (e.g., "1.0")
        generated: ISO 8601 timestamp
        registry_path: Absolute path to registry used
        items: Map of item name to lock entry
    """
    version: str
    generated: str
    registry_path: str
    items: Dict[str, LockItem] = field(default_factory=dict)

    def __post_init__(self):
        """Validate lock file constraints."""
        # Validate version is semver-like
        if not re.match(r'^\d+\.\d+', self.version):
            raise ValueError(
                f"Invalid lock file version '{self.version}'. "
                "Must match semantic version (e.g., '1.0')"
            )

        # Validate ISO 8601 timestamp format
        try:
            datetime.fromisoformat(self.generated.replace('Z', '+00:00'))
        except ValueError as e:
            raise ValueError(
                f"Invalid timestamp '{self.generated}'. "
                f"Must be valid ISO 8601 format: {e}"
            )

    @staticmethod
    def create_new(registry_path: str) -> 'LockFile':
        """Create a new lock file with current timestamp."""
        return LockFile(
            version="1.0",
            generated=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            registry_path=registry_path,
            items={}
        )

    def add_item(self, name: str, lock_item: LockItem):
        """Add item to lock file."""
        self.items[name] = lock_item

    def get_item(self, name: str) -> Optional[LockItem]:
        """Get lock item by name."""
        return self.items.get(name)

    def has_item(self, name: str) -> bool:
        """Check if lock file contains item."""
        return name in self.items

    def to_dict(self) -> Dict:
        """Convert lock file to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "generated": self.generated,
            "registry_path": self.registry_path,
            "items": {
                name: {
                    "type": item.type.value,
                    "version": item.version,
                    "files": item.files
                }
                for name, item in self.items.items()
            }
        }

    @staticmethod
    def from_dict(data: Dict) -> 'LockFile':
        """Create lock file from dictionary (JSON deserialization)."""
        items = {
            name: LockItem(
                type=LockItemType(item_data["type"]),
                version=item_data["version"],
                files=item_data["files"]
            )
            for name, item_data in data.get("items", {}).items()
        }

        return LockFile(
            version=data["version"],
            generated=data["generated"],
            registry_path=data["registry_path"],
            items=items
        )
