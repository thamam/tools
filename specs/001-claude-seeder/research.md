# Research: Claude Code Project Seeder

**Feature**: 001-claude-seeder
**Date**: 2025-10-25
**Purpose**: Technology selection and best practices for CLI seeder implementation

## Python CLI Framework Selection

### Decision: Click

**Rationale**:
- Industry-standard CLI framework with excellent command composition
- Native support for multi-command CLIs (`init`, `install`, dry-run modes)
- Automatic help generation and parameter validation
- Minimal dependencies and stable API (v8.x)
- Better suited than argparse for complex CLI apps with subcommands
- Integrates well with questionary for interactive prompts

**Alternatives Considered**:
- **argparse** (stdlib): Rejected because verbose API for multi-command CLIs, poor help formatting
- **typer**: Rejected because heavier dependency chain (FastAPI-style), overkill for this use case
- **docopt**: Rejected because requires manual parsing logic, less maintainable

**Implementation Notes**:
- Use `@click.group()` for main command
- `@click.command()` decorators for `init` and `install` subcommands
- `--dry-run`, `--force`, `--registry-path` as options
- Exit codes: 0=success, 1=user error, 2=system error, 3=conflict detected

---

## Interactive Prompts Library

### Decision: Questionary

**Rationale**:
- Rich interactive prompts with keyboard navigation
- Native multi-select with tag filtering support
- Clean API: `questionary.checkbox()` with search and selection
- Handles terminal sizing and rendering edge cases
- Lightweight (~100KB) with no heavy dependencies

**Alternatives Considered**:
- **PyInquirer**: Rejected because unmaintained since 2019, dependency conflicts
- **prompt_toolkit**: Rejected because too low-level, requires custom UI building
- **Rich**: Rejected because designed for output rendering, not input collection

**Implementation Notes**:
- Use `questionary.checkbox()` for multi-select
- Implement custom filter function for tag-based search
- Graceful degradation: if terminal doesn't support, fall back to numbered selection

---

## JSON Merging Strategy

### Decision: Custom Merge with Conflict Detection

**Rationale**:
- MCP `.mcp.json` has nested structure that requires deep merging
- Must detect key collisions at any depth (e.g., `mcpServers.foo` conflicts)
- Standard `dict.update()` silently overwrites - unacceptable per FR-006
- Need deterministic merge order (alphabetical by item name) for reproducibility

**Alternatives Considered**:
- **jsonmerge** library: Rejected because doesn't expose conflict detection hooks
- **deepmerge**: Rejected because default strategy is last-write-wins (silent overwrite)
- **jq** via subprocess: Rejected because external dependency, slower, harder to test

**Implementation Algorithm**:
```
1. Sort selected items alphabetically by name
2. Initialize result = {}
3. For each item's MCP fragment:
   a. Recursively walk both trees simultaneously
   b. On leaf value collision: record conflict path
   c. On dict merge: continue recursion
   d. On list merge: concatenate and deduplicate
4. If conflicts detected and not --force: fail with paths
5. If --force: warn and use last value
6. Return merged JSON
```

**Implementation Notes**:
- Write recursive `deep_merge(target, source, path=[])` function
- Track conflicts as list of tuples: `[(path, old_value, new_value)]`
- Use `json.dumps(sort_keys=True)` for deterministic output

---

## File Hashing for Lock Files

### Decision: SHA-256 with Content Addressing

**Rationale**:
- Need cryptographically secure hash for integrity verification
- SHA-256 is standard, fast, and widely supported
- Hash file contents, not metadata (mtime), for reproducibility
- Store hashes in lock file to detect registry changes

**Alternatives Considered**:
- **MD5**: Rejected because cryptographically broken, collision attacks
- **Git SHA-1**: Rejected because doesn't add value over SHA-256, git not required
- **File mtime**: Rejected because not portable across machines

**Implementation Notes**:
- Use `hashlib.sha256()` from stdlib
- Hash format: `sha256:HEX_DIGEST`
- Lock file structure:
```json
{
  "version": "1.0",
  "generated": "2025-10-25T12:00:00Z",
  "items": {
    "subagent-research": {
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

## Atomic File Operations Strategy

### Decision: Temp Directory + Atomic Rename

**Rationale**:
- Requirement FR-014: all-or-nothing file operations
- POSIX guarantees atomic `rename()` within same filesystem
- Temp directory staging prevents partial writes on error
- Rollback is simple: delete temp dir and return

**Implementation Pattern**:
```
1. Create temp dir: /tmp/claude-seed-{random}
2. Perform all file operations in temp dir
3. Validate all outputs (schema, existence)
4. If validation passes: rename temp → target (atomic)
5. On any error: remove temp dir
```

**Alternatives Considered**:
- **Git stash**: Rejected because requires git, user may not want git tracking
- **Manual rollback**: Rejected because error-prone, hard to test all paths
- **Database transactions**: Rejected because no database in this design

**Implementation Notes**:
- Use `tempfile.mkdtemp(prefix='claude-seed-')`
- Implement context manager for automatic cleanup
- Test rollback by injecting errors mid-operation

---

## Dependency Resolution Algorithm

### Decision: Topological Sort with Cycle Detection

**Rationale**:
- Registry items declare dependencies in metadata
- Must resolve transitive dependencies automatically (FR-011)
- Must detect circular dependencies and fail fast (FR-012)
- Topological sort produces deterministic dependency order

**Algorithm**:
```
1. Build dependency graph from metadata
2. Run DFS with cycle detection:
   - Mark nodes: unvisited, visiting, visited
   - If visiting node reached again: cycle detected
3. Topological sort via post-order DFS traversal
4. Return sorted list of items to install
```

**Alternatives Considered**:
- **Breadth-first search**: Rejected because doesn't detect cycles efficiently
- **External solver** (pip, npm): Rejected because overkill, we control the registry

**Implementation Notes**:
- Use `collections.defaultdict` for adjacency list
- Raise `DependencyCycleError` with cycle path for debugging
- Cache resolution results per registry version

---

## JSON Schema Validation

### Decision: jsonschema Library with Pinned Draft-07

**Rationale**:
- Need to validate `.mcp.json` structure per FR-009
- `jsonschema` is Python reference implementation
- Pin to Draft-07 for stability (Claude Code compatibility)
- Bundle schema file with seeder for offline validation

**Alternatives Considered**:
- **Pydantic**: Rejected because requires model definitions, slower validation
- **Cerberus**: Rejected because different schema format, less standard
- **Custom validation**: Rejected because reinventing wheel, error-prone

**Implementation Notes**:
- Store schema in `src/validation/mcp-schema.json`
- Validate before final write: `jsonschema.validate(data, schema)`
- Catch `ValidationError` and format user-friendly error messages
- Schema source: Claude Code official `.mcp.json` specification

---

## CLI Exit Codes Convention

### Decision: Standard Unix Exit Codes

**Rationale**:
- Requirement FR-013: CI-friendly exit codes
- 0 = success, non-zero = failure is universal
- Use specific codes for different failure types

**Exit Code Table**:
- `0`: Success - operation completed
- `1`: User error - invalid selection, bad flags
- `2`: System error - file I/O, permissions, malformed registry
- `3`: Conflict detected - MCP key collision without --force
- `4`: Validation failed - schema error, circular dependencies

**Implementation Notes**:
- Use `sys.exit(code)` explicitly, not exceptions
- Log errors to stderr before exit
- Include exit codes in CLI help text

---

## Technology Stack Summary

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.8+ |
| CLI Framework | Click | 8.x |
| Interactive UI | Questionary | 2.x |
| Schema Validation | jsonschema | 4.x |
| Metadata Format | YAML | PyYAML 6.x |
| Testing | pytest | 7.x |
| Hashing | hashlib (stdlib) | SHA-256 |
| File Ops | tempfile, shutil (stdlib) | - |

**Rationale for Python 3.8+**:
- Minimum version with f-strings, type hints, and pathlib improvements
- Available on Ubuntu 20.04 LTS and macOS 10.15+
- Dataclasses available (PEP 557) for clean data structures
- No need for 3.10+ features (match/case not required)

---

## Best Practices Applied

### Performance
- Lazy-load registry: only parse metadata for selected namespace
- Use `shutil.copytree()` for bulk file operations (faster than individual copies)
- Cache dependency resolution per session
- Target: <60s for 10 items (measured with `time` command)

### Security
- Validate all user inputs (paths, selections, flags)
- Prevent path traversal: reject `..` in registry paths
- No shell execution: pure Python file operations
- Hash verification prevents tampering

### Maintainability
- Type hints for all public functions
- Docstrings in Google style
- Unit tests for pure functions (merge, resolve, hash)
- Integration tests for full CLI flows
- Configuration via environment: `CLAUDE_REGISTRY_PATH`

### Error Handling
- Clear error messages with context and actionable advice
- Example: "Conflict: mcpServers.foo defined in both 'mcp-serena' and 'mcp-magic'. Use --force to overwrite."
- Log debug info to `~/.claude-seed/logs/` for troubleshooting
- Graceful degradation: if questionary fails, use simple input()

---

## Open Questions Resolved

1. **How to handle existing .claude/ directory?**
   - Decision: Fail with clear error message
   - Rationale: Prevents accidental overwrites, user must explicitly clean or merge

2. **Should lock file be committed to git?**
   - Decision: Yes, document in quickstart.md
   - Rationale: Enables team reproducibility, like package-lock.json

3. **Support Windows?**
   - Decision: Not in MVP (out of scope)
   - Rationale: POSIX requirement in spec, can add later if demand exists

4. **Versioning strategy for registry schema?**
   - Decision: Semver with schema version in metadata
   - Rationale: Allows registry evolution, seeder checks compatibility
