# BMAD Dashboard

A real-time terminal UI dashboard for visualizing BMAD (BMAD Method) project state with activity heatmaps, story tracking, and automatic refresh capabilities.

![BMAD Dashboard](https://img.shields.io/badge/BMAD-Dashboard-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![Status](https://img.shields.io/badge/Status-Production%20Ready-success)

## 🎯 Overview

BMAD Dashboard provides real-time visualization of BMAD project state in a beautiful terminal UI, including:

- **📊 Live Project Status** - Project name, level, phase, and next actions
- **🌳 Story Tree View** - Visual hierarchy of BACKLOG → TODO → IN PROGRESS → DONE
- **🎨 Activity Heatmap** - Color-coded indicators showing recent file modifications
- **📚 Artifacts Tracking** - Automatic detection of PRDs, epics, specs, and contexts
- **🔄 Auto-Refresh** - Updates automatically when BMAD commands are executed
- **⚡ Next Actions** - Shows available actions at each story node

## 🎬 Demo

```text
╭─────────────────── BMAD Project Dashboard ────────────────────╮
│ Project: MyApp          Phase: 4-Implementation               │
│ Level: 3                Next: Continue drafting stories       │
╰────────────────────────────────────────────────────────────────╯

╭─────────────────────── Stories ────────────────────────────────╮
│ 📊 BMAD Project Stories                                        │
│ ├── 📋 BACKLOG (3 stories)                                     │
│ │   └── Story 1.3: User Profile Management ⚪                  │
│ │       → *create-story                                        │
│ ├── 📝 TODO (1 story)                                          │
│ │   └── Story 1.2: Social Login 🔴                            │
│ │       → *story-ready                                         │
│ ├── ⚙️ IN PROGRESS (1 story)                                   │
│ │   └── Story 1.1: Authentication 🔴                           │
│ │       ├── 📄 story-1.1-auth.story.md 🔴                     │
│ │       └── ▶ *story-context, *dev-story, *story-done         │
│ └── ✅ DONE (1 story)                                          │
╰────────────────────────────────────────────────────────────────╯

╭────────────────────── Artifacts ───────────────────────────────╮
│ 📚 Generated Artifacts                                         │
│ ├── PRD (1) - 📄 PRD.md 🔴                                    │
│ └── Architecture (1) - 📄 architecture.md 🟡                  │
╰────────────────────────────────────────────────────────────────╯

╭──────────────────── Activity Heatmap ──────────────────────────╮
│ 🔴 Recent (< 1h)  🟠 Active (< 4h)   🟡 Today (< 24h)        │
│ 🟢 Week (< 7d)    🔵 Month (< 30d)   ⚪ Old (> 30d)          │
╰────────────────────────────────────────────────────────────────╯
```

## 🚀 Features

### Core Features

- **Real-time Visualization**: Live terminal UI built with Rich library
- **Activity Tracking**: File modification-based heatmap with 6 time categories
- **Smart Detection**: Automatically finds BMAD projects by searching for `bmm-workflow-status.md`
- **Story State Machine**: Tracks progression through BACKLOG → TODO → IN PROGRESS → DONE
- **Artifact Discovery**: Detects PRDs, epics, specs, contexts, and more
- **Next Action Inference**: Shows available BMAD commands based on current state

### Auto-Refresh System

- Hook-based triggering on BMAD command execution
- 1-second polling for smooth updates
- Trigger file mechanism for minimal overhead

### Multiple Modes

- **Live Mode**: Real-time dashboard with auto-refresh
- **Summary Mode**: Quick text-based status overview
- **JSON Export**: Machine-readable state output

## 📋 Prerequisites

- **Python 3.8+**
- **Rich library**: `pip install rich`
- **BMAD Method**: A BMAD-managed project

## 🛠️ Installation

### Quick Install

```bash
# Clone or navigate to this repository
cd /path/to/bmad-dashboard

# Run the installer
./install.sh

# Or install manually:
./install.sh --help
```

### Manual Installation

```bash
# Create directories
mkdir -p ~/.config/claude-code/{tools,apps,hooks}
mkdir -p ~/.claude/commands

# Copy files
cp tools/bmad-state-reader.py ~/.config/claude-code/tools/
cp apps/bmad-dashboard.py ~/.config/claude-code/apps/
cp apps/launch-dashboard.sh ~/.config/claude-code/apps/
cp hooks/tool-result.sh ~/.config/claude-code/hooks/
cp commands/bmad-dashboard.md ~/.claude/commands/

# Set permissions
chmod +x ~/.config/claude-code/tools/bmad-state-reader.py
chmod +x ~/.config/claude-code/apps/bmad-dashboard.py
chmod +x ~/.config/claude-code/apps/launch-dashboard.sh
chmod +x ~/.config/claude-code/hooks/tool-result.sh

# Install dependencies
pip install rich
```

## 📖 Usage

### Basic Usage

Navigate to any BMAD project and run:

```bash
# Live dashboard (auto-updates)
~/.config/claude-code/apps/bmad-dashboard.py

# Summary mode (one-time output)
~/.config/claude-code/apps/bmad-dashboard.py --summary

# Specify project path
~/.config/claude-code/apps/bmad-dashboard.py --path /path/to/project
```

### In Claude Code

Use the built-in slash command:

```
/bmad-dashboard
```

### Open in New Terminal

```bash
~/.config/claude-code/apps/launch-dashboard.sh
```

### Get JSON State

```bash
~/.config/claude-code/tools/bmad-state-reader.py --pretty
```

## 🎨 Activity Heatmap

Files are color-coded based on modification time:

| Icon | Color | Time Range | Meaning |
|------|-------|------------|---------|
| 🔴 | Bright Red | < 1 hour | Just modified |
| 🟠 | Orange | < 4 hours | Recent work |
| 🟡 | Yellow | < 24 hours | Today |
| 🟢 | Green | < 7 days | This week |
| 🔵 | Blue | < 30 days | This month |
| ⚪ | Gray | > 30 days | Old/Untouched |

## 🏗️ Architecture

### Components

```
bmad-dashboard/
├── tools/
│   └── bmad-state-reader.py      # Parses BMAD project structure
├── apps/
│   ├── bmad-dashboard.py         # Main TUI application
│   └── launch-dashboard.sh       # Launcher for new terminal
├── hooks/
│   └── tool-result.sh            # Auto-refresh hook
├── commands/
│   └── bmad-dashboard.md         # Claude Code command definition
└── docs/
    └── ARCHITECTURE.md            # Technical documentation
```

### Data Flow

```
BMAD Command → Hook Detects → Touch Trigger → Dashboard Polls → Refresh
  /bmad:*       tool-result.sh    /tmp/trigger    1s interval    Live Update
```

### State Reader

The state reader (`bmad-state-reader.py`) parses:

- **Project Configuration**: From `bmm-workflow-status.md`
- **Story States**: BACKLOG, TODO, IN PROGRESS, DONE sections
- **Story Files**: All `*.story.md` files with metadata extraction
- **Artifacts**: PRD, epics, specs, contexts, etc.
- **Activity**: File modification times for heatmap

## 🧪 Testing

Test the installation:

```bash
# Test state reader
~/.config/claude-code/tools/bmad-state-reader.py --help

# Test dashboard
~/.config/claude-code/apps/bmad-dashboard.py --help

# Test on a project
cd /path/to/bmad/project
~/.config/claude-code/apps/bmad-dashboard.py --summary
```

## 🔧 Configuration

### Custom Poll Interval

```bash
# Poll every 0.5 seconds (faster updates)
~/.config/claude-code/apps/bmad-dashboard.py --poll 0.5
```

### Disable Hook

To disable auto-refresh, remove or rename the hook:

```bash
mv ~/.config/claude-code/hooks/tool-result.sh ~/.config/claude-code/hooks/tool-result.sh.disabled
```

## 📊 Use Cases

### During Active Development

Keep dashboard open in a separate terminal while working on stories:

```bash
# Terminal 1: Dashboard
cd ~/my-bmad-project
~/.config/claude-code/apps/bmad-dashboard.py

# Terminal 2: Work
# Run BMAD commands - dashboard auto-updates!
/bmad:bmm:workflows:create-story
```

### Project Status Check

Quick overview of project state:

```bash
cd ~/my-bmad-project
~/.config/claude-code/apps/bmad-dashboard.py --summary
```

### CI/CD Integration

Export state as JSON for automation:

```bash
~/.config/claude-code/tools/bmad-state-reader.py | jq '.stories["IN PROGRESS"] | length'
```

## 🐛 Troubleshooting

### Dashboard shows "No BMAD project"

**Solution**: Navigate to a directory containing `bmm-workflow-status.md` or specify path:
```bash
~/.config/claude-code/apps/bmad-dashboard.py --path /path/to/project
```

### Dashboard not auto-updating

**Check hook is installed:**
```bash
ls -la ~/.config/claude-code/hooks/tool-result.sh
```

**Manually trigger refresh:**
```bash
touch /tmp/bmad-dashboard-trigger
```

### Rich library not found

**Install rich:**
```bash
pip install rich
# or
pip3 install rich
# or for user install
pip install --user rich
```

### Story files not showing activity

**Ensure files match pattern:**
- Files should be named: `story-1.1-title.story.md`
- Must have `.story.md` extension
- Must be in subdirectories under project root

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

Part of the BMAD Method tooling ecosystem.

## 🙏 Acknowledgments

- Built for the [BMAD Method](https://github.com/your-org/BMAD-METHOD)
- Uses [Rich](https://github.com/Textualize/rich) for terminal UI
- Inspired by modern development workflows

## 📚 Additional Resources

- [BMAD Method Documentation](link-to-bmad-docs)
- [Installation Guide](docs/INSTALLATION.md)
- [Architecture Details](docs/ARCHITECTURE.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

## 📞 Support

For issues or questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review the documentation in `docs/`
3. Open an issue on GitHub
4. Contact the maintainers

---

**Version**: 1.0.0
**Status**: Production Ready
**Last Updated**: October 2025
