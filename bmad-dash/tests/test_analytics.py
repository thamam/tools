"""
Tests for analytics module
"""
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from analytics import DashboardAnalytics
from bmad_dash import Project, Story, Feature


@pytest.fixture
def sample_projects():
    """Create sample projects for testing."""
    stories = [
        Story(
            project="test-project",
            feature="auth",
            name="login",
            state="Done",
            path=Path("/tmp/test/features/auth/stories/login"),
            prd_title="User Login",
            acceptance_criteria="Users can log in",
            last_commit_time=datetime.now() - timedelta(days=2),
            last_commit_sha="abc123",
            missing_artifacts=[],
        ),
        Story(
            project="test-project",
            feature="auth",
            name="signup",
            state="Ready",
            path=Path("/tmp/test/features/auth/stories/signup"),
            prd_title="User Signup",
            acceptance_criteria="Users can sign up",
            last_commit_time=datetime.now() - timedelta(days=10),
            last_commit_sha="def456",
            missing_artifacts=["design", "tests"],
        ),
        Story(
            project="test-project",
            feature="dashboard",
            name="overview",
            state="Draft",
            path=Path("/tmp/test/features/dashboard/stories/overview"),
            prd_title="Dashboard Overview",
            acceptance_criteria="",
            last_commit_time=datetime.now() - timedelta(days=15),
            last_commit_sha="ghi789",
            missing_artifacts=["prd", "design", "tests", "logs"],
        ),
    ]
    
    features = [
        Feature(name="auth", path=Path("/tmp/test/features/auth"), stories=[stories[0], stories[1]]),
        Feature(name="dashboard", path=Path("/tmp/test/features/dashboard"), stories=[stories[2]]),
    ]
    
    project = Project(
        name="test-project",
        path=Path("/tmp/test-project"),
        features=features,
    )
    
    return [project]


def test_executive_summary(sample_projects):
    """Test executive summary generation."""
    analytics = DashboardAnalytics(sample_projects)
    summary = analytics.get_executive_summary()
    
    assert summary["total_stories"] == 3
    assert summary["done_stories"] == 1
    assert summary["completion_pct"] == pytest.approx(33.3, rel=0.1)
    assert summary["health_status"] in ["HEALTHY", "WARNING", "CRITICAL"]
    assert "velocity" in summary
    assert "eta_weeks" in summary


def test_story_distribution(sample_projects):
    """Test story state distribution calculation."""
    analytics = DashboardAnalytics(sample_projects)
    distribution = analytics.get_state_distribution()
    
    assert distribution["Done"] == 1
    assert distribution["Ready"] == 1
    assert distribution["Draft"] == 1
    assert sum(distribution.values()) == 3


def test_epic_progress(sample_projects):
    """Test epic-level progress tracking."""
    analytics = DashboardAnalytics(sample_projects)
    epics = analytics.get_epic_breakdown()
    
    # Should group by epic (based on story name pattern)
    assert len(epics) >= 1
    
    # Check that epics have correct structure
    for epic in epics:
        assert "name" in epic
        assert "total_stories" in epic
        assert "done_stories" in epic
        assert "progress_pct" in epic
        assert "status" in epic


def test_stale_stories(sample_projects):
    """Test stale story detection."""
    analytics = DashboardAnalytics(sample_projects)
    risks = analytics.get_risks_and_attention()
    stale = risks["stale_stories"]
    
    # Should find the story that's 10+ days old
    assert len(stale) >= 1
    assert all(s["story"].state != "Done" for s in stale)

def test_missing_artifacts(sample_projects):
    """Test missing artifact detection."""
    analytics = DashboardAnalytics(sample_projects)
    risks = analytics.get_risks_and_attention()
    
    # Should find stories with missing artifacts (design, tests, logs, prd)
    assert len(risks["missing_artifacts_summary"]) >= 1


def test_health_status_thresholds(sample_projects):
    """Test health status threshold logic."""
    analytics = DashboardAnalytics(sample_projects)
    summary = analytics.get_executive_summary()
    
    # With 2 stale stories and 6 missing artifacts, should be HEALTHY
    # (thresholds: WARNING at 5/20, CRITICAL at 10/40)
    assert summary["health_status"] in ["HEALTHY", "WARNING"]


def test_recent_activity(sample_projects):
    """Test recent activity tracking."""
    analytics = DashboardAnalytics(sample_projects)
    activity = analytics.get_recent_activity(days=7)
    
    # Should find stories with recent commits
    assert len(activity) >= 1
    assert activity[0]["story"].name == "login"  # Most recent


def test_velocity_calculation(sample_projects):
    """Test velocity calculation."""
    analytics = DashboardAnalytics(sample_projects)
    summary = analytics.get_executive_summary()
    
    # Velocity should be calculated based on Done stories
    assert "velocity" in summary
    assert isinstance(summary["velocity"], (int, float))
    assert summary["velocity"] >= 0


def test_empty_projects():
    """Test analytics with no projects."""
    analytics = DashboardAnalytics([])
    summary = analytics.get_executive_summary()
    
    assert summary["total_stories"] == 0
    assert summary["done_stories"] == 0
    assert summary["completion_pct"] == 0
    assert summary["health_status"] == "HEALTHY"
