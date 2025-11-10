# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BMAD Dashboard is a real-time terminal UI visualization tool for BMAD (BMAD Method) projects. It provides live visualization of project state, story tracking, activity heatmaps, and next action recommendations.

**Tech Stack**: Python 3.8+, Rich library for TUI rendering

## Common Commands

### Installation
```bash
# Install the entire system
./install.sh

# Verify installation
~/.config/claude-code/tools/bmad-state-reader.py --help
~/.config/claude-code/apps/bmad-dashboard.py --help
```

### Testing
```bash
# Test state reader on a BMAD project
cd /path/to/bmad/project
~/.config/claude-code/tools/bmad-state-reader.py --pretty

# Test dashboard summary mode
~/.config/claude-code/apps/bmad-dashboard.py --summary

# Run live dashboard
~/.config/claude-code/apps/bmad-dashboard.py

# Run with custom poll interval
~/.config/claude-code/apps/bmad-dashboard.py --poll 0.5
```

### Development
```bash
# Test state reader directly
python3 tools/bmad-state-reader.py --path /path/to/project --pretty

# Test dashboard without installation
python3 apps/bmad-dashboard.py --path /path/to/project --summary

# Check if hook is working
ls -la ~/.config/claude-code/hooks/tool-result.sh
cat ~/.config/claude-code/hooks/tool-result.sh
```

## Architecture

### Component Structure

The system has three main components:

1. **State Reader** (`tools/bmad-state-reader.py`):
   - Searches for `bmm-workflow-status.md` to locate BMAD projects
   - Parses workflow status file to extract project configuration and story states
   - Supports BMAD Development Queue format with `STORIES_SEQUENCE`, `TODO_STORY`, `IN_PROGRESS_STORY`, `STORIES_DONE`
   - Finds and analyzes story files (`*.story.md` and `story-*.md`)
   - Detects artifacts (PRD, epics, architecture docs, etc.)
   - Calculates activity heatmap based on file modification times
   - Returns JSON output with complete project state

2. **Dashboard TUI** (`apps/bmad-dashboard.py`):
   - Rich-based terminal UI with live updates
   - Calls state reader to get project data
   - Polls trigger file for refresh signals (default: 1 second interval)
   - Trigger file location: `/tmp/bmad-dashboard-trigger` (cross-platform via `tempfile.gettempdir()`)
   - Displays: header panel, story tree, artifacts tree, activity legend
   - Two modes: live dashboard (default) and static summary (`--summary`)

3. **Auto-Refresh Hook** (`hooks/tool-result.sh`):
   - Claude Code hook that runs after any tool execution
   - Detects BMAD commands (`/bmad:*`, `*bmad*` in tool name)
   - Touches trigger file to signal dashboard refresh
   - Non-blocking (always exits 0)

### Data Flow

```
BMAD Command → Hook Detects → Touch Trigger → Dashboard Polls → Refresh
  /bmad:*       tool-result.sh   /tmp/trigger   1s interval     Live Update
```

### Key Files

- `tools/bmad-state-reader.py`: Core state parsing logic (429 lines)
  - `find_bmad_project_root()`: Searches up directory tree for `bmm-workflow-status.md`
  - `parse_workflow_status()`: Parses project config and story states
  - `find_story_files()`: Locates and analyzes `*.story.md` files
  - `find_artifacts()`: Discovers BMAD artifacts
  - `get_time_ago_category()`: Categorizes file ages for heatmap

- `apps/bmad-dashboard.py`: TUI application (433 lines)
  - `read_bmad_state()`: Subprocess call to state reader
  - `build_story_tree()`: Rich Tree visualization of stories
  - `build_dashboard()`: Assembles complete layout
  - `run_dashboard()`: Main live update loop with trigger file polling

- `hooks/tool-result.sh`: Auto-refresh integration
  - Monitors `$TOOL_NAME` environment variable
  - Uses `$TMPDIR` for cross-platform temp file support

### Activity Heatmap

Files are color-coded based on modification time:
- 🔴 Recent (< 1 hour): `bright_red`
- 🟠 Active (< 4 hours): `bright_yellow`
- 🟡 Today (< 24 hours): `yellow`
- 🟢 Week (< 7 days): `green`
- 🔵 Month (< 30 days): `blue`
- ⚪ Old (> 30 days): `dim white`

Implementation: `get_time_ago_category()` in `tools/bmad-state-reader.py:181-204`

## Story State Parsing

The state reader supports BMAD Development Queue format:

- **BACKLOG**: Parsed from `STORIES_SEQUENCE` (JSON array)
- **TODO**: Parsed from `TODO_STORY` and `TODO_TITLE` fields
- **IN PROGRESS**: Parsed from `IN_PROGRESS_STORY` and `IN_PROGRESS_TITLE` fields
- **DONE**: Parsed from `STORIES_DONE` (JSON array)

Story files are discovered using patterns:
- `*.story.md` anywhere in project tree
- `story-*.md` anywhere in project tree
- Story ID extraction from filename (e.g., `story-1.2-auth.md` → ID: `1.2`)

## Installation System

The `install.sh` script:
1. Creates directory structure in `~/.config/claude-code/` and `~/.claude/`
2. Copies all components with executable permissions
3. Verifies Python 3 installation
4. Auto-installs Rich library if missing
5. Provides installation summary and quick start guide

Installed locations:
- `~/.config/claude-code/tools/bmad-state-reader.py`
- `~/.config/claude-code/apps/bmad-dashboard.py`
- `~/.config/claude-code/apps/launch-dashboard.sh`
- `~/.config/claude-code/hooks/tool-result.sh`
- `~/.claude/commands/bmad-dashboard.md`

## Fixed Issues (v1.1)

### Issue 1: Missing Artifacts (FIXED)

**Problem**: The artifact detection patterns were too restrictive:
- `**/architecture.md` only matched exact filename, missing files like `gear3-architecture.md`
- No patterns for completion reports, implementation plans, and other common BMAD documents

**Fix Applied** (`tools/bmad-state-reader.py:273-283`):
- Changed architecture pattern to `**/*architecture*.md` (more flexible wildcard)
- Added new artifact types:
  - Completion Report: `**/*completion-report*.md`
  - Implementation Plan: `**/*implementation-plan*.md`
  - Planning Doc: `**/*plan*.md`

### Issue 2: Dashboard Not Auto-Updating (FIXED)

**Problem**: Race condition in timestamp update caused missed refreshes.

**Root Cause**: In `apps/bmad-dashboard.py:342-356`, the code captured `current_time` BEFORE checking the trigger file, then updated `last_trigger_check` to that old timestamp. This meant if the file was touched between capturing `current_time` and checking the file, it would be missed.

**Fix Applied** (`apps/bmad-dashboard.py:342-355`):
- Removed premature `current_time = time.time()` capture
- Moved `last_trigger_check = time.time()` INSIDE the `if should_refresh:` block
- Now timestamp is captured AFTER processing the refresh, eliminating race condition

**Additional Improvements**:
- Enabled hook logging in `hooks/tool-result.sh:27` for debugging
- Created `test-trigger.sh` utility to manually test the trigger mechanism

## Debugging and Testing

### Test Trigger Mechanism
```bash
# Test if dashboard responds to trigger file
./test-trigger.sh

# Or manually:
touch /tmp/bmad-dashboard-trigger
# Dashboard should refresh within 1-2 seconds
```

### Check Hook Activity
```bash
# View hook log to see when BMAD commands trigger updates
tail -f /tmp/bmad-dashboard.log

# Clear log
rm /tmp/bmad-dashboard.log
```

### Verify Artifact Detection
```bash
# Run state reader to see all detected artifacts
~/.config/claude-code/tools/bmad-state-reader.py --pretty | jq '.artifacts'
```

### Hook Not Firing

**Check**: The hook may not be detecting BMAD commands properly.
**Solution**: Verify the pattern matching in `hooks/tool-result.sh:18-21` captures your BMAD commands.

### Rich Library Not Found

**Solution**: Install with `pip install rich` or `pip3 install rich` or `pip install --user rich`

## Development Notes

- State reader returns JSON, making it easy to integrate with other tools or CI/CD
- Dashboard uses Rich's Live context for smooth updates without flicker
- Trigger file mechanism is cross-platform (uses `tempfile.gettempdir()`)
- All Python scripts have shebang `#!/usr/bin/env python3` for portability
- Hook must always exit 0 to avoid blocking tool execution

## Claude Code Integration

The `/bmad-dashboard` slash command (`commands/bmad-dashboard.md`) provides Claude Code with:
- Instructions for launching the dashboard
- Guidance for analyzing project state
- Recommendations based on bottlenecks (e.g., many TODO stories but nothing IN PROGRESS)
- Troubleshooting steps for common issues

The agent can run the state reader directly to analyze project state and provide actionable insights.
