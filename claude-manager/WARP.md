# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**claude-seed** is a CLI tool for initializing Claude Code projects by selecting and installing sub-agents, commands, and MCP servers from a private registry. It handles dependency resolution, conflict detection, file copying, and lock file generation for reproducible setups.

## Commands

### Development

```bash
# Install in development mode (from project root)
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/unit/test_file.py

# Run specific test function
pytest tests/unit/test_file.py::test_function_name
```

### Running the CLI

```bash
# Interactive initialization with item selection
claude-seed init

# Initialize with tag filters
claude-seed init --filter research --filter prod-safe

# Dry run to preview changes
claude-seed init --dry-run

# Force overwrite existing files
claude-seed init --force

# Install from lock file
claude-seed install

# Install with hash verification
claude-seed install --verify

# List available registry items
claude-seed list

# List with filters
claude-seed list --filter research --type mcp

# List as JSON
claude-seed list --json
```

### Environment Variables

- `CLAUDE_REGISTRY_PATH`: Override default registry location (default: `~/.claude-registry`)

## Architecture

### Core Workflow

The tool follows a multi-stage pipeline:

1. **Registry Loading** (`src/registry/`): Parses YAML metadata from registry directories (subagents/, commands/, mcp/)
2. **Selection** (`src/selection/`): Interactive UI for item selection with tag filtering
3. **Dependency Resolution** (`src/registry/resolver.py`): Graph-based topological sort with cycle detection
4. **Conflict Detection** (`src/operations/merger.py`): Deep JSON merge with path-based conflict tracking
5. **File Operations** (`src/operations/copier.py`): Atomic directory operations with rollback on failure
6. **Lock File Generation** (`src/operations/lockfile.py`): SHA-256 hashing for reproducibility

### Key Design Patterns

#### Registry Item Model
All items (sub-agents, commands, MCP servers) are represented by `RegistryItem` with:
- Metadata in `metadata.yaml` (name, version, dependencies, env_vars, tags, files mapping)
- Optional `mcp-fragment.json` for MCP server configurations
- Source files referenced in the `files` mapping

#### Dependency Resolution
Uses `DependencyGraph` with DFS-based topological sorting:
- Detects circular dependencies before installation
- Resolves transitive dependencies automatically
- Orders items so dependencies are installed first

#### Conflict Detection
`JSONMerger` performs recursive deep merge with tracking:
- Records which item contributed each JSON path
- Detects overlapping keys with different values
- Lists are concatenated and deduplicated
- Nested objects are merged recursively

#### Atomic Operations
`atomic_operation` context manager in `src/validation/integrity.py`:
- Creates temporary directory for staging
- Performs all file operations in temp location
- Atomically moves to final destination on success
- Automatic rollback/cleanup on any error

#### Lock File Format
`.claude.lock.json` contains:
- Registry path and timestamp
- Item versions
- SHA-256 hashes for every installed file (format: `sha256:<64_hex_chars>`)
- Enables reproducible installs and integrity verification

### Module Responsibilities

- **`src/cli/main.py`**: Click-based CLI commands (init, install, list) with exit codes
- **`src/registry/loader.py`**: YAML parsing and RegistryItem construction
- **`src/registry/resolver.py`**: Dependency graph and resolution logic
- **`src/registry/models.py`**: Data models (RegistryItem, EnvVar, ItemType enum)
- **`src/selection/prompter.py`**: Questionary-based interactive selection UI
- **`src/selection/filter.py`**: Tag and type filtering logic
- **`src/selection/models.py`**: Selection-related models (Conflict dataclass)
- **`src/operations/copier.py`**: File copying with size calculation
- **`src/operations/merger.py`**: JSON deep merge with conflict detection
- **`src/operations/generator.py`**: Generate `.env.example` and README sections
- **`src/operations/lockfile.py`**: Lock file creation and parsing
- **`src/validation/schema.py`**: JSON Schema validation for MCP configs
- **`src/validation/integrity.py`**: Atomic file operations and SHA-256 hashing

### Exit Codes

Following `contracts/cli-commands.md`:
- `0`: Success
- `1`: User error (bad input, cancelled operation)
- `2`: System error (registry not found, I/O failure)
- `3`: Conflict detected (items have overlapping configurations)
- `4`: Validation error (invalid lock file, schema mismatch)

### Registry Structure

Expected registry layout at `~/.claude-registry/` or `$CLAUDE_REGISTRY_PATH`:

```
registry/
├── subagents/
│   └── <item-name>/
│       ├── metadata.yaml
│       └── <source-files>
├── commands/
│   └── <item-name>/
│       ├── metadata.yaml
│       └── <source-files>
└── mcp/
    └── <item-name>/
        ├── metadata.yaml
        ├── mcp-fragment.json
        └── <source-files>
```

## Spec-Driven Development Context

This project uses the `.specify/` framework for structured development:

- **`.claude/commands/speckit.*.md`**: Claude-specific command templates for spec operations
- **`.specify/templates/`**: Template files for specs, plans, tasks, and checklists
- **`.specify/memory/constitution.md`**: Project principles and governance
- **`.specify/scripts/`**: Automation scripts for spec management

When working with specifications:
- Follow the constitution principles in `.specify/memory/constitution.md`
- Use speckit commands for creating/updating specs, plans, tasks, and checklists
- Maintain consistency between constitution and dependent templates

## Testing Structure

- **`tests/unit/`**: Unit tests for individual modules
- **`tests/integration/`**: Integration tests for end-to-end workflows
- **`tests/fixtures/`**: Test data and mock registry structures

## Important Constraints

### Validation Rules
- Item names: `^[a-z0-9-]+$`
- Environment variable names: `^[A-Z_][A-Z0-9_]*$`
- Versions: Semantic versioning (e.g., `2.1.0`)
- Hash format: `sha256:<64_hex_chars>`

### Error Handling
- Use custom exceptions: `RegistryLoadError`, `DependencyError`, `CircularDependencyError`, `CopyError`, `MergeError`, `GeneratorError`, `SchemaValidationError`
- Always provide context in error messages (file paths, item names)
- Use atomic operations for all file system modifications

### MCP Configuration
- All MCP items must have `mcp-fragment.json` with `mcpServers` key
- Validate merged configs against `src/validation/mcp-schema.json`
- Server names must match: `^[a-zA-Z0-9_-]+$`
