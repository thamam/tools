# BMAD V6 Dashboard Improvements
## Proposal for Next-Generation Dashboard with Full V6 Support

---

## Executive Summary

The current bmad-dashboard only supports the legacy "Development Queue" format (`bmm-workflow-status.md`). BMAD V6 introduces a revolutionary **Agent-as-Code** architecture with modular design, scale-adaptive workflows, and multi-phase methodology that the dashboard should fully support.

**Impact:** Upgrading to V6 support would:
- ✅ Track workflow execution across 34 workflows and 12 agents
- ✅ Visualize four-phase methodology (Analysis → Planning → Solutioning → Implementation)
- ✅ Monitor agent assignments and execution patterns
- ✅ Display module usage (bmm, bmb, cis)
- ✅ Track planning track selection (Quick Flow, BMad Method, Enterprise Method)
- ✅ Support document sharding and token optimization metrics

---

## Current State Analysis

### What Works (Legacy Support)
✅ Parses `bmm-workflow-status.md` for basic project info
✅ Tracks story states: BACKLOG → TODO → IN PROGRESS → DONE
✅ Activity heatmap based on file modification times
✅ Artifact detection (PRD, epics, specs, architecture)
✅ Auto-refresh on BMAD command execution

### What's Missing (V6 Gaps)

❌ **No V6 Module Detection**: Cannot find `bmad/` directory structure
❌ **No Agent Tracking**: Doesn't show which of 12 agents are active
❌ **No Workflow Visualization**: Can't display 34 workflow execution states
❌ **No Phase Tracking**: Missing Analysis → Planning → Solutioning → Implementation
❌ **No Scale-Adaptive Detection**: Doesn't identify Quick Flow vs BMad Method vs Enterprise
❌ **No Configuration Monitoring**: Ignores `bmad/_cfg/` customizations
❌ **Limited Artifact Types**: Misses V6-specific documents (sharded docs, multi-language outputs)
❌ **No Token Metrics**: Can't show document sharding optimization stats

---

## Proposed V6 Feature Set

### 1. **V6 Project Detection** 🔍

**Current:**
```python
def find_bmad_project_root(start_path: str = ".") -> Optional[Path]:
    # Only looks for bmm-workflow-status.md
    status_file = current / "bmm-workflow-status.md"
```

**Proposed:**
```python
def find_bmad_v6_project(start_path: str = ".") -> Optional[Dict]:
    """
    Detect BMAD V6 project structure:
    - bmad/ directory with core/, bmm/, bmb/, cis/ modules
    - .bmad.yaml or .bmad/ configuration
    - Legacy bmm-workflow-status.md for backward compatibility
    """
    current = Path(start_path).resolve()

    for _ in range(10):
        # V6 detection: Look for bmad/ directory structure
        bmad_dir = current / "bmad"
        if bmad_dir.exists() and bmad_dir.is_dir():
            modules = {
                'core': (bmad_dir / 'core').exists(),
                'bmm': (bmad_dir / 'bmm').exists(),
                'bmb': (bmad_dir / 'bmb').exists(),
                'cis': (bmad_dir / 'cis').exists()
            }
            return {
                'version': 'v6',
                'root': current,
                'bmad_dir': bmad_dir,
                'modules': modules,
                'config_dir': bmad_dir / '_cfg'
            }

        # Legacy detection: bmm-workflow-status.md
        legacy_status = current / "bmm-workflow-status.md"
        if legacy_status.exists():
            return {
                'version': 'legacy',
                'root': current,
                'status_file': legacy_status
            }

        current = current.parent
        if current.parent == current:
            break

    return None
```

**Dashboard Display:**
```
╭─────────────────── BMAD V6 Project ────────────────────╮
│ Project: MyApp               Version: V6 Alpha         │
│ Modules: ✓ Core  ✓ BMM  ✓ BMB  ✓ CIS                  │
│ Config: bmad/_cfg/           Custom Agents: 3         │
╰─────────────────────────────────────────────────────────╯
```

---

### 2. **Four-Phase Methodology Tracking** 📊

**Proposed Visualization:**
```
╭──────────────── Project Methodology ───────────────╮
│ Scale Track: BMad Method (Full PRD/Architecture)   │
│                                                     │
│ ┌─────────────────────────────────────────────┐   │
│ │ 1️⃣  Analysis      │ ✅ Complete (3 docs)    │   │
│ │ 2️⃣  Planning      │ 🔄 In Progress         │   │
│ │ 3️⃣  Solutioning   │ ⏸️  Not Started        │   │
│ │ 4️⃣  Implementation│ ⏸️  Not Started        │   │
│ └─────────────────────────────────────────────┘   │
│                                                     │
│ Current Phase: Planning                             │
│ Phase Progress: 67% (2/3 planning workflows)        │
╰─────────────────────────────────────────────────────╯
```

**Implementation:**
```python
def parse_v6_methodology_state(bmad_dir: Path) -> Dict:
    """
    Parse BMAD V6 four-phase methodology state

    Detects:
    - Which scale track is active (Quick Flow / BMad Method / Enterprise)
    - Phase completion (Analysis, Planning, Solutioning, Implementation)
    - Workflow execution status per phase
    - Document generation progress
    """
    phases = {
        "Analysis": {
            "workflows": ["brainstorm", "research"],
            "artifacts": ["research-notes.md", "brainstorm-output.md"],
            "status": "not_started",
            "progress": 0
        },
        "Planning": {
            "workflows": ["create-prd", "architecture"],
            "artifacts": ["prd.md", "architecture.md"],
            "status": "in_progress",
            "progress": 50
        },
        "Solutioning": {
            "workflows": ["technical-spec", "test-plan"],
            "artifacts": ["tech-spec.md", "test-plan.md"],
            "status": "not_started",
            "progress": 0
        },
        "Implementation": {
            "workflows": ["dev-cycle", "story-iteration"],
            "artifacts": ["*.story.md", "implementation-log.md"],
            "status": "not_started",
            "progress": 0
        }
    }

    # Detect scale track from configuration
    scale_track = detect_scale_track(bmad_dir)

    # Scan for phase artifacts and update status
    for phase, info in phases.items():
        completed_artifacts = find_phase_artifacts(bmad_dir, info["artifacts"])
        info["progress"] = (len(completed_artifacts) / len(info["artifacts"])) * 100

        if info["progress"] == 100:
            info["status"] = "completed"
        elif info["progress"] > 0:
            info["status"] = "in_progress"

    return {
        "scale_track": scale_track,  # "Quick Flow" | "BMad Method" | "Enterprise Method"
        "phases": phases,
        "current_phase": detect_current_phase(phases)
    }
```

---

### 3. **Agent Activity Dashboard** 👥

**Proposed Visualization:**
```
╭─────────────────── Active Agents ──────────────────────╮
│ 👤 PM               │ Last: 2h ago   Tasks: 5 ✅       │
│ 🔍 Analyst          │ Last: 1d ago   Tasks: 3 ✅       │
│ 🏗️  Architect        │ Last: 30m ago  Tasks: 2 🔄       │
│ 📝 Scrum Master     │ Last: 4h ago   Tasks: 8 ✅       │
│ 💻 Developer        │ Last: 5m ago   Tasks: 12 🔄      │
│ 🧪 Test Architect   │ Idle           Tasks: 0 ⏸️        │
│ 🎨 UX Designer      │ Idle           Tasks: 0 ⏸️        │
│ 📖 Technical Writer │ Last: 1h ago   Tasks: 1 ✅       │
╰─────────────────────────────────────────────────────────╯

Agent Utilization: █████████░░ 75%
Most Active: Developer (12 tasks, 5m ago)
```

**Implementation:**
```python
def track_agent_activity(bmad_dir: Path) -> Dict[str, Any]:
    """
    Track which agents are active and their task history

    Parses:
    - Agent assignment logs in bmad/_cfg/
    - Workflow execution history
    - Document metadata (created by which agent)
    - Custom agent configurations
    """
    agents = {
        "PM": {"emoji": "👤", "tasks": [], "last_active": None},
        "Analyst": {"emoji": "🔍", "tasks": [], "last_active": None},
        "Architect": {"emoji": "🏗️", "tasks": [], "last_active": None},
        "Scrum Master": {"emoji": "📝", "tasks": [], "last_active": None},
        "Developer": {"emoji": "💻", "tasks": [], "last_active": None},
        "Test Architect": {"emoji": "🧪", "tasks": [], "last_active": None},
        "UX Designer": {"emoji": "🎨", "tasks": [], "last_active": None},
        "Technical Writer": {"emoji": "📖", "tasks": [], "last_active": None},
        "Game Designer": {"emoji": "🎮", "tasks": [], "last_active": None},
        "Game Developer": {"emoji": "🕹️", "tasks": [], "last_active": None},
        "Game Architect": {"emoji": "🏰", "tasks": [], "last_active": None},
        "BMad Master": {"emoji": "🎯", "tasks": [], "last_active": None}
    }

    # Scan workflow execution logs
    for log_file in (bmad_dir / "_cfg" / "logs").rglob("*.log"):
        # Parse agent assignments from logs
        pass

    # Check custom agent configurations
    custom_agents = (bmad_dir / "_cfg" / "agents").glob("*.yaml")

    return {
        "agents": agents,
        "utilization": calculate_agent_utilization(agents),
        "most_active": find_most_active_agent(agents)
    }
```

---

### 4. **Workflow Execution Tracker** 🔄

**Proposed Visualization:**
```
╭─────────────── Workflow Execution (34 Total) ─────────────────╮
│                                                                │
│ Module: bmm (BMad Method)              [12 agents, 34 flows]  │
│ ├─ 📋 Planning Workflows                          Status      │
│ │  ├─ create-prd                                  ✅ Complete │
│ │  ├─ architecture                                ✅ Complete │
│ │  ├─ technical-spec                              🔄 Running  │
│ │  └─ test-strategy                               ⏸️  Pending │
│ ├─ 🔨 Implementation Workflows                                │
│ │  ├─ dev-cycle                                   🔄 Running  │
│ │  ├─ story-iteration                             ⏸️  Pending │
│ │  └─ code-review                                 ⏸️  Pending │
│ └─ 🧪 Quality Workflows                                       │
│    ├─ unit-testing                                ⏸️  Pending │
│    └─ integration-testing                         ⏸️  Pending │
│                                                                │
│ Module: bmb (Builder)                  [1 agent, 7 flows]     │
│ └─ All workflows idle                                         │
│                                                                │
│ Module: cis (Creative Intelligence)    [5 agents, 5 flows]    │
│ └─ All workflows idle                                         │
│                                                                │
│ Execution Stats:                                              │
│ • Completed: 15/34 (44%)                                      │
│ • In Progress: 2/34 (6%)                                      │
│ • Pending: 17/34 (50%)                                        │
╰────────────────────────────────────────────────────────────────╯
```

**Implementation:**
```python
def parse_v6_workflows(bmad_dir: Path) -> Dict:
    """
    Parse all 34 BMAD V6 workflows across modules

    Workflow detection:
    - bmad/bmm/workflows/ (34 workflows)
    - bmad/bmb/workflows/ (7 workflows)
    - bmad/cis/workflows/ (5 workflows)

    Status tracking:
    - Completed: Artifacts exist for all workflow outputs
    - In Progress: Some artifacts exist, some missing
    - Pending: No artifacts generated
    """
    modules = {
        'bmm': {
            'name': 'BMad Method',
            'agents': 12,
            'workflows': parse_module_workflows(bmad_dir / 'bmm')
        },
        'bmb': {
            'name': 'Builder',
            'agents': 1,
            'workflows': parse_module_workflows(bmad_dir / 'bmb')
        },
        'cis': {
            'name': 'Creative Intelligence',
            'agents': 5,
            'workflows': parse_module_workflows(bmad_dir / 'cis')
        }
    }

    return modules

def parse_module_workflows(module_dir: Path) -> List[Dict]:
    """Parse individual module workflows"""
    workflows = []
    workflow_dir = module_dir / 'workflows'

    if not workflow_dir.exists():
        return workflows

    for workflow_file in workflow_dir.glob('*.yaml'):
        workflow = {
            'name': workflow_file.stem,
            'file': workflow_file,
            'status': detect_workflow_status(workflow_file),
            'agent': extract_workflow_agent(workflow_file),
            'dependencies': extract_workflow_dependencies(workflow_file),
            'outputs': extract_expected_outputs(workflow_file)
        }
        workflows.append(workflow)

    return workflows
```

---

### 5. **Configuration & Customization Monitor** ⚙️

**Proposed Visualization:**
```
╭──────────────── Configuration Status ─────────────────╮
│ Config Directory: bmad/_cfg/                          │
│                                                        │
│ 🔧 Custom Agents:            3 modified               │
│    • PM: "Product Visionary" (custom personality)     │
│    • Developer: "Senior Engineer" (custom role)       │
│    • Architect: "Tech Lead" (custom role)             │
│                                                        │
│ 🌍 Language Settings:                                 │
│    • Agent Communication: English                     │
│    • Output Generation: Spanish                       │
│                                                        │
│ 📝 Update Safety:            ✅ Enabled                │
│    Customizations persist through updates             │
╰────────────────────────────────────────────────────────╯
```

---

### 6. **Token Optimization Metrics** 📉

**Proposed Visualization:**
```
╭──────────── Document Sharding & Optimization ──────────────╮
│                                                             │
│ Phase 4 Token Optimization:         90% reduction          │
│                                                             │
│ Sharded Documents:                                          │
│ ├─ prd.md                    Original: 45K → Shard: 4.5K   │
│ ├─ architecture.md           Original: 38K → Shard: 3.8K   │
│ └─ tech-spec.md              Original: 52K → Shard: 5.2K   │
│                                                             │
│ Total Tokens Saved:          120,500 tokens                │
│ Cost Savings (Est.):         $2.41 per iteration           │
╰─────────────────────────────────────────────────────────────╯
```

**Implementation:**
```python
def analyze_token_optimization(project_root: Path) -> Dict:
    """
    Analyze document sharding and token optimization

    V6 Feature: Document sharding reduces context by 90%+ for Phase 4
    """
    sharded_docs = []
    total_saved = 0

    # Find original docs and their sharded versions
    for doc_file in project_root.rglob('*.md'):
        shard_file = doc_file.parent / f"{doc_file.stem}.shard.md"

        if shard_file.exists():
            original_tokens = estimate_tokens(doc_file)
            shard_tokens = estimate_tokens(shard_file)
            saved = original_tokens - shard_tokens

            sharded_docs.append({
                'name': doc_file.name,
                'original_tokens': original_tokens,
                'shard_tokens': shard_tokens,
                'saved_tokens': saved,
                'reduction_pct': (saved / original_tokens) * 100
            })

            total_saved += saved

    return {
        'sharded_docs': sharded_docs,
        'total_saved': total_saved,
        'cost_savings': (total_saved / 1000000) * 2.0  # Rough estimate
    }

def estimate_tokens(file_path: Path) -> int:
    """Rough token estimation: ~4 chars per token"""
    content = file_path.read_text(encoding='utf-8', errors='ignore')
    return len(content) // 4
```

---

### 7. **Party Mode Indicator** 🎉

When multiple agents collaborate on a single workflow:

```
╭───────────── Party Mode Active 🎉 ──────────────╮
│ Strategic Decision Session                      │
│                                                  │
│ Participants:                                    │
│ • 👤 PM               • 🔍 Analyst              │
│ • 🏗️  Architect        • 📝 Scrum Master        │
│ • 💻 Developer        • 🧪 Test Architect       │
│                                                  │
│ Workflow: architecture-review                   │
│ Status: In collaborative discussion             │
╰──────────────────────────────────────────────────╯
```

---

## Implementation Roadmap

### Phase 1: V6 Detection & Compatibility (Week 1)
- [ ] Implement dual-mode detection (V6 + Legacy)
- [ ] Parse `bmad/` directory structure
- [ ] Identify installed modules (bmm, bmb, cis)
- [ ] Backward compatibility with `bmm-workflow-status.md`

### Phase 2: Four-Phase Methodology (Week 2)
- [ ] Parse Analysis → Planning → Solutioning → Implementation
- [ ] Detect scale track (Quick Flow / BMad Method / Enterprise)
- [ ] Track phase completion percentage
- [ ] Visualize current phase and progress

### Phase 3: Agent & Workflow Tracking (Week 3)
- [ ] Parse all 34 workflows across modules
- [ ] Track workflow execution status
- [ ] Monitor agent activity and assignments
- [ ] Display agent utilization metrics

### Phase 4: Advanced Features (Week 4)
- [ ] Configuration monitoring (`bmad/_cfg/`)
- [ ] Token optimization metrics
- [ ] Party mode detection
- [ ] Multi-language support indicators

### Phase 5: UI/UX Enhancements (Week 5)
- [ ] Redesign dashboard layout for V6 data
- [ ] Add color-coded workflow states
- [ ] Interactive drill-down for workflows
- [ ] Export V6-aware JSON for integrations

---

## Example V6 Dashboard Output

```
╭──────────────────────── BMAD V6 Project Dashboard ────────────────────────────╮
│ Project: E-Commerce Platform        Track: BMad Method (Full PRD/Architecture)│
│ Version: V6 Alpha                    Modules: ✓ Core ✓ BMM ✓ BMB ✗ CIS       │
╰────────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────── Methodology Progress ─────────────────────────────────╮
│ 1️⃣  Analysis      ████████████████████ 100%  ✅ Complete                     │
│ 2️⃣  Planning      ████████████░░░░░░░░  67%  🔄 In Progress                  │
│ 3️⃣  Solutioning   ░░░░░░░░░░░░░░░░░░░░   0%  ⏸️  Not Started                │
│ 4️⃣  Implementation░░░░░░░░░░░░░░░░░░░░   0%  ⏸️  Not Started                │
╰────────────────────────────────────────────────────────────────────────────────╯

╭────────────────────── Active Workflows (5/34) ────────────────────────────────╮
│ 🔄 create-prd              PM               75% → prd.md (draft)              │
│ 🔄 architecture            Architect        40% → architecture.md (draft)     │
│ ⏸️  technical-spec         Architect         0% → Waiting for architecture    │
│ ⏸️  dev-cycle              Developer         0% → Waiting for planning        │
│ ⏸️  story-iteration        Scrum Master      0% → Waiting for stories         │
╰────────────────────────────────────────────────────────────────────────────────╯

╭─────────────────────── Agent Activity ────────────────────────────────────────╮
│ 👤 PM              │ Active    │ Last: 5m ago   │ Tasks: 3 ✅ 1 🔄            │
│ 🏗️  Architect       │ Active    │ Last: 12m ago  │ Tasks: 2 🔄                │
│ 💻 Developer       │ Idle      │ Last: 2h ago   │ Tasks: 0 ⏸️                 │
│ 📝 Scrum Master    │ Idle      │ Last: 3h ago   │ Tasks: 1 ✅                │
│                    │           │                │                             │
│ Utilization: ████████░░ 65%    Most Active: PM (5m ago)                       │
╰────────────────────────────────────────────────────────────────────────────────╯

╭────────────────────── Configuration ──────────────────────────────────────────╮
│ Custom Agents: 2          Language: EN→ES         Party Mode: Disabled        │
│ Token Optimization: ✅    Sharded Docs: 3         Tokens Saved: 98,500        │
╰────────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────── Next Actions ─────────────────────────────────────────╮
│ • Complete prd.md (25% remaining)                                             │
│ • Finalize architecture.md for technical-spec workflow                        │
│ • Review and approve Planning phase artifacts                                 │
╰────────────────────────────────────────────────────────────────────────────────╯
```

---

## Benefits Summary

### For Users
✅ **Complete V6 Visibility**: Track all 34 workflows and 12 agents
✅ **Better Decision Making**: See which phase you're in and what's next
✅ **Resource Optimization**: Monitor agent utilization and balance workload
✅ **Cost Tracking**: View token optimization savings from document sharding
✅ **Customization Awareness**: Know which agents have custom configurations

### For Teams
✅ **Collaboration Insights**: See Party Mode sessions and multi-agent work
✅ **Progress Transparency**: Clear view of four-phase methodology status
✅ **Module Usage**: Understand which modules (bmm/bmb/cis) are active
✅ **Scale Track Awareness**: Know if project is Quick Flow vs Enterprise

### For Developers
✅ **Extensible Architecture**: Easy to add new workflow types
✅ **JSON Export**: Machine-readable V6-aware state for integrations
✅ **Backward Compatible**: Supports both V6 and legacy formats

---

## Migration Strategy

### For Existing Users

**Option 1: Auto-Detection** (Recommended)
```python
# Dashboard automatically detects project type
if detect_v6_project():
    render_v6_dashboard()
else:
    render_legacy_dashboard()
```

**Option 2: Explicit Flag**
```bash
# Force V6 mode
bmad-dashboard --mode v6

# Force legacy mode
bmad-dashboard --mode legacy

# Auto-detect (default)
bmad-dashboard
```

### Backward Compatibility

All existing features remain functional:
- ✅ `bmm-workflow-status.md` still supported
- ✅ Story state tracking works as before
- ✅ Activity heatmap unchanged
- ✅ Artifact detection enhanced (not removed)

New V6 features activate only when `bmad/` directory detected.

---

## Open Questions

1. **Workflow State Persistence**: Where does V6 store workflow execution state?
   - Option A: In `.bmad/state.yaml`
   - Option B: In `bmad/_cfg/workflow-state.yaml`
   - Option C: Inferred from artifact existence

2. **Agent Activity Logs**: Does V6 generate activity logs?
   - Need to confirm log format and location

3. **Party Mode Detection**: How to detect when Party Mode is active?
   - Check for specific workflow type?
   - Parse configuration?

4. **Multi-Language Output**: How to display mixed-language artifacts?
   - Show both languages?
   - Detect user's preferred display language?

---

## Next Steps

1. **User Feedback**: Validate these proposals with BMAD V6 users
2. **V6 Structure Analysis**: Deep dive into actual V6 project structure
3. **Prototype**: Build proof-of-concept V6 dashboard panel
4. **Testing**: Test with real V6 projects (bmm, bmb, cis modules)
5. **Documentation**: Update CLAUDE.md with V6 guidance

---

**Version**: V6 Improvement Proposal v1.0
**Date**: November 9, 2025
**Status**: 🟡 Proposal / Awaiting Implementation
