#!/usr/bin/env python3
"""
BMAD Dashboard V2 - Enhanced with visual navigation and working shortcuts
"""
import argparse
import json
import sys
from pathlib import Path
from typing import List

from bmad_dash import BMADParser, Project, console, health_check
from analytics import DashboardAnalytics
from vision_parser import VisionParser, ProductVision

from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, ScrollableContainer
from textual.widgets import Static, Footer, Header
from textual.binding import Binding
from textual.reactive import reactive


class BreadcrumbPanel(Static):
    """Breadcrumb showing current position in project."""
    
    def __init__(self, analytics: DashboardAnalytics, current_view: str = "overview"):
        super().__init__()
        self.analytics = analytics
        self.current_view = current_view
    
    def update_view(self, view: str):
        """Update the current view."""
        self.current_view = view
    
    def render(self) -> Panel:
        """Render breadcrumb."""
        summary = self.analytics.get_executive_summary()
        
        # Build breadcrumb path
        views = {
            "vision": "🎯 Product Vision",
            "overview": "📊 Overview",
            "summary": "📊 Executive Summary",
            "distribution": "📈 Story Distribution",
            "epics": "🗺️  Epic Map",
            "risks": "⚠️  Risks & Attention",
            "tree": "🌳 Project Tree"
        }
        
        current = views.get(self.current_view, "Overview")
        progress_pct = summary["completion_pct"]
        
        # Create visual progress indicator
        total_steps = 5
        current_step = int(progress_pct / 20)  # 0-5 steps
        progress_visual = "".join([
            "●" if i < current_step else "○" 
            for i in range(total_steps)
        ])
        
        content = f"""[bold cyan]📍 You are here:[/bold cyan] {current}
[dim]Project Progress:[/dim] {progress_visual} {progress_pct:.1f}% complete
[dim]Navigation:[/dim] Press 0-6 to switch views, 'r' to refresh, 'q' to quit"""
        
        return Panel(content, border_style="cyan", padding=(0, 1))


class ProjectTreePanel(Static):
    """Visual tree showing project structure and progress."""
    
    def __init__(self, analytics: DashboardAnalytics):
        super().__init__()
        self.analytics = analytics
    
    def render(self) -> Panel:
        """Render project tree."""
        epics = self.analytics.get_epic_breakdown()
        summary = self.analytics.get_executive_summary()
        
        # Create tree
        tree = Tree(f"[bold]📦 Project Overview[/bold] ({summary['completion_pct']:.1f}% complete)")
        
        for epic in epics:
            # Epic status emoji
            status_emoji = {
                "Complete": "✅",
                "In Progress": "🔄",
                "Active": "📝",
                "Not Started": "⏳"
            }.get(epic["status"], "❓")
            
            # Add epic node
            epic_label = f"{status_emoji} {epic['name']} [{epic['progress_pct']:.0f}%]"
            epic_node = tree.add(epic_label)
            
            # Add story nodes (show first 5)
            for story in epic["stories"][:5]:
                state_emoji = {
                    "Done": "✅",
                    "Review": "👀",
                    "Dev": "💻",
                    "Ready": "📝",
                    "Draft": "📄"
                }.get(story.state, "❓")
                
                # Highlight current story (if in Dev or Review)
                if story.state in ["Dev", "Review"]:
                    story_label = f"[bold yellow]→ {state_emoji} {story.name}[/bold yellow]"
                else:
                    story_label = f"  {state_emoji} {story.name}"
                
                epic_node.add(story_label)
            
            # Show if there are more stories
            if len(epic["stories"]) > 5:
                epic_node.add(f"[dim]... and {len(epic['stories']) - 5} more stories[/dim]")
        
        from rich.console import Console as RichConsole
        from io import StringIO
        
        # Render tree to string
        buffer = StringIO()
        temp_console = RichConsole(file=buffer, force_terminal=True, width=80)
        temp_console.print(tree)
        tree_str = buffer.getvalue()
        
        return Panel(tree_str, title="🌳 Project Tree - You Are Here", border_style="green")


class SequenceDiagramPanel(Static):
    """Sequence diagram showing project flow from start to finish."""
    
    def __init__(self, analytics: DashboardAnalytics):
        super().__init__()
        self.analytics = analytics
    
    def render(self) -> Panel:
        """Render sequence diagram."""
        epics = self.analytics.get_epic_breakdown()
        
        lines = []
        lines.append("[bold]Project Journey:[/bold]")
        lines.append("")
        
        for i, epic in enumerate(epics):
            # Determine position in journey
            if epic["status"] == "Complete":
                marker = "✅"
                connector = "═══"
            elif epic["status"] in ["In Progress", "Active"]:
                marker = "🔄"
                connector = "───"
            else:
                marker = "⏳"
                connector = "···"
            
            # Build the line
            if i == 0:
                line = f"START ═══> {marker} {epic['name']}"
            else:
                line = f"      {connector}> {marker} {epic['name']}"
            
            # Add progress
            line += f" [{epic['progress_pct']:.0f}%]"
            
            # Highlight current epic
            if epic["status"] in ["In Progress", "Active"]:
                line = f"[bold yellow]{line} ← YOU ARE HERE[/bold yellow]"
            
            lines.append(line)
        
        lines.append(f"      ···> 🏁 END")
        
        content = "\n".join(lines)
        return Panel(content, title="🗺️  Project Roadmap", border_style="magenta")


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
            line = f"{status_emoji} [bold]{name:30}[/bold] {bar} {epic['progress_pct']:5.1f}% ({epic['done_stories']}/{epic['total_stories']})"
            
            # Highlight active epics
            if epic["status"] in ["In Progress", "Active"]:
                line = f"[yellow]{line}[/yellow]"
            
            lines.append(line)
        
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


class EnhancedDashboardV2(App):
    """Enhanced BMAD Dashboard V2 with visual navigation."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #breadcrumb {
        height: auto;
    }
    
    #content {
        height: 1fr;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("0", "show_vision", "Vision"),
        Binding("1", "show_overview", "Overview"),
        Binding("2", "show_summary", "Summary"),
        Binding("3", "show_distribution", "Distribution"),
        Binding("4", "show_epics", "Epics"),
        Binding("5", "show_risks", "Risks"),
        Binding("6", "show_tree", "Tree View"),
    ]
    
    # Reactive variable to track current view
    current_view = reactive("overview")
    
    def __init__(self, projects: List[Project]):
        super().__init__()
        self.projects = projects
        self.analytics = DashboardAnalytics(projects)
        # Parse vision from first project
        self.vision = None
        if projects:
            vision_parser = VisionParser(projects[0].path)
            self.vision = vision_parser.parse_vision()
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield Container(id="breadcrumb")
        
        with ScrollableContainer(id="content"):
            yield Container(id="dynamic_content")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Set up the dashboard when app starts."""
        self.update_content()
    
    def watch_current_view(self, new_view: str) -> None:
        """React to view changes."""
        self.update_content()
    
    def update_content(self) -> None:
        """Update the dynamic content based on current view."""
        # Update breadcrumb
        breadcrumb_container = self.query_one("#breadcrumb", Container)
        breadcrumb_container.remove_children()
        breadcrumb = BreadcrumbPanel(self.analytics, self.current_view)
        breadcrumb_container.mount(breadcrumb)
        
        # Update content
        container = self.query_one("#dynamic_content", Container)
        container.remove_children()
        
        # Add content based on current view
        if self.current_view == "vision":
            if self.vision:
                container.mount(ProductVisionPanel(self.vision, self.analytics))
                container.mount(ExecutiveSummaryPanel(self.analytics))
                container.mount(SequenceDiagramPanel(self.analytics))
            else:
                container.mount(Panel("No product vision found. Add docs/product-brief-*.md or docs/epics.md to your repository.", title="🎯 Product Vision"))
        elif self.current_view == "overview":
            container.mount(SequenceDiagramPanel(self.analytics))
            container.mount(ExecutiveSummaryPanel(self.analytics))
            container.mount(EpicMapPanel(self.analytics))
        elif self.current_view == "summary":
            container.mount(ExecutiveSummaryPanel(self.analytics))
            container.mount(StateDistributionPanel(self.analytics))
            container.mount(ActivityPanel(self.analytics))
        elif self.current_view == "distribution":
            container.mount(StateDistributionPanel(self.analytics))
            container.mount(EpicMapPanel(self.analytics))
        elif self.current_view == "epics":
            container.mount(EpicMapPanel(self.analytics))
            container.mount(ProjectTreePanel(self.analytics))
        elif self.current_view == "risks":
            container.mount(RiskPanel(self.analytics))
            container.mount(ActivityPanel(self.analytics))
        elif self.current_view == "tree":
            container.mount(ProjectTreePanel(self.analytics))
            container.mount(SequenceDiagramPanel(self.analytics))
    
    def action_refresh(self):
        """Refresh the dashboard."""
        self.analytics = DashboardAnalytics(self.projects)
        self.update_content()
        self.notify("Dashboard refreshed")
    
    def action_show_overview(self):
        """Show overview."""
        self.current_view = "overview"
        self.notify("Overview")
    
    def action_show_summary(self):
        """Show executive summary."""
        self.current_view = "summary"
        self.notify("Executive Summary")
    
    def action_show_distribution(self):
        """Show story distribution."""
        self.current_view = "distribution"
        self.notify("Story Distribution")
    
    def action_show_epics(self):
        """Show epic map."""
        self.current_view = "epics"
        self.notify("Epic Map")
    
    def action_show_risks(self):
        """Show risks and attention."""
        self.current_view = "risks"
        self.notify("Risks & Attention")
    
    def action_show_tree(self):
        """Show project tree."""
        self.current_view = "tree"
        self.notify("Project Tree")
    
    def action_show_vision(self):
        """Show product vision."""
        self.current_view = "vision"
        self.notify("Product Vision")


def print_executive_summary_static(projects: List[Project]):
    """Print executive summary to console (non-interactive)."""
    from bmad_dash_enhanced import print_executive_summary_static as orig_print
    orig_print(projects)


def main():
    parser = argparse.ArgumentParser(description="BMAD Dashboard V2")
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
    app = EnhancedDashboardV2(projects)
    app.run()


if __name__ == "__main__":
    main()


class ProductVisionPanel(Static):
    """Product vision panel showing strategic context."""
    
    def __init__(self, vision, analytics: DashboardAnalytics):
        super().__init__()
        self.vision = vision
        self.analytics = analytics
    
    def render(self) -> Panel:
        """Render product vision panel."""
        if not self.vision:
            return Panel("No product vision found", title="🎯 Product Vision")
        
        summary = self.analytics.get_executive_summary()
        
        lines = []
        lines.append(f"[bold cyan]📱 {self.vision.project_name}[/bold cyan]")
        lines.append("")
        
        # Goal
        if self.vision.goal:
            lines.append("[bold]Goal:[/bold]")
            lines.append(f"  {self.vision.goal}")
            lines.append("")
        
        # Overall status
        lines.append(f"[bold]Status:[/bold] {summary['completion_pct']:.1f}% complete ({summary['done_stories']}/{summary['total_stories']} stories)")
        lines.append("")
        
        # Milestones
        if self.vision.milestones:
            lines.append("[bold]Key Milestones:[/bold]")
            for milestone in self.vision.milestones[:5]:
                status_emoji = {
                    "Done": "✅",
                    "In Progress": "🔄",
                    "Not Started": "⏳"
                }.get(milestone.status, "❓")
                lines.append(f"  {status_emoji} {milestone.name}")
            lines.append("")
        
        # Success criteria
        if self.vision.success_criteria:
            lines.append("[bold]Success Criteria:[/bold]")
            for criteria in self.vision.success_criteria[:3]:
                lines.append(f"  • {criteria}")
        
        content = "\n".join(lines)
        return Panel(content, title="🎯 Product Vision", border_style="cyan")
