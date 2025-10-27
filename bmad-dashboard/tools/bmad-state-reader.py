#!/usr/bin/env python3
"""
BMAD State Reader Tool
Parses BMAD project structure and returns JSON with project state, stories, and artifacts.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


def find_bmad_project_root(start_path: str = ".") -> Optional[Path]:
    """
    Search upward from start_path to find bmm-workflow-status.md
    Returns the directory containing the status file, or None if not found.
    """
    current = Path(start_path).resolve()

    # Search up to 10 levels or until we hit root
    for _ in range(10):
        status_file = current / "bmm-workflow-status.md"
        if status_file.exists():
            return current

        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        current = parent

    return None


def parse_workflow_status(status_file: Path) -> Dict[str, Any]:
    """
    Parse bmm-workflow-status.md file to extract project info and story states.
    """
    if not status_file.exists():
        return {}

    content = status_file.read_text()

    # Parse project configuration
    project = {}
    config_patterns = {
        "name": r"PROJECT_NAME:\s*(.+)",
        "type": r"PROJECT_TYPE:\s*(.+)",
        "level": r"PROJECT_LEVEL:\s*(.+)",
        "field_type": r"FIELD_TYPE:\s*(.+)",
        "start_date": r"START_DATE:\s*(.+)",
    }

    for key, pattern in config_patterns.items():
        match = re.search(pattern, content)
        if match:
            project[key] = match.group(1).strip()

    # Parse current state
    state_patterns = {
        "current_phase": r"CURRENT_PHASE:\s*(.+)",
        "current_workflow": r"CURRENT_WORKFLOW:\s*(.+)",
        "current_agent": r"CURRENT_AGENT:\s*(.+)",
    }

    for key, pattern in state_patterns.items():
        match = re.search(pattern, content)
        if match:
            project[key] = match.group(1).strip()

    # Parse next action
    next_action_match = re.search(r"NEXT_ACTION:\s*(.+)", content)
    if next_action_match:
        project["next_action"] = next_action_match.group(1).strip()

    # Parse story states (BACKLOG, TODO, IN PROGRESS, DONE)
    stories = {
        "BACKLOG": [],
        "TODO": [],
        "IN PROGRESS": [],
        "DONE": []
    }

    # Look for sections like "## BACKLOG", "## TODO", etc.
    for state in stories.keys():
        # Match section header and capture content until next ## or end
        pattern = rf"##\s+{re.escape(state)}.*?\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, content, re.DOTALL)

        if match:
            section_content = match.group(1)
            # Parse story entries (format: - Story X.Y: Title (file: path/to/file.md))
            story_pattern = r"-\s+Story\s+(\d+\.\d+):\s+(.+?)(?:\s+\(file:\s+(.+?)\))?$"

            for line in section_content.split("\n"):
                story_match = re.match(story_pattern, line.strip())
                if story_match:
                    story_id = story_match.group(1)
                    title = story_match.group(2).strip()
                    file_path = story_match.group(3)

                    stories[state].append({
                        "id": story_id,
                        "title": title,
                        "file": file_path,
                        "state": state
                    })

    return {
        "project": project,
        "stories": stories
    }


def get_file_mtime(file_path: Path) -> Optional[float]:
    """Get file modification time as Unix timestamp."""
    try:
        return file_path.stat().st_mtime
    except OSError:
        return None


def get_time_ago_category(mtime: Optional[float]) -> str:
    """
    Categorize how long ago a file was modified.
    Returns: recent, hour, day, week, month, old, never
    """
    if mtime is None:
        return "never"

    now = datetime.now().timestamp()
    age_seconds = now - mtime

    # Define thresholds
    if age_seconds < 3600:  # < 1 hour
        return "recent"
    elif age_seconds < 14400:  # < 4 hours
        return "hour"
    elif age_seconds < 86400:  # < 24 hours
        return "day"
    elif age_seconds < 604800:  # < 7 days
        return "week"
    elif age_seconds < 2592000:  # < 30 days
        return "month"
    else:
        return "old"


def find_story_files(project_root: Path) -> List[Dict[str, Any]]:
    """
    Find all .story.md files and extract metadata.
    """
    story_files = []

    # Search for *.story.md files
    for story_file in project_root.rglob("*.story.md"):
        try:
            content = story_file.read_text()

            # Extract story number from filename (e.g., story-1.2-title.md)
            filename = story_file.name
            id_match = re.search(r"story[- ](\d+\.\d+)", filename, re.IGNORECASE)
            story_id = id_match.group(1) if id_match else None

            # Extract title from first line
            first_line = content.split("\n")[0] if content else ""
            title_match = re.search(r"#\s+Story\s+[\d.]+:\s+(.+)", first_line)
            title = title_match.group(1).strip() if title_match else filename

            # Extract status
            status_match = re.search(r"Status:\s*(\w+)", content)
            status = status_match.group(1) if status_match else "unknown"

            # Get modification time
            mtime = get_file_mtime(story_file)

            story_files.append({
                "id": story_id,
                "title": title,
                "file": str(story_file.relative_to(project_root)),
                "status": status,
                "mtime": mtime,
                "activity": get_time_ago_category(mtime)
            })
        except Exception as e:
            print(f"Warning: Could not parse {story_file}: {e}", file=sys.stderr)

    return story_files


def find_artifacts(project_root: Path) -> List[Dict[str, Any]]:
    """
    Find common BMAD artifacts (PRD, epics, architecture, tech specs, etc.)
    """
    artifacts = []

    # Common artifact patterns
    artifact_patterns = [
        ("PRD", "**/PRD.md"),
        ("Epics", "**/epics*.md"),
        ("Architecture", "**/architecture.md"),
        ("Tech Spec", "**/tech-spec*.md"),
        ("Game Design", "**/GDD.md"),
        ("Product Brief", "**/product-brief.md"),
        ("Game Brief", "**/game-brief.md"),
        ("Story Context", "**/*context*.xml"),
        ("Sprint Status", "**/sprint-status*.yaml"),
    ]

    for artifact_type, pattern in artifact_patterns:
        for file_path in project_root.glob(pattern):
            if file_path.is_file():
                mtime = get_file_mtime(file_path)

                artifacts.append({
                    "type": artifact_type,
                    "file": str(file_path.relative_to(project_root)),
                    "mtime": mtime,
                    "activity": get_time_ago_category(mtime)
                })

    return artifacts


def infer_next_actions(story: Dict[str, Any], story_file_data: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Infer available next actions based on story state and status.
    """
    state = story.get("state")

    # Get detailed status from story file if available
    status = story_file_data.get("status", "unknown") if story_file_data else "unknown"

    actions = []

    if state == "BACKLOG":
        actions.append("*create-story")
    elif state == "TODO":
        if status in ["draft", "drafted"]:
            actions.append("*story-ready")
        else:
            actions.append("*story-ready")
    elif state == "IN PROGRESS":
        actions.append("*story-context")
        actions.append("*dev-story")
        actions.append("*story-done")
    elif state == "DONE":
        pass  # No actions for completed stories

    return actions


def merge_story_data(status_stories: Dict[str, List], story_files: List[Dict[str, Any]]) -> Dict[str, List]:
    """
    Merge data from workflow status and actual story files.
    """
    # Create lookup by story ID
    file_lookup = {sf["id"]: sf for sf in story_files if sf["id"]}

    merged = {}

    for state, stories in status_stories.items():
        merged[state] = []

        for story in stories:
            story_id = story["id"]

            # Merge with file data if available
            if story_id in file_lookup:
                file_data = file_lookup[story_id]
                merged_story = {
                    **story,
                    "status": file_data["status"],
                    "mtime": file_data["mtime"],
                    "activity": file_data["activity"],
                }
            else:
                merged_story = {
                    **story,
                    "status": "unknown",
                    "mtime": None,
                    "activity": "never",
                }

            # Add next actions
            merged_story["next_actions"] = infer_next_actions(
                merged_story,
                file_lookup.get(story_id)
            )

            merged[state].append(merged_story)

    return merged


def get_bmad_state(project_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main function to get complete BMAD project state.
    """
    # Find project root if not provided
    if project_root is None:
        project_root = find_bmad_project_root()

    if project_root is None:
        return {
            "error": "No BMAD project found (no bmm-workflow-status.md)",
            "project": None,
            "stories": {},
            "artifacts": []
        }

    # Parse workflow status
    status_file = project_root / "bmm-workflow-status.md"
    status_data = parse_workflow_status(status_file)

    # Find all story files
    story_files = find_story_files(project_root)

    # Find artifacts
    artifacts = find_artifacts(project_root)

    # Merge story data
    merged_stories = merge_story_data(status_data.get("stories", {}), story_files)

    return {
        "project_root": str(project_root),
        "project": status_data.get("project", {}),
        "stories": merged_stories,
        "artifacts": artifacts,
        "story_files": story_files,
    }


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Parse BMAD project state")
    parser.add_argument("--path", help="Project root path (default: search from current dir)")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON")

    args = parser.parse_args()

    # Get project root
    project_root = Path(args.path).resolve() if args.path else None

    # Get state
    state = get_bmad_state(project_root)

    # Output JSON
    indent = 2 if args.pretty else None
    print(json.dumps(state, indent=indent, default=str))


if __name__ == "__main__":
    main()
