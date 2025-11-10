# BMAD Dashboard v1.0

**Executive terminal dashboard for managing BMAD projects with multi-resolution views**

BMAD Dashboard provides VP R&D, project managers, and developers with a powerful command-line interface for tracking project health, progress, and strategic alignment across multiple BMAD (Breakthrough Method for Agile AI-Driven Development) projects.

## Features

### 🎯 Multi-Resolution Navigation (7 Levels)

Navigate seamlessly between strategic vision and tactical execution:

- **Level 0 (Vision)** - Product goals, milestones, and success criteria
- **Level 1 (Overview)** - Project roadmap, summary, and epic map
- **Level 2 (Summary)** - Executive metrics, velocity, and KPIs
- **Level 3 (Distribution)** - Story state breakdown and bottlenecks
- **Level 4 (Epics)** - Epic-level progress with tree structure
- **Level 5 (Risks)** - Attention items and actionable recommendations
- **Level 6 (Tree)** - Complete project hierarchy with "you are here" markers

### 📊 Executive Dashboard

- **Progress tracking** with visual indicators and completion percentages
- **Velocity metrics** (stories/week) calculated from Git history
- **Health status** (🚨 CRITICAL, ⚠️ WARNING, ✅ HEALTHY) based on stale stories and missing artifacts
- **ETA calculation** for project completion
- **Story distribution** charts showing bottlenecks

### 🗺️ Visual Orientation

- **Project roadmap** showing journey from START to END with "YOU ARE HERE" markers
- **Tree view** with hierarchical structure of epics and stories
- **Breadcrumb navigation** always visible at the top
- **Progress dots** (●○○○○) showing visual completion status

### 🔍 Risk & Attention Panel

- **Stale story detection** (>7 days without updates, configurable)
- **Missing artifact tracking** (PRDs, tests, context files, logs)
- **Actionable recommendations** (not just data)
- **Health check command** with JSON output for CI/CD integration

### 🎨 Interactive TUI

- **Rich terminal UI** using Textual framework for beautiful rendering
- **Keyboard shortcuts** (0-6 for views, r for refresh, q for quit)
- **Color-coded status** indicators for instant understanding
- **Real-time updates** - refresh to pick up new commits and artifacts

### 🔧 Flexible Architecture

- **Multiple BMAD structures** supported:
  - Directory-based: `features/[feature]/stories/[story]/state.yaml`
  - File-based: `docs/stories/story-*.md`
- **Automatic detection** of project structure using pattern matching
- **Git integration** for accurate commit tracking and story updates
- **Multi-repository support** - track multiple projects simultaneously

## Installation

### Quick Start

```bash
cd bmad-dash
./install.sh
```

This creates a virtual environment and installs all dependencies.

### Manual Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Using pipx (Global Installation)

```bash
pipx install .
```

## Usage

### Interactive Dashboard (Recommended)

```bash
./dashboard.sh --repos ~/your/bmad/project
```

**Keyboard Shortcuts:**
- `0` - Product Vision (strategic goals and milestones)
- `1` - Overview (roadmap + summary + epics)
- `2` - Summary (executive metrics and KPIs)
- `3` - Distribution (story state breakdown)
- `4` - Epics (epic-level progress tracking)
- `5` - Risks (attention items and recommendations)
- `6` - Tree (full project hierarchy with "you are here")
- `r` - Refresh (reparse repos from disk)
- `q` - Quit

### Quick Summary (Non-Interactive)

```bash
./dashboard.sh --repos ~/your/project --summary
```

Prints executive summary to console and exits.

### Health Check (JSON Output)

```bash
./dashboard.sh check --repos ~/your/project > health.json
```

Outputs health check results in JSON format for CI/CD integration.

### Simple Table View

```bash
./dashboard.sh --view table --repos ~/your/project
```

Uses the original simple table interface (bmad_dash.py).

### Multiple Repositories

```bash
./dashboard.sh --repos ~/project1 ~/project2 ~/project3
```

Track multiple BMAD projects in a single dashboard.

## Requirements

- **Python** ≥3.10
- **Git** (for commit tracking)
- **Terminal** with color support

### Dependencies

- `rich` - Terminal formatting and rendering
- `textual` - Interactive TUI framework
- `PyYAML` - YAML parsing for state files
- `GitPython` - Git integration

All dependencies are automatically installed in the virtual environment.

## Project Structure

```
bmad-dash/
├── bmad_dash.py          # Original parser and table view
├── bmad_dash_v2.py       # Enhanced dashboard with multi-resolution views
├── analytics.py          # Dashboard analytics and metrics
├── vision_parser.py      # Product vision extraction
├── dashboard.sh          # Main launcher script
├── install.sh            # Installation script
├── run.sh                # Simple runner for table view
├── demo.sh               # Demo script
├── requirements.txt      # Python dependencies
├── setup.py              # Package configuration
├── tests/                # Unit tests
│   ├── test_bmad_dash.py
│   ├── test_analytics.py
│   └── test_vision_parser.py
└── README.md             # This file
```

## Configuration

### Health Thresholds

Edit `analytics.py` to customize health status thresholds:

```python
STALE_WARNING_THRESHOLD = 5      # Stories >5 days old → WARNING
STALE_CRITICAL_THRESHOLD = 10    # Stories >10 days old → CRITICAL
ARTIFACTS_WARNING_THRESHOLD = 20  # >20 missing artifacts → WARNING
ARTIFACTS_CRITICAL_THRESHOLD = 40 # >40 missing artifacts → CRITICAL
```

### Vision Documents

Place these files in your project's `docs/` directory for automatic parsing:

- `product-brief-executive-*.md` - Product goals and strategic overview
- `epics.md` - Project milestones and epics
- `MVP_*.md` - Success criteria and MVP definition

## Testing

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

**Test Coverage:**
- Repository parsing (both structures)
- Story state management
- PRD extraction
- Artifact validation
- Git commit tracking
- State transitions
- Health checks
- Multi-repo support
- Analytics calculations
- Vision parsing

## Examples

### Example 1: Daily Standup

```bash
./dashboard.sh --repos ~/project --summary
```

Get a quick overview of project health before standup.

### Example 2: Sprint Planning

```bash
./dashboard.sh --repos ~/project
```

Press `4` for Epics view to see what's completed and what's next.

### Example 3: Executive Review

```bash
./dashboard.sh --repos ~/project
```

Press `0` for Vision view to align on strategic goals, then `1` for Overview to show progress.

### Example 4: CI/CD Integration

```bash
./dashboard.sh check --repos ~/project | jq '.health_status'
```

Check project health in your CI pipeline.

## Troubleshooting

### Dashboard shows "No BMAD projects found"

**Solution:** Ensure your repository has one of these structures:
- `features/[feature]/stories/[story]/state.yaml` (directory-based)
- `docs/stories/story-*.md` (file-based)

### Refresh doesn't show new commits

**Solution:** Press `r` to refresh. The dashboard now reparses repositories from disk.

### Virtual environment issues

**Solution:** Delete `venv/` and run `./install.sh` again.

### Import errors

**Solution:** Ensure you're in the virtual environment:
```bash
source venv/bin/activate
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run tests: `python -m pytest tests/ -v`
6. Submit a pull request

## License

MIT License - See LICENSE file for details

## Version History

### v1.0.0-rc1 (Current)
- Multi-resolution navigation (7 levels)
- Product Vision level
- Enhanced executive dashboard
- Flexible parser for multiple BMAD structures
- Comprehensive test coverage
- Production-ready quality

### v0.1.0
- Initial release
- Basic table view
- Directory-based parsing

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Built with ❤️ for the BMAD community**
