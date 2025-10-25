"""Dependency graph builder and resolver with cycle detection."""

from typing import List, Dict, Set, Optional
from collections import defaultdict

from src.registry.models import RegistryItem


class DependencyError(Exception):
    """Exception raised when dependency resolution fails."""
    pass


class CircularDependencyError(DependencyError):
    """Exception raised when circular dependencies are detected."""
    pass


class MissingDependencyError(DependencyError):
    """Exception raised when required dependencies are missing."""
    pass


class DependencyGraph:
    """Dependency graph for resolving item dependencies.

    Uses adjacency list representation and DFS-based topological sort
    with cycle detection.
    """

    def __init__(self):
        """Initialize empty dependency graph."""
        self.nodes: Dict[str, RegistryItem] = {}
        self.edges: Dict[str, List[str]] = defaultdict(list)
        self.visited: Set[str] = set()
        self.visiting: Set[str] = set()
        self._sorted: List[RegistryItem] = []

    def add_item(self, item: RegistryItem):
        """Add item to dependency graph.

        Args:
            item: RegistryItem to add
        """
        self.nodes[item.name] = item
        # Initialize edges list even if no dependencies
        if item.name not in self.edges:
            self.edges[item.name] = []
        # Add dependency edges
        for dep_name in item.dependencies:
            self.edges[item.name].append(dep_name)

    def add_items(self, items: List[RegistryItem]):
        """Add multiple items to dependency graph.

        Args:
            items: List of RegistryItem instances
        """
        for item in items:
            self.add_item(item)

    def has_cycle(self) -> bool:
        """Check if graph contains cycles.

        Returns:
            True if cycle detected, False otherwise
        """
        try:
            self.resolve()
            return False
        except CircularDependencyError:
            return True

    def find_cycle(self) -> Optional[List[str]]:
        """Find and return a cycle if one exists.

        Returns:
            List of item names forming a cycle, or None if no cycle
        """
        self.visited = set()
        self.visiting = set()

        for node in self.nodes:
            if node not in self.visited:
                try:
                    cycle = self._dfs_cycle_detection(node, [])
                    if cycle:
                        return cycle
                except CircularDependencyError as e:
                    # Extract cycle from error message
                    return str(e).split(": ")[1].split(" -> ")

        return None

    def _dfs_cycle_detection(
        self,
        node: str,
        path: List[str]
    ) -> Optional[List[str]]:
        """DFS-based cycle detection.

        Args:
            node: Current node name
            path: Current path from root

        Returns:
            Cycle path if found, None otherwise

        Raises:
            CircularDependencyError: If cycle detected
        """
        if node in self.visiting:
            # Found a cycle - construct cycle path
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            raise CircularDependencyError(
                f"Circular dependency detected: {' -> '.join(cycle)}"
            )

        if node in self.visited:
            return None

        self.visiting.add(node)
        path.append(node)

        # Visit dependencies
        for dep in self.edges.get(node, []):
            if dep not in self.nodes:
                continue  # Skip missing dependencies for now
            self._dfs_cycle_detection(dep, path)

        path.pop()
        self.visiting.remove(node)
        self.visited.add(node)

        return None

    def resolve(self) -> List[RegistryItem]:
        """Resolve dependencies using topological sort.

        Returns:
            List of items in dependency order (dependencies first)

        Raises:
            CircularDependencyError: If cycle detected
            MissingDependencyError: If required dependency not in graph
        """
        # Check for missing dependencies
        missing = self._check_missing_dependencies()
        if missing:
            error_msg = "\n".join(
                f"  - {item} requires missing dependency: {dep}"
                for item, deps in missing.items()
                for dep in deps
            )
            raise MissingDependencyError(
                f"Missing dependencies:\n{error_msg}"
            )

        # Reset state for topological sort
        self.visited = set()
        self.visiting = set()
        self._sorted = []

        # Run DFS on all nodes
        for node in self.nodes:
            if node not in self.visited:
                self._dfs_topological_sort(node)

        # Reverse to get correct dependency order (dependencies first)
        self._sorted.reverse()

        return self._sorted

    def _dfs_topological_sort(self, node: str):
        """DFS-based topological sort with cycle detection.

        Args:
            node: Current node name

        Raises:
            CircularDependencyError: If cycle detected
        """
        if node in self.visiting:
            # Build cycle path
            raise CircularDependencyError(
                f"Circular dependency detected involving: {node}"
            )

        if node in self.visited:
            return

        self.visiting.add(node)

        # Visit dependencies first
        for dep in self.edges.get(node, []):
            if dep in self.nodes:
                self._dfs_topological_sort(dep)

        self.visiting.remove(node)
        self.visited.add(node)

        # Add to sorted list after all dependencies processed
        self._sorted.append(self.nodes[node])

    def _check_missing_dependencies(self) -> Dict[str, List[str]]:
        """Check for missing dependencies.

        Returns:
            Dictionary mapping item names to missing dependency names
        """
        missing = {}
        for node_name, item in self.nodes.items():
            missing_deps = [
                dep for dep in item.dependencies
                if dep not in self.nodes
            ]
            if missing_deps:
                missing[node_name] = missing_deps
        return missing

    def get_transitive_dependencies(self, item_name: str) -> List[RegistryItem]:
        """Get all transitive dependencies of an item.

        Args:
            item_name: Name of item to get dependencies for

        Returns:
            List of all dependencies (direct and transitive) in dependency order

        Raises:
            KeyError: If item not in graph
            CircularDependencyError: If cycle detected
        """
        if item_name not in self.nodes:
            raise KeyError(f"Item '{item_name}' not in dependency graph")

        # Build subgraph with only this item and its dependencies
        subgraph = DependencyGraph()
        self._collect_dependencies(item_name, subgraph)

        # Resolve subgraph
        try:
            resolved = subgraph.resolve()
            # Remove the original item from result (only return dependencies)
            return [item for item in resolved if item.name != item_name]
        except CircularDependencyError:
            raise
        except MissingDependencyError:
            # Re-raise with more context
            raise DependencyError(
                f"Item '{item_name}' has missing dependencies"
            )

    def _collect_dependencies(
        self,
        node: str,
        subgraph: 'DependencyGraph',
        visited: Optional[Set[str]] = None
    ):
        """Recursively collect all dependencies into subgraph.

        Args:
            node: Current node name
            subgraph: DependencyGraph to populate
            visited: Set of already visited nodes
        """
        if visited is None:
            visited = set()

        if node in visited or node not in self.nodes:
            return

        visited.add(node)
        item = self.nodes[node]
        subgraph.add_item(item)

        # Recursively collect dependencies
        for dep in item.dependencies:
            self._collect_dependencies(dep, subgraph, visited)


class DependencyResolver:
    """High-level dependency resolver for registry items."""

    @staticmethod
    def resolve_dependencies(
        selected_items: List[RegistryItem],
        available_items: List[RegistryItem]
    ) -> List[RegistryItem]:
        """Resolve dependencies for selected items.

        Args:
            selected_items: Items explicitly selected by user
            available_items: All available items in registry

        Returns:
            List of all items (selected + dependencies) in dependency order

        Raises:
            CircularDependencyError: If cycle detected
            MissingDependencyError: If required dependency not available
        """
        # Build graph with all available items
        graph = DependencyGraph()
        graph.add_items(available_items)

        # Collect all items we need (selected + dependencies)
        needed_items = set()
        for item in selected_items:
            needed_items.add(item.name)
            # Get transitive dependencies
            deps = graph.get_transitive_dependencies(item.name)
            for dep in deps:
                needed_items.add(dep.name)

        # Build final graph with only needed items
        final_graph = DependencyGraph()
        for name in needed_items:
            final_graph.add_item(graph.nodes[name])

        # Resolve in dependency order
        return final_graph.resolve()

    @staticmethod
    def check_cycles(items: List[RegistryItem]) -> Optional[List[str]]:
        """Check for circular dependencies.

        Args:
            items: List of items to check

        Returns:
            Cycle path if found, None otherwise
        """
        graph = DependencyGraph()
        graph.add_items(items)
        return graph.find_cycle()

    @staticmethod
    def get_dependency_tree(
        item: RegistryItem,
        available_items: List[RegistryItem]
    ) -> Dict[str, List[str]]:
        """Get dependency tree for an item.

        Args:
            item: Item to get dependency tree for
            available_items: All available items

        Returns:
            Dictionary mapping item names to their direct dependencies
        """
        graph = DependencyGraph()
        graph.add_items(available_items)

        tree = {}
        visited = set()

        def build_tree(node_name: str):
            if node_name in visited or node_name not in graph.nodes:
                return
            visited.add(node_name)

            node_item = graph.nodes[node_name]
            tree[node_name] = node_item.dependencies

            for dep in node_item.dependencies:
                build_tree(dep)

        build_tree(item.name)
        return tree
