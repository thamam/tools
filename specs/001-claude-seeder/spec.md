# Feature Specification: Claude Code Project Seeder

**Feature Branch**: `001-claude-seeder`
**Created**: 2025-10-25
**Status**: Draft
**Input**: User description: "CLI seeder that copies selected sub-agents, commands, and MCPs from a private registry into a repo and generates minimal configs for Claude Code"

## User Scenarios & Testing

### User Story 1 - Initialize New Repository (Priority: P1)

A developer starts a new project and wants to set up Claude Code with a curated set of sub-agents, commands, and MCP servers from their organization's approved registry, completing the setup in under 60 seconds.

**Why this priority**: This is the core MVP functionality - the primary value proposition of the seeder. Without this, the tool has no purpose.

**Independent Test**: Can be fully tested by running the seeder command in an empty repository and verifying that .claude/ and .mcp.json are created with selected items.

**Acceptance Scenarios**:

1. **Given** an empty repository, **When** developer runs `claude-seed init` and selects items from the registry, **Then** .claude/ directory is created with selected sub-agents and commands
2. **Given** a registry with 20 items across three namespaces, **When** developer filters by "research" tag and selects 3 items, **Then** only those 3 items are copied to the repository
3. **Given** selected MCP servers require environment variables, **When** seeder completes, **Then** .env.example is created with all required variables documented

---

### User Story 2 - Reproducible Setup (Priority: P2)

A developer needs to replicate an exact project configuration on a different machine or share the configuration with team members, ensuring deterministic and auditable setups.

**Why this priority**: Reproducibility is critical for team consistency but can be delivered after the basic initialization works.

**Independent Test**: Can be tested by running seeder with same inputs on two different machines and verifying identical output via file hashing.

**Acceptance Scenarios**:

1. **Given** a .claude.lock.json file from another machine, **When** developer runs `claude-seed install`, **Then** exact same versions and items are installed
2. **Given** two developers select the same items in different orders, **When** seeder completes, **Then** generated files are byte-for-byte identical (deterministic merges)
3. **Given** a completed setup, **When** developer inspects .claude.lock.json, **Then** all selected items are listed with their versions and source hashes

---

### User Story 3 - Conflict Detection (Priority: P3)

A developer selects multiple MCP servers that define conflicting configuration keys, and the seeder prevents silent overwrites by failing fast with clear error messages.

**Why this priority**: Important for data safety but less critical than getting basic functionality working.

**Independent Test**: Can be tested by intentionally selecting conflicting items and verifying error messages and rollback behavior.

**Acceptance Scenarios**:

1. **Given** two MCP servers define the same mcpServers key, **When** developer tries to merge them, **Then** seeder fails with error listing the conflict and which items caused it
2. **Given** a conflict is detected, **When** seeder fails, **Then** no partial changes are written (atomic operation)
3. **Given** a conflict exists, **When** developer runs with `--force` flag, **Then** seeder warns about overwrite and uses last-selected item's value

---

### User Story 4 - Dry Run Preview (Priority: P3)

A developer wants to preview what changes the seeder will make before actually modifying their repository files.

**Why this priority**: Nice-to-have safety feature that improves confidence but not essential for core functionality.

**Independent Test**: Can be tested by running `--dry-run` and verifying no files are modified while output shows planned changes.

**Acceptance Scenarios**:

1. **Given** a selection of items, **When** developer runs `claude-seed init --dry-run`, **Then** seeder outputs planned file changes without writing anything
2. **Given** a dry run output, **When** developer reviews it, **Then** output shows file paths that would be created, content diffs, and any conflicts
3. **Given** a dry run with conflicts, **When** seeder completes, **Then** exit code indicates error and no changes are made

---

### Edge Cases

- What happens when registry contains invalid metadata (missing required fields, malformed JSON)?
- How does system handle registry items with circular dependencies?
- What if .claude/ or .mcp.json already exists in the repository?
- How are registry schema version mismatches handled?
- What happens if a selected item references files that don't exist in registry?
- How does seeder behave when run with insufficient file system permissions?
- What if multiple items provide the same command name with different implementations?

## Requirements

### Functional Requirements

- **FR-001**: System MUST load a local registry from a configurable directory path with three namespaces: subagents/, commands/, and mcp/
- **FR-002**: System MUST present an interactive multi-select interface showing all available items with their names, versions, categories, and tags
- **FR-003**: System MUST support filtering registry items by tags (e.g., "research", "code-editing", "prod-safe")
- **FR-004**: System MUST copy selected sub-agents and commands into .claude/ directory, preserving the original directory structure
- **FR-005**: System MUST merge selected MCP server fragments into a single .mcp.json file at repository root
- **FR-006**: System MUST detect and fail on conflicting configuration keys during MCP merge unless --force flag is provided
- **FR-007**: System MUST generate .env.example file containing all environment variables required by selected items
- **FR-008**: System MUST create a lock file (.claude.lock.json) recording selected items with their versions and content hashes
- **FR-009**: System MUST validate .mcp.json against a pinned JSON Schema before writing
- **FR-010**: System MUST support --dry-run flag that shows planned changes without modifying files
- **FR-011**: System MUST resolve dependencies between registry items and automatically include required dependencies
- **FR-012**: System MUST detect circular dependencies in registry metadata and fail with descriptive error
- **FR-013**: System MUST provide clear error messages with exit codes suitable for CI/CD integration
- **FR-014**: System MUST perform all file operations atomically - either all succeed or all rollback
- **FR-015**: System MUST generate README sections with setup instructions for selected items

### Key Entities

- **Registry**: A versioned directory containing vetted templates organized in three namespaces (subagents/, commands/, mcp/), each with metadata files
- **Registry Item**: A template with metadata including name, version, category, tags, prerequisites, required environment variables, and compatibility notes
- **Selection**: User's chosen set of registry items for a specific repository
- **Lock File**: A JSON file recording the exact versions and hashes of installed items for reproducibility
- **Configuration Fragment**: A partial .mcp.json structure provided by an MCP registry item that must be merged with others

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can complete repository initialization from empty state to working Claude Code setup in under 60 seconds for a typical selection (5-10 items)
- **SC-002**: Zero manual file copying required for standard setups - all configuration is generated
- **SC-003**: Reproducible output verified by file hashing - same inputs produce identical outputs across different machines
- **SC-004**: Seeder runs successfully in offline mode after registry is cloned locally
- **SC-005**: 100% of conflict scenarios are detected and reported before any files are written
- **SC-006**: Error messages clearly identify the issue and provide actionable resolution steps in 90% of common failure cases
- **SC-007**: System completes initialization without requiring any binary dependencies beyond POSIX shell and Node.js or Python

## Assumptions

- Users have basic command-line proficiency and understand concepts like environment variables
- Registry is maintained in a Git repository or local directory that users have read access to
- Users understand their organization's policies for which sub-agents/commands/MCPs are approved
- Target repositories are Git-initialized before running the seeder
- Users run the seeder from the repository root directory
- Node.js (v16+) or Python (3.8+) is available on the target system
- File system supports POSIX permissions and atomic file operations
- Registry items follow a documented metadata schema that includes version, dependencies, and required environment variables
- Users will handle secret management separately - seeder only documents required secrets in .env.example

## Dependencies

- Local clone or mount of the organization's registry repository
- JSON Schema validator for .mcp.json validation
- POSIX-compliant shell environment (bash, zsh, or sh)
- Either Node.js v16+ or Python 3.8+ runtime

## Scope

### In Scope

- Single-command initialization from local registry
- Interactive multi-select interface with tag filtering
- File copying, JSON merging, and configuration generation
- Dependency resolution and circular dependency detection
- Lock file generation for reproducibility
- Dry-run preview mode
- Atomic operations with rollback on failure
- Offline operation after registry is local
- Schema validation for .mcp.json
- Clear error messages and CI-friendly exit codes

### Out of Scope

- GUI or web-based interface
- Secret storage backends (Vault, 1Password, etc.)
- Remote registry hosting or fetching
- Automatic updates of installed items
- Live MCP service lifecycle management
- Public marketplace or registry sharing
- Version conflict resolution beyond fail-fast
- Migration tools for existing .claude/ setups
- IDE or editor integrations
- Telemetry or usage analytics
