"""JSON Schema validator for .mcp.json files."""

import json
from pathlib import Path
from typing import Dict, List, Tuple
import jsonschema
from jsonschema import ValidationError


class SchemaValidationError(Exception):
    """Exception raised when schema validation fails."""
    pass


class MCPSchemaValidator:
    """Validator for MCP configuration files."""

    def __init__(self):
        """Initialize validator with bundled MCP schema."""
        schema_path = Path(__file__).parent / "mcp-schema.json"

        if not schema_path.exists():
            raise SchemaValidationError(
                f"MCP schema not found at: {schema_path}"
            )

        try:
            with open(schema_path, 'r') as f:
                self.schema = json.load(f)
        except Exception as e:
            raise SchemaValidationError(
                f"Failed to load MCP schema: {e}"
            )

    def validate(self, mcp_config: Dict) -> Tuple[bool, List[str]]:
        """Validate MCP configuration against schema.

        Args:
            mcp_config: MCP configuration dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        try:
            jsonschema.validate(instance=mcp_config, schema=self.schema)
            return (True, [])
        except ValidationError as e:
            errors.append(self._format_validation_error(e))
            return (False, errors)
        except Exception as e:
            errors.append(f"Validation failed: {e}")
            return (False, errors)

    def validate_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Validate MCP configuration file.

        Args:
            file_path: Path to .mcp.json file

        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            with open(file_path, 'r') as f:
                mcp_config = json.load(f)
        except json.JSONDecodeError as e:
            return (False, [f"Invalid JSON: {e}"])
        except Exception as e:
            return (False, [f"Failed to read file: {e}"])

        return self.validate(mcp_config)

    def _format_validation_error(self, error: ValidationError) -> str:
        """Format validation error message.

        Args:
            error: ValidationError from jsonschema

        Returns:
            Formatted error message
        """
        path = " -> ".join([str(p) for p in error.path]) if error.path else "root"
        return f"Validation error at '{path}': {error.message}"

    def validate_fragment(self, fragment: Dict) -> Tuple[bool, List[str]]:
        """Validate MCP fragment (partial configuration).

        Args:
            fragment: MCP fragment dictionary (e.g., from registry item)

        Returns:
            Tuple of (is_valid, error_messages)
        """
        # MCP fragments must have mcpServers key
        if "mcpServers" not in fragment:
            return (False, ["MCP fragment must contain 'mcpServers' key"])

        # Validate as full config (fragment should be valid when merged)
        return self.validate(fragment)

    def merge_fragments(
        self,
        fragments: List[Dict]
    ) -> Tuple[Dict, List[str]]:
        """Merge multiple MCP fragments into single configuration.

        Args:
            fragments: List of MCP fragment dictionaries

        Returns:
            Tuple of (merged_config, error_messages)

        Note:
            This is a simple merge without conflict detection.
            Use the conflict detector in operations/merger.py for conflict checking.
        """
        merged = {"mcpServers": {}}
        errors = []

        for fragment in fragments:
            if "mcpServers" not in fragment:
                errors.append("Fragment missing 'mcpServers' key")
                continue

            for server_name, server_config in fragment["mcpServers"].items():
                merged["mcpServers"][server_name] = server_config

        # Validate merged result
        is_valid, validation_errors = self.validate(merged)
        if not is_valid:
            errors.extend(validation_errors)

        return (merged, errors)

    @staticmethod
    def create_empty_config() -> Dict:
        """Create empty but valid MCP configuration.

        Returns:
            Empty MCP configuration dictionary
        """
        return {"mcpServers": {}}

    @staticmethod
    def is_valid_server_name(name: str) -> bool:
        """Check if server name is valid.

        Args:
            name: Server name to validate

        Returns:
            True if valid, False otherwise
        """
        import re
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))

    @staticmethod
    def get_server_names(mcp_config: Dict) -> List[str]:
        """Extract server names from MCP configuration.

        Args:
            mcp_config: MCP configuration dictionary

        Returns:
            List of server names
        """
        if "mcpServers" not in mcp_config:
            return []

        return list(mcp_config["mcpServers"].keys())

    @staticmethod
    def has_server(mcp_config: Dict, server_name: str) -> bool:
        """Check if configuration contains server.

        Args:
            mcp_config: MCP configuration dictionary
            server_name: Server name to check

        Returns:
            True if server present, False otherwise
        """
        if "mcpServers" not in mcp_config:
            return False

        return server_name in mcp_config["mcpServers"]
