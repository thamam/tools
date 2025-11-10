"""Registry metadata loader for parsing YAML files."""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import yaml

from src.registry.models import RegistryItem, EnvVar, ItemType


class RegistryLoadError(Exception):
    """Exception raised when registry loading fails."""
    pass


class RegistryLoader:
    """Loader for registry metadata from YAML files."""

    def __init__(self, registry_path: str):
        """Initialize loader with registry path.

        Args:
            registry_path: Absolute path to registry directory
        """
        self.registry_path = Path(registry_path)
        if not self.registry_path.exists():
            raise RegistryLoadError(
                f"Registry not found at: {registry_path}"
            )

    def load_item(self, namespace: str, item_name: str) -> RegistryItem:
        """Load a single registry item from metadata.yaml.

        Args:
            namespace: Namespace directory (e.g., "subagents", "commands", "mcp")
            item_name: Item directory name

        Returns:
            RegistryItem with loaded metadata

        Raises:
            RegistryLoadError: If metadata file not found or invalid
        """
        metadata_path = (
            self.registry_path / namespace / item_name / "metadata.yaml"
        )

        if not metadata_path.exists():
            raise RegistryLoadError(
                f"Metadata not found: {metadata_path}"
            )

        try:
            with open(metadata_path, 'r') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise RegistryLoadError(
                f"Invalid YAML in {metadata_path}: {e}"
            )
        except Exception as e:
            raise RegistryLoadError(
                f"Failed to read {metadata_path}: {e}"
            )

        return self._parse_registry_item(data, namespace, metadata_path)

    def _parse_registry_item(
        self,
        data: Dict,
        namespace: str,
        metadata_path: Path
    ) -> RegistryItem:
        """Parse metadata dictionary into RegistryItem.

        Args:
            data: Parsed YAML dictionary
            namespace: Namespace for this item
            metadata_path: Path to metadata file (for error reporting)

        Returns:
            RegistryItem instance

        Raises:
            RegistryLoadError: If required fields missing or invalid
        """
        try:
            # Parse environment variables
            env_vars = []
            for env_data in data.get("env_vars", []):
                env_vars.append(EnvVar(
                    name=env_data["name"],
                    description=env_data["description"],
                    required=env_data["required"],
                    default=env_data.get("default")
                ))

            # Load MCP fragment if present
            mcp_fragment = None
            if data.get("type") == "mcp":
                mcp_fragment_path = metadata_path.parent / "mcp-fragment.json"
                if mcp_fragment_path.exists():
                    with open(mcp_fragment_path, 'r') as f:
                        mcp_fragment = json.load(f)

            # Create RegistryItem
            return RegistryItem(
                name=data["name"],
                version=data["version"],
                type=ItemType(data["type"]),
                category=data.get("category"),
                tags=data.get("tags", []),
                description=data["description"],
                dependencies=data.get("dependencies", []),
                env_vars=env_vars,
                files=data["files"],
                mcp_fragment=mcp_fragment,
                compatibility_notes=data.get("compatibility_notes")
            )

        except KeyError as e:
            raise RegistryLoadError(
                f"Missing required field in {metadata_path}: {e}"
            )
        except ValueError as e:
            raise RegistryLoadError(
                f"Invalid value in {metadata_path}: {e}"
            )
        except Exception as e:
            raise RegistryLoadError(
                f"Failed to parse {metadata_path}: {e}"
            )

    def load_namespace(self, namespace: str) -> List[RegistryItem]:
        """Load all items from a namespace.

        Args:
            namespace: Namespace directory (e.g., "subagents", "commands", "mcp")

        Returns:
            List of RegistryItem instances

        Raises:
            RegistryLoadError: If namespace not found
        """
        namespace_path = self.registry_path / namespace
        if not namespace_path.exists():
            raise RegistryLoadError(
                f"Namespace not found: {namespace_path}"
            )

        items = []
        for item_dir in namespace_path.iterdir():
            if item_dir.is_dir():
                try:
                    item = self.load_item(namespace, item_dir.name)
                    items.append(item)
                except RegistryLoadError as e:
                    # Log warning but continue loading other items
                    print(f"Warning: Failed to load {item_dir.name}: {e}")

        return items

    def load_all(self) -> List[RegistryItem]:
        """Load all items from all namespaces.

        Returns:
            List of all RegistryItem instances

        Raises:
            RegistryLoadError: If registry structure is invalid
        """
        items = []
        namespaces = ["subagents", "commands", "mcp"]

        for namespace in namespaces:
            namespace_path = self.registry_path / namespace
            if namespace_path.exists():
                items.extend(self.load_namespace(namespace))

        return items

    def find_item(self, name: str) -> Optional[RegistryItem]:
        """Find item by name across all namespaces.

        Args:
            name: Item name to search for

        Returns:
            RegistryItem if found, None otherwise
        """
        for item in self.load_all():
            if item.name == name:
                return item
        return None

    def filter_by_tags(
        self,
        items: List[RegistryItem],
        tags: List[str]
    ) -> List[RegistryItem]:
        """Filter items by tags.

        Args:
            items: List of items to filter
            tags: Tags to filter by (OR logic)

        Returns:
            List of items matching any of the tags
        """
        if not tags:
            return items

        filtered = []
        for item in items:
            if any(tag in item.tags for tag in tags):
                filtered.append(item)

        return filtered

    def filter_by_type(
        self,
        items: List[RegistryItem],
        item_type: ItemType
    ) -> List[RegistryItem]:
        """Filter items by type.

        Args:
            items: List of items to filter
            item_type: Type to filter by

        Returns:
            List of items matching the type
        """
        return [item for item in items if item.type == item_type]
