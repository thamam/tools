"""Tag-based filtering for registry items."""

from typing import List, Set, Optional
from src.registry.models import RegistryItem, ItemType


class ItemFilter:
    """Filter registry items by tags, type, and search terms."""

    @staticmethod
    def by_tags(
        items: List[RegistryItem],
        tags: List[str],
        match_all: bool = False
    ) -> List[RegistryItem]:
        """Filter items by tags.

        Args:
            items: List of items to filter
            tags: Tags to filter by
            match_all: If True, item must have ALL tags (AND logic)
                      If False, item must have ANY tag (OR logic)

        Returns:
            Filtered list of items
        """
        if not tags:
            return items

        filtered = []
        for item in items:
            item_tags = set(item.tags)
            filter_tags = set(tags)

            if match_all:
                # AND logic: item must have all specified tags
                if filter_tags.issubset(item_tags):
                    filtered.append(item)
            else:
                # OR logic: item must have at least one specified tag
                if filter_tags.intersection(item_tags):
                    filtered.append(item)

        return filtered

    @staticmethod
    def by_type(
        items: List[RegistryItem],
        item_type: ItemType
    ) -> List[RegistryItem]:
        """Filter items by type.

        Args:
            items: List of items to filter
            item_type: Type to filter by

        Returns:
            Filtered list of items
        """
        return [item for item in items if item.type == item_type]

    @staticmethod
    def by_category(
        items: List[RegistryItem],
        category: str
    ) -> List[RegistryItem]:
        """Filter items by category.

        Args:
            items: List of items to filter
            category: Category to filter by

        Returns:
            Filtered list of items
        """
        return [
            item for item in items
            if item.category and item.category.lower() == category.lower()
        ]

    @staticmethod
    def by_search(
        items: List[RegistryItem],
        search_term: str
    ) -> List[RegistryItem]:
        """Filter items by search term (name or description).

        Args:
            items: List of items to filter
            search_term: Search term (case-insensitive)

        Returns:
            Filtered list of items
        """
        if not search_term:
            return items

        search_lower = search_term.lower()
        filtered = []

        for item in items:
            # Search in name
            if search_lower in item.name.lower():
                filtered.append(item)
                continue

            # Search in description
            if search_lower in item.description.lower():
                filtered.append(item)
                continue

            # Search in tags
            if any(search_lower in tag.lower() for tag in item.tags):
                filtered.append(item)
                continue

        return filtered

    @staticmethod
    def by_version(
        items: List[RegistryItem],
        min_version: Optional[str] = None,
        max_version: Optional[str] = None
    ) -> List[RegistryItem]:
        """Filter items by version range.

        Args:
            items: List of items to filter
            min_version: Minimum version (inclusive)
            max_version: Maximum version (inclusive)

        Returns:
            Filtered list of items
        """
        from packaging.version import parse, InvalidVersion

        # Parse min/max versions once before the loop
        min_ver = parse(min_version) if min_version else None
        max_ver = parse(max_version) if max_version else None

        filtered = []
        for item in items:
            try:
                item_ver = parse(item.version)
            except InvalidVersion:
                # Skip items with invalid versions
                continue

            if min_ver and item_ver < min_ver:
                continue
            if max_ver and item_ver > max_ver:
                continue
            filtered.append(item)

        return filtered

    @staticmethod
    def has_dependencies(
        items: List[RegistryItem],
        include_with_deps: bool = True
    ) -> List[RegistryItem]:
        """Filter items by dependency presence.

        Args:
            items: List of items to filter
            include_with_deps: If True, include items WITH dependencies
                             If False, include items WITHOUT dependencies

        Returns:
            Filtered list of items
        """
        if include_with_deps:
            return [item for item in items if item.dependencies]
        else:
            return [item for item in items if not item.dependencies]

    @staticmethod
    def requires_env_vars(
        items: List[RegistryItem],
        include_with_env: bool = True
    ) -> List[RegistryItem]:
        """Filter items by environment variable requirements.

        Args:
            items: List of items to filter
            include_with_env: If True, include items WITH env vars
                            If False, include items WITHOUT env vars

        Returns:
            Filtered list of items
        """
        if include_with_env:
            return [item for item in items if item.env_vars]
        else:
            return [item for item in items if not item.env_vars]

    @staticmethod
    def combine_filters(
        items: List[RegistryItem],
        tags: List[str] = None,
        item_type: ItemType = None,
        category: str = None,
        search: str = None,
        match_all_tags: bool = False
    ) -> List[RegistryItem]:
        """Apply multiple filters in sequence.

        Args:
            items: List of items to filter
            tags: Tags to filter by (OR logic by default)
            item_type: Type to filter by
            category: Category to filter by
            search: Search term for name/description
            match_all_tags: If True, require ALL tags (AND logic)

        Returns:
            Filtered list of items
        """
        result = items

        if tags:
            result = ItemFilter.by_tags(result, tags, match_all=match_all_tags)

        if item_type:
            result = ItemFilter.by_type(result, item_type)

        if category:
            result = ItemFilter.by_category(result, category)

        if search:
            result = ItemFilter.by_search(result, search)

        return result

    @staticmethod
    def get_available_tags(items: List[RegistryItem]) -> List[str]:
        """Get all unique tags from items.

        Args:
            items: List of items

        Returns:
            Sorted list of unique tags
        """
        tags: Set[str] = set()
        for item in items:
            tags.update(item.tags)
        return sorted(list(tags))

    @staticmethod
    def get_available_categories(items: List[RegistryItem]) -> List[str]:
        """Get all unique categories from items.

        Args:
            items: List of items

        Returns:
            Sorted list of unique categories (excluding None)
        """
        categories: Set[str] = set()
        for item in items:
            if item.category:
                categories.add(item.category)
        return sorted(list(categories))

    @staticmethod
    def sort_by_name(items: List[RegistryItem]) -> List[RegistryItem]:
        """Sort items by name.

        Args:
            items: List of items to sort

        Returns:
            Sorted list
        """
        return sorted(items, key=lambda x: x.name)

    @staticmethod
    def sort_by_type(items: List[RegistryItem]) -> List[RegistryItem]:
        """Sort items by type then name.

        Args:
            items: List of items to sort

        Returns:
            Sorted list
        """
        return sorted(items, key=lambda x: (x.type.value, x.name))
