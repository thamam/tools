# CLI Commands Contract: Claude Code Project Seeder

**Feature**: 001-claude-seeder
**Date**: 2025-10-25
**Purpose**: Define command-line interface contracts for the seeder tool

## Command: `claude-seed`

Main entry point for the seeder CLI.

### Synopsis

```bash
claude-seed [OPTIONS] COMMAND [ARGS]...
```

### Global Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--registry-path PATH` | path | `$CLAUDE_REGISTRY_PATH` or `~/.claude-registry` | Absolute path to registry directory |
| `--verbose` | flag | false | Enable debug logging to stderr |
| `--version` | flag | - | Show version and exit |
| `--help` | flag | - | Show help and exit |

### Exit Codes

- `0`: Success
- `1`: User error (invalid arguments, bad selection)
- `2`: System error (I/O failure, permissions)
- `3`: Conflict detected without --force
- `4`: Validation failed (schema, circular dependencies)

---

## Command: `claude-seed init`

Initialize a new repository with selected registry items.

### Synopsis

```bash
claude-seed init [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--dry-run` | flag | false | Preview changes without writing files |
| `--force` | flag | false | Overwrite on conflicts (use last selected value) |
| `--filter TAG` | string | - | Pre-filter registry by tag (repeatable) |
| `--output PATH` | path | `.` | Target directory for installation |

### Behavior

1. **Load Registry**: Read metadata from `--registry-path`
2. **Interactive Selection**: Present multi-select UI with all items
   - Show: name, version, category, description
   - Search: by name or tag
   - Filter: apply `--filter` tags if provided
3. **Resolve Dependencies**: Automatically include required items
4. **Detect Conflicts**: Check for MCP key collisions
5. **Preview**: If `--dry-run`, show planned changes and exit
6. **Validate**: Run schema validation on merged .mcp.json
7. **Install**: Atomic copy to `--output` directory
8. **Generate Lock**: Write `.claude.lock.json`

### Examples

```bash
# Standard initialization
claude-seed init

# Dry run with debug output
claude-seed init --dry-run --verbose

# Pre-filter to research agents only
claude-seed init --filter research --filter prod-safe

# Force overwrite on conflicts
claude-seed init --force

# Install to different directory
claude-seed init --output /path/to/repo
```

### Output (Success)

```
✓ Loaded registry: 50 items
✓ Selected 5 items, resolved 2 dependencies
✓ Validated: no conflicts
✓ Copied 12 files to .claude/
✓ Generated .mcp.json (3 servers)
✓ Generated .env.example (4 variables)
✓ Created .claude.lock.json

Initialization complete! Next steps:
  1. Review .env.example and create .env
  2. Run: claude --version  (verify Claude Code detects config)
  3. Commit .claude.lock.json to version control
```

### Output (Dry Run)

```
DRY RUN - no files will be modified

Planned changes:
  CREATE .claude/subagents/research.md (2.3 KB)
  CREATE .claude/commands/spec.md (1.8 KB)
  CREATE .mcp.json (merged from 2 fragments)
  CREATE .env.example (4 variables)
  CREATE .claude.lock.json

MCP servers to be configured:
  - serena (semantic code tools)
  - context7 (documentation search)

Environment variables required:
  - SERENA_LOG_LEVEL (optional, default: info)
  - CONTEXT7_API_KEY (required)

No conflicts detected.
```

### Output (Error: Conflict)

```
ERROR: Configuration conflicts detected

Conflicts:
  1. mcpServers.serena.command
     - Defined in: mcp-serena-v1
       Value: "node /opt/serena/1.0/index.js"
     - Defined in: mcp-serena-v2
       Value: "node /opt/serena/2.0/index.js"

Resolution:
  - Use --force to overwrite with last selected value
  - Or deselect one of the conflicting items and retry

Exit code: 3
```

---

## Command: `claude-seed install`

Install from an existing lock file (reproducible setup).

### Synopsis

```bash
claude-seed install [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--lock-file PATH` | path | `.claude.lock.json` | Path to lock file |
| `--verify` | flag | false | Verify installed files match lock file hashes |
| `--output PATH` | path | `.` | Target directory for installation |

### Behavior

1. **Read Lock File**: Parse `.claude.lock.json`
2. **Verify Registry**: Ensure items at exact versions exist
3. **Resolve Items**: Load items from registry
4. **Install**: Copy files to `--output` directory
5. **Verify Hashes**: If `--verify`, check SHA-256 matches

### Examples

```bash
# Install from lock file
claude-seed install

# Install and verify integrity
claude-seed install --verify

# Use different lock file
claude-seed install --lock-file ../shared-config/.claude.lock.json

# Install to different directory
claude-seed install --output /path/to/repo
```

### Output (Success)

```
✓ Loaded lock file: 5 items
✓ Verified registry: all items found at exact versions
✓ Copied 12 files to .claude/
✓ Generated .mcp.json (3 servers)
✓ Verified hashes: all match

Installation complete!
```

### Output (Error: Version Mismatch)

```
ERROR: Lock file version mismatch

Lock file requires:
  - research-agent v2.1.0

Registry contains:
  - research-agent v2.2.0 (newer)

Resolution:
  - Update registry to include v2.1.0
  - Or regenerate lock file with: claude-seed init

Exit code: 2
```

---

## Command: `claude-seed list`

List available registry items (optional convenience command).

### Synopsis

```bash
claude-seed list [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--filter TAG` | string | - | Filter by tag (repeatable) |
| `--type TYPE` | enum | - | Filter by type: subagent, command, mcp |
| `--json` | flag | false | Output as JSON array |

### Examples

```bash
# List all items
claude-seed list

# List research agents
claude-seed list --filter research --type subagent

# JSON output for scripting
claude-seed list --json | jq '.[] | select(.category == "research")'
```

### Output (Table Format)

```
NAME                TYPE       VERSION  CATEGORY       TAGS
research-agent      subagent   2.1.0    research       research, web-search, prod-safe
code-reviewer       subagent   1.5.2    quality        review, testing
spec-command        command    1.0.0    workflow       specification, planning
mcp-serena          mcp        2.3.0    code-tools     semantic, refactoring
mcp-context7        mcp        1.2.1    documentation  docs, search

5 items found
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_REGISTRY_PATH` | `~/.claude-registry` | Default registry location |
| `CLAUDE_SEED_LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG, INFO, WARN, ERROR) |
| `CLAUDE_SEED_LOG_FILE` | `~/.claude-seed/logs/seed.log` | Log file location |

---

## Configuration File (Optional)

Location: `~/.claude-seed/config.yaml`

```yaml
registry_path: /home/user/org-registry
default_filters:
  - prod-safe
log_level: INFO
```

---

## Interactive Selection UI

### Multi-Select Interface

```
Claude Code Project Seeder - Select Items

? Select items to install (use arrow keys, space to select, enter to confirm):
  [X] research-agent (v2.1.0) - Web research with adaptive strategies
      Tags: research, web-search, prod-safe

  [ ] code-reviewer (v1.5.2) - Automated code review and quality checks
      Tags: review, testing, quality

  [X] spec-command (v1.0.0) - Specification-driven development workflow
      Tags: specification, planning, workflow

  [ ] mcp-serena (v2.3.0) - Semantic code intelligence and refactoring
      Tags: semantic, refactoring, code-tools
      Requires: SERENA_LOG_LEVEL (optional)

  [X] mcp-context7 (v1.2.1) - Documentation search and patterns
      Tags: docs, search, reference
      Requires: CONTEXT7_API_KEY (required)

  Depends on: base-context (v1.0.0) - automatically included

/search_  (type to filter by name or tag)

Selected: 3 items, 1 dependency resolved
```

### Search/Filter

```
? Select items to install (filtered by "research"):
  [X] research-agent (v2.1.0) - Web research with adaptive strategies
  [ ] research-validator (v1.0.0) - Validate research sources

/research_  (clear filter: backspace)

Showing 2 of 50 items
```

---

## Error Messages

### Registry Not Found

```
ERROR: Registry not found at: /home/user/.claude-registry

Resolution:
  - Clone the registry: git clone <repo-url> ~/.claude-registry
  - Or specify path: claude-seed init --registry-path /path/to/registry

Exit code: 2
```

### Invalid Metadata

```
ERROR: Invalid registry metadata

File: /home/user/.claude-registry/subagents/research-agent/metadata.yaml
Line: 12
Error: Missing required field 'version'

Resolution:
  - Fix metadata.yaml in registry
  - Or skip this item in selection

Exit code: 2
```

### Circular Dependency

```
ERROR: Circular dependency detected

Cycle: agent-a → agent-b → agent-c → agent-a

Resolution:
  - Fix registry metadata to break cycle
  - Contact registry maintainer

Exit code: 4
```

### Insufficient Permissions

```
ERROR: Permission denied

Failed to create: /repo/.claude/subagents/research.md
Reason: Permission denied (errno 13)

Resolution:
  - Run with appropriate permissions
  - Or specify writable --output directory

Exit code: 2
```

---

## Testing Contracts

### Unit Test Commands

```bash
# Test CLI parsing
pytest tests/unit/test_cli.py

# Test with mock registry
pytest tests/integration/test_init_flow.py --registry=tests/fixtures/mock_registry
```

### Integration Test Scenarios

1. **Happy Path**: Select 3 items, no conflicts, verify files created
2. **Conflict Detection**: Select 2 items with MCP collision, verify error
3. **Dependency Resolution**: Select item with dependencies, verify auto-inclusion
4. **Dry Run**: Verify no files written, correct preview output
5. **Lock File Install**: Create lock, delete .claude/, reinstall, verify identical
6. **Hash Verification**: Tamper with file, run install --verify, detect mismatch
