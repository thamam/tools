"""JSON merger with recursive deep merge and conflict detection."""

from typing import Dict, List, Any, Tuple
from copy import deepcopy
from src.selection.models import Conflict


class MergeError(Exception):
    """Exception raised when merge operation fails."""
    pass


class JSONMerger:
    """Merger for JSON configurations with conflict detection."""

    @staticmethod
    def merge(
        fragments: List[Dict[str, Any]],
        detect_conflicts: bool = True
    ) -> Tuple[Dict[str, Any], List[Conflict]]:
        """Merge multiple JSON fragments with conflict detection.

        Args:
            fragments: List of JSON dictionaries to merge
            detect_conflicts: If True, detect and return conflicts

        Returns:
            Tuple of (merged_dict, conflicts_list)

        Note:
            When conflicts occur:
            - Last value wins (overwrites previous)
            - Conflict is recorded for reporting
        """
        if not fragments:
            return ({}, [])

        conflicts = []
        result = {}

        # Track which item contributed each value (for conflict detection)
        value_sources = {}

        # Merge fragments one by one
        for i, fragment in enumerate(fragments):
            item_name = f"item_{i}"  # Will be replaced with actual name by caller

            if detect_conflicts:
                # Deep merge with conflict tracking
                JSONMerger._merge_with_tracking(
                    result,
                    fragment,
                    value_sources,
                    item_name,
                    conflicts,
                    path=[]
                )
            else:
                # Simple deep merge without conflict tracking
                JSONMerger._deep_merge(result, fragment)

        return (result, conflicts)

    @staticmethod
    def merge_with_item_names(
        item_fragments: Dict[str, Dict[str, Any]],
        detect_conflicts: bool = True
    ) -> Tuple[Dict[str, Any], List[Conflict]]:
        """Merge fragments with item names for better conflict reporting.

        Args:
            item_fragments: Dictionary mapping item names to their fragments
            detect_conflicts: If True, detect and return conflicts

        Returns:
            Tuple of (merged_dict, conflicts_list)
        """
        if not item_fragments:
            return ({}, [])

        conflicts = []
        result = {}
        value_sources = {}

        for item_name, fragment in item_fragments.items():
            if detect_conflicts:
                JSONMerger._merge_with_tracking(
                    result,
                    fragment,
                    value_sources,
                    item_name,
                    conflicts,
                    path=[]
                )
            else:
                JSONMerger._deep_merge(result, fragment)

        return (result, conflicts)

    @staticmethod
    def _deep_merge(target: Dict, source: Dict):
        """Deep merge source into target (no conflict tracking).

        Args:
            target: Target dictionary (modified in place)
            source: Source dictionary
        """
        for key, value in source.items():
            if key in target:
                if isinstance(target[key], dict) and isinstance(value, dict):
                    # Recursively merge nested dictionaries
                    JSONMerger._deep_merge(target[key], value)
                else:
                    # Overwrite with source value
                    target[key] = deepcopy(value)
            else:
                # Add new key
                target[key] = deepcopy(value)

    @staticmethod
    def _merge_with_tracking(
        target: Dict,
        source: Dict,
        value_sources: Dict,
        item_name: str,
        conflicts: List[Conflict],
        path: List[str]
    ):
        """Deep merge with conflict tracking.

        Args:
            target: Target dictionary (modified in place)
            source: Source dictionary
            value_sources: Dictionary tracking value sources
            item_name: Name of item providing source values
            conflicts: List to append conflicts to
            path: Current path in nested structure
        """
        for key, value in source.items():
            current_path = path + [key]
            path_key = ".".join(current_path)

            if key in target:
                # Key already exists - check for conflict
                if isinstance(target[key], dict) and isinstance(value, dict):
                    # Both are dicts - recursively merge
                    JSONMerger._merge_with_tracking(
                        target[key],
                        value,
                        value_sources,
                        item_name,
                        conflicts,
                        current_path
                    )
                else:
                    # Values are not both dicts - potential conflict
                    if target[key] != value:
                        # Record conflict
                        previous_source = value_sources.get(path_key, "unknown")
                        conflict = Conflict(
                            path=current_path,
                            item_a=previous_source,
                            item_b=item_name,
                            value_a=target[key],
                            value_b=value
                        )
                        conflicts.append(conflict)

                    # Last value wins
                    target[key] = deepcopy(value)
                    value_sources[path_key] = item_name
            else:
                # New key - add it
                target[key] = deepcopy(value)
                value_sources[path_key] = item_name

    @staticmethod
    def detect_conflicts_only(
        item_fragments: Dict[str, Dict[str, Any]]
    ) -> List[Conflict]:
        """Detect conflicts without performing merge.

        Args:
            item_fragments: Dictionary mapping item names to fragments

        Returns:
            List of conflicts found
        """
        _, conflicts = JSONMerger.merge_with_item_names(
            item_fragments,
            detect_conflicts=True
        )
        return conflicts

    @staticmethod
    def merge_mcp_fragments(
        item_fragments: Dict[str, Dict[str, Any]],
        detect_conflicts: bool = True
    ) -> Tuple[Dict[str, Any], List[Conflict]]:
        """Merge MCP fragments specifically.

        Args:
            item_fragments: Dictionary mapping item names to MCP fragments
            detect_conflicts: If True, detect and return conflicts

        Returns:
            Tuple of (merged_config, conflicts_list)
        """
        # Validate all fragments have mcpServers key
        for item_name, fragment in item_fragments.items():
            if "mcpServers" not in fragment:
                raise MergeError(
                    f"MCP fragment from '{item_name}' missing 'mcpServers' key"
                )

        return JSONMerger.merge_with_item_names(
            item_fragments,
            detect_conflicts=detect_conflicts
        )

    @staticmethod
    def has_conflicts(
        item_fragments: Dict[str, Dict[str, Any]]
    ) -> bool:
        """Check if merging would produce conflicts.

        Args:
            item_fragments: Dictionary mapping item names to fragments

        Returns:
            True if conflicts detected, False otherwise
        """
        conflicts = JSONMerger.detect_conflicts_only(item_fragments)
        return len(conflicts) > 0

    @staticmethod
    def get_conflict_paths(
        conflicts: List[Conflict]
    ) -> List[str]:
        """Extract conflict paths as strings.

        Args:
            conflicts: List of Conflict instances

        Returns:
            List of conflict path strings
        """
        return [conflict.path_str for conflict in conflicts]

    @staticmethod
    def format_conflicts(
        conflicts: List[Conflict]
    ) -> str:
        """Format conflicts as human-readable string.

        Args:
            conflicts: List of Conflict instances

        Returns:
            Formatted multi-line string
        """
        if not conflicts:
            return "No conflicts detected"

        lines = [f"Found {len(conflicts)} conflict(s):\n"]

        for i, conflict in enumerate(conflicts, 1):
            lines.append(f"{i}. Path: {conflict.path_str}")
            lines.append(f"   - '{conflict.item_a}' defines: {conflict.value_a!r}")
            lines.append(f"   - '{conflict.item_b}' defines: {conflict.value_b!r}")
            lines.append("")

        return "\n".join(lines)
