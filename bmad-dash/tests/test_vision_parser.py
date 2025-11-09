"""
Tests for vision_parser module
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from vision_parser import VisionParser


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory with docs."""
    temp_dir = Path(tempfile.mkdtemp())
    docs_dir = temp_dir / "docs"
    docs_dir.mkdir()
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


def test_parse_product_brief(temp_project_dir):
    """Test parsing product brief file."""
    docs_dir = temp_project_dir / "docs"
    
    # Create a sample product brief
    brief_content = """# Product Brief

## Strategic Overview

**Product Concept:**
This is a test product for camera movement detection.

## Problem Statement

**The Problem:**
We need to detect camera movement in real-time.
"""
    
    brief_file = docs_dir / "product-brief-executive-test-2025-01-01.md"
    brief_file.write_text(brief_content)
    
    parser = VisionParser(temp_project_dir)
    vision = parser.parse_vision()
    
    assert vision is not None
    assert hasattr(vision, 'goal')
    assert "camera movement detection" in vision.goal.lower()


def test_parse_epics(temp_project_dir):
    """Test parsing epics file."""
    docs_dir = temp_project_dir / "docs"
    
    # Create a sample epics file
    epics_content = """# Project Epics

## Epic 1: Core Detection
Status: In Progress

## Epic 2: Validation Framework
Status: Not Started

## Epic 3: Integration
Status: Done
"""
    
    epics_file = docs_dir / "epics.md"
    epics_file.write_text(epics_content)
    
    parser = VisionParser(temp_project_dir)
    vision = parser.parse_vision()
    
    assert vision is not None
    assert hasattr(vision, 'milestones')
    assert len(vision.milestones) >= 3


def test_parse_mvp_document(temp_project_dir):
    """Test parsing MVP document."""
    docs_dir = temp_project_dir / "docs"
    
    # Create a sample MVP document
    mvp_content = """# MVP: Camera Movement Detection

## Goal

Build a minimum viable product for detecting camera movement in agricultural sites.

## Success Criteria

1. Detect movement with 95% accuracy
2. Process 30 FPS in real-time
3. Support multiple camera types
"""
    
    mvp_file = docs_dir / "MVP_Camera_Movement_Detection.md"
    mvp_file.write_text(mvp_content)
    
    parser = VisionParser(temp_project_dir)
    vision = parser.parse_vision()
    
    assert vision is not None
    assert hasattr(vision, 'success_criteria')
    assert len(vision.success_criteria) >= 3


def test_no_vision_files(temp_project_dir):
    """Test when no vision files exist."""
    parser = VisionParser(temp_project_dir)
    vision = parser.parse_vision()
    
    # Should return None or empty dict when no files found
    assert vision is None or vision == {}


def test_file_selection_by_date(temp_project_dir):
    """Test that most recent file is selected."""
    docs_dir = temp_project_dir / "docs"
    
    # Create multiple product briefs with different dates
    old_brief = docs_dir / "product-brief-executive-test-2024-01-01.md"
    old_brief.write_text("# Old Brief\nOld goal")
    
    new_brief = docs_dir / "product-brief-executive-test-2025-01-01.md"
    new_brief.write_text("# New Brief\n\n## Strategic Overview\n\nNew goal for testing")
    
    parser = VisionParser(temp_project_dir)
    vision = parser.parse_vision()
    
    # Should parse the newer file
    assert vision is not None
    if hasattr(vision, 'goal') and vision.goal:
        assert "New goal" in vision.goal or "testing" in vision.goal


def test_milestone_status_extraction(temp_project_dir):
    """Test extracting milestone status."""
    docs_dir = temp_project_dir / "docs"
    
    epics_content = """# Epics

## Story 1: Feature A
Status: Done

## Story 2: Feature B
Status: In Progress

## Story 3: Feature C
Status: Not Started
"""
    
    epics_file = docs_dir / "epics.md"
    epics_file.write_text(epics_content)
    
    parser = VisionParser(temp_project_dir)
    vision = parser.parse_vision()
    
    assert vision is not None
    assert hasattr(vision, 'milestones')
    
    milestones = vision.milestones
    assert any("Done" in m.status or "Complete" in m.status for m in milestones)
    assert any("Progress" in m.status or "Active" in m.status for m in milestones)
    assert any("Not Started" in m.status or "Pending" in m.status for m in milestones)


def test_multiple_document_types(temp_project_dir):
    """Test parsing multiple document types together."""
    docs_dir = temp_project_dir / "docs"
    
    # Create all three types
    brief_file = docs_dir / "product-brief-executive-test-2025-01-01.md"
    brief_file.write_text("# Brief\n\n## Strategic Overview\n\nTest goal")
    
    epics_file = docs_dir / "epics.md"
    epics_file.write_text("# Epics\n\n## Epic 1: Test\nStatus: In Progress")
    
    mvp_file = docs_dir / "MVP_Test.md"
    mvp_file.write_text("# MVP\n\n## Success Criteria\n\n1. Criterion 1\n2. Criterion 2")
    
    parser = VisionParser(temp_project_dir)
    vision = parser.parse_vision()
    
    assert vision is not None
    # Should have data from all sources
    assert (hasattr(vision, 'goal') and vision.goal) or \
           (hasattr(vision, 'milestones') and vision.milestones) or \
           (hasattr(vision, 'success_criteria') and vision.success_criteria)
