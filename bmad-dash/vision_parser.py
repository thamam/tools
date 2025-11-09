"""
Vision Parser - Extract product vision, goals, and milestones from project documentation
"""
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Milestone:
    """Represents a project milestone."""
    name: str
    status: str  # "Done", "In Progress", "Not Started"
    description: Optional[str] = None


@dataclass
class ProductVision:
    """Represents the product vision and strategic context."""
    project_name: str
    goal: str
    milestones: List[Milestone]
    success_criteria: List[str]
    scope_in: List[str]
    scope_out: List[str]


class VisionParser:
    """Parse product vision from documentation files."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
        self.docs_path = self.repo_path / "docs"
    
    def parse_vision(self) -> Optional[ProductVision]:
        """Parse product vision from documentation."""
        # Try to find vision documents
        vision_files = [
            "product-brief-executive-*.md",
            "product-brief-*.md",
            "MVP_*.md",
            "PRD_*.md",
            "epics.md"
        ]
        
        vision_data = {}
        
        for pattern in vision_files:
            files = list(self.docs_path.glob(pattern))
            if files:
                # Use the most recently modified file
                file_path = max(files, key=lambda f: f.stat().st_mtime)
                data = self._parse_vision_file(file_path)
                vision_data.update(data)
        
        if not vision_data:
            return None
        
        # Extract project name from repo
        project_name = self.repo_path.name.replace("-", " ").title()
        
        return ProductVision(
            project_name=vision_data.get("project_name", project_name),
            goal=vision_data.get("goal", ""),
            milestones=vision_data.get("milestones", []),
            success_criteria=vision_data.get("success_criteria", []),
            scope_in=vision_data.get("scope_in", []),
            scope_out=vision_data.get("scope_out", [])
        )
    
    def _parse_vision_file(self, file_path: Path) -> Dict:
        """Parse a single vision file."""
        content = file_path.read_text()
        
        data = {}
        
        # Extract goal/problem statement
        goal_patterns = [
            r"##\s+(?:Strategic Overview|Problem Statement|Product Concept)\s*\n\s*(?:\*\*Product Concept:\*\*\s*\n\s*)?(.*?)(?=\n##|\Z)",
            r"##\s+(?:1\.\s+)?Problem Statement\s*\n\s*(?:\*\*The Problem:\*\*\s*\n\s*)?(.*?)(?=\n##|\Z)",
            r"##\s+🎯\s+Strategic Overview\s*\n\s*(?:\*\*Product Concept:\*\*\s*\n\s*)?(.*?)(?=\n##|\Z)"
        ]
        
        for pattern in goal_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                goal_text = match.group(1).strip()
                # Clean up the text
                goal_text = re.sub(r'\n+', ' ', goal_text)
                goal_text = re.sub(r'\s+', ' ', goal_text)
                goal_text = goal_text[:300]  # Limit length
                data["goal"] = goal_text
                break
        
        # Extract milestones
        milestones = []
        
        # Look for milestone patterns
        milestone_patterns = [
            r"(?:Key Milestones|Implementation Timeline|Story Map):\s*\n(.*?)(?=\n##|\Z)",
            r"##\s+Implementation Timeline\s*\n(.*?)(?=\n##|\Z)"
        ]
        
        for pattern in milestone_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                milestone_text = match.group(1)
                # Extract individual milestones
                milestone_lines = re.findall(r'[✅✓🔄⏳📝❌]\s+(.+?)(?:\(|:|\n)', milestone_text)
                for line in milestone_lines:
                    status = "Done" if any(x in line for x in ["✅", "✓", "Complete", "Done"]) else \
                             "In Progress" if any(x in line for x in ["🔄", "In Progress", "Active"]) else \
                             "Not Started"
                    milestones.append(Milestone(
                        name=line.strip(),
                        status=status
                    ))
                break
        
        # If no milestones found, try to extract from story map or simple headers
        if not milestones:
            story_map_match = re.search(r"##\s+Story Map\s*\n```(.*?)```", content, re.DOTALL)
            if story_map_match:
                story_map = story_map_match.group(1)
                # Extract stories from tree
                story_lines = re.findall(r'[├└│]\s*(?:Story\s+\d+|─+)\s*(.+)', story_map)
                for line in story_lines[:5]:  # Limit to 5
                    milestones.append(Milestone(
                        name=line.strip(),
                        status="Not Started"
                    ))
            else:
                # Try simple ## Story pattern with Status
                story_matches = re.findall(r"##\s+(?:Story\s+\d+:|Epic\s+\d+:)?\s*(.+?)\n(?:.*?Status:\s*(\w+[^\n]*))?", content, re.DOTALL)
                for name, status in story_matches[:5]:
                    status_clean = status.strip() if status else "Not Started"
                    milestones.append(Milestone(
                        name=name.strip(),
                        status=status_clean
                    ))
        
        data["milestones"] = milestones
        
        # Extract success criteria
        success_criteria = []
        success_match = re.search(r"##\s+(?:MVP\s+)?Success Criteria\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
        if success_match:
            criteria_text = success_match.group(1)
            criteria_lines = re.findall(r'(?:✅|\d+\.)\s+(.+)', criteria_text)
            success_criteria = [c.strip() for c in criteria_lines[:5]]  # Limit to 5
        
        data["success_criteria"] = success_criteria
        
        # Extract scope
        scope_in = []
        scope_out = []
        
        scope_in_match = re.search(r"(?:###\s+)?(?:✅\s+)?What'?s\s+IN\s+Scope\s*\n(.*?)(?=\n###|\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
        if scope_in_match:
            scope_text = scope_in_match.group(1)
            scope_lines = re.findall(r'(?:[-•*]|\d+\.)\s+(.+)', scope_text)
            scope_in = [s.strip() for s in scope_lines[:5]]
        
        scope_out_match = re.search(r"(?:###\s+)?(?:❌\s+)?What'?s\s+OUT\s+(?:of\s+)?Scope\s*\n(.*?)(?=\n###|\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
        if scope_out_match:
            scope_text = scope_out_match.group(1)
            scope_lines = re.findall(r'(?:[-•*]|\d+\.)\s+(.+)', scope_text)
            scope_out = [s.strip() for s in scope_lines[:5]]
        
        data["scope_in"] = scope_in
        data["scope_out"] = scope_out
        
        return data
    
    def get_milestone_status_summary(self, milestones: List[Milestone]) -> Dict[str, int]:
        """Get summary of milestone statuses."""
        summary = {"Done": 0, "In Progress": 0, "Not Started": 0}
        for milestone in milestones:
            summary[milestone.status] = summary.get(milestone.status, 0) + 1
        return summary
