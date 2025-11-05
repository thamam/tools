# Data Model: Claude Code Project Seeder

**Feature**: 001-claude-seeder
**Date**: 2025-10-25
**Purpose**: Define data structures for registry, selection, and lock file

## Core Entities

### RegistryItem

Represents a single item (sub-agent, command, or MCP server) in the registry.

**Fields**:
- `name` (string, required): Unique identifier within namespace (e.g., "research-agent")
- `version` (string, required): Semver version (e.g., "2.1.0")
- `type` (enum, required): "subagent" | "command" | "mcp"
- `category` (string, optional): Grouping label (e.g., "research", "code-editing")
- `tags` (list[string], required): Filterable keywords (e.g., ["research", "web-search", "prod-safe"])
- `description` (string, required): Human-readable summary for selection UI
- `dependencies` (list[string], optional): Names of other registry items required (e.g., ["base-agent"])
- `env_vars` (list[EnvVar], optional): Environment variables required by this item
- `files` (dict[string, string], required): Map of destination paths to source paths in registry
- `mcp_fragment` (dict, optional): Partial .mcp.json structure (only for type="mcp")
- `compatibility_notes` (string, optional): Version constraints or warnings

**Validation Rules**:
- `name` must match regex: `^[a-z0-9-]+$`
- `version` must be valid semver
- `type` must be one of three allowed values
- `files` must have at least one entry
- `mcp_fragment` required if and only if `type == "mcp"`
- `dependencies` must reference existing registry items

**Example (YAML metadata)**:
```yaml
name: research-agent
version: 2.1.0
type: subagent
category: research
tags:
  - research
  - web-search
  - prod-safe
description: "Web research agent with adaptive search strategies"
dependencies:
  - base-context
env_vars:
  - name: TAVILY_API_KEY
    description: "API key for Tavily search"
    required: true
files:
  .claude/subagents/research.md: subagents/research.md
```

---

### EnvVar

Represents an environment variable required by a registry item.

**Fields**:
- `name` (string, required): Environment variable name (e.g., "TAVILY_API_KEY")
- `description` (string, required): What this variable is for
- `required` (bool, required): Whether the item fails without this variable
- `default` (string, optional): Default value if not provided

**Validation Rules**:
- `name` must match regex: `^[A-Z_][A-Z0-9_]*$`
- `required` must be explicitly set (no default)

---

### Selection

User's chosen set of registry items for installation.

**Fields**:
- `items` (list[RegistryItem], required): Selected items in dependency order
- `resolved_dependencies` (list[RegistryItem], required): Items automatically included
- `conflicts` (list[Conflict], required): Detected conflicts (empty if none)

**State Transitions**:
1. **Initial**: User makes manual selections
2. **Resolved**: Dependencies computed, conflicts detected
3. **Validated**: All items exist, no circular dependencies
4. **Ready**: Can proceed to installation

**Validation Rules**:
- All items in `resolved_dependencies` must also be in registry
- `conflicts` must be empty unless `--force` flag provided

---

### Conflict

Represents a configuration key collision during merge.

**Fields**:
- `path` (list[string], required): JSON path to conflicting key (e.g., ["mcpServers", "serena", "command"])
- `item_a` (string, required): Name of first item defining this key
- `item_b` (string, required): Name of second item defining this key
- `value_a` (any, required): Value from item_a
- `value_b` (any, required): Value from item_b

**Example**:
```python
Conflict(
    path=["mcpServers", "serena", "command"],
    item_a="mcp-serena-v1",
    item_b="mcp-serena-v2",
    value_a="node serena-1.0.js",
    value_b="node serena-2.0.js"
)
```

---

### LockFile

Records the exact versions and hashes of installed items.

**Fields**:
- `version` (string, required): Lock file format version (e.g., "1.0")
- `generated` (string, required): ISO 8601 timestamp
- `registry_path` (string, required): Absolute path to registry used
- `items` (dict[string, LockItem], required): Map of item name to lock entry

**Validation Rules**:
- `version` must match semantic version
- `generated` must be valid ISO 8601
- All paths in `items` must be absolute or relative to repo root

**Example (JSON)**:
```json
{
  "version": "1.0",
  "generated": "2025-10-25T14:30:00Z",
  "registry_path": "/home/user/.claude-registry",
  "items": {
    "research-agent": {
      "type": "subagent",
      "version": "2.1.0",
      "files": {
        ".claude/subagents/research.md": "sha256:abc123..."
      }
    }
  }
}
```

---

### LockItem

Individual item entry in lock file.

**Fields**:
- `type` (enum, required): "subagent" | "command" | "mcp"
- `version` (string, required): Semver version installed
- `files` (dict[string, string], required): Map of destination path to SHA-256 hash

**Validation Rules**:
- `version` must match semver format
- `files` keys must be relative paths from repo root
- Hash values must be `sha256:` prefix + 64 hex chars

---

### DependencyGraph

Internal structure for dependency resolution.

**Fields**:
- `nodes` (dict[string, RegistryItem], required): All items in graph
- `edges` (dict[string, list[string]], required): Adjacency list (name → dependencies)
- `visited` (set[string]): Tracking for cycle detection
- `visiting` (set[string]): Nodes currently in DFS stack

**Methods** (conceptual):
- `add_item(item)`: Add node to graph
- `resolve()` → list[RegistryItem]: Topological sort, detect cycles
- `has_cycle()` → bool: Check for circular dependencies

**State Transitions**:
1. **Building**: Adding items and edges
2. **Resolving**: Running topological sort
3. **Complete**: Sorted list ready or cycle detected

---

## Data Relationships

```
Registry (directory)
  ├── contains many → RegistryItem
  │
RegistryItem
  ├── has many → EnvVar
  ├── depends on many → RegistryItem (dependencies)
  ├── has one → MCP Fragment (if type=mcp)
  │
Selection
  ├── includes many → RegistryItem (items)
  ├── resolves to many → RegistryItem (resolved_dependencies)
  ├── may have many → Conflict
  │
LockFile
  ├── records many → LockItem
  │
DependencyGraph
  ├── models many → RegistryItem (as nodes)
  ├── tracks many edges between → RegistryItem
```

---

## File Formats

### Registry Metadata (YAML)

Location: `registry/{namespace}/{item-name}/metadata.yaml`

```yaml
name: research-agent
version: 2.1.0
type: subagent
category: research
tags: [research, web-search, prod-safe]
description: "Web research agent with adaptive search strategies"
dependencies:
  - base-context
env_vars:
  - name: TAVILY_API_KEY
    description: "API key for Tavily search"
    required: true
files:
  .claude/subagents/research.md: subagents/research.md
```

### MCP Fragment (JSON)

Location: `registry/mcp/{item-name}/mcp-fragment.json`

```json
{
  "mcpServers": {
    "serena": {
      "command": "node",
      "args": ["/path/to/serena-mcp/dist/index.js"],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

### Lock File (JSON)

Location: `.claude.lock.json` (repo root)

```json
{
  "version": "1.0",
  "generated": "2025-10-25T14:30:00Z",
  "registry_path": "/home/user/.claude-registry",
  "items": {
    "research-agent": {
      "type": "subagent",
      "version": "2.1.0",
      "files": {
        ".claude/subagents/research.md": "sha256:abc123def456..."
      }
    }
  }
}
```

---

## Validation State Machine

```
[User Selections]
       ↓
[Load Registry Items] → Invalid metadata? → ERROR
       ↓
[Resolve Dependencies] → Cycle detected? → ERROR
       ↓
[Detect Conflicts] → Conflicts found? → ERROR (unless --force)
       ↓
[Validate Schema] → Schema invalid? → ERROR
       ↓
[Atomic Install]
```

---

## Performance Characteristics

| Operation | Complexity | Target |
|-----------|------------|--------|
| Load registry | O(n) items | <500ms for 1000 items |
| Dependency resolution | O(V + E) graph | <100ms for 50 items |
| Conflict detection | O(n * d) depth | <200ms for 10 items |
| File copying | O(f) files | <10s for 100 files |
| Hash computation | O(s) bytes | <1s for 10MB total |

**Notes**:
- n = number of registry items
- V = vertices, E = edges in dependency graph
- d = max JSON depth
- f = number of files
- s = total file size in bytes
