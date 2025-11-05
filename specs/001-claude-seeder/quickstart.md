# Quickstart: Claude Code Project Seeder

**Feature**: 001-claude-seeder
**Date**: 2025-10-25
**Purpose**: Validate the implementation and document basic usage

## Prerequisites

Before testing the seeder, ensure:

1. **Python 3.8+** installed
   ```bash
   python3 --version  # Should be 3.8 or higher
   ```

2. **Registry cloned** to local machine
   ```bash
   git clone <your-org-registry-url> ~/.claude-registry
   ```

3. **Test repository** created
   ```bash
   mkdir ~/test-repo && cd ~/test-repo
   git init
   ```

---

## Installation

### From Source (Development)

```bash
cd /path/to/claude-seeder
pip install -e .
```

### From Package (Production)

```bash
pip install claude-seed
```

---

## Basic Usage

### 1. Initialize a New Repository

```bash
cd ~/test-repo
claude-seed init
```

**Expected Behavior**:
- Interactive prompt appears with registry items
- Use arrow keys to navigate, space to select
- Press Enter to confirm selection
- Files are copied to `.claude/` and `.mcp.json` created

**Verification**:
```bash
ls -la .claude/              # Should see subagents, commands
cat .mcp.json                # Should see merged MCP config
cat .env.example             # Should list required env vars
cat .claude.lock.json        # Should record versions and hashes
```

---

### 2. Dry Run (Preview Mode)

```bash
claude-seed init --dry-run
```

**Expected Output**:
```
DRY RUN - no files will be modified

Planned changes:
  CREATE .claude/subagents/research.md (2.3 KB)
  CREATE .mcp.json (merged from 2 fragments)
  ...
```

**Verification**:
```bash
ls .claude/  # Should not exist yet
```

---

### 3. Filter by Tags

```bash
claude-seed init --filter research --filter prod-safe
```

**Expected Behavior**:
- Selection UI only shows items with matching tags
- Fewer options displayed

---

### 4. Install from Lock File

```bash
# On a different machine
cd ~/test-repo
git clone <repo-with-lock-file> .
claude-seed install
```

**Expected Behavior**:
- Reads `.claude.lock.json`
- Installs exact versions from registry
- No interactive prompts

**Verification**:
```bash
claude-seed install --verify  # Should pass hash checks
```

---

## User Story Validation

### US1: Initialize New Repository (P1)

**Scenario**: First-time setup in under 60 seconds

```bash
# Start timer
time (cd ~/fresh-repo && claude-seed init)

# Steps:
# 1. Select 5-10 items from registry
# 2. Press Enter to confirm
# 3. Wait for completion

# Expected:
# - Total time < 60 seconds
# - .claude/ directory created
# - .mcp.json generated
# - .env.example created
```

**Acceptance**:
- [ ] Initialization completes in <60s
- [ ] All selected items appear in `.claude/`
- [ ] `.mcp.json` validates against schema
- [ ] `.env.example` documents all required variables

---

### US2: Reproducible Setup (P2)

**Scenario**: Install same config on two machines

```bash
# Machine 1
cd ~/repo1
claude-seed init
# Select items: research-agent, spec-command, mcp-serena
git add .claude.lock.json
git commit -m "Add Claude Code config"
git push

# Machine 2
git clone <repo> ~/repo2
cd ~/repo2
claude-seed install

# Compare
diff -r ~/repo1/.claude ~/repo2/.claude  # Should be identical
sha256sum ~/repo1/.mcp.json ~/repo2/.mcp.json  # Should match
```

**Acceptance**:
- [ ] Lock file records exact versions
- [ ] Install from lock produces identical files
- [ ] Hashes in lock file match installed files

---

### US3: Conflict Detection (P3)

**Scenario**: Select two MCP servers with same key

```bash
# Create test registry with conflicting items
cd ~/.claude-registry/mcp
mkdir mcp-serena-v1 mcp-serena-v2

# Both define mcpServers.serena.command differently

# Run seeder
claude-seed init
# Select both mcp-serena-v1 and mcp-serena-v2

# Expected: Error with conflict details
```

**Acceptance**:
- [ ] Seeder detects conflict before writing files
- [ ] Error message shows conflicting path and values
- [ ] Exit code is 3
- [ ] No partial files written

**Force Overwrite**:
```bash
claude-seed init --force
# Should succeed, use last selected value
```

**Acceptance**:
- [ ] `--force` allows overwrite
- [ ] Warning displayed about conflict
- [ ] Last-selected item's value used

---

### US4: Dry Run Preview (P3)

**Scenario**: Preview changes before applying

```bash
claude-seed init --dry-run > preview.txt

# Verify no files created
ls .claude/  # Should not exist
ls .mcp.json # Should not exist

# Review preview
cat preview.txt
# Should show:
# - Files to be created
# - MCP servers to configure
# - Env vars required
# - Any conflicts
```

**Acceptance**:
- [ ] No files modified in dry-run mode
- [ ] Preview shows all planned changes
- [ ] Conflicts detected and reported
- [ ] Exit code matches outcome (0=success, 3=conflict)

---

## Edge Case Testing

### Invalid Registry Metadata

```bash
# Corrupt metadata.yaml
echo "invalid: [" > ~/.claude-registry/subagents/test/metadata.yaml

# Run seeder
claude-seed init

# Expected: Clear error message
```

**Acceptance**:
- [ ] Error identifies problematic file
- [ ] Error shows line number and issue
- [ ] Exit code is 2

---

### Circular Dependencies

```bash
# Create circular dependency in test registry
# agent-a depends on agent-b
# agent-b depends on agent-c
# agent-c depends on agent-a

claude-seed init
# Select agent-a

# Expected: Cycle detected error
```

**Acceptance**:
- [ ] Cycle detection before file operations
- [ ] Error shows dependency path
- [ ] Exit code is 4

---

### Existing `.claude/` Directory

```bash
mkdir -p .claude/subagents
echo "existing content" > .claude/subagents/old.md

claude-seed init

# Expected: Error about existing directory
```

**Acceptance**:
- [ ] Seeder fails with clear error
- [ ] Suggests removal or merge strategy
- [ ] Exit code is 2

---

### Permission Errors

```bash
# Remove write permission
chmod -w .

claude-seed init

# Expected: Permission denied error
```

**Acceptance**:
- [ ] Clear error message with errno
- [ ] Suggests resolution (fix permissions)
- [ ] Exit code is 2

---

## Performance Benchmarks

### Target Metrics

| Scenario | Target | Command |
|----------|--------|---------|
| Load 1000-item registry | <500ms | `time claude-seed list --json > /dev/null` |
| Select 10 items | <60s total | `time claude-seed init` (interactive) |
| Dry run with 10 items | <2s | `time claude-seed init --dry-run` |
| Install from lock (10 items) | <10s | `time claude-seed install` |

### Benchmark Commands

```bash
# Registry load time
time claude-seed list --json > /dev/null

# Initialization (automated selection for timing)
time (echo -e "\n" | claude-seed init --filter research)

# Dry run
time claude-seed init --dry-run --filter research

# Install from lock
time claude-seed install
```

**Acceptance**:
- [ ] All benchmarks meet or exceed targets
- [ ] No memory leaks over repeated runs
- [ ] Stable performance with large registries (1000+ items)

---

## Integration Testing

### Full Workflow Test

```bash
#!/bin/bash
set -e

# 1. Initialize
cd ~/test-repo
claude-seed init --filter research --dry-run  # Preview
claude-seed init --filter research            # Execute

# 2. Verify structure
test -d .claude/subagents
test -f .mcp.json
test -f .env.example
test -f .claude.lock.json

# 3. Validate MCP config
jsonschema -i .mcp.json schema/mcp-schema.json

# 4. Commit lock file
git add .claude.lock.json
git commit -m "Add Claude Code config"

# 5. Clone to new location
cd ~
git clone test-repo test-repo-clone
cd test-repo-clone

# 6. Install from lock
claude-seed install --verify

# 7. Compare directories
diff -r ../test-repo/.claude .claude/

echo "✓ Full workflow test passed"
```

---

## Troubleshooting

### Seeder Not Found

```bash
claude-seed: command not found
```

**Solution**:
```bash
which claude-seed  # Check if installed
pip show claude-seed  # Verify package
pip install --force-reinstall claude-seed
```

---

### Registry Not Found

```bash
ERROR: Registry not found at: /home/user/.claude-registry
```

**Solution**:
```bash
# Clone registry
git clone <org-registry-url> ~/.claude-registry

# Or specify custom path
export CLAUDE_REGISTRY_PATH=/custom/path
claude-seed init
```

---

### Schema Validation Failed

```bash
ERROR: .mcp.json validation failed
```

**Solution**:
```bash
# Check merged config
cat .mcp.json | jq .

# Validate manually
jsonschema -i .mcp.json schema/mcp-schema.json

# Report issue to registry maintainer
```

---

## Next Steps After Validation

1. **Create test fixtures**: Generate mock registry with various scenarios
2. **Write pytest suite**: Cover all user stories and edge cases
3. **Document registry schema**: Create metadata schema specification
4. **Performance testing**: Benchmark with realistic registries
5. **CI integration**: Add seeder tests to CI pipeline

---

## Validation Checklist

- [ ] US1: Initialize completes in <60s with 10 items
- [ ] US2: Lock file enables byte-for-byte reproducibility
- [ ] US3: Conflicts detected before any file writes
- [ ] US4: Dry run shows accurate preview without side effects
- [ ] Edge case: Invalid metadata error is clear
- [ ] Edge case: Circular dependencies detected
- [ ] Edge case: Existing .claude/ directory handled
- [ ] Performance: All benchmarks meet targets
- [ ] Integration: Full workflow test passes
- [ ] Security: No path traversal vulnerabilities
