#!/usr/bin/env python3
"""
BMAD Dashboard TUI
Real-time visualization of BMAD project state with activity heatmap and next actions.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Check for rich library
try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.tree import Tree
except ImportError:
    print("Error: 'rich' library not found. Install with: pip install rich", file=sys.stderr)
    sys.exit(1)


class BMADStateError(Exception):
    """Custom exception for BMAD state reader errors."""
    pass


# Color mapping for activity heatmap
ACTIVITY_COLORS = {
    "recent": "bright_red",      # < 1 hour
    "hour": "bright_yellow",     # < 4 hours
    "day": "yellow",             # < 24 hours
    "week": "green",             # < 7 days
    "month": "blue",             # < 30 days
    "old": "dim white",          # Older
    "never": "dim white",        # Never touched
}

ACTIVITY_ICONS = {
    "recent": "🔴",
    "hour": "🟠",
    "day": "🟡",
    "week": "🟢",
    "month": "🔵",
    "old": "⚪",
    "never": "⚪",
}

STATE_ICONS = {
    "BACKLOG": "📋",
    "TODO": "📝",
    "IN PROGRESS": "⚙️",
    "DONE": "✅",
}


def get_state_reader_path() -> Path:
    """Get path to bmad-state-reader.py tool."""
    home = Path.home()
    tool_path = home / ".config" / "claude-code" / "tools" / "bmad-state-reader.py"

    if not tool_path.exists():
        raise FileNotFoundError(f"State reader not found at {tool_path}")

    return tool_path


def read_bmad_state(project_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Call bmad-state-reader.py to get project state.

    Raises:
        BMADStateError: If state reader fails or returns invalid data
        FileNotFoundError: If state reader tool is not found
    """
    tool_path = get_state_reader_path()

    cmd = [str(tool_path)]
    if project_path:
        cmd.extend(["--path", project_path])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        raise BMADStateError(f"Failed to read state: {e.stderr}")
    except json.JSONDecodeError as e:
        raise BMADStateError(f"Invalid JSON from state reader: {e}")
    except Exception as e:
        raise BMADStateError(f"Unexpected error reading state: {e}")


def build_story_tree(stories: Dict[str, List], console: Console) -> Tree:
    """
    Build a rich Tree showing stories organized by state.
    """
    root = Tree("📊 [bold cyan]BMAD Project Stories[/bold cyan]")

    # Process each state
    for state in ["BACKLOG", "TODO", "IN PROGRESS", "DONE"]:
        story_list = stories.get(state, [])

        # State node with count
        state_icon = STATE_ICONS.get(state, "📌")
        count = len(story_list)
        state_label = f"{state_icon} [bold]{state}[/bold] ({count} stories)"

        if count == 0:
            root.add(f"{state_label} [dim]- empty[/dim]")
            continue

        state_node = root.add(state_label)

        # Add each story
        for story in story_list:
            story_id = story.get("id", "?")
            title = story.get("title", "Unknown")
            activity = story.get("activity", "never")
            next_actions = story.get("next_actions", [])

            # Activity indicator
            activity_icon = ACTIVITY_ICONS.get(activity, "⚪")
            color = ACTIVITY_COLORS.get(activity, "white")

            # Story label
            story_label = Text()
            story_label.append(f"[{state}] ", style="dim")
            story_label.append(f"Story {story_id}: {title}", style=f"bold {color}")
            story_label.append(f" {activity_icon}")

            story_node = state_node.add(story_label)

            # Add file info if available
            story_file = story.get("file")
            if story_file:
                file_text = Text()
                file_text.append("📄 ", style="dim")
                file_text.append(story_file, style=f"{color}")
                story_node.add(file_text)

            # Add next actions
            if next_actions:
                actions_text = Text()
                actions_text.append("▶ ", style="bright_cyan")
                actions_text.append(", ".join(next_actions), style="cyan")
                story_node.add(actions_text)

    return root


def build_artifacts_tree(artifacts: List[Dict], console: Console) -> Tree:
    """
    Build a rich Tree showing generated artifacts.
    """
    root = Tree("📚 [bold cyan]Generated Artifacts[/bold cyan]")

    if not artifacts:
        root.add("[dim]No artifacts found[/dim]")
        return root

    # Group by type
    by_type: Dict[str, List] = {}
    for artifact in artifacts:
        artifact_type = artifact.get("type", "Unknown")
        if artifact_type not in by_type:
            by_type[artifact_type] = []
        by_type[artifact_type].append(artifact)

    # Add each type
    for artifact_type, items in sorted(by_type.items()):
        type_node = root.add(f"[bold]{artifact_type}[/bold] ({len(items)})")

        for item in items:
            file_path = item.get("file", "?")
            activity = item.get("activity", "never")
            activity_icon = ACTIVITY_ICONS.get(activity, "⚪")
            color = ACTIVITY_COLORS.get(activity, "white")

            file_text = Text()
            file_text.append("📄 ", style="dim")
            file_text.append(file_path, style=color)
            file_text.append(f" {activity_icon}")

            type_node.add(file_text)

    return root


def build_header_panel(project: Dict[str, Any]) -> Panel:
    """
    Build header panel with project info.
    """
    if not project:
        return Panel(
            "[bold red]No BMAD Project Detected[/bold red]\n"
            "Navigate to a BMAD project directory or specify path.",
            title="BMAD Dashboard",
            border_style="red"
        )

    name = project.get("name", "Unknown Project")
    level = project.get("level", "?")
    phase = project.get("current_phase", "?")
    next_action = project.get("next_action", "N/A")

    header = Table.grid(padding=(0, 2))
    header.add_column(justify="left", style="bold")
    header.add_column(justify="left")

    header.add_row("Project:", f"[cyan]{name}[/cyan]")
    header.add_row("Level:", f"[yellow]{level}[/yellow]")
    header.add_row("Phase:", f"[green]{phase}[/green]")
    header.add_row("Next Action:", f"[bright_cyan]{next_action}[/bright_cyan]")

    return Panel(
        header,
        title="[bold]BMAD Project Dashboard[/bold]",
        border_style="cyan",
        padding=(1, 2)
    )


def build_legend_panel() -> Panel:
    """
    Build legend panel explaining colors and icons.
    """
    legend = Table.grid(padding=(0, 1))
    legend.add_column(justify="left")
    legend.add_column(justify="left", style="dim")

    legend.add_row("🔴 Recent", "< 1 hour")
    legend.add_row("🟠 Active", "< 4 hours")
    legend.add_row("🟡 Today", "< 24 hours")
    legend.add_row("🟢 This Week", "< 7 days")
    legend.add_row("🔵 This Month", "< 30 days")
    legend.add_row("⚪ Old", "> 30 days")

    return Panel(legend, title="Activity Heatmap", border_style="dim")


def build_dashboard(state: Dict[str, Any], console: Console) -> Layout:
    """
    Build the complete dashboard layout.
    """
    # Check for error
    if "error" in state:
        error_panel = Panel(
            f"[bold red]Error:[/bold red] {state['error']}",
            border_style="red"
        )
        layout = Layout()
        layout.update(error_panel)
        return layout

    # Extract data
    project = state.get("project", {})
    stories = state.get("stories", {})
    artifacts = state.get("artifacts", [])

    # Build components
    header = build_header_panel(project)
    story_tree = build_story_tree(stories, console)
    artifacts_tree = build_artifacts_tree(artifacts, console)
    legend = build_legend_panel()

    # Build layout
    layout = Layout()
    layout.split_column(
        Layout(header, size=8, name="header"),
        Layout(name="main"),
        Layout(legend, size=9, name="legend")
    )

    # Split main into stories and artifacts
    layout["main"].split_row(
        Layout(Panel(story_tree, border_style="green"), name="stories"),
        Layout(Panel(artifacts_tree, border_style="blue"), name="artifacts")
    )

    return layout


def check_trigger_file(trigger_path: Path, last_check: float) -> bool:
    """
    Check if trigger file has been modified since last check.
    """
    if not trigger_path.exists():
        return False

    try:
        mtime = trigger_path.stat().st_mtime
        return mtime > last_check
    except OSError:
        return False


def run_dashboard(project_path: Optional[str] = None, poll_interval: float = 1.0):
    """
    Main dashboard loop with live updates.
    """
    console = Console()
    # Use cross-platform temporary directory
    trigger_path = Path(tempfile.gettempdir()) / "bmad-dashboard-trigger"

    # Create trigger file if it doesn't exist
    trigger_path.touch(exist_ok=True)
    last_trigger_check = time.time()

    # Initial state load with error handling
    try:
        state = read_bmad_state(project_path)
    except FileNotFoundError as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        console.print("\n[yellow]State reader tool not found.[/yellow]")
        console.print("Please install the BMAD Dashboard:")
        console.print("  cd bmad-dashboard && ./install.sh")
        return
    except BMADStateError as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        return

    with Live(build_dashboard(state, console), console=console, refresh_per_second=1) as live:
        try:
            while True:
                time.sleep(poll_interval)

                # Check if we should refresh
                current_time = time.time()
                should_refresh = check_trigger_file(trigger_path, last_trigger_check)

                if should_refresh:
                    try:
                        # Reload state
                        state = read_bmad_state(project_path)
                        # Update display
                        live.update(build_dashboard(state, console))
                    except (BMADStateError, FileNotFoundError):
                        # Continue with last known state on errors during refresh
                        pass

                    # Update last check time
                    last_trigger_check = current_time

        except KeyboardInterrupt:
            console.print("\n[yellow]Dashboard stopped by user[/yellow]")


def print_static_summary(project_path: Optional[str] = None):
    """
    Print a static summary of project state (non-live mode).
    """
    console = Console()

    console.print("\n[bold cyan]BMAD Project Summary[/bold cyan]\n")

    try:
        state = read_bmad_state(project_path)
    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        console.print("\n[yellow]State reader tool not found.[/yellow]")
        console.print("Please install the BMAD Dashboard:")
        console.print("  cd bmad-dashboard && ./install.sh")
        return
    except BMADStateError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return

    # Project info
    project = state.get("project", {})
    console.print(f"[bold]Project:[/bold] {project.get('name', 'Unknown')}")
    console.print(f"[bold]Level:[/bold] {project.get('level', '?')}")
    console.print(f"[bold]Phase:[/bold] {project.get('current_phase', '?')}")
    console.print(f"[bold]Next Action:[/bold] {project.get('next_action', 'N/A')}\n")

    # Story counts
    stories = state.get("stories", {})
    console.print("[bold]Story Status:[/bold]")
    for state_name in ["BACKLOG", "TODO", "IN PROGRESS", "DONE"]:
        count = len(stories.get(state_name, []))
        icon = STATE_ICONS.get(state_name, "📌")
        console.print(f"  {icon} {state_name}: {count}")

    console.print()


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="BMAD Dashboard - Real-time project visualization"
    )
    parser.add_argument(
        "--path",
        help="Project root path (default: search from current dir)"
    )
    parser.add_argument(
        "--poll",
        type=float,
        default=1.0,
        help="Polling interval in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print static summary instead of live dashboard"
    )

    args = parser.parse_args()

    if args.summary:
        print_static_summary(args.path)
    else:
        run_dashboard(args.path, args.poll)


if __name__ == "__main__":
    main()
