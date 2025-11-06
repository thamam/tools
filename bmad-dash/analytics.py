"""
Analytics module for BMAD Dashboard
Calculates metrics, velocity, and insights from project data
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
import re


class DashboardAnalytics:
    """Calculate executive metrics and insights from BMAD project data."""
    
    def __init__(self, projects: List):
        """Initialize with list of Project objects."""
        self.projects = projects
        self.all_stories = []
        
        # Flatten all stories from all projects
        for project in projects:
            for feature in project.features:
                for story in feature.stories:
                    story.project_name = project.name
                    story.feature_name = feature.name
                    self.all_stories.append(story)
    
    def get_executive_summary(self) -> Dict:
        """Get high-level executive summary metrics."""
        total_stories = len(self.all_stories)
        done_stories = len([s for s in self.all_stories if s.state == "Done"])
        
        completion_pct = (done_stories / total_stories * 100) if total_stories > 0 else 0
        
        # Calculate velocity (stories per week)
        velocity = self._calculate_velocity()
        
        # Estimate remaining time
        remaining_stories = total_stories - done_stories
        eta_weeks = (remaining_stories / velocity) if velocity > 0 else 0
        
        # Health indicators
        stale_count = len(self._get_stale_stories())
        missing_artifacts_count = sum(len(s.missing_artifacts) for s in self.all_stories)
        
        health_status = "HEALTHY"
        if stale_count > 5 or missing_artifacts_count > 20:
            health_status = "WARNING"
        if stale_count > 10 or missing_artifacts_count > 40:
            health_status = "CRITICAL"
        
        return {
            "total_stories": total_stories,
            "done_stories": done_stories,
            "completion_pct": completion_pct,
            "velocity": velocity,
            "eta_weeks": eta_weeks,
            "health_status": health_status,
            "stale_count": stale_count,
            "missing_artifacts_count": missing_artifacts_count
        }
    
    def get_state_distribution(self) -> Dict[str, int]:
        """Get count of stories in each state."""
        distribution = defaultdict(int)
        for story in self.all_stories:
            distribution[story.state] += 1
        return dict(distribution)
    
    def get_epic_breakdown(self) -> List[Dict]:
        """Group stories by epic and calculate progress."""
        epics = defaultdict(list)
        
        for story in self.all_stories:
            epic_name = self._extract_epic_name(story.name)
            epics[epic_name].append(story)
        
        epic_list = []
        for epic_name, stories in epics.items():
            total = len(stories)
            done = len([s for s in stories if s.state == "Done"])
            progress_pct = (done / total * 100) if total > 0 else 0
            
            # Determine status
            if done == total:
                status = "Complete"
            elif done > 0:
                status = "In Progress"
            elif any(s.state in ["Ready", "Dev", "Review"] for s in stories):
                status = "Active"
            else:
                status = "Not Started"
            
            epic_list.append({
                "name": epic_name,
                "total_stories": total,
                "done_stories": done,
                "progress_pct": progress_pct,
                "status": status,
                "stories": stories
            })
        
        # Sort by progress (in-progress first, then not started)
        epic_list.sort(key=lambda x: (x["status"] == "Complete", -x["progress_pct"]))
        
        return epic_list
    
    def get_risks_and_attention(self) -> Dict:
        """Identify stories and issues that need attention."""
        stale_stories = self._get_stale_stories()
        
        # Group missing artifacts
        missing_artifacts_summary = defaultdict(int)
        for story in self.all_stories:
            for artifact in story.missing_artifacts:
                missing_artifacts_summary[artifact] += 1
        
        # Generate recommendations
        recommendations = []
        if len(stale_stories) > 0:
            recommendations.append(f"Move {len(stale_stories)} stale stories to active development")
        if missing_artifacts_summary.get("context", 0) > 5:
            recommendations.append(f"Add context files for {missing_artifacts_summary['context']} stories")
        if missing_artifacts_summary.get("tests", 0) > 5:
            recommendations.append(f"Add tests for {missing_artifacts_summary['tests']} stories")
        
        # Identify bottlenecks
        state_dist = self.get_state_distribution()
        if state_dist.get("Draft", 0) > state_dist.get("Done", 0):
            recommendations.append("Too many stories in Draft - focus on moving to Ready/Dev")
        
        return {
            "stale_stories": stale_stories,
            "missing_artifacts_summary": dict(missing_artifacts_summary),
            "recommendations": recommendations
        }
    
    def get_recent_activity(self, days: int = 7) -> List[Dict]:
        """Get recent story updates."""
        cutoff = datetime.now() - timedelta(days=days)
        recent = []
        
        for story in self.all_stories:
            if story.last_commit_time and story.last_commit_time >= cutoff:
                recent.append({
                    "story": story,
                    "days_ago": (datetime.now() - story.last_commit_time).days,
                    "commit_sha": story.last_commit_sha
                })
        
        # Sort by most recent first
        recent.sort(key=lambda x: x["days_ago"])
        
        return recent
    
    def _calculate_velocity(self) -> float:
        """Calculate stories completed per week based on Git history."""
        # Get all done stories with commit times
        done_with_time = [s for s in self.all_stories 
                         if s.state == "Done" and s.last_commit_time]
        
        if len(done_with_time) < 2:
            return 0.0
        
        # Sort by commit time
        done_with_time.sort(key=lambda s: s.last_commit_time)
        
        # Calculate time span
        first_commit = done_with_time[0].last_commit_time
        last_commit = done_with_time[-1].last_commit_time
        
        days_span = (last_commit - first_commit).days
        if days_span < 1:
            return 0.0
        
        weeks_span = days_span / 7.0
        velocity = len(done_with_time) / weeks_span
        
        return round(velocity, 1)
    
    def _get_stale_stories(self, days: int = 7) -> List:
        """Get stories that haven't been updated in N days and aren't Done."""
        cutoff = datetime.now() - timedelta(days=days)
        stale = []
        
        for story in self.all_stories:
            if story.state != "Done":
                if story.last_commit_time:
                    if story.last_commit_time < cutoff:
                        days_old = (datetime.now() - story.last_commit_time).days
                        stale.append({
                            "story": story,
                            "days_old": days_old
                        })
                else:
                    # No commit time means very old
                    stale.append({
                        "story": story,
                        "days_old": 999
                    })
        
        # Sort by most stale first
        stale.sort(key=lambda x: x["days_old"], reverse=True)
        
        return stale
    
    def _extract_epic_name(self, story_name: str) -> str:
        """Extract epic/feature name from story name."""
        # Pattern: story-{epic}-{number} or story-{number}.{subnumber}
        
        # Try numbered pattern first (story-1.1, story-1.2)
        match = re.match(r'story-(\d+)\.', story_name)
        if match:
            epic_num = match.group(1)
            return f"Epic {epic_num}.x"
        
        # Try named pattern (story-validation-1, story-charuco-v1-phase1)
        match = re.match(r'story-([a-zA-Z0-9-]+?)-(?:\d+|v\d+)', story_name)
        if match:
            epic_name = match.group(1)
            # Clean up the name
            epic_name = epic_name.replace('-', ' ').title()
            return epic_name
        
        # Try prefix pattern (validation-1, stage4-mode-a)
        match = re.match(r'([a-zA-Z0-9]+)-', story_name)
        if match:
            prefix = match.group(1)
            return prefix.title()
        
        # Default: use the story name itself
        return "Uncategorized"
    
    def get_velocity_trend(self, weeks: int = 5) -> List[Dict]:
        """Calculate velocity trend over past N weeks."""
        done_stories = [s for s in self.all_stories 
                       if s.state == "Done" and s.last_commit_time]
        
        if not done_stories:
            return []
        
        # Sort by commit time
        done_stories.sort(key=lambda s: s.last_commit_time)
        
        # Group by week
        now = datetime.now()
        weekly_counts = []
        
        for week_offset in range(weeks, 0, -1):
            week_start = now - timedelta(weeks=week_offset)
            week_end = now - timedelta(weeks=week_offset - 1)
            
            count = len([s for s in done_stories 
                        if week_start <= s.last_commit_time < week_end])
            
            weekly_counts.append({
                "week": f"Week {weeks - week_offset + 1}",
                "count": count,
                "week_start": week_start
            })
        
        return weekly_counts
