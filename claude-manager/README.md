# Claude Code Project Seeder (`claude-seed`)

A CLI tool for initializing Claude Code projects by selecting and installing sub-agents, commands, and MCP servers from a private registry. Handles dependency resolution, conflict detection, and generates reproducible configurations.

## Features

- **Interactive Selection**: Multi-select UI for choosing registry items with filtering by tags
- **Dependency Resolution**: Automatic resolution of dependencies with circular dependency detection
- **Conflict Detection**: Identifies and reports configuration conflicts before installation
- **Reproducible Setups**: Lock file generation ensures deterministic installations
- **Atomic Operations**: All-or-nothing file operations with automatic rollback on errors
- **Security**: Path traversal protection and schema validation
- **Dry Run Mode**: Preview changes without modifying files

## Installation

### From Source

```bash
# Clone the repository
git clone <repository-url>
cd claude-manager

# Install in development mode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

### Requirements

- Python 3.8 or higher
- Dependencies: click, jsonschema, PyYAML, questionary, packaging

## Quick Start

### Initialize a New Project

```bash
# Interactive initialization with item selection
claude-seed init

# Filter items by tags
claude-seed init --filter research --filter prod-safe

# Preview changes without modifying files
claude-seed init --dry-run

# Force overwrite existing files
claude-seed init --force --output .claude
```

### Install from Lock File

```bash
# Install exact versions from lock file
claude-seed install

# Verify file integrity after installation
claude-seed install --verify

# Use custom lock file
claude-seed install --lock-file custom-lock.json
```

### List Registry Items

```bash
# List all available items
claude-seed list

# Filter by tags and type
claude-seed list --filter research --type mcp

# Output as JSON
claude-seed list --json
```

## Registry Structure

The tool expects a registry at `~/.claude-registry` or `$CLAUDE_REGISTRY_PATH` with this structure:

```
registry/
├── subagents/
│   └── research-agent/
│       ├── metadata.yaml
│       └── agent.md
├── commands/
│   └── analyze/
│       ├── metadata.yaml
│       └── analyze.md
└── mcp/
    └── web-search/
        ├── metadata.yaml
        ├── mcp-fragment.json
        └── config.json
```

### Metadata Format

Each item requires a `metadata.yaml` file:

```yaml
name: research-agent
version: 2.1.0
type: subagent
category: research
tags:
  - research
  - web-search
  - prod-safe
description: Advanced research agent with web search capabilities
dependencies:
  - web-search-mcp
env_vars:
  - name: TAVILY_API_KEY
    description: API key for Tavily search service
    required: true
    default: null
files:
  subagents/research-agent.md: agent.md
```

### MCP Fragment Format

MCP items must include `mcp-fragment.json`:

```json
{
  "mcpServers": {
    "web-search": {
      "command": "uvx",
      "args": ["mcp-server-tavily"],
      "env": {
        "TAVILY_API_KEY": "${TAVILY_API_KEY}"
      }
    }
  }
}
```

## Configuration

### Environment Variables

- `CLAUDE_REGISTRY_PATH`: Override default registry location (default: `~/.claude-registry`)

### Exit Codes

- `0`: Success
- `1`: User error (invalid input, operation cancelled)
- `2`: System error (registry not found, I/O failure)
- `3`: Conflict detected (overlapping configurations)
- `4`: Validation error (invalid lock file, schema mismatch)

## Workflow

### 1. Selection Workflow

```bash
claude-seed init
```

1. **Load Registry**: Parses items from registry directories
2. **Filter Items**: Apply tag filters if specified
3. **Interactive Selection**: Multi-select UI for choosing items
4. **Resolve Dependencies**: Automatically include required dependencies
5. **Detect Conflicts**: Check for configuration conflicts
6. **Preview**: Show summary of changes (if --dry-run)
7. **Install**: Copy files, merge configs, generate lock file

### 2. Installation Workflow

```bash
claude-seed install
```

1. **Read Lock File**: Parse `.claude.lock.json`
2. **Verify Registry**: Check registry path and item versions
3. **Load Items**: Fetch exact versions from registry
4. **Install**: Atomic installation with rollback on error
5. **Verify**: Optional hash verification of installed files

## Generated Files

### `.claude/`

Directory containing installed sub-agents and commands:

```
.claude/
├── subagents/
│   └── research-agent.md
└── commands/
    └── analyze.md
```

### `.mcp.json`

Merged MCP server configuration:

```json
{
  "mcpServers": {
    "web-search": {
      "command": "uvx",
      "args": ["mcp-server-tavily"],
      "env": {
        "TAVILY_API_KEY": "${TAVILY_API_KEY}"
      }
    }
  }
}
```

### `.claude.lock.json`

Lock file for reproducible installations:

```json
{
  "version": "1.0",
  "generated": "2025-10-25T10:30:00Z",
  "registry_path": "/home/user/.claude-registry",
  "items": {
    "research-agent": {
      "type": "subagent",
      "version": "2.1.0",
      "files": {
        "subagents/research-agent.md": "sha256:abc123..."
      }
    }
  }
}
```

### `.env.example`

Template for required environment variables:

```bash
# Required by: research-agent
# API key for Tavily search service
TAVILY_API_KEY=

# Required by: code-analysis
# GitHub personal access token
GITHUB_TOKEN=
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/unit/test_lockfile.py::test_verify_file_hash
```

### Project Structure

```
claude-manager/
├── src/
│   ├── cli/              # CLI commands
│   ├── registry/         # Registry loading and dependency resolution
│   ├── selection/        # Interactive selection and filtering
│   ├── operations/       # File operations and merging
│   └── validation/       # Schema validation and integrity checks
├── tests/
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── fixtures/        # Test data
├── .specify/            # Spec-driven development framework
├── pyproject.toml       # Package configuration
└── WARP.md             # WARP IDE guidance

```

### Architecture

- **Registry Loading**: YAML parsing and item model construction
- **Dependency Resolution**: Graph-based topological sort with cycle detection
- **Conflict Detection**: Deep JSON merge with path-based tracking
- **Atomic Operations**: Temporary directory pattern with rollback
- **Lock File**: SHA-256 hashing for reproducibility

See [WARP.md](./WARP.md) for detailed architecture documentation.

## Troubleshooting

### Registry Not Found

```bash
Error: Registry not found at ~/.claude-registry
```

**Solution**: Set `CLAUDE_REGISTRY_PATH` environment variable or create registry at default location.

### Circular Dependencies

```bash
Error: Circular dependency detected: item-a -> item-b -> item-a
```

**Solution**: Fix registry metadata to remove circular dependencies.

### Conflicts Detected

```bash
Error: Conflicts detected. Use --force to override.
```

**Solution**: Review conflicts and either:
- Deselect conflicting items
- Use `--force` to use last-selected item's value

### Version Mismatch

```bash
Warning: Version mismatch detected:
  - research-agent: lock=2.1.0, registry=2.2.0
```

**Solution**: Either:
- Update registry to match lock file versions
- Regenerate lock file with `claude-seed init`

## Contributing

1. Follow the spec-driven development process in `.specify/`
2. Write tests for new features
3. Ensure all tests pass: `pytest`
4. Update documentation as needed

## License

MIT License - See LICENSE file for details

## Support

For issues and feature requests, please use the project's issue tracker.
