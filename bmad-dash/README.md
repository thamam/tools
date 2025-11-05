# BMAD Dashboard

**Terminal-based MVP dashboard for managing BMAD (Breakthrough Method for Agile AI-Driven Development) projects.**

BMAD Dashboard provides a unified, interactive view of multiple BMAD repositories, enabling you to track feature progress, story states, artifact completeness, and Git history—all from a single terminal interface.

## Features

### Core Capabilities

**Unified Project View**: Monitor multiple BMAD repositories simultaneously with a consolidated dashboard that displays all features and stories across projects.

**State Tracking**: Visualize story states (Draft, Ready, Dev, Review, Done) with color-coded indicators and track progression through the development lifecycle.

**Artifact Validation**: Automatically detect missing artifacts including PRD documents, design specifications, test files, and logs to ensure project completeness.

**Git Integration**: Display last commit SHA and timestamps for each story, helping you identify stale work and recent activity.

**Interactive TUI**: Navigate stories using arrow keys, view detailed information, and execute quick actions without leaving the terminal.

**Health Check**: Run automated checks to identify stale stories, missing artifacts, and other project health issues with JSON output for scripting.

### Quick Actions

The dashboard supports several keyboard shortcuts for common operations:

- **Enter**: View detailed information about the selected story including PRD title, acceptance criteria, and recent log entries
- **s**: Display valid state transitions based on the current story state
- **o**: Show the command to open the story's PRD in your configured editor
- **l**: Show the command to tail the story's log file
- **r**: Refresh the dashboard to reflect latest changes from disk and Git
- **q**: Quit the application

## Installation

### Using pipx (Recommended)

```bash
pipx install bmad-dash
```

### Using pip

```bash
pip install -r requirements.txt
```

### From Source

```bash
git clone <repository-url>
cd bmad-dash
pip install -r requirements.txt
chmod +x bmad_dash.py
```

## Usage

### Interactive Dashboard

Launch the interactive TUI to browse and manage your BMAD projects:

```bash
python bmad_dash.py --repos ~/projects/repo1 ~/projects/repo2
```

You can also set the `BMAD_REPOS` environment variable to avoid specifying repositories each time:

```bash
export BMAD_REPOS="~/projects/repo1 ~/projects/repo2"
python bmad_dash.py
```

### Health Check Command

Run a health check to get a JSON report of project issues:

```bash
python bmad_dash.py check --repos ~/projects/repo1
```

The health check identifies:

- **Stale stories**: Stories without commits in the last 7 days that are not in Done state
- **Missing artifacts**: Stories lacking required files (PRD.md, design.md, logs, tests)
- **Missing PR links**: Stories in Review or Done state without pull request references (future enhancement)

Example output:

```json
{
  "stale_stories": [
    {
      "project": "my-project",
      "feature": "auth",
      "story": "password-reset",
      "days_old": 14
    }
  ],
  "missing_artifacts": [
    {
      "project": "my-project",
      "feature": "dashboard",
      "story": "overview",
      "missing": ["design", "logs"]
    }
  ],
  "missing_pr_links": []
}
```

## BMAD Repository Structure

BMAD Dashboard expects repositories to follow this structure:

```
project-root/
├── features/
│   ├── feature-name/
│   │   ├── stories/
│   │   │   ├── story-name/
│   │   │   │   ├── state.yaml
│   │   │   │   ├── PRD.md
│   │   │   │   ├── design.md
│   │   │   │   ├── code/
│   │   │   │   └── logs/
│   │   │   │       └── latest.log
```

### Required Files

**state.yaml**: Contains the current state and owner information for the story.

```yaml
state: Dev
owner: Developer
updated: 2025-11-04
```

**PRD.md**: Product Requirements Document with title, overview, and acceptance criteria.

**design.md**: Technical design specifications for the story.

**logs/**: Directory containing development logs, with `latest.log` being the most recent.

**code/**: Directory containing implementation code and tests.

## State Machine

BMAD Dashboard enforces a state machine for story progression:

| Current State | Valid Transitions |
|---------------|-------------------|
| Draft         | Ready             |
| Ready         | Dev, Draft        |
| Dev           | Review, Ready     |
| Review        | Done, Dev         |
| Done          | (none)            |

The dashboard validates state transitions and prevents invalid moves, ensuring consistent workflow progression.

## Dashboard Interface

The interactive dashboard displays the following columns:

- **Project**: Repository name
- **Feature**: Feature directory name
- **Story**: Story directory name
- **State**: Current state with color coding (yellow=Draft, cyan=Ready, blue=Dev, magenta=Review, green=Done)
- **SHA**: Last commit short SHA (7 characters)
- **Updated**: Time since last commit (e.g., "2d ago", "5h ago")
- **Owner**: Story owner from state.yaml
- **Missing**: Missing artifacts or ✓ if complete

## Development

### Running Tests

The project includes comprehensive unit tests covering parsing, state transitions, and health checks:

```bash
pytest tests/test_bmad_dash.py -v
```

All tests should pass:

```
============================= test session starts ==============================
collected 13 items

tests/test_bmad_dash.py::TestBMADParser::test_parse_repo_structure PASSED
tests/test_bmad_dash.py::TestBMADParser::test_parse_story_state PASSED
tests/test_bmad_dash.py::TestBMADParser::test_parse_prd PASSED
tests/test_bmad_dash.py::TestBMADParser::test_check_artifacts PASSED
tests/test_bmad_dash.py::TestBMADParser::test_missing_artifacts PASSED
tests/test_bmad_dash.py::TestBMADParser::test_git_commit_info PASSED
tests/test_bmad_dash.py::TestBMADParser::test_log_parsing PASSED
tests/test_bmad_dash.py::TestStateTransitions::test_valid_transitions PASSED
tests/test_bmad_dash.py::TestStateTransitions::test_done_has_no_transitions PASSED
tests/test_bmad_dash.py::TestStateTransitions::test_backward_transitions PASSED
tests/test_bmad_dash.py::TestHealthCheck::test_missing_artifacts_detection PASSED
tests/test_bmad_dash.py::TestHealthCheck::test_no_issues PASSED
tests/test_bmad_dash.py::TestMultipleRepos::test_multiple_repos_parsing PASSED

============================== 13 passed in 0.48s
```

### Code Structure

The implementation follows a clean architecture with three main components:

**BMADParser**: Handles repository discovery, file parsing, and data extraction. Recursively scans feature directories, parses YAML and Markdown files, and integrates with Git to extract commit history.

**BMADDashboard**: Textual-based TUI application that provides the interactive interface. Manages the data table, detail pane, keyboard bindings, and user notifications.

**health_check**: Standalone function that analyzes parsed projects and generates health reports in JSON format for scripting and automation.

## Technical Details

- **Language**: Python ≥3.10
- **Dependencies**: Rich (terminal formatting), Textual (TUI framework), GitPython (Git integration), PyYAML (YAML parsing)
- **Footprint**: Single `.py` file (~500 LOC)
- **Platform**: macOS and Linux (requires terminal with color support)

## Limitations and Future Enhancements

This is an MVP implementation focused on core functionality. Potential enhancements include:

- **State modification**: Currently shows valid transitions but doesn't modify state.yaml files
- **File opening**: Shows commands but doesn't launch editors directly
- **Search/filter**: Placeholder for fuzzy search across stories
- **PR link tracking**: Framework exists but not fully implemented
- **Real-time refresh**: Manual refresh (r key) works; automatic polling could be added
- **Export**: Could add CSV/JSON export of dashboard data

## License

This project is provided as-is for BMAD workflow management.

## Contributing

Contributions are welcome! Please ensure:

- All tests pass before submitting changes
- New features include corresponding unit tests
- Code follows the existing style (single-file constraint for MVP)
- Documentation is updated to reflect changes

## Support

For issues, questions, or feature requests, please open an issue in the repository.

---

**Built with ❤️ for BMAD practitioners seeking better project visibility and control.**
