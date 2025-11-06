#!/usr/bin/env python3
"""
BMAD Dashboard Enhanced - Executive view with multi-resolution big picture
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import List

# Import from existing modules
from bmad_dash import (
    BMADParser, Project, console, health_check
)
from analytics import DashboardAnalytics

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Footer, Header
from textual.binding import Binding


class ExecutiveSummaryPanel(Static):
    """Executive summary panel showing key metrics."""
    
    def __init__(self, analytics: DashboardAnalytics):
        super().__init__()
        self.analytics = analytics
    
    def render(self) -> Panel:
        """Render the executive summary."""
        summary = self.analytics.get_executive_summary()
        
        # Progress bar
        progress_bar = "█" * int(summary["completion_pct"] / 5) + "░" * (20 - int(summary["completion_pct"] / 5))
        
        # Health indicator
        health_emoji = {
            "HEALTHY": "✅",
            "WARNING": "⚠️",
            "CRITICAL": "🚨"
        }.get(summary["health_status"], "❓")
        
        content = f"""[bold]Progress:[/bold] {progress_bar} {summary['completion_pct']:.1f}% ({summary['done_stories']}/{summary['total_stories']} stories)
[bold]Velocity:[/bold] {summary['velocity']} stories/week  │  [bold]ETA:[/bold] ~{summary['eta_weeks']:.1f} weeks remaining
[bold]Health:[/bold] {health_emoji} {summary['health_status']} - {summary['stale_count']} stale stories, {summary['missing_artifacts_count']} missing artifacts"""
        
        return Panel(content, title="📊 Executive Summary", border_style="cyan")


class StateDistributionPanel(Static):
    """Story state distribution panel."""
    
    def __init__(self, analytics: DashboardAnalytics):
        super().__init__()
        self.analytics = analytics
    
    def render(self) -> Panel:
        """Render state distribution."""
        dist = self.analytics.get_state_distribution()
        total = sum(dist.values())
        
        if total == 0:
            return Panel("No stories found", title="📈 Story Distribution")
        
        lines = []
        for state in ["Done", "Review", "Dev", "Ready", "Draft"]:
            count = dist.get(state, 0)
            pct = (count / total * 100) if total > 0 else 0
            bar_len = int(pct / 5)  # Scale to 20 chars max
            bar = "█" * bar_len + "░" * (20 - bar_len)
            lines.append(f"[bold]{state:10}[/bold] {bar} {count:2} ({pct:5.1f}%)")
        
        content = "\n".join(lines)
        return Panel(content, title="📈 Story Distribution", border_style="green")


class EpicMapPanel(Static):
    """Epic/Feature map showing big picture."""
    
    def __init__(self, analytics: DashboardAnalytics):
        super().__init__()
        self.analytics = analytics
    
    def render(self) -> Panel:
        """Render epic map."""
        epics = self.analytics.get_epic_breakdown()
        
        if not epics:
            return Panel("No epics found", title="🗺️  Epic Map")
        
        lines = []
        for epic in epics[:10]:  # Show top 10 epics
            # Status emoji
            status_emoji = {
                "Complete": "✅",
                "In Progress": "🔄",
                "Active": "📝",
                "Not Started": "⏳"
            }.get(epic["status"], "❓")
            
            # Progress bar
            bar_len = int(epic["progress_pct"] / 5)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            
            name = epic["name"][:30]  # Truncate long names
            lines.append(f"{status_emoji} [bold]{name:30}[/bold] {bar} {epic['progress_pct']:5.1f}% ({epic['done_stories']}/{epic['total_stories']})")
        
        content = "\n".join(lines)
        return Panel(content, title="🗺️  Epic Map - Big Picture", border_style="magenta")


class RiskPanel(Static):
    """Risk and attention panel."""
    
    def __init__(self, analytics: DashboardAnalytics):
        super().__init__()
        self.analytics = analytics
    
    def render(self) -> Panel:
        """Render risk panel."""
        risks = self.analytics.get_risks_and_attention()
        
        lines = []
        
        # Stale stories
        stale = risks["stale_stories"][:5]  # Top 5
        if stale:
            lines.append("[bold red]🚨 STALE (>7 days, not Done):[/bold red]")
            for item in stale:
                story = item["story"]
                lines.append(f"  • {story.name} ({story.state}, {item['days_old']} days old)")
            lines.append("")
        
        # Missing artifacts
        missing = risks["missing_artifacts_summary"]
        if missing:
            lines.append("[bold yellow]⚠️  MISSING ARTIFACTS:[/bold yellow]")
            for artifact, count in list(missing.items())[:3]:
                lines.append(f"  • {count} missing {artifact}")
            lines.append("")
        
        # Recommendations
        if risks["recommendations"]:
            lines.append("[bold green]💡 RECOMMENDATIONS:[/bold green]")
            for rec in risks["recommendations"][:3]:
                lines.append(f"  • {rec}")
        
        content = "\n".join(lines) if lines else "No issues detected"
        return Panel(content, title="⚠️  Needs Attention", border_style="yellow")


class ActivityPanel(Static):
    """Recent activity panel."""
    
    def __init__(self, analytics: DashboardAnalytics):
        super().__init__()
        self.analytics = analytics
    
    def render(self) -> Panel:
        """Render activity panel."""
        recent = self.analytics.get_recent_activity(days=7)
        
        if not recent:
            return Panel("No recent activity", title="📅 Recent Activity")
        
        lines = ["[bold]📅 Last 7 Days:[/bold]"]
        for item in recent[:5]:  # Top 5
            story = item["story"]
            days_text = "today" if item["days_ago"] == 0 else f"{item['days_ago']}d ago"
            lines.append(f"  {days_text:8} {story.name} ({story.state})")
        
        content = "\n".join(lines)
        return Panel(content, title="📅 Recent Activity", border_style="blue")


class EnhancedDashboard(App):
    """Enhanced BMAD Dashboard with executive views."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #summary_container {
        height: auto;
        padding: 1;
    }
    
    #panels_container {
        height: 1fr;
    }
    
    .panel_row {
        height: auto;
        layout: horizontal;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("1", "show_summary", "Summary"),
        Binding("2", "show_distribution", "Distribution"),
        Binding("3", "show_epics", "Epics"),
        Binding("4", "show_risks", "Risks"),
        Binding("5", "show_activity", "Activity"),
        Binding("t", "toggle_view", "Toggle View"),
    ]
    
    def __init__(self, projects: List[Project]):
        super().__init__()
        self.projects = projects
        self.analytics = DashboardAnalytics(projects)
        self.current_view = "dashboard"
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        
        with ScrollableContainer(id="panels_container"):
            yield ExecutiveSummaryPanel(self.analytics)
            yield Horizontal(
                StateDistributionPanel(self.analytics),
                ActivityPanel(self.analytics),
                classes="panel_row"
            )
            yield EpicMapPanel(self.analytics)
            yield RiskPanel(self.analytics)
        
        yield Footer()
    
    def action_refresh(self):
        """Refresh the dashboard."""
        # Reparse projects
        self.analytics = DashboardAnalytics(self.projects)
        self.refresh()
        self.notify("Dashboard refreshed")
    
    def action_show_summary(self):
        """Show executive summary."""
        self.notify("Executive Summary view")
    
    def action_show_distribution(self):
        """Show story distribution."""
        self.notify("Story Distribution view")
    
    def action_show_epics(self):
        """Show epic map."""
        self.notify("Epic Map view")
    
    def action_show_risks(self):
        """Show risks and attention."""
        self.notify("Risks & Attention view")
    
    def action_show_activity(self):
        """Show recent activity."""
        self.notify("Recent Activity view")
    
    def action_toggle_view(self):
        """Toggle between dashboard and table views."""
        self.notify("Toggle view (table view not yet implemented)")


def print_executive_summary_static(projects: List[Project]):
    """Print executive summary to console (non-interactive)."""
    analytics = DashboardAnalytics(projects)
    
    console = Console()
    
    # Executive Summary
    summary = analytics.get_executive_summary()
    progress_bar = "█" * int(summary["completion_pct"] / 5) + "░" * (20 - int(summary["completion_pct"] / 5))
    health_emoji = {"HEALTHY": "✅", "WARNING": "⚠️", "CRITICAL": "🚨"}.get(summary["health_status"], "❓")
    
    summary_content = f"""[bold]Progress:[/bold] {progress_bar} {summary['completion_pct']:.1f}% ({summary['done_stories']}/{summary['total_stories']} stories)
[bold]Velocity:[/bold] {summary['velocity']} stories/week  │  [bold]ETA:[/bold] ~{summary['eta_weeks']:.1f} weeks remaining
[bold]Health:[/bold] {health_emoji} {summary['health_status']} - {summary['stale_count']} stale stories, {summary['missing_artifacts_count']} missing artifacts"""
    
    console.print(Panel(summary_content, title="📊 Executive Summary", border_style="cyan"))
    console.print()
    
    # Epic Map
    epics = analytics.get_epic_breakdown()
    epic_lines = []
    for epic in epics[:10]:
        status_emoji = {"Complete": "✅", "In Progress": "🔄", "Active": "📝", "Not Started": "⏳"}.get(epic["status"], "❓")
        bar_len = int(epic["progress_pct"] / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        name = epic["name"][:30]
        epic_lines.append(f"{status_emoji} [bold]{name:30}[/bold] {bar} {epic['progress_pct']:5.1f}% ({epic['done_stories']}/{epic['total_stories']})")
    
    console.print(Panel("\n".join(epic_lines), title="🗺️  Epic Map - Big Picture", border_style="magenta"))
    console.print()
    
    # Risks
    risks = analytics.get_risks_and_attention()
    risk_lines = []
    
    stale = risks["stale_stories"][:5]
    if stale:
        risk_lines.append("[bold red]🚨 STALE (>7 days, not Done):[/bold red]")
        for item in stale:
            story = item["story"]
            risk_lines.append(f"  • {story.name} ({story.state}, {item['days_old']} days old)")
        risk_lines.append("")
    
    if risks["recommendations"]:
        risk_lines.append("[bold green]💡 RECOMMENDATIONS:[/bold green]")
        for rec in risks["recommendations"][:3]:
            risk_lines.append(f"  • {rec}")
    
    console.print(Panel("\n".join(risk_lines) if risk_lines else "No issues detected", 
                       title="⚠️  Needs Attention", border_style="yellow"))


def main():
    parser = argparse.ArgumentParser(description="BMAD Dashboard Enhanced")
    parser.add_argument("command", nargs="?", choices=["check"], help="Command to run")
    parser.add_argument("--repos", nargs="+", required=True, help="Repository paths")
    parser.add_argument("--summary", action="store_true", help="Print summary and exit")
    
    args = parser.parse_args()
    
    # Parse repositories
    bmad_parser = BMADParser(args.repos)
    projects = bmad_parser.parse_all()
    
    if not projects:
        console.print("[red]No BMAD projects found in specified repositories[/red]")
        sys.exit(1)
    
    # Handle commands
    if args.command == "check":
        report = health_check(projects)
        print(json.dumps(report, indent=2, default=str))
        sys.exit(0)
    
    if args.summary:
        print_executive_summary_static(projects)
        sys.exit(0)
    
    # Run interactive dashboard
    app = EnhancedDashboard(projects)
    app.run()


if __name__ == "__main__":
    main()
