"""Interactive multi-select UI for registry item selection."""

from typing import List, Optional
import questionary
from questionary import Choice

from src.registry.models import RegistryItem


class SelectionCancelled(Exception):
    """Exception raised when user cancels selection."""
    pass


class InteractivePrompter:
    """Interactive UI for selecting registry items."""

    @staticmethod
    def select_items(
        items: List[RegistryItem],
        pre_selected: Optional[List[str]] = None
    ) -> List[RegistryItem]:
        """Display interactive multi-select UI for item selection.

        Args:
            items: List of available items
            pre_selected: List of item names to pre-select

        Returns:
            List of selected RegistryItem instances

        Raises:
            SelectionCancelled: If user cancels selection
        """
        if not items:
            print("No items available for selection")
            return []

        # Create choices with formatted display names
        choices = []
        for item in items:
            # Format: [type] name v1.0.0 - description
            display = f"[{item.type.value}] {item.name} v{item.version} - {item.description}"

            # Check if pre-selected
            checked = False
            if pre_selected and item.name in pre_selected:
                checked = True

            choices.append(Choice(
                title=display,
                value=item.name,
                checked=checked
            ))

        # Display multi-select UI with graceful degradation
        try:
            selected_names = questionary.checkbox(
                message="Select items to install (use space to select, enter to confirm):",
                choices=choices,
                style=questionary.Style([
                    ('checkbox', 'fg:cyan'),
                    ('highlighted', 'fg:cyan bold'),
                    ('selected', 'fg:green'),
                ])
            ).ask()

            # Handle cancellation (Ctrl+C or empty selection)
            if selected_names is None:
                raise SelectionCancelled("Selection cancelled by user")

            if not selected_names:
                print("No items selected")
                return []

            # Map selected names back to items
            selected_items = [
                item for item in items
                if item.name in selected_names
            ]

            return selected_items

        except KeyboardInterrupt:
            raise SelectionCancelled("Selection cancelled by user")
        except Exception as e:
            # Graceful degradation: fall back to simple input prompts
            print(f"\n⚠️  Interactive UI failed ({e}), falling back to simple prompts")
            return InteractivePrompter._fallback_selection(items, pre_selected)

    @staticmethod
    def _fallback_selection(
        items: List[RegistryItem],
        pre_selected: Optional[List[str]] = None
    ) -> List[RegistryItem]:
        """Fallback selection using simple input() prompts.

        Args:
            items: List of available items
            pre_selected: List of item names to pre-select

        Returns:
            List of selected RegistryItem instances
        """
        print("\nAvailable items:")
        for i, item in enumerate(items, 1):
            marker = "[*]" if pre_selected and item.name in pre_selected else "[ ]"
            print(f"{i:3d}. {marker} {item.name} v{item.version} - {item.description}")

        print("\nEnter item numbers separated by commas (e.g., 1,3,5) or 'all' for all items:")
        try:
            user_input = input("> ").strip().lower()

            if not user_input:
                print("No items selected")
                return []

            if user_input == "all":
                return items

            # Parse comma-separated numbers
            selected_items = []
            for num_str in user_input.split(','):
                try:
                    num = int(num_str.strip())
                    if 1 <= num <= len(items):
                        selected_items.append(items[num - 1])
                    else:
                        print(f"⚠️  Skipping invalid number: {num}")
                except ValueError:
                    print(f"⚠️  Skipping invalid input: {num_str}")

            return selected_items

        except KeyboardInterrupt:
            raise SelectionCancelled("Selection cancelled by user")

    @staticmethod
    def confirm(message: str, default: bool = False) -> bool:
        """Display confirmation prompt.

        Args:
            message: Confirmation message
            default: Default value if user presses enter

        Returns:
            True if confirmed, False otherwise
        """
        try:
            return questionary.confirm(
                message=message,
                default=default
            ).ask()
        except KeyboardInterrupt:
            return False

    @staticmethod
    def select_from_list(
        message: str,
        choices: List[str],
        default: Optional[str] = None
    ) -> Optional[str]:
        """Display single-select list.

        Args:
            message: Prompt message
            choices: List of choice strings
            default: Default choice

        Returns:
            Selected choice or None if cancelled
        """
        try:
            return questionary.select(
                message=message,
                choices=choices,
                default=default
            ).ask()
        except KeyboardInterrupt:
            return None

    @staticmethod
    def input_text(
        message: str,
        default: str = "",
        validate: Optional[callable] = None
    ) -> Optional[str]:
        """Display text input prompt.

        Args:
            message: Prompt message
            default: Default value
            validate: Optional validation function

        Returns:
            Input text or None if cancelled
        """
        try:
            return questionary.text(
                message=message,
                default=default,
                validate=validate
            ).ask()
        except KeyboardInterrupt:
            return None

    @staticmethod
    def display_summary(
        selected_items: List[RegistryItem],
        resolved_dependencies: List[RegistryItem]
    ):
        """Display summary of selected items and dependencies.

        Args:
            selected_items: Items explicitly selected by user
            resolved_dependencies: Items included as dependencies
        """
        print("\n" + "=" * 60)
        print("SELECTION SUMMARY")
        print("=" * 60)

        print(f"\n✓ Selected Items ({len(selected_items)}):")
        for item in selected_items:
            print(f"  - {item.name} v{item.version} ({item.type.value})")

        if resolved_dependencies:
            print(f"\n+ Dependencies ({len(resolved_dependencies)}):")
            for item in resolved_dependencies:
                print(f"  - {item.name} v{item.version} ({item.type.value})")

        total = len(selected_items) + len(resolved_dependencies)
        print(f"\nTotal items to install: {total}")
        print("=" * 60 + "\n")

    @staticmethod
    def display_conflicts(conflicts: List):
        """Display conflict warnings.

        Args:
            conflicts: List of Conflict instances
        """
        print("\n" + "!" * 60)
        print("CONFLICTS DETECTED")
        print("!" * 60)

        for i, conflict in enumerate(conflicts, 1):
            print(f"\n{i}. {conflict}")

        print(f"\nTotal conflicts: {len(conflicts)}")
        print("\nOptions:")
        print("  - Use --force to allow overwrites (last selected value wins)")
        print("  - Deselect conflicting items and try again")
        print("!" * 60 + "\n")

    @staticmethod
    def display_env_vars(
        required_vars: List,
        optional_vars: List
    ):
        """Display required and optional environment variables.

        Args:
            required_vars: List of required EnvVar instances
            optional_vars: List of optional EnvVar instances
        """
        if not required_vars and not optional_vars:
            return

        print("\n" + "-" * 60)
        print("ENVIRONMENT VARIABLES")
        print("-" * 60)

        if required_vars:
            print(f"\n✓ Required ({len(required_vars)}):")
            for env in required_vars:
                print(f"  - {env.name}: {env.description}")

        if optional_vars:
            print(f"\n○ Optional ({len(optional_vars)}):")
            for env in optional_vars:
                default_text = f" (default: {env.default})" if env.default else ""
                print(f"  - {env.name}: {env.description}{default_text}")

        print("\nThese will be documented in .env.example")
        print("-" * 60 + "\n")
