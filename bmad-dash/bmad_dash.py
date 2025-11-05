#!/usr/bin/env python3
"""
BMAD Dashboard - Terminal-based MVP for managing BMAD projects.
Single-file implementation with Rich/Textual TUI.
"""
import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Set

import yaml
from git import Repo, InvalidGitRepositoryError
from rich.console import Console
from rich.table import Table
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import DataTable, Footer, Header, Static
from textual.binding import Binding
from textual.screen import Screen

console = Console()

# State machine transitions
STATE_TRANSITIONS = {
    "Draft": ["Ready"],
    "Ready": ["Dev", "Draft"],
    "Dev": ["Review", "Ready"],
    "Review": ["Done", "Dev"],
    "Done": []
}

STATE_COLORS = {
    "Draft": "yellow",
    "Ready": "cyan",
    "Dev": "blue",
    "Review": "magenta",
    "Done": "green"
}


@dataclass
class Story:
    """Represents a single story in BMAD."""
    project: str
    feature: str
    name: str
    state: str
    path: Path
    state_file: Optional[Path] = None
    last_commit_sha: str = ""
    last_commit_time: Optional[datetime] = None
    owner: str = ""
    missing_artifacts: List[str] = field(default_factory=list)
    prd_title: str = ""
    acceptance_criteria: str = ""
    log_lines: List[str] = field(default_factory=list)


@dataclass
class Feature:
    """Represents a feature containing stories."""
    name: str
    path: Path
    stories: List[Story] = field(default_factory=list)


@dataclass
class Project:
    """Represents a BMAD project repository."""
    name: str
    path: Path
    features: List[Feature] = field(default_factory=list)


class BMADParser:
    """Parses BMAD repository structure and extracts project data."""
    
    def __init__(self, repo_paths: List[str]):
        self.repo_paths = [Path(p).expanduser().resolve() for p in repo_paths]
        self.projects: List[Project] = []
    
    def parse_all(self) -> List[Project]:
        """Parse all repositories and return project data."""
        for repo_path in self.repo_paths:
            if not repo_path.exists():
                console.print(f"[red]Warning: {repo_path} does not exist[/red]")
                continue
            
            project = self._parse_repo(repo_path)
            if project:
                self.projects.append(project)
        
        return self.projects
    
    def _parse_repo(self, repo_path: Path) -> Optional[Project]:
        """Parse a single repository."""
        project_name = repo_path.name
        project = Project(name=project_name, path=repo_path)
        
        # Find all feature directories
        feature_paths = self._find_features(repo_path)
        
        for feature_path in feature_paths:
            feature = self._parse_feature(project_name, feature_path, repo_path)
            if feature and feature.stories:
                project.features.append(feature)
        
        return project if project.features else None
    
    def _find_features(self, base_path: Path) -> List[Path]:
        """Find all feature directories."""
        features = []
        
        # Look for features/* pattern
        features_dir = base_path / "features"
        if features_dir.exists() and features_dir.is_dir():
            for item in features_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    features.append(item)
        
        return features
    
    def _parse_feature(self, project_name: str, feature_path: Path, repo_path: Path) -> Optional[Feature]:
        """Parse a single feature directory."""
        feature_name = feature_path.name
        feature = Feature(name=feature_name, path=feature_path)
        
        # Look for stories directory
        stories_dir = feature_path / "stories"
        if stories_dir.exists():
            for story_dir in stories_dir.iterdir():
                if story_dir.is_dir() and not story_dir.name.startswith('.'):
                    story = self._parse_story(project_name, feature_name, story_dir, repo_path)
                    if story:
                        feature.stories.append(story)
        
        return feature if feature.stories else None
    
    def _parse_story(self, project_name: str, feature_name: str, story_path: Path, repo_path: Path) -> Optional[Story]:
        """Parse a single story directory."""
        story_name = story_path.name
        
        # Parse state.yaml
        state_file = story_path / "state.yaml"
        state = "Draft"
        owner = ""
        
        if state_file.exists():
            try:
                with open(state_file) as f:
                    state_data = yaml.safe_load(f)
                    if state_data:
                        state = state_data.get("state", "Draft")
                        owner = state_data.get("owner", "")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not parse {state_file}: {e}[/yellow]")
        
        story = Story(
            project=project_name,
            feature=feature_name,
            name=story_name,
            state=state,
            path=story_path,
            state_file=state_file if state_file.exists() else None,
            owner=owner
        )
        
        # Check for missing artifacts
        story.missing_artifacts = self._check_artifacts(story_path)
        
        # Parse PRD
        prd_file = story_path / "PRD.md"
        if prd_file.exists():
            story.prd_title, story.acceptance_criteria = self._parse_prd(prd_file)
        
        # Get Git info
        try:
            repo = Repo(repo_path)
            commits = list(repo.iter_commits(paths=str(story_path.relative_to(repo_path)), max_count=1))
            if commits:
                story.last_commit_sha = commits[0].hexsha[:7]
                story.last_commit_time = datetime.fromtimestamp(commits[0].committed_date)
        except (InvalidGitRepositoryError, Exception):
            pass
        
        # Get last log lines
        log_file = story_path / "logs" / "latest.log"
        if log_file.exists():
            try:
                with open(log_file) as f:
                    story.log_lines = f.readlines()[-5:]
            except Exception:
                pass
        
        return story
    
    def _check_artifacts(self, story_path: Path) -> List[str]:
        """Check for missing artifacts."""
        missing = []
        
        required_files = {
            "PRD.md": "PRD",
            "design.md": "design",
        }
        
        for filename, label in required_files.items():
            if not (story_path / filename).exists():
                missing.append(label)
        
        # Check for logs directory
        if not (story_path / "logs").exists():
            missing.append("logs")
        
        # Check for tests
        code_dir = story_path / "code"
        if code_dir.exists():
            has_tests = any(
                f.name.startswith("test_") or f.name.endswith("_test.py")
                for f in code_dir.rglob("*.py")
            )
            if not has_tests:
                missing.append("tests")
        
        return missing
    
    def _parse_prd(self, prd_file: Path) -> tuple[str, str]:
        """Parse PRD file for title and acceptance criteria."""
        title = ""
        criteria = ""
        
        try:
            with open(prd_file) as f:
                content = f.read()
                
                # Extract title (first # heading)
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                if title_match:
                    title = title_match.group(1).strip()
                
                # Extract acceptance criteria section
                ac_match = re.search(
                    r'##\s+Acceptance\s+Criteria\s*\n(.*?)(?=\n##|\Z)',
                    content,
                    re.IGNORECASE | re.DOTALL
                )
                if ac_match:
                    criteria = ac_match.group(1).strip()[:200]  # First 200 chars
        except Exception:
            pass
        
        return title, criteria


class BMADDashboard(App):
    """Textual TUI application for BMAD dashboard."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    DataTable {
        height: 1fr;
    }
    
    #detail {
        height: 10;
        background: $panel;
        border: solid $primary;
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("enter", "show_detail", "Detail"),
        Binding("s", "set_state", "Set State"),
        Binding("o", "open_file", "Open"),
        Binding("l", "tail_logs", "Logs"),
        Binding("/", "search", "Search"),
    ]
    
    def __init__(self, projects: List[Project]):
        super().__init__()
        self.projects = projects
        self.stories: List[Story] = []
        self.selected_story: Optional[Story] = None
        self._flatten_stories()
    
    def _flatten_stories(self):
        """Flatten project structure into list of stories."""
        self.stories = []
        for project in self.projects:
            for feature in project.features:
                for story in feature.stories:
                    self.stories.append(story)
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield DataTable(id="stories_table")
        yield Static("", id="detail")
        yield Footer()
    
    def on_mount(self) -> None:
        """Set up the table when app starts."""
        table = self.query_one("#stories_table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True
        
        # Add columns
        table.add_column("Project", width=15)
        table.add_column("Feature", width=20)
        table.add_column("Story", width=25)
        table.add_column("State", width=10)
        table.add_column("SHA", width=8)
        table.add_column("Updated", width=12)
        table.add_column("Owner", width=12)
        table.add_column("Missing", width=20)
        
        self._populate_table()
    
    def _populate_table(self):
        """Populate the table with story data."""
        table = self.query_one("#stories_table", DataTable)
        table.clear()
        
        for story in self.stories:
            # Calculate time ago
            time_ago = ""
            if story.last_commit_time:
                delta = datetime.now() - story.last_commit_time
                if delta.days > 0:
                    time_ago = f"{delta.days}d ago"
                elif delta.seconds > 3600:
                    time_ago = f"{delta.seconds // 3600}h ago"
                else:
                    time_ago = f"{delta.seconds // 60}m ago"
            
            # Format missing artifacts
            missing = ", ".join(story.missing_artifacts) if story.missing_artifacts else "✓"
            
            # Add row with color coding
            state_color = STATE_COLORS.get(story.state, "white")
            table.add_row(
                story.project,
                story.feature,
                story.name,
                f"[{state_color}]{story.state}[/{state_color}]",
                story.last_commit_sha,
                time_ago,
                story.owner,
                missing,
                key=str(id(story))
            )
    
    def action_refresh(self):
        """Refresh the dashboard data."""
        # Re-parse projects
        parser = BMADParser([str(p.path) for p in self.projects])
        self.projects = parser.parse_all()
        self._flatten_stories()
        self._populate_table()
        self.notify("Dashboard refreshed")
    
    def action_show_detail(self):
        """Show detail pane for selected story."""
        table = self.query_one("#stories_table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self.stories):
            story = self.stories[table.cursor_row]
            self.selected_story = story
            
            detail_text = f"[bold]{story.prd_title or story.name}[/bold]\n\n"
            
            if story.acceptance_criteria:
                detail_text += f"[cyan]Acceptance Criteria:[/cyan]\n{story.acceptance_criteria}\n\n"
            
            if story.log_lines:
                detail_text += f"[yellow]Last 5 log lines:[/yellow]\n"
                detail_text += "".join(story.log_lines)
            
            detail = self.query_one("#detail", Static)
            detail.update(detail_text)
    
    def action_set_state(self):
        """Set state for selected story."""
        table = self.query_one("#stories_table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self.stories):
            story = self.stories[table.cursor_row]
            self.selected_story = story
            
            valid_transitions = STATE_TRANSITIONS.get(story.state, [])
            if valid_transitions:
                self.notify(f"Valid transitions from {story.state}: {', '.join(valid_transitions)}")
                # In a full implementation, would show a modal to select new state
                # For MVP, just show what's possible
            else:
                self.notify("No valid transitions from Done state")
    
    def action_open_file(self):
        """Open story file in editor."""
        table = self.query_one("#stories_table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self.stories):
            story = self.stories[table.cursor_row]
            self.selected_story = story
            
            editor = os.environ.get("EDITOR", "vim")
            prd_file = story.path / "PRD.md"
            if prd_file.exists():
                self.notify(f"To open: {editor} {prd_file}")
            else:
                self.notify(f"PRD.md not found for {story.name}")
    
    def action_tail_logs(self):
        """Tail live logs."""
        table = self.query_one("#stories_table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self.stories):
            story = self.stories[table.cursor_row]
            self.selected_story = story
            
            log_file = story.path / "logs" / "latest.log"
            if log_file.exists():
                self.notify(f"To tail: tail -f {log_file}")
            else:
                self.notify(f"No logs found for {story.name}")
    
    def action_search(self):
        """Search/filter stories."""
        self.notify("Search feature - type to filter")


def health_check(projects: List[Project]) -> Dict:
    """Run health check and return JSON report."""
    report = {
        "stale_stories": [],
        "missing_artifacts": [],
        "missing_pr_links": []
    }
    
    for project in projects:
        for feature in project.features:
            for story in feature.stories:
                # Check for stale stories (no commit in 7+ days)
                if story.last_commit_time:
                    days_old = (datetime.now() - story.last_commit_time).days
                    if days_old > 7 and story.state not in ["Done"]:
                        report["stale_stories"].append({
                            "project": story.project,
                            "feature": story.feature,
                            "story": story.name,
                            "days_old": days_old
                        })
                
                # Check for missing artifacts
                if story.missing_artifacts:
                    report["missing_artifacts"].append({
                        "project": story.project,
                        "feature": story.feature,
                        "story": story.name,
                        "missing": story.missing_artifacts
                    })
    
    return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="BMAD Dashboard - Manage BMAD projects")
    parser.add_argument(
        "--repos",
        nargs="+",
        help="Repository paths to scan"
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["check"],
        help="Command to run (optional)"
    )
    
    args = parser.parse_args()
    
    # Get repo paths from args or environment
    repo_paths = args.repos or os.environ.get("BMAD_REPOS", "").split()
    
    if not repo_paths:
        console.print("[red]Error: No repositories specified. Use --repos or set BMAD_REPOS[/red]")
        sys.exit(1)
    
    # Parse projects
    bmad_parser = BMADParser(repo_paths)
    projects = bmad_parser.parse_all()
    
    if not projects:
        console.print("[yellow]No BMAD projects found in specified repositories[/yellow]")
        sys.exit(0)
    
    # Run command or start TUI
    if args.command == "check":
        report = health_check(projects)
        print(json.dumps(report, indent=2))
    else:
        app = BMADDashboard(projects)
        app.run()


if __name__ == "__main__":
    main()
