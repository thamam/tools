# BMAD Dashboard V2 - Views Demo

## Overview View (Press 1)

Shows the big picture with:
- **Project Roadmap** (sequence diagram) showing journey from START to END
- **"YOU ARE HERE"** markers on active epics
- **Executive Summary** with progress, velocity, health
- **Epic Map** with all epics and progress bars

```
╭─────────────────────────────── 🗺️  Project Roadmap ───────────────────────────╮
│ Project Journey:                                                             │
│                                                                              │
│ START ═══> 🔄 Epic 1.x [67%] ← YOU ARE HERE                                  │
│       ···> ⏳ Comparison Tool [0%]                                           │
│       ···> ⏳ Release Prep [0%]                                              │
│       ───> 🔄 Stage3 Validation [0%] ← YOU ARE HERE                          │
│       ···> ⏳ Story [0%]                                                     │
│       ···> ⏳ Charuco [0%]                                                   │
│       ···> 🏁 END                                                            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Summary View (Press 2)

Executive dashboard with:
- Executive Summary
- Story Distribution Chart
- Recent Activity Timeline

## Distribution View (Press 3)

Focus on story states:
- Story Distribution Chart (detailed)
- Epic Map

## Epics View (Press 4)

Deep dive into epics:
- Epic Map (detailed)
- **Project Tree** showing hierarchical structure

```
╭────────────────────────── 🌳 Project Tree - You Are Here ─────────────────────╮
│ 📦 Project Overview (22.2% complete)                                         │
│ ├── 🔄 Epic 1.x [67%]                                                        │
│ │   ├── ✅ story-1.1                                                         │
│ │   ├── ✅ story-1.2                                                         │
│ │   ├── ✅ story-1.3                                                         │
│ │   ├── 📝 story-1.4                                                         │
│ │   ├── 📝 story-1.5                                                         │
│ │   └── ... and 4 more stories                                              │
│ ├── ⏳ Comparison Tool [0%]                                                  │
│ │   ├── 📄 story-comparison-tool-1                                          │
│ │   └── ... and 3 more stories                                              │
│ └── ⏳ Release Prep [0%]                                                     │
│     ├── 📄 story-release-prep-1                                             │
│     └── ... and 2 more stories                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Risks View (Press 5)

Action items:
- Risk & Attention Panel (stale stories, missing artifacts, recommendations)
- Recent Activity Timeline

## Tree View (Press 6)

Visual navigation:
- **Project Tree** (full hierarchical view)
- **Project Roadmap** (sequence diagram)

## Breadcrumb (Always Visible)

```
╭──────────────────────────────────────────────────────────────────────────────╮
│ 📍 You are here: 📊 Overview                                                 │
│ Project Progress: ●○○○○ 22.2% complete                                       │
│ Navigation: Press 1-6 to switch views, 'r' to refresh, 'q' to quit           │
╰──────────────────────────────────────────────────────────────────────────────╯
```

Shows:
- Current view name
- Visual progress indicator (●○○○○)
- Keyboard shortcuts

## Keyboard Shortcuts

- **`1`** - Overview (roadmap + summary + epic map)
- **`2`** - Summary (executive summary + distribution + activity)
- **`3`** - Distribution (story states + epic map)
- **`4`** - Epics (epic map + project tree)
- **`5`** - Risks (attention items + activity)
- **`6`** - Tree View (project tree + roadmap)
- **`r`** - Refresh dashboard
- **`q`** - Quit

## Visual Elements

### Progress Indicator
- ●●●○○ = 60% complete
- ●○○○○ = 20% complete
- ●●●●● = 100% complete

### Epic Status
- ✅ Complete
- 🔄 In Progress
- 📝 Active
- ⏳ Not Started

### Story Status
- ✅ Done
- 👀 Review
- 💻 Dev
- 📝 Ready
- 📄 Draft

### Roadmap Connectors
- ═══> Completed path
- ───> Active path
- ···> Future path

## Usage Examples

### Daily Standup
```bash
./dashboard.sh --repos ~/project
# Press 1 for Overview
# See: Where are we? What's done? What's next?
```

### Sprint Planning
```bash
./dashboard.sh --repos ~/project
# Press 4 for Epics View
# See: Which epics are ready? What stories are in each?
```

### Risk Review
```bash
./dashboard.sh --repos ~/project
# Press 5 for Risks
# See: What's stale? What's missing? What should we do?
```

### Executive Review
```bash
./dashboard.sh --repos ~/project
# Press 2 for Summary
# See: Progress, velocity, health, distribution
```
