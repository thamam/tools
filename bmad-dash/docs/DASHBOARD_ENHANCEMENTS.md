# BMAD Dashboard Enhancements - Executive View

## 🎯 Goal
Transform the minimal table view into an executive dashboard that helps VP R&D/PM understand project health, progress, and make data-driven decisions.

## 👤 User Persona: VP R&D / Project Manager

### Key Questions They Need Answered:
1. **Progress**: How far along are we? What percentage is complete?
2. **Velocity**: Are we moving fast enough? What's our story completion rate?
3. **Blockers**: What's stuck? What needs attention?
4. **Forecast**: When will we finish? What's coming next?
5. **Quality**: Are we maintaining standards? Missing artifacts?
6. **Team Health**: Is work distributed? Any bottlenecks?

## 📊 Proposed Enhancements

### 1. **Executive Summary Panel** (Top of Dashboard)
```
╭─────────────────── Project: cam-shift-detector ───────────────────╮
│ Progress: ████████████░░░░░░░░ 60% (17/28 stories done)          │
│ Velocity: 2.3 stories/week  │  ETA: ~5 weeks remaining           │
│ Health: ⚠️  WARNING - 8 stale stories, 24 missing artifacts       │
╰────────────────────────────────────────────────────────────────────╯
```

**Metrics:**
- Overall completion percentage
- Story velocity (stories/week based on Git commits)
- Estimated time to completion
- Health indicators (stale stories, missing artifacts)

### 2. **Story State Distribution** (Visual Breakdown)
```
╭──────────────────── Story Distribution ────────────────────╮
│ Done:     ████████████████ 17 (60.7%)                      │
│ Ready:    ███░░░░░░░░░░░░░  5 (17.9%)                      │
│ Draft:    ██░░░░░░░░░░░░░░  6 (21.4%)                      │
│ Dev:      ░░░░░░░░░░░░░░░░  0 (0.0%)                       │
│ Review:   ░░░░░░░░░░░░░░░░  0 (0.0%)                       │
╰─────────────────────────────────────────────────────────────╯
```

**Insights:**
- Visual bar chart of story states
- Percentage breakdown
- Identify bottlenecks (e.g., too many in Draft, none in Dev)

### 3. **Activity Timeline** (Recent Progress)
```
╭─────────────────── Recent Activity ────────────────────╮
│ 📅 Last 7 Days:                                        │
│   Nov 4: story-stage4-mode-c (Draft → Done)           │
│   Nov 3: story-stage4-mode-b (Draft → Done)           │
│   Nov 1: story-release-prep-1 (Draft → Ready)         │
│                                                         │
│ 🔥 Most Active: docs/stories/ (5 updates)             │
│ ⏰ Last Update: 1 day ago                              │
╰─────────────────────────────────────────────────────────╯
```

**Features:**
- Recent story transitions
- Most active areas
- Last update timestamp

### 4. **Risk & Attention Panel**
```
╭──────────────────── Needs Attention ───────────────────╮
│ 🚨 STALE (>7 days, not Done):                          │
│   • story-1.4 (Ready, 11 days old)                     │
│   • story-1.8 (Ready, 11 days old)                     │
│   • story-1.9 (Ready, 8 days old)                      │
│                                                         │
│ ⚠️  MISSING ARTIFACTS (24 stories):                    │
│   • 24 missing context files                           │
│   • 24 missing tests                                   │
│                                                         │
│ 💡 RECOMMENDATIONS:                                     │
│   • Move stale Ready stories to Dev                    │
│   • Add context files for active stories               │
╰─────────────────────────────────────────────────────────╯
```

**Insights:**
- Stale stories that need attention
- Missing artifacts summary
- Actionable recommendations

### 5. **Sprint/Epic View** (Grouping)
```
╭─────────────────── Epics / Features ───────────────────╮
│ 📦 MVP v1.0 (Stories 1.1-1.9)                          │
│    Progress: ████████░░░░ 77% (7/9 done)               │
│    Status: On track                                     │
│                                                         │
│ 📦 CharuCo Integration (charuco-v1-*)                  │
│    Progress: ░░░░░░░░░░░░ 0% (0/5 done)                │
│    Status: Not started                                  │
│                                                         │
│ 📦 Stage 4 Tools (stage4-mode-*)                       │
│    Progress: ░░░░░░░░░░░░ 0% (0/3 done)                │
│    Status: Draft phase                                  │
╰─────────────────────────────────────────────────────────╯
```

**Features:**
- Group stories by epic/feature (extracted from story names)
- Progress per epic
- Identify which epics are blocked

### 6. **Velocity Chart** (Trend Analysis)
```
╭─────────────────── Velocity Trend ─────────────────────╮
│ Stories Completed per Week:                            │
│ Week 1: ████ 4 stories                                 │
│ Week 2: ██ 2 stories                                   │
│ Week 3: ████████ 8 stories                             │
│ Week 4: ██ 2 stories                                   │
│ Week 5: ██ 1 story (current)                           │
│                                                         │
│ Avg: 3.4 stories/week  │  Trend: ↓ Slowing             │
╰─────────────────────────────────────────────────────────╯
```

**Insights:**
- Track completion velocity over time
- Identify trends (accelerating/slowing)
- Forecast based on historical data

### 7. **Interactive Drill-Down**
- Press **'1'** - Show Executive Summary
- Press **'2'** - Show Story Distribution
- Press **'3'** - Show Recent Activity
- Press **'4'** - Show Risks & Attention
- Press **'5'** - Show Epic View
- Press **'6'** - Show Velocity Chart
- Press **'t'** - Toggle between Table and Dashboard views

### 8. **Enhanced Table View**
Add columns:
- **Epic/Feature** - Group identifier (extracted from story name)
- **Days in State** - How long in current state
- **Completion %** - Based on tasks/subtasks if available
- **Risk** - 🔴 High (stale + missing artifacts), 🟡 Medium, 🟢 Low

## 🛠️ Implementation Plan

### Phase 1: Data Collection & Analysis
- Extract epic/feature from story names (pattern: story-{epic}-{number})
- Calculate velocity from Git commit history
- Compute days in state from last state change
- Aggregate statistics (completion %, distribution)

### Phase 2: Summary Panels
- Implement Executive Summary panel
- Implement Story Distribution panel
- Implement Risk & Attention panel

### Phase 3: Advanced Analytics
- Implement Activity Timeline
- Implement Epic View with grouping
- Implement Velocity Chart

### Phase 4: Interactive Navigation
- Add keyboard shortcuts to toggle views
- Implement drill-down from summary to details
- Add filtering by epic/state/risk level

## 📈 Expected Benefits

### For VP R&D:
- **5-second health check**: Glance at dashboard to know project status
- **Data-driven decisions**: See velocity trends, identify blockers
- **Risk management**: Proactively address stale stories and missing artifacts
- **Resource allocation**: Identify bottlenecks and redistribute work

### For Project Manager:
- **Sprint planning**: See which epics are ready, which are blocked
- **Stakeholder updates**: Export metrics for status reports
- **Team coordination**: Identify areas needing attention
- **Quality assurance**: Track artifact completion

### For Development Team:
- **Transparency**: Everyone sees the same progress view
- **Motivation**: Visual progress bars show impact
- **Prioritization**: Clear view of what's next
- **Accountability**: Days in state shows work pace

## 🎨 Design Principles

1. **Information Density**: Show maximum relevant info without clutter
2. **Visual Hierarchy**: Most important metrics at top
3. **Actionable Insights**: Not just data, but recommendations
4. **Progressive Disclosure**: Summary first, details on demand
5. **Consistent Updates**: Real-time or near-real-time refresh
6. **Export Friendly**: JSON export for CI/CD and reporting

## 🔄 Future Enhancements

- **Burndown Chart**: Track remaining work over time
- **Team View**: Show work distribution by owner
- **Dependency Graph**: Visualize story dependencies
- **Comparison Mode**: Compare multiple projects side-by-side
- **Alerts**: Notifications for stale stories, failed tests
- **Integration**: Export to Jira, GitHub Projects, etc.


## 🔭 Multi-Resolution Big Picture View

### The Problem
When working on individual stories, developers lose sight of:
- **Where this story fits** in the overall product vision
- **What comes next** after this story
- **Why this matters** to the end goal
- **How components connect** across the system

### The Solution: Zoomable Context Hierarchy

Provide **5 levels of resolution** that users can toggle through:

---

### **Level 1: Product Vision** (Highest Level)
```
╭─────────────────── PRODUCT VISION ───────────────────╮
│ 📱 Camera Movement Detection System                  │
│                                                       │
│ Goal: Detect camera movement in video streams using  │
│       computer vision to distinguish between camera   │
│       motion and object motion                        │
│                                                       │
│ Status: MVP Complete (60%), CharuCo Enhancement (0%) │
│                                                       │
│ Key Milestones:                                       │
│ ✅ Stage 1: Core Detection (Done)                    │
│ ✅ Stage 2: ROI Selection (Done)                     │
│ ✅ Stage 3: Validation (Done)                        │
│ 🔄 Stage 4: Comparison Tools (In Progress)           │
│ ⏳ Stage 5: CharuCo Integration (Not Started)        │
╰───────────────────────────────────────────────────────╯
```

**Data Source**: 
- Parse from `docs/product-brief-*.md` or `docs/PRD_Evolution_Analysis.md`
- Extract project goals, key milestones
- Map stories to milestones

---

### **Level 2: Epic/Feature Map** (Strategic View)
```
╭──────────────────── EPIC MAP ────────────────────────╮
│                                                       │
│  MVP v1.0 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  ├─ Core Detection (1.1-1.3) ✅ Done                 │
│  ├─ API & Tools (1.4-1.7) ✅ Done                    │
│  └─ Testing & Validation (1.8-1.9) 🔄 In Progress   │
│                                                       │
│  Stage 3 Validation ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  ├─ Infrastructure (validation-1) ✅ Ready           │
│  ├─ Test Harness (validation-2) ✅ Ready            │
│  └─ Integration (validation-3) 📝 Draft             │
│                                                       │
│  Stage 4 Tools ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  ├─ Mode A: 4-Image Compare (mode-a) 📝 Draft       │
│  ├─ Mode B: Baseline Tool (mode-b) 📝 Draft         │
│  └─ Mode C: Alpha Blending (mode-c) 📝 Draft        │
│                                                       │
│  CharuCo v1.0 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  ├─ Intrinsic Calibration (phase1) ⏳ Not Started   │
│  ├─ 3D Auto-Calibration (phase2) ⏳ Not Started     │
│  ├─ Runtime Pose (phase3) ⏳ Not Started            │
│  └─ API Integration (charuco-api) ⏳ Not Started    │
│                                                       │
│  Release Prep ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  └─ Documentation & Packaging (prep-1,2,3) 📝 Draft │
│                                                       │
╰───────────────────────────────────────────────────────╯
```

**Features**:
- Tree view of all epics and their stories
- Visual progress indicators
- Dependency arrows (if available)
- Current position highlighted

---

### **Level 3: Current Sprint/Focus** (Tactical View)
```
╭─────────────── CURRENT FOCUS: MVP v1.0 ──────────────╮
│                                                       │
│ Epic: MVP Camera Movement Detection                  │
│ Goal: Complete core detection and validation         │
│ Progress: ████████░░ 77% (7/9 stories)               │
│                                                       │
│ ✅ COMPLETED (7 stories):                            │
│   1.1 Static Region Manager                          │
│   1.2 Feature Extractor                              │
│   1.3 Movement Detector                              │
│   1.5 Camera Movement Detector API                   │
│   1.6 ROI Selection Tool                             │
│   1.7 Recalibration Script                           │
│   comparison-tool-1 Core Comparison Infrastructure   │
│                                                       │
│ 🔄 IN PROGRESS (2 stories):                          │
│   1.4 Result Manager (Ready, stale 11 days) ⚠️       │
│   1.8 Test Coverage (Ready, stale 11 days) ⚠️        │
│                                                       │
│ 🎯 NEXT UP:                                           │
│   → Move 1.4 and 1.8 to Dev                          │
│   → Complete validation story 1.9                    │
│   → Begin Stage 4 tools                              │
│                                                       │
│ 📊 Velocity: 2.3 stories/week → ETA: 1 week          │
╰───────────────────────────────────────────────────────╯
```

**Features**:
- Focus on current epic/sprint
- Show completed, in-progress, and next stories
- Recommendations for next actions
- ETA for epic completion

---

### **Level 4: Story Detail** (Current Work)
```
╭──────────── STORY: 1.1 Static Region Manager ────────╮
│                                                       │
│ Status: ✅ Done                                       │
│ Epic: MVP v1.0 → Core Detection                      │
│ Last Updated: 11 days ago (943a0b8)                  │
│                                                       │
│ 📝 DESCRIPTION:                                       │
│ As a camera movement detection system, I want to     │
│ load ROI coordinates from configuration and generate │
│ binary masks for the static region.                  │
│                                                       │
│ ✅ ACCEPTANCE CRITERIA (4/4):                        │
│   ✓ AC-1.1.1: Config Loading                         │
│   ✓ AC-1.1.2: Binary Mask Generation                 │
│   ✓ AC-1.1.3: Boundary Validation                    │
│   ✓ AC-1.1.4: Error Handling                         │
│                                                       │
│ 📦 ARTIFACTS:                                         │
│   ✓ Story File: docs/stories/story-1.1.md            │
│   ⚠️ Context: Missing                                │
│   ⚠️ Tests: Missing                                  │
│                                                       │
│ 🔗 RELATED:                                           │
│   → Depends on: config.json                          │
│   → Enables: Story 1.2 (Feature Extractor)           │
│   → Part of: Core Detection subsystem                │
│                                                       │
│ 💡 SYSTEM CONTEXT:                                    │
│ This story implements the foundation for ROI-based   │
│ feature extraction, enabling the system to focus on  │
│ stable regions and ignore dynamic elements.          │
╰───────────────────────────────────────────────────────╯
```

**Features**:
- Full story details
- Breadcrumb showing position in hierarchy
- Related stories and dependencies
- System context explanation

---

### **Level 5: Technical Architecture** (System View)
```
╭─────────────── SYSTEM ARCHITECTURE ──────────────────╮
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │         Camera Movement Detector            │    │
│  │              (Story 1.5) ✅                 │    │
│  └──────────────────┬──────────────────────────┘    │
│                     │                                │
│      ┌──────────────┼──────────────┐                │
│      ▼              ▼               ▼                │
│  ┌────────┐  ┌────────────┐  ┌──────────┐          │
│  │ Static │  │  Feature   │  │ Movement │          │
│  │ Region │  │ Extractor  │  │ Detector │          │
│  │Manager │  │ (1.2) ✅   │  │ (1.3) ✅ │          │
│  │(1.1) ✅│  └────────────┘  └──────────┘          │
│  └────────┘                                          │
│      │                                               │
│      ▼                                               │
│  ┌────────────┐                                      │
│  │ config.json│                                      │
│  │   (ROI)    │                                      │
│  └────────────┘                                      │
│                                                       │
│  Supporting Tools:                                   │
│  • ROI Selection Tool (1.6) ✅                       │
│  • Recalibration Script (1.7) ✅                     │
│  • Result Manager (1.4) 🔄                           │
│                                                       │
│  Testing Layer:                                      │
│  • Test Coverage (1.8) 🔄                            │
│  • Validation Suite (1.9) 🔄                         │
│                                                       │
╰───────────────────────────────────────────────────────╯
```

**Data Source**:
- Parse from `docs/tech-spec*.md` or `docs/architecture.md`
- Extract component relationships
- Map stories to components
- Show dependency graph

---

## 🎮 Navigation Between Levels

### Keyboard Shortcuts:
- **`z`** - Zoom out (go to higher level)
- **`x`** - Zoom in (go to lower level)
- **`1-5`** - Jump directly to level 1-5
- **`b`** - Show breadcrumb (where am I in the hierarchy?)
- **`m`** - Show mini-map (overview of all levels)

### Breadcrumb Display:
```
📍 You are here: Product Vision → MVP v1.0 → Core Detection → Story 1.1
```

### Mini-Map (Always Visible):
```
┌─ Resolution ─┐
│ 1. Vision    │ ← You are here
│ 2. Epics     │
│ 3. Sprint    │
│ 4. Story     │
│ 5. Arch      │
└──────────────┘
```

---

## 📊 Data Sources for Big Picture

### Automatically Parsed:
1. **Product Vision**: 
   - `docs/product-brief*.md`
   - `docs/PRD_Evolution_Analysis.md`
   - `README.md` (project description)

2. **Epic Map**:
   - Story naming patterns (story-{epic}-{number})
   - Group by prefix (1.x, validation-x, stage4-x, charuco-x)

3. **Architecture**:
   - `docs/tech-spec*.md`
   - `docs/architecture.md`
   - Extract component diagrams and dependencies

4. **Story Relationships**:
   - Parse "Depends on" / "Enables" from story content
   - Extract from acceptance criteria references
   - Infer from file/module references

### User-Configurable:
```yaml
# .bmad-dash-config.yaml
big_picture:
  vision_file: "docs/product-brief-cam-shift-detector-2025-10-25.md"
  architecture_file: "docs/tech-spec.md"
  epic_grouping:
    - pattern: "story-1\\..*"
      name: "MVP v1.0"
      goal: "Core detection and validation"
    - pattern: "story-charuco-.*"
      name: "CharuCo v1.0"
      goal: "3D calibration integration"
```

---

## 🎯 Use Cases

### Use Case 1: Daily Standup
**Developer**: "What am I working on and why?"
- Start at **Level 4** (current story)
- Press `z` to see **Level 3** (sprint context)
- Press `z` again to see **Level 2** (how this fits in epic map)
- **Result**: "I'm working on story 1.4, part of MVP v1.0 Core Detection, which enables the overall Camera Movement Detection system"

### Use Case 2: Sprint Planning
**PM**: "What should we work on next?"
- Start at **Level 2** (Epic Map)
- See MVP v1.0 is 77% done, Stage 4 is 0%
- Drill into **Level 3** (Current Focus)
- See 2 stories stale in Ready state
- **Decision**: "Let's finish MVP v1.0 stories before starting Stage 4"

### Use Case 3: Stakeholder Update
**VP R&D**: "How's the project going overall?"
- Start at **Level 1** (Product Vision)
- See 60% complete, 5 weeks remaining
- Press `x` to drill into **Level 2** (Epic Map)
- See MVP done, CharuCo not started, Stage 4 in draft
- **Insight**: "We're on track for MVP, but need to start CharuCo soon"

### Use Case 4: Technical Review
**Architect**: "How does this story fit in the system?"
- Start at **Level 4** (Story Detail)
- Press `5` to jump to **Level 5** (Architecture)
- See how Story 1.1 (Static Region Manager) feeds into Feature Extractor
- **Understanding**: "This is a foundational component that blocks other work"

---

## 🔄 Context Switching

### Problem: 
Developers lose context when switching between:
- Writing code (micro level)
- Reviewing PRs (story level)
- Planning sprints (epic level)
- Discussing strategy (vision level)

### Solution:
**One-key context switch**:
- Press `b` (breadcrumb) → See where you are
- Press `1-5` → Jump to any level instantly
- Press `z/x` → Zoom in/out smoothly

---

## 💡 Implementation Priority

### Phase 1: Foundation
1. Parse epic grouping from story names
2. Extract product vision from docs
3. Implement Level 2 (Epic Map) - most valuable first

### Phase 2: Drill-Down
4. Implement Level 3 (Current Focus)
5. Enhance Level 4 (Story Detail) with context
6. Add navigation (z/x/1-5/b)

### Phase 3: Advanced
7. Parse architecture from tech specs
8. Implement Level 5 (System Architecture)
9. Implement Level 1 (Product Vision)
10. Add mini-map and breadcrumb

---

## 📈 Expected Impact

**Before**: "I'm working on story-1.4... not sure why it matters"

**After**: 
```
📍 story-1.4 Result Manager
   ↓ Part of Core Detection
   ↓ Part of MVP v1.0 (77% done)
   ↓ Enables Camera Movement Detection
   ↓ Supports Product Goal: Distinguish camera motion from object motion
```

**Result**: Developer understands the "why" and makes better decisions!
