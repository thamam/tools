"""Registry item validator for metadata schema validation."""

import re
from typing import List, Tuple
from src.registry.models import RegistryItem, EnvVar, ItemType


class ValidationError(Exception):
    """Exception raised when validation fails."""
    pass


class RegistryValidator:
    """Validator for registry item metadata."""

    @staticmethod
    def validate_item(item: RegistryItem) -> Tuple[bool, List[str]]:
        """Validate a registry item.

        Args:
            item: RegistryItem to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Validate name format
        if not re.match(r'^[a-z0-9-]+$', item.name):
            errors.append(
                f"Invalid name '{item.name}': must match ^[a-z0-9-]+$"
            )

        # Validate version format
        if not re.match(r'^\d+\.\d+\.\d+', item.version):
            errors.append(
                f"Invalid version '{item.version}': must be semver (e.g., '2.1.0')"
            )

        # Validate type
        if not isinstance(item.type, ItemType):
            errors.append(
                f"Invalid type: must be one of {[t.value for t in ItemType]}"
            )

        # Validate tags
        if not item.tags:
            errors.append("At least one tag is required")

        # Validate description
        if not item.description or not item.description.strip():
            errors.append("Description is required and cannot be empty")

        # Validate files
        if not item.files:
            errors.append("At least one file mapping is required")
        else:
            for dest, src in item.files.items():
                if not dest or not src:
                    errors.append(
                        f"Invalid file mapping: destination and source cannot be empty"
                    )

        # Validate MCP fragment requirement
        if item.type == ItemType.MCP:
            if item.mcp_fragment is None:
                errors.append(
                    f"Item type is 'mcp' but mcp_fragment is missing"
                )
            else:
                # Validate MCP fragment structure
                mcp_errors = RegistryValidator._validate_mcp_fragment(
                    item.mcp_fragment
                )
                errors.extend(mcp_errors)
        elif item.mcp_fragment is not None:
            errors.append(
                f"Item type is not 'mcp' but mcp_fragment is present"
            )

        # Validate environment variables
        for env in item.env_vars:
            env_errors = RegistryValidator._validate_env_var(env)
            errors.extend(env_errors)

        # Validate dependencies format
        for dep in item.dependencies:
            if not re.match(r'^[a-z0-9-]+$', dep):
                errors.append(
                    f"Invalid dependency name '{dep}': must match ^[a-z0-9-]+$"
                )

        return (len(errors) == 0, errors)

    @staticmethod
    def _validate_env_var(env: EnvVar) -> List[str]:
        """Validate an environment variable.

        Args:
            env: EnvVar to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Validate name format
        if not re.match(r'^[A-Z_][A-Z0-9_]*$', env.name):
            errors.append(
                f"Invalid env var name '{env.name}': must match ^[A-Z_][A-Z0-9_]*$"
            )

        # Validate description
        if not env.description or not env.description.strip():
            errors.append(
                f"Env var '{env.name}' description is required and cannot be empty"
            )

        # Validate required is explicitly set
        if not isinstance(env.required, bool):
            errors.append(
                f"Env var '{env.name}' required field must be explicitly true or false"
            )

        return errors

    @staticmethod
    def _validate_mcp_fragment(fragment: dict) -> List[str]:
        """Validate MCP fragment structure.

        Args:
            fragment: MCP fragment dictionary

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check for mcpServers key
        if "mcpServers" not in fragment:
            errors.append(
                "MCP fragment must contain 'mcpServers' key"
            )
            return errors

        mcp_servers = fragment["mcpServers"]
        if not isinstance(mcp_servers, dict):
            errors.append(
                "MCP fragment 'mcpServers' must be a dictionary"
            )
            return errors

        # Validate each server configuration
        for server_name, server_config in mcp_servers.items():
            if not isinstance(server_config, dict):
                errors.append(
                    f"MCP server '{server_name}' configuration must be a dictionary"
                )
                continue

            # Check for required 'command' field
            if "command" not in server_config:
                errors.append(
                    f"MCP server '{server_name}' missing required 'command' field"
                )

            # Validate 'args' if present
            if "args" in server_config:
                if not isinstance(server_config["args"], list):
                    errors.append(
                        f"MCP server '{server_name}' 'args' must be a list"
                    )

            # Validate 'env' if present
            if "env" in server_config:
                if not isinstance(server_config["env"], dict):
                    errors.append(
                        f"MCP server '{server_name}' 'env' must be a dictionary"
                    )

        return errors

    @staticmethod
    def validate_items(items: List[RegistryItem]) -> Tuple[bool, dict]:
        """Validate multiple registry items.

        Args:
            items: List of RegistryItem instances

        Returns:
            Tuple of (all_valid, {item_name: error_messages})
        """
        all_errors = {}
        all_valid = True

        for item in items:
            is_valid, errors = RegistryValidator.validate_item(item)
            if not is_valid:
                all_valid = False
                all_errors[item.name] = errors

        return (all_valid, all_errors)

    @staticmethod
    def check_duplicate_names(items: List[RegistryItem]) -> List[str]:
        """Check for duplicate item names.

        Args:
            items: List of RegistryItem instances

        Returns:
            List of duplicate names (empty if no duplicates)
        """
        seen = set()
        duplicates = []

        for item in items:
            if item.name in seen:
                duplicates.append(item.name)
            seen.add(item.name)

        return duplicates

    @staticmethod
    def check_missing_dependencies(items: List[RegistryItem]) -> dict:
        """Check for missing dependencies.

        Args:
            items: List of RegistryItem instances

        Returns:
            Dictionary mapping item names to list of missing dependency names
        """
        available_names = {item.name for item in items}
        missing = {}

        for item in items:
            missing_deps = [
                dep for dep in item.dependencies
                if dep not in available_names
            ]
            if missing_deps:
                missing[item.name] = missing_deps

        return missing
