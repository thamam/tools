# Tree View (Level 6) - "You Are Here" Visual Orientation

## Overview

The **Tree View** provides complete visual orientation by showing:
1. **Hierarchical structure** - The full project tree from top to bottom
2. **Current position** - Highlighted indicators showing where you are
3. **Progress context** - Visual status of all epics and stories
4. **Journey map** - Sequence diagram showing the path from START to END

## Visual Elements

### 1. Breadcrumb Panel (Always Visible)
```
╭──────────────────────────────────────────────────────────────────╮
│ 📍 You are here: 🌳 Project Tree                                 │
│ Project Progress: ●○○○○ 22.2% complete                           │
│ Navigation: Press 0-6 to switch views, 'r' to refresh, 'q' to quit│
╰──────────────────────────────────────────────────────────────────╯
```

**What it tells you:**
- **📍 You are here** - Current view name
- **Progress dots** - ●○○○○ shows 1 out of 5 stages complete (22.2%)
- **Navigation hints** - Keyboard shortcuts to move between views

### 2. Project Tree Panel

```
╭─────────────── 🌳 Project Tree - You Are Here ──────────────────╮
│ 📦 Project Overview (22.2% complete)                            │
│ ├── 🔄 Epic 1.x [67%]                                           │
│ │   ├── ✅ story-1.1                                            │
│ │   ├── ✅ story-1.2                                            │
│ │   ├── ✅ story-1.3                                            │
│ │   ├── ✅ story-1.5                                            │
│ │   ├── ✅ story-1.6                                            │
│ │   └── ... and 4 more stories                                 │
│ ├── ⏳ Comparison Tool [0%]                                     │
│ │   ├── 📄 story-comparison-tool-1                             │
│ │   ├── 📄 story-comparison-tool-2                             │
│ │   ├── 📄 story-comparison-tool-3                             │
│ │   └── 📄 story-comparison-tool-4                             │
│ ├── ⏳ Release Prep [0%]                                        │
│ │   ├── 📄 story-release-prep-1                                │
│ │   ├── 📄 story-release-prep-2                                │
│ │   └── 📄 story-release-prep-3                                │
│ ├── 📝 Stage3 Validation [0%]                                  │
│ │   ├── → 💻 story-stage3-validation-1  ← CURRENT WORK         │
│ │   ├── 📄 story-stage3-validation-2                           │
│ │   └── 📄 story-stage3-validation-3                           │
│ ├── ⏳ Story [0%]                                               │
│ │   ├── 📄 story-story-1                                       │
│ │   ├── 📄 story-story-2                                       │
│ │   └── 📄 story-story-3                                       │
│ └── ⏳ Charuco [0%]                                             │
│     ├── 📄 story-charuco-1                                     │
│     ├── 📄 story-charuco-2                                     │
│     ├── 📄 story-charuco-3                                     │
│     ├── 📄 story-charuco-4                                     │
│     └── 📄 story-charuco-5                                     │
╰─────────────────────────────────────────────────────────────────╯
```

**Visual Indicators:**

#### Epic Status Icons
- **✅ Complete** - All stories done
- **🔄 In Progress** - Some stories done, some in progress
- **📝 Active** - Currently being worked on
- **⏳ Not Started** - No work begun yet

#### Story Status Icons
- **✅ Done** - Story completed
- **👀 Review** - In code review
- **💻 Dev** - In active development
- **📝 Ready** - Ready to start
- **📄 Draft** - Still being planned

#### "You Are Here" Markers
- **→ 💻 story-name** - Arrow points to current work (highlighted in yellow)
- **← CURRENT WORK** - Explicit label showing active story

### 3. Project Roadmap Panel (Sequence Diagram)

```
╭──────────────────── 🗺️  Project Roadmap ────────────────────────╮
│ Project Journey:                                                │
│                                                                 │
│ START ═══> 🔄 Epic 1.x [67%] ← YOU ARE HERE                     │
│       ···> ⏳ Comparison Tool [0%]                              │
│       ···> ⏳ Release Prep [0%]                                 │
│       ───> 📝 Stage3 Validation [0%] ← YOU ARE HERE             │
│       ···> ⏳ Story [0%]                                        │
│       ···> ⏳ Charuco [0%]                                      │
│       ···> 🏁 END                                               │
╰─────────────────────────────────────────────────────────────────╯
```

**Journey Visualization:**

#### Connection Types
- **═══>** - Solid line = Completed path
- **───>** - Dashed line = Current path (in progress)
- **···>** - Dotted line = Future path (not started)

#### Position Markers
- **← YOU ARE HERE** - Shows which epic(s) you're currently working on
- Multiple markers possible if working on multiple epics simultaneously

## How It Provides "You Are Here" Orientation

### 1. **Hierarchical Context**
The tree shows:
- **Where you are** - Current story highlighted with → and yellow color
- **What's above** - The epic containing your current story
- **What's around** - Other stories in the same epic
- **What's next** - Upcoming epics and stories

### 2. **Progress Context**
Each level shows completion:
- **Project level**: 22.2% complete (top of tree)
- **Epic level**: [67%], [0%], etc. (epic nodes)
- **Story level**: ✅ vs 📄 (individual stories)

### 3. **Journey Context**
The roadmap shows:
- **Where you started** - START node
- **Where you've been** - Completed epics (═══>)
- **Where you are** - Current epics (───>) with ← YOU ARE HERE
- **Where you're going** - Future epics (···>)
- **Where you'll end** - 🏁 END node

### 4. **Visual Scanning**
At a glance, you can see:
- **Completed work** - All ✅ icons
- **Current focus** - The → 💻 highlighted story
- **Upcoming work** - All 📄 icons
- **Project health** - Ratio of ✅ to 📄 icons

## Example: Finding Your Position

Let's say you open the Tree view and see:

```
├── 📝 Stage3 Validation [0%]
│   ├── → 💻 story-stage3-validation-1  ← CURRENT WORK
│   ├── 📄 story-stage3-validation-2
│   └── 📄 story-stage3-validation-3
```

**This tells you:**
1. **Current epic**: Stage3 Validation (📝 Active status)
2. **Epic progress**: 0% complete (just started)
3. **Current story**: story-stage3-validation-1
4. **Story status**: 💻 Dev (in active development)
5. **What's next**: 2 more stories in this epic (validation-2 and validation-3)
6. **Position in project**: This is the 4th epic out of 6 total

## Comparison with Other Views

### Level 0: Product Vision
- **Shows**: Strategic goals and milestones
- **Orientation**: "Why does this project exist?"

### Level 1: Overview
- **Shows**: Roadmap + summary + epics
- **Orientation**: "What's the overall status?"

### Level 6: Tree View (Current)
- **Shows**: Complete hierarchical structure
- **Orientation**: "Where am I in the entire project?"

## Benefits

### For Developers
- **Context switching** - Quickly see where you are when returning to work
- **Next task** - See what comes after current story
- **Epic scope** - Understand the full epic you're working on

### For Project Managers
- **Team location** - See which epics have active work
- **Progress visualization** - Tree structure shows completion at all levels
- **Planning** - See which epics are ready to start

### For VP R&D
- **Strategic alignment** - See how current work maps to epics
- **Resource allocation** - Identify which epics need attention
- **Risk assessment** - Spot epics with no progress

## Interactive Features

### Navigation
- **Press 6** - Jump to Tree View from any other view
- **Press 0-5** - Zoom to other resolution levels
- **Press r** - Refresh to see latest changes
- **Press q** - Quit

### Dynamic Updates
The tree automatically:
- **Highlights current work** - Stories in Dev or Review state
- **Shows progress** - Percentage complete for each epic
- **Counts stories** - "... and 4 more stories" for large epics
- **Updates status** - Epic icons change as work progresses

## Technical Implementation

### Story Highlighting Logic
```python
if story.state in ["Dev", "Review"]:
    story_label = f"[bold yellow]→ {state_emoji} {story.name}[/bold yellow]"
else:
    story_label = f"  {state_emoji} {story.name}"
```

Stories in **Dev** or **Review** state are:
1. Prefixed with **→** arrow
2. Highlighted in **yellow**
3. Labeled with **← CURRENT WORK** in roadmap

### Epic Status Determination
```python
status_emoji = {
    "Complete": "✅",      # All stories done
    "In Progress": "🔄",  # Some stories done, some active
    "Active": "📝",       # Has stories in Dev/Review
    "Not Started": "⏳"   # No stories started
}
```

## Summary

The Tree View provides complete "you are here" orientation through:

1. **Visual hierarchy** - See the entire project structure
2. **Current position markers** - → arrow and yellow highlighting
3. **Progress indicators** - Percentage and emoji status
4. **Journey visualization** - Roadmap showing path from START to END
5. **Multi-level context** - Project → Epic → Story levels all visible

This solves the problem: **"I want to see from where we are to the big picture at different resolutions"**

You can instantly answer:
- Where am I? (→ 💻 story-stage3-validation-1)
- What epic am I in? (📝 Stage3 Validation)
- How far along? (22.2% project, 67% Epic 1.x, 0% Stage3)
- What's next? (story-stage3-validation-2 and -3)
- Where in the journey? (4th epic out of 6, between Release Prep and Story epics)
