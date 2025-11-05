"""
Unit tests for BMAD Dashboard
"""
import os
import tempfile
from pathlib import Path
from datetime import datetime
import yaml
import pytest
from git import Repo

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from bmad_dash import (
    BMADParser, Story, Feature, Project,
    STATE_TRANSITIONS, health_check
)


@pytest.fixture
def temp_repo():
    """Create a temporary BMAD repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "test-repo"
        repo_path.mkdir()
        
        # Initialize git repo
        repo = Repo.init(repo_path)
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()
        
        # Create feature structure
        feature_path = repo_path / "features" / "auth" / "stories" / "login"
        feature_path.mkdir(parents=True)
        
        # Create state.yaml
        state_file = feature_path / "state.yaml"
        state_file.write_text(yaml.dump({"state": "Dev", "owner": "Developer"}))
        
        # Create PRD.md
        prd_file = feature_path / "PRD.md"
        prd_file.write_text("""# Login Feature

## Overview
User authentication feature.

## Acceptance Criteria
- User can login with email and password
- Session persists for 24 hours
""")
        
        # Create design.md
        design_file = feature_path / "design.md"
        design_file.write_text("# Design\n\nREST API endpoint.")
        
        # Create logs
        logs_dir = feature_path / "logs"
        logs_dir.mkdir()
        log_file = logs_dir / "latest.log"
        log_file.write_text("2025-11-04 10:00:00 - INFO - Test log\n")
        
        # Commit
        repo.index.add([str(p.relative_to(repo_path)) for p in [state_file, prd_file, design_file, log_file]])
        repo.index.commit("Initial commit")
        
        yield repo_path


class TestBMADParser:
    """Test the BMAD parser functionality."""
    
    def test_parse_repo_structure(self, temp_repo):
        """Test parsing repository structure."""
        parser = BMADParser([str(temp_repo)])
        projects = parser.parse_all()
        
        assert len(projects) == 1
        assert projects[0].name == "test-repo"
        assert len(projects[0].features) == 1
        assert projects[0].features[0].name == "auth"
        assert len(projects[0].features[0].stories) == 1
    
    def test_parse_story_state(self, temp_repo):
        """Test parsing story state from state.yaml."""
        parser = BMADParser([str(temp_repo)])
        projects = parser.parse_all()
        
        story = projects[0].features[0].stories[0]
        assert story.name == "login"
        assert story.state == "Dev"
        assert story.owner == "Developer"
    
    def test_parse_prd(self, temp_repo):
        """Test parsing PRD file."""
        parser = BMADParser([str(temp_repo)])
        projects = parser.parse_all()
        
        story = projects[0].features[0].stories[0]
        assert story.prd_title == "Login Feature"
        assert "User can login" in story.acceptance_criteria
    
    def test_check_artifacts(self, temp_repo):
        """Test artifact checking."""
        parser = BMADParser([str(temp_repo)])
        projects = parser.parse_all()
        
        story = projects[0].features[0].stories[0]
        # Should have no missing artifacts (has PRD, design, logs)
        assert "PRD" not in story.missing_artifacts
        assert "design" not in story.missing_artifacts
        assert "logs" not in story.missing_artifacts
    
    def test_missing_artifacts(self, temp_repo):
        """Test detection of missing artifacts."""
        # Remove design.md
        design_file = temp_repo / "features" / "auth" / "stories" / "login" / "design.md"
        design_file.unlink()
        
        parser = BMADParser([str(temp_repo)])
        projects = parser.parse_all()
        
        story = projects[0].features[0].stories[0]
        assert "design" in story.missing_artifacts
    
    def test_git_commit_info(self, temp_repo):
        """Test Git commit information extraction."""
        parser = BMADParser([str(temp_repo)])
        projects = parser.parse_all()
        
        story = projects[0].features[0].stories[0]
        assert story.last_commit_sha != ""
        assert len(story.last_commit_sha) == 7  # Short SHA
        assert story.last_commit_time is not None
        assert isinstance(story.last_commit_time, datetime)
    
    def test_log_parsing(self, temp_repo):
        """Test log file parsing."""
        parser = BMADParser([str(temp_repo)])
        projects = parser.parse_all()
        
        story = projects[0].features[0].stories[0]
        assert len(story.log_lines) > 0
        assert "Test log" in story.log_lines[0]


class TestStateTransitions:
    """Test state transition validation."""
    
    def test_valid_transitions(self):
        """Test valid state transitions."""
        assert "Ready" in STATE_TRANSITIONS["Draft"]
        assert "Dev" in STATE_TRANSITIONS["Ready"]
        assert "Review" in STATE_TRANSITIONS["Dev"]
        assert "Done" in STATE_TRANSITIONS["Review"]
    
    def test_done_has_no_transitions(self):
        """Test that Done state has no valid transitions."""
        assert STATE_TRANSITIONS["Done"] == []
    
    def test_backward_transitions(self):
        """Test that backward transitions are allowed."""
        assert "Draft" in STATE_TRANSITIONS["Ready"]
        assert "Ready" in STATE_TRANSITIONS["Dev"]
        assert "Dev" in STATE_TRANSITIONS["Review"]


class TestHealthCheck:
    """Test health check functionality."""
    
    def test_missing_artifacts_detection(self, temp_repo):
        """Test detection of missing artifacts in health check."""
        # Remove design.md
        design_file = temp_repo / "features" / "auth" / "stories" / "login" / "design.md"
        design_file.unlink()
        
        parser = BMADParser([str(temp_repo)])
        projects = parser.parse_all()
        
        report = health_check(projects)
        assert len(report["missing_artifacts"]) == 1
        assert report["missing_artifacts"][0]["story"] == "login"
        assert "design" in report["missing_artifacts"][0]["missing"]
    
    def test_no_issues(self, temp_repo):
        """Test health check with no issues."""
        parser = BMADParser([str(temp_repo)])
        projects = parser.parse_all()
        
        report = health_check(projects)
        assert len(report["stale_stories"]) == 0
        assert len(report["missing_artifacts"]) == 0


class TestMultipleRepos:
    """Test handling multiple repositories."""
    
    def test_multiple_repos_parsing(self):
        """Test parsing multiple repositories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two repos
            repo1_path = Path(tmpdir) / "repo1"
            repo2_path = Path(tmpdir) / "repo2"
            
            for repo_path in [repo1_path, repo2_path]:
                repo_path.mkdir()
                repo = Repo.init(repo_path)
                repo.config_writer().set_value("user", "name", "Test").release()
                repo.config_writer().set_value("user", "email", "test@test.com").release()
                
                feature_path = repo_path / "features" / "test" / "stories" / "story1"
                feature_path.mkdir(parents=True)
                
                state_file = feature_path / "state.yaml"
                state_file.write_text(yaml.dump({"state": "Draft"}))
                
                prd_file = feature_path / "PRD.md"
                prd_file.write_text("# Test\n\n## Acceptance Criteria\nTest")
                
                repo.index.add([str(state_file.relative_to(repo_path)), str(prd_file.relative_to(repo_path))])
                repo.index.commit("Initial")
            
            parser = BMADParser([str(repo1_path), str(repo2_path)])
            projects = parser.parse_all()
            
            assert len(projects) == 2
            assert projects[0].name in ["repo1", "repo2"]
            assert projects[1].name in ["repo1", "repo2"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
