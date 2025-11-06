# BMAD Dashboard Enhanced - Executive View

A powerful terminal dashboard for VP R&D and Project Managers to track BMAD project progress, identify risks, and make data-driven decisions.

## 🎯 What's New

### Executive Summary Panel
- **Progress tracking**: Visual progress bar with completion percentage
- **Velocity metrics**: Stories completed per week
- **ETA calculation**: Estimated time to completion
- **Health indicators**: Instant visibility into project health (Healthy/Warning/Critical)

### Epic Map - Big Picture View
- **Multi-epic visualization**: See all epics and their progress at a glance
- **Progress bars**: Visual representation of completion per epic
- **Status indicators**: ✅ Complete, 🔄 In Progress, 📝 Active, ⏳ Not Started
- **Grouping**: Automatically groups stories by epic (Epic 1.x, CharuCo, Stage 4, etc.)

### Story Distribution Chart
- **State breakdown**: Visual chart showing stories in Done/Review/Dev/Ready/Draft
- **Percentage view**: See where stories are concentrated
- **Bottleneck detection**: Quickly identify if too many stories are stuck in one state

### Risk & Attention Panel
- **Stale story detection**: Identifies stories not updated in 7+ days
- **Missing artifacts**: Summary of missing context files, tests, etc.
- **Actionable recommendations**: Not just data, but what to do about it

### Recent Activity Timeline
- **Last 7 days**: See what's been completed recently
- **Activity tracking**: Most active areas of the project
- **Momentum indicator**: Is the project moving forward?

## 🚀 Quick Start

### Installation
```bash
cd /path/to/tools/bmad-dash
./install.sh
```

### Usage

**Executive Dashboard (Default)**:
```bash
./dashboard.sh --repos ~/my-project
```

**Summary View (Quick Check)**:
```bash
./dashboard.sh --repos ~/my-project --summary
```

**Health Check (JSON Output)**:
```bash
./dashboard.sh check --repos ~/my-project
```

**Table View (Simple)**:
```bash
./dashboard.sh --view table --repos ~/my-project
```

### Multiple Repositories
```bash
./dashboard.sh --repos ~/project1 ~/project2 ~/project3
```

## 📊 Dashboard Views

### 1. Executive Summary
```
╭──────────────────────────── 📊 Executive Summary ────────────────────────────╮
│ Progress: ████████████░░░░░░░░ 60% (17/28 stories done)                      │
│ Velocity: 2.3 stories/week  │  ETA: ~5 weeks remaining                       │
│ Health: ⚠️  WARNING - 8 stale stories, 24 missing artifacts                   │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**Metrics Explained**:
- **Progress**: Overall completion percentage and story count
- **Velocity**: Average stories completed per week (calculated from Git history)
- **ETA**: Estimated weeks to completion based on velocity
- **Health**: 
  - ✅ HEALTHY: < 5 stale stories, < 20 missing artifacts
  - ⚠️ WARNING: 5-10 stale stories, 20-40 missing artifacts
  - 🚨 CRITICAL: > 10 stale stories, > 40 missing artifacts

### 2. Epic Map - Big Picture
```
╭───────────────────────── 🗺️  Epic Map - Big Picture ──────────────────────────╮
│ 🔄 Epic 1.x                       █████████████░░░░░░░  66.7% (6/9)          │
│ ⏳ Comparison Tool                ░░░░░░░░░░░░░░░░░░░░   0.0% (0/4)          │
│ ⏳ Release Prep                   ░░░░░░░░░░░░░░░░░░░░   0.0% (0/3)          │
│ 📝 Stage3 Validation              ░░░░░░░░░░░░░░░░░░░░   0.0% (0/3)          │
│ ⏳ Charuco                        ░░░░░░░░░░░░░░░░░░░░   0.0% (0/5)          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**Epic Grouping**:
- Automatically extracts epic names from story patterns:
  - `story-1.1`, `story-1.2` → "Epic 1.x"
  - `story-charuco-v1-phase1` → "Charuco"
  - `story-stage4-mode-a` → "Stage4 Mode"
  - `story-validation-1` → "Validation"

### 3. Story Distribution
```
╭─────────────────────────── 📈 Story Distribution ────────────────────────────╮
│ Done       ████████████████ 17 (60.7%)                                       │
│ Ready      ███░░░░░░░░░░░░░  5 (17.9%)                                       │
│ Draft      ██░░░░░░░░░░░░░░  6 (21.4%)                                       │
│ Dev        ░░░░░░░░░░░░░░░░  0 (0.0%)                                        │
│ Review     ░░░░░░░░░░░░░░░░  0 (0.0%)                                        │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**Insights**:
- High % in Draft → Need to move stories to Ready
- High % in Ready → Need to start development
- Zero in Dev/Review → Potential bottleneck

### 4. Needs Attention
```
╭───────────────────────────── ⚠️  Needs Attention ─────────────────────────────╮
│ 🚨 STALE (>7 days, not Done):                                                │
│   • story-1.4 (Ready, 11 days old)                                           │
│   • story-1.8 (Ready, 11 days old)                                           │
│                                                                              │
│ ⚠️  MISSING ARTIFACTS:                                                        │
│   • 24 missing context files                                                 │
│   • 24 missing tests                                                         │
│                                                                              │
│ 💡 RECOMMENDATIONS:                                                          │
│   • Move stale Ready stories to Dev                                          │
│   • Add context files for active stories                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## 🎮 Keyboard Shortcuts

### Interactive Dashboard
- **`q`** - Quit
- **`r`** - Refresh dashboard
- **`1`** - Jump to Executive Summary
- **`2`** - Jump to Story Distribution
- **`3`** - Jump to Epic Map
- **`4`** - Jump to Risks & Attention
- **`5`** - Jump to Recent Activity
- **`t`** - Toggle between Executive and Table views

## 📈 Use Cases

### Daily Standup (Developer)
```bash
./dashboard.sh --repos ~/project --summary
```
Quick check: What's the overall progress? Any blockers?

### Sprint Planning (PM)
```bash
./dashboard.sh --repos ~/project
```
Interactive view: Which epics are ready? What's blocked? What should we work on next?

### Executive Review (VP R&D)
```bash
./dashboard.sh --repos ~/project1 ~/project2 ~/project3 --summary
```
Multi-project view: How are all projects progressing? Any risks?

### CI/CD Integration
```bash
./dashboard.sh check --repos ~/project | jq '.stale_stories | length'
```
Automated checks: Fail build if too many stale stories

## 🔧 Configuration

### Custom Stale Threshold
Edit `analytics.py` to change the stale story threshold (default: 7 days):
```python
def _get_stale_stories(self, days: int = 7):  # Change to 14 for 2 weeks
```

### Epic Grouping Patterns
The dashboard automatically detects epics from story names. To customize, edit `analytics.py`:
```python
def _extract_epic_name(self, story_name: str) -> str:
    # Add custom patterns here
```

## 📊 Data Sources

### Automatic Detection
- **Stories**: Searches for `story-*.md` files in `docs/stories/`
- **Status**: Extracts from markdown content (`Status: Done`, `Status: Ready`, etc.)
- **Git History**: Uses Git commits for velocity and activity tracking
- **Artifacts**: Checks for context files, tests, PRDs

### Supported BMAD Structures
1. **File-based** (like cam-shift-detector):
   ```
   docs/
     stories/
       story-1.1.md
       story-1.2.md
   ```

2. **Directory-based** (original):
   ```
   features/
     auth/
       stories/
         login/
           state.yaml
           PRD.md
   ```

## 🎯 Metrics Explained

### Velocity Calculation
- Counts stories in "Done" state with Git commit timestamps
- Calculates time span from first to last done story
- Formula: `velocity = done_stories / (days_span / 7)`

### ETA Calculation
- Remaining stories = Total - Done
- Formula: `ETA = remaining_stories / velocity`

### Health Status
- **Stale stories**: Stories not updated in 7+ days (excluding Done)
- **Missing artifacts**: Context files, tests, design docs
- Thresholds:
  - Healthy: < 5 stale, < 20 missing
  - Warning: 5-10 stale, 20-40 missing
  - Critical: > 10 stale, > 40 missing

## 🐛 Troubleshooting

### "No BMAD projects found"
**Solution**: Ensure your repository has:
- `docs/stories/story-*.md` files, OR
- `features/*/stories/*/state.yaml` structure

### Velocity shows 0.0
**Reason**: Not enough done stories with Git history
**Solution**: Complete at least 2 stories and commit them

### Epic names are "Uncategorized"
**Reason**: Story names don't match expected patterns
**Solution**: Use naming patterns like `story-{epic}-{number}` or `story-{number}.{subnumber}`

## 📚 Architecture

```
bmad-dash/
├── bmad_dash.py              # Original table view
├── bmad_dash_enhanced.py     # Executive dashboard
├── analytics.py              # Metrics and insights engine
├── dashboard.sh              # Unified launcher
├── install.sh                # Installation script
├── run.sh                    # Legacy launcher
└── README_ENHANCED.md        # This file
```

## 🔄 Migration from Original Dashboard

The enhanced dashboard is fully backward compatible. You can:
1. Use `./dashboard.sh` (new) instead of `./run.sh` (old)
2. Switch between views with `--view executive` or `--view table`
3. All existing commands still work

## 🚀 Future Enhancements

Planned features (see `DASHBOARD_ENHANCEMENTS.md`):
- **Multi-resolution navigation**: Zoom in/out between vision, epic, sprint, story, architecture levels
- **Velocity trend chart**: Track velocity over time
- **Burndown chart**: Visualize remaining work
- **Team view**: Work distribution by owner
- **Dependency graph**: Story relationships

## 📝 License

Part of the BMAD Method tooling ecosystem.

## 🙏 Acknowledgments

Built with:
- [Rich](https://github.com/Textualize/rich) - Terminal UI
- [Textual](https://github.com/Textualize/textual) - TUI framework
- [GitPython](https://github.com/gitpython-developers/GitPython) - Git integration

---

**Version**: 2.0.0 (Enhanced)
**Status**: Production Ready
**Last Updated**: November 2025
