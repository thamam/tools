"""Data models for item selection and conflicts."""

from dataclasses import dataclass, field
from typing import List, Any, Optional
from src.registry.models import RegistryItem


@dataclass
class Conflict:
    """Configuration key collision during merge.

    Attributes:
        path: JSON path to conflicting key (e.g., ["mcpServers", "serena", "command"])
        item_a: Name of first item defining this key
        item_b: Name of second item defining this key
        value_a: Value from item_a
        value_b: Value from item_b
    """
    path: List[str]
    item_a: str
    item_b: str
    value_a: Any
    value_b: Any

    @property
    def path_str(self) -> str:
        """Return path as dot-separated string."""
        return ".".join(self.path)

    def __str__(self) -> str:
        """Return human-readable conflict description."""
        return (
            f"Conflict at '{self.path_str}': "
            f"'{self.item_a}' defines {self.value_a!r} but "
            f"'{self.item_b}' defines {self.value_b!r}"
        )


@dataclass
class Selection:
    """User's chosen set of registry items for installation.

    Attributes:
        items: Selected items in dependency order
        resolved_dependencies: Items automatically included
        conflicts: Detected conflicts (empty if none)

    State Transitions:
        1. Initial: User makes manual selections
        2. Resolved: Dependencies computed, conflicts detected
        3. Validated: All items exist, no circular dependencies
        4. Ready: Can proceed to installation
    """
    items: List[RegistryItem] = field(default_factory=list)
    resolved_dependencies: List[RegistryItem] = field(default_factory=list)
    conflicts: List[Conflict] = field(default_factory=list)

    @property
    def all_items(self) -> List[RegistryItem]:
        """Return all items including resolved dependencies."""
        return self.items + self.resolved_dependencies

    @property
    def has_conflicts(self) -> bool:
        """Check if there are any conflicts."""
        return len(self.conflicts) > 0

    @property
    def is_ready(self) -> bool:
        """Check if selection is ready for installation (no conflicts)."""
        return not self.has_conflicts

    def get_item_by_name(self, name: str) -> Optional[RegistryItem]:
        """Find item by name in selection."""
        for item in self.all_items:
            if item.name == name:
                return item
        return None

    def add_item(self, item: RegistryItem):
        """Add item to selection."""
        if item not in self.items:
            self.items.append(item)

    def add_resolved_dependency(self, item: RegistryItem):
        """Add resolved dependency to selection."""
        if item not in self.resolved_dependencies and item not in self.items:
            self.resolved_dependencies.append(item)

    def add_conflict(self, conflict: Conflict):
        """Add conflict to selection."""
        self.conflicts.append(conflict)

    def get_all_env_vars(self) -> List[str]:
        """Get all unique environment variable names from all items."""
        env_vars = set()
        for item in self.all_items:
            for env in item.env_vars:
                env_vars.add(env.name)
        return sorted(list(env_vars))

    def get_required_env_vars(self) -> List[str]:
        """Get all required environment variable names."""
        env_vars = set()
        for item in self.all_items:
            for env in item.get_required_env_vars():
                env_vars.add(env.name)
        return sorted(list(env_vars))
