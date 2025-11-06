# Product Vision Feature - Level 0

## Overview

The Product Vision view provides the **highest-level strategic context** for your BMAD project, answering the fundamental questions:
- **Why does this project exist?**
- **What are we trying to achieve?**
- **What are the key milestones?**
- **How do we measure success?**

This is **Level 0** in the multi-resolution navigation system - the most zoomed-out view that provides complete strategic context.

## Features

### 1. **Project Goal**
Automatically extracted from your documentation:
- `docs/product-brief-executive-*.md`
- `docs/product-brief-*.md`
- `docs/MVP_*.md`
- `docs/PRD_*.md`

Shows the core problem statement or strategic overview.

### 2. **Key Milestones**
Extracted from:
- `docs/epics.md` (Story Map section)
- Product briefs (Key Milestones section)
- Implementation Timeline sections

Each milestone shows:
- ✅ **Done** - Completed milestones
- 🔄 **In Progress** - Active work
- ⏳ **Not Started** - Future work

### 3. **Success Criteria**
Shows the top 3-5 success criteria from your documentation, helping you understand what "done" looks like.

### 4. **Project Status**
Integrates with dashboard analytics to show:
- Overall completion percentage
- Number of stories completed vs. total
- Current project health

## How to Access

### Interactive Dashboard
```bash
./dashboard.sh --repos ~/your/project
```

Then press **`0`** to jump to Product Vision view.

### Navigation
- **Press `0`** - Product Vision (strategic context)
- **Press `1`** - Overview (tactical view)
- **Press `2-6`** - Other detailed views

## Example Output

```
╭─────────────────────── 🎯 Product Vision ───────────────────────╮
│ 📱 Cam Shift Detector                                           │
│                                                                 │
│ Goal:                                                           │
│   The Stage 3 Validation Framework validates the camera shift  │
│   detection algorithm against real DAF agricultural site       │
│   imagery, providing quantifiable performance metrics...       │
│                                                                 │
│ Status: 22.2% complete (6/27 stories)                          │
│                                                                 │
│ Key Milestones:                                                 │
│   ⏳ Story 1: Phase 1 - Intrinsic Calibration Module           │
│   ⏳ Story 2: Phase 2 - 3D Map Auto-Calibration Module         │
│   ⏳ Story 3: Phase 3 - Runtime Pose Estimation Module         │
│   ⏳ Story 4: CharucoMovementDetector API                      │
│   ⏳ Story 5: PoC Backyard Validation                          │
│                                                                 │
│ Success Criteria:                                               │
│   • Validation executed across all 50 sample images            │
│   • Metrics documented (accuracy, false positives, FPS)        │
│   • Go/no-go recommendation with supporting evidence           │
╰─────────────────────────────────────────────────────────────────╯
```

## How It Works

### Vision Parser
The `vision_parser.py` module:
1. Scans your `docs/` directory for vision documents
2. Uses regex patterns to extract key information
3. Parses markdown structure (headings, lists, sections)
4. Builds a structured `ProductVision` object

### Supported Document Formats

**Product Briefs:**
- Looks for "Strategic Overview", "Problem Statement", "Product Concept"
- Extracts goal/vision from these sections

**Epics:**
- Parses "Story Map" sections with tree structure
- Extracts milestone names and deliverables

**MVP Documents:**
- Finds "Success Criteria" sections
- Extracts "What's IN Scope" and "What's OUT Scope"

### Fallback Behavior
If no vision documents are found, the dashboard shows:
```
No product vision found. Add docs/product-brief-*.md or 
docs/epics.md to your repository.
```

## Benefits for VP R&D / PM

### Strategic Alignment
- Always see the "why" behind the work
- Understand how current stories map to strategic goals
- Keep the big picture in mind during execution

### Stakeholder Communication
- Quick reference for project goals
- Milestone status at a glance
- Success criteria for reporting

### Context Switching
- Quickly zoom out from tactical details
- Remind yourself of the overall mission
- Navigate between strategic and tactical views

## Multi-Resolution Navigation

The Product Vision view is part of a complete multi-resolution system:

```
Level 0: Product Vision ← YOU ARE HERE
    ↓ Press '1' to zoom in
Level 1: Overview (Roadmap + Summary)
    ↓ Press '2' to zoom in
Level 2: Executive Summary (Metrics)
    ↓ Press '3' to zoom in
Level 3: Story Distribution
    ↓ Press '4' to zoom in
Level 4: Epic Breakdown
    ↓ Press '5' to zoom in
Level 5: Risk Analysis
    ↓ Press '6' to zoom in
Level 6: Full Project Tree
```

## Customization

### Adding Your Own Vision Documents

1. **Create a product brief:**
   ```bash
   touch docs/product-brief-myproject-2025-11-06.md
   ```

2. **Add key sections:**
   ```markdown
   ## Strategic Overview
   
   **Product Concept:**
   Your project vision here...
   
   ## Key Milestones
   
   - ✅ Phase 1: Complete
   - 🔄 Phase 2: In Progress
   - ⏳ Phase 3: Not Started
   
   ## Success Criteria
   
   1. Criterion 1
   2. Criterion 2
   3. Criterion 3
   ```

3. **Refresh the dashboard:**
   Press `r` in the interactive dashboard to reload.

### Supported Markdown Patterns

**Milestones:**
- Lines starting with ✅, 🔄, ⏳, ✓, ❌
- "Key Milestones" or "Implementation Timeline" sections

**Success Criteria:**
- "Success Criteria" or "MVP Success Criteria" sections
- Numbered or bulleted lists

**Scope:**
- "What's IN Scope" sections
- "What's OUT of Scope" sections

## Technical Details

### VisionParser Class
```python
from vision_parser import VisionParser
from pathlib import Path

parser = VisionParser(Path("/path/to/repo"))
vision = parser.parse_vision()

if vision:
    print(f"Project: {vision.project_name}")
    print(f"Goal: {vision.goal}")
    print(f"Milestones: {len(vision.milestones)}")
```

### ProductVision Data Structure
```python
@dataclass
class ProductVision:
    project_name: str
    goal: str
    milestones: List[Milestone]
    success_criteria: List[str]
    scope_in: List[str]
    scope_out: List[str]
```

### Milestone Status
```python
@dataclass
class Milestone:
    name: str
    status: str  # "Done", "In Progress", "Not Started"
    description: Optional[str] = None
```

## Future Enhancements

Potential additions:
- **Dependency mapping** - Show how milestones depend on each other
- **Timeline visualization** - Gantt chart of milestone schedule
- **Stakeholder view** - Map milestones to stakeholder needs
- **Risk tracking** - Associate risks with milestones
- **Budget tracking** - Link milestones to budget allocation

## Troubleshooting

### "No product vision found"
**Solution:** Add one of these files to your `docs/` directory:
- `product-brief-*.md`
- `epics.md`
- `MVP_*.md`

### Milestones not showing
**Solution:** Ensure your document has a section like:
```markdown
## Key Milestones

- ✅ Milestone 1
- 🔄 Milestone 2
- ⏳ Milestone 3
```

### Goal text is truncated
This is intentional - goals are limited to 300 characters for display. The full text is still parsed and available in the `ProductVision` object.

## Related Documentation

- [DASHBOARD_ENHANCEMENTS.md](./DASHBOARD_ENHANCEMENTS.md) - Complete enhancement design
- [DELIVERY_V2.md](./DELIVERY_V2.md) - V2 delivery summary
- [VIEWS_DEMO.md](./VIEWS_DEMO.md) - Guide to all dashboard views
- [README_ENHANCED.md](./README_ENHANCED.md) - Enhanced dashboard user guide
