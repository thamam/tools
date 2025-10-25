"""Data models for registry items and environment variables."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class ItemType(Enum):
    """Types of registry items."""
    SUBAGENT = "subagent"
    COMMAND = "command"
    MCP = "mcp"


@dataclass
class EnvVar:
    """Environment variable required by a registry item.

    Attributes:
        name: Environment variable name (e.g., "TAVILY_API_KEY")
        description: What this variable is for
        required: Whether the item fails without this variable
        default: Default value if not provided
    """
    name: str
    description: str
    required: bool
    default: Optional[str] = None

    def __post_init__(self):
        """Validate environment variable name format."""
        import re
        if not re.match(r'^[A-Z_][A-Z0-9_]*$', self.name):
            raise ValueError(
                f"Invalid env var name '{self.name}'. "
                "Must match pattern: ^[A-Z_][A-Z0-9_]*$"
            )


@dataclass
class RegistryItem:
    """Registry item (sub-agent, command, or MCP server).

    Attributes:
        name: Unique identifier within namespace (e.g., "research-agent")
        version: Semver version (e.g., "2.1.0")
        type: Item type (subagent, command, or mcp)
        category: Grouping label (e.g., "research", "code-editing")
        tags: Filterable keywords (e.g., ["research", "web-search", "prod-safe"])
        description: Human-readable summary for selection UI
        dependencies: Names of other registry items required
        env_vars: Environment variables required by this item
        files: Map of destination paths to source paths in registry
        mcp_fragment: Partial .mcp.json structure (only for type="mcp")
        compatibility_notes: Version constraints or warnings
    """
    name: str
    version: str
    type: ItemType
    tags: List[str]
    description: str
    files: Dict[str, str]
    category: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    env_vars: List[EnvVar] = field(default_factory=list)
    mcp_fragment: Optional[Dict[str, Any]] = None
    compatibility_notes: Optional[str] = None

    def __post_init__(self):
        """Validate registry item constraints."""
        import re

        # Validate name format
        if not re.match(r'^[a-z0-9-]+$', self.name):
            raise ValueError(
                f"Invalid item name '{self.name}'. "
                "Must match pattern: ^[a-z0-9-]+$"
            )

        # Validate version is semver-like
        if not re.match(r'^\d+\.\d+\.\d+', self.version):
            raise ValueError(
                f"Invalid version '{self.version}'. "
                "Must be valid semver (e.g., '2.1.0')"
            )

        # Validate files not empty
        if not self.files:
            raise ValueError(f"Item '{self.name}' must have at least one file")

        # Validate mcp_fragment required if and only if type is MCP
        if self.type == ItemType.MCP and self.mcp_fragment is None:
            raise ValueError(
                f"Item '{self.name}' has type 'mcp' but no mcp_fragment"
            )
        if self.type != ItemType.MCP and self.mcp_fragment is not None:
            raise ValueError(
                f"Item '{self.name}' has mcp_fragment but type is not 'mcp'"
            )

        # Convert string type to enum if needed
        if isinstance(self.type, str):
            self.type = ItemType(self.type)

    @property
    def full_name(self) -> str:
        """Return full name with version."""
        return f"{self.name}@{self.version}"

    def has_dependency(self, dep_name: str) -> bool:
        """Check if this item depends on another item."""
        return dep_name in self.dependencies

    def requires_env_var(self, var_name: str) -> bool:
        """Check if this item requires a specific environment variable."""
        return any(env.name == var_name for env in self.env_vars)

    def get_required_env_vars(self) -> List[EnvVar]:
        """Get list of required environment variables."""
        return [env for env in self.env_vars if env.required]

    def get_optional_env_vars(self) -> List[EnvVar]:
        """Get list of optional environment variables."""
        return [env for env in self.env_vars if not env.required]
