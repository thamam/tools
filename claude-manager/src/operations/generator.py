"""Generators for .env.example and README sections."""

from pathlib import Path
from typing import List, Set
from datetime import datetime

from src.registry.models import RegistryItem, EnvVar


class GeneratorError(Exception):
    """Exception raised when generation fails."""
    pass


class EnvExampleGenerator:
    """Generator for .env.example files."""

    @staticmethod
    def generate(
        items: List[RegistryItem],
        output_path: Path = None
    ) -> str:
        """Generate .env.example content from registry items.

        Args:
            items: List of RegistryItem instances
            output_path: Optional path to write file to

        Returns:
            Generated .env.example content as string
        """
        # Collect all unique environment variables
        env_vars_dict = {}
        for item in items:
            for env in item.env_vars:
                if env.name not in env_vars_dict:
                    env_vars_dict[env.name] = env

        if not env_vars_dict:
            content = "# No environment variables required\n"
        else:
            # Sort by required status (required first) then by name
            sorted_vars = sorted(
                env_vars_dict.values(),
                key=lambda e: (not e.required, e.name)
            )

            lines = [
                "# Environment variables for Claude Code setup",
                f"# Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                "",
                "# Copy this file to .env and fill in your values",
                "# DO NOT commit .env to version control",
                ""
            ]

            # Add required variables
            required_vars = [v for v in sorted_vars if v.required]
            if required_vars:
                lines.append("# === REQUIRED ===")
                lines.append("")
                for env in required_vars:
                    lines.extend(EnvExampleGenerator._format_env_var(env))

            # Add optional variables
            optional_vars = [v for v in sorted_vars if not v.required]
            if optional_vars:
                if required_vars:
                    lines.append("")
                lines.append("# === OPTIONAL ===")
                lines.append("")
                for env in optional_vars:
                    lines.extend(EnvExampleGenerator._format_env_var(env))

            content = "\n".join(lines) + "\n"

        # Write to file if path provided
        if output_path:
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(content)
            except Exception as e:
                raise GeneratorError(
                    f"Failed to write .env.example: {e}"
                ) from e

        return content

    @staticmethod
    def _format_env_var(env: EnvVar) -> List[str]:
        """Format environment variable for .env.example.

        Args:
            env: EnvVar instance

        Returns:
            List of lines (including comments and value)
        """
        lines = []

        # Add description as comment
        lines.append(f"# {env.description}")

        # Add default value hint if present
        if env.default:
            lines.append(f"# Default: {env.default}")

        # Add variable with placeholder or default
        if env.default:
            lines.append(f"{env.name}={env.default}")
        else:
            lines.append(f"{env.name}=")

        lines.append("")  # Blank line between variables

        return lines


class READMEGenerator:
    """Generator for README sections."""

    @staticmethod
    def generate_setup_section(
        items: List[RegistryItem],
        output_path: Path = None
    ) -> str:
        """Generate setup instructions section for README.

        Args:
            items: List of RegistryItem instances
            output_path: Optional path to write section to

        Returns:
            Generated README section content
        """
        lines = [
            "# Claude Code Setup",
            "",
            "This repository uses Claude Code with the following components:",
            ""
        ]

        # Group items by type
        subagents = [i for i in items if i.type.value == "subagent"]
        commands = [i for i in items if i.type.value == "command"]
        mcp_servers = [i for i in items if i.type.value == "mcp"]

        # List sub-agents
        if subagents:
            lines.append("## Sub-Agents")
            lines.append("")
            for item in sorted(subagents, key=lambda x: x.name):
                lines.append(f"- **{item.name}** (v{item.version}): {item.description}")
            lines.append("")

        # List commands
        if commands:
            lines.append("## Commands")
            lines.append("")
            for item in sorted(commands, key=lambda x: x.name):
                lines.append(f"- **/{item.name}** (v{item.version}): {item.description}")
            lines.append("")

        # List MCP servers
        if mcp_servers:
            lines.append("## MCP Servers")
            lines.append("")
            for item in sorted(mcp_servers, key=lambda x: x.name):
                lines.append(f"- **{item.name}** (v{item.version}): {item.description}")
            lines.append("")

        # Add environment variables section if needed
        env_vars = READMEGenerator._collect_env_vars(items)
        if env_vars:
            lines.append("## Environment Variables")
            lines.append("")
            lines.append("Copy `.env.example` to `.env` and configure:")
            lines.append("")

            required = [e for e in env_vars if e.required]
            optional = [e for e in env_vars if not e.required]

            if required:
                lines.append("### Required")
                lines.append("")
                for env in sorted(required, key=lambda x: x.name):
                    lines.append(f"- `{env.name}`: {env.description}")
                lines.append("")

            if optional:
                lines.append("### Optional")
                lines.append("")
                for env in sorted(optional, key=lambda x: x.name):
                    lines.append(f"- `{env.name}`: {env.description}")
                    if env.default:
                        lines.append(f"  - Default: `{env.default}`")
                lines.append("")

        # Add setup instructions
        lines.extend([
            "## Setup Instructions",
            "",
            "1. Ensure you have Claude Code installed",
            "2. Copy `.env.example` to `.env` and fill in required values",
            "3. The configuration in `.claude/` and `.mcp.json` is ready to use",
            "4. Start using Claude Code with the configured components",
            ""
        ])

        content = "\n".join(lines)

        # Write to file if path provided
        if output_path:
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(content)
            except Exception as e:
                raise GeneratorError(
                    f"Failed to write README section: {e}"
                ) from e

        return content

    @staticmethod
    def _collect_env_vars(items: List[RegistryItem]) -> List[EnvVar]:
        """Collect unique environment variables from items.

        Args:
            items: List of RegistryItem instances

        Returns:
            List of unique EnvVar instances
        """
        env_vars_dict = {}
        for item in items:
            for env in item.env_vars:
                if env.name not in env_vars_dict:
                    env_vars_dict[env.name] = env
        return list(env_vars_dict.values())

    @staticmethod
    def generate_compatibility_notes(
        items: List[RegistryItem]
    ) -> str:
        """Generate compatibility notes section.

        Args:
            items: List of RegistryItem instances

        Returns:
            Compatibility notes content
        """
        items_with_notes = [
            item for item in items
            if item.compatibility_notes
        ]

        if not items_with_notes:
            return ""

        lines = [
            "## Compatibility Notes",
            ""
        ]

        for item in sorted(items_with_notes, key=lambda x: x.name):
            lines.append(f"### {item.name} (v{item.version})")
            lines.append("")
            lines.append(item.compatibility_notes)
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def generate_quick_reference(
        items: List[RegistryItem]
    ) -> str:
        """Generate quick reference section.

        Args:
            items: List of RegistryItem instances

        Returns:
            Quick reference content
        """
        lines = [
            "## Quick Reference",
            ""
        ]

        # Commands reference
        commands = [i for i in items if i.type.value == "command"]
        if commands:
            lines.append("### Available Commands")
            lines.append("")
            for cmd in sorted(commands, key=lambda x: x.name):
                lines.append(f"- `/{cmd.name}` - {cmd.description}")
            lines.append("")

        # Sub-agents reference
        subagents = [i for i in items if i.type.value == "subagent"]
        if subagents:
            lines.append("### Sub-Agents")
            lines.append("")
            for agent in sorted(subagents, key=lambda x: x.name):
                lines.append(f"- `@{agent.name}` - {agent.description}")
            lines.append("")

        # MCP servers reference
        mcp_servers = [i for i in items if i.type.value == "mcp"]
        if mcp_servers:
            lines.append("### MCP Servers")
            lines.append("")
            for server in sorted(mcp_servers, key=lambda x: x.name):
                lines.append(f"- `{server.name}` - {server.description}")
            lines.append("")

        return "\n".join(lines)
