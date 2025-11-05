# Tasks: Claude Code Project Seeder

**Input**: Design documents from `/specs/001-claude-seeder/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/cli-commands.md

**Tests**: Not explicitly requested in specification - tests are OPTIONAL per Constitution Principle III

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths assume single project structure per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project directory structure per implementation plan in src/
- [x] T002 Initialize Python project with pyproject.toml and dependencies (click, jsonschema, PyYAML, questionary)
- [x] T003 [P] Create src/__init__.py and module __init__.py files for registry/, selection/, operations/, validation/, cli/
- [x] T004 [P] Configure pytest in tests/ with fixtures/ subdirectory
- [x] T005 [P] Create .gitignore for Python project (__pycache__, *.pyc, .pytest_cache, dist/, build/, *.egg-info)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create RegistryItem dataclass in src/registry/models.py with all fields from data-model.md
- [x] T007 Create EnvVar dataclass in src/registry/models.py with validation rules
- [x] T008 [P] Create Selection dataclass in src/selection/models.py
- [x] T009 [P] Create Conflict dataclass in src/operations/models.py
- [x] T010 [P] Create LockFile and LockItem dataclasses in src/operations/lockfile.py
- [x] T011 Implement registry metadata loader in src/registry/loader.py to parse YAML files
- [x] T012 Implement registry item validator in src/registry/validator.py for metadata schema validation
- [x] T013 Implement dependency graph builder in src/registry/resolver.py with adjacency list
- [x] T014 Implement topological sort algorithm in src/registry/resolver.py for dependency resolution
- [x] T015 Implement cycle detection in src/registry/resolver.py using DFS with visited/visiting sets
- [x] T016 Create CLI entry point in src/cli/main.py with Click @click.group() decorator
- [x] T017 Implement atomic file operations context manager in src/validation/integrity.py using tempfile.mkdtemp
- [x] T018 Bundle MCP JSON Schema in src/validation/mcp-schema.json from Claude Code specification

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Initialize New Repository (Priority: P1) 🎯 MVP

**Goal**: Enable developers to initialize Claude Code setup by selecting items from registry in <60 seconds

**Independent Test**: Run `claude-seed init` in empty repo, verify .claude/ and .mcp.json created

### Implementation for User Story 1

- [x] T019 [P] [US1] Implement interactive multi-select UI in src/selection/prompter.py using questionary.checkbox()
- [x] T020 [P] [US1] Implement tag-based filtering in src/selection/filter.py with search functionality
- [x] T021 [US1] Implement file copier in src/operations/copier.py using shutil.copytree() with structure preservation
- [x] T022 [US1] Implement JSON merger in src/operations/merger.py with recursive deep merge algorithm
- [x] T023 [US1] Implement conflict detector in src/operations/merger.py to track key collisions at any depth
- [x] T024 [US1] Implement .env.example generator in src/operations/generator.py from EnvVar metadata
- [x] T025 [US1] Implement README section generator in src/operations/generator.py for setup instructions
- [x] T026 [US1] Implement `claude-seed init` command in src/cli/main.py with --filter, --force, --output options
- [x] T027 [US1] Add selection workflow: load registry → filter → prompt → resolve deps → detect conflicts
- [x] T028 [US1] Add installation workflow: validate → atomic copy → generate files → report success
- [x] T029 [US1] Implement deterministic JSON output with json.dumps(sort_keys=True) for reproducibility
- [x] T030 [US1] Add error handling with exit codes: 0=success, 1=user error, 2=system error, 3=conflict, 4=validation

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Reproducible Setup (Priority: P2)

**Goal**: Enable deterministic configuration reproduction via lock files for team consistency

**Independent Test**: Run init, save lock file, install from lock on different machine, verify byte-for-byte identical

### Implementation for User Story 2

- [x] T031 [P] [US2] Implement SHA-256 hash computation in src/operations/lockfile.py using hashlib
- [x] T032 [P] [US2] Implement lock file writer in src/operations/lockfile.py with version, timestamp, registry path
- [x] T033 [US2] Implement lock file reader in src/operations/lockfile.py with validation
- [x] T034 [US2] Add lock file generation to init workflow after successful installation
- [x] T035 [US2] Implement `claude-seed install` command in src/cli/main.py with --lock-file, --verify options
- [x] T036 [US2] Add install workflow: read lock → verify registry versions → copy files → optionally verify hashes
- [x] T037 [US2] Implement hash verification in src/operations/lockfile.py to detect file tampering
- [x] T038 [US2] Add error handling for version mismatches with actionable resolution messages

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Conflict Detection (Priority: P3)

**Goal**: Prevent silent overwrites by detecting MCP key collisions and failing fast with clear errors

**Independent Test**: Select items with conflicting MCP keys, verify error before any file writes

### Implementation for User Story 3

- [x] T039 [US3] Enhance conflict detector in src/operations/merger.py to record path, items, and values
- [x] T040 [US3] Implement conflict reporter in src/operations/merger.py with formatted error messages
- [x] T041 [US3] Add conflict check gate before file operations in init workflow
- [x] T042 [US3] Implement --force flag handling to allow overwrites with warnings
- [x] T043 [US3] Ensure atomic rollback on conflict: delete temp dir without partial writes
- [x] T044 [US3] Add conflict resolution guidance in error messages (--force or deselect items)

**Checkpoint**: All user stories 1, 2, and 3 should now be independently functional

---

## Phase 6: User Story 4 - Dry Run Preview (Priority: P3)

**Goal**: Allow developers to preview changes before applying for increased confidence

**Independent Test**: Run `--dry-run`, verify no files modified while preview shows planned changes

### Implementation for User Story 4

- [x] T045 [US4] Add --dry-run flag to `claude-seed init` command
- [x] T046 [US4] Implement dry-run mode in src/operations/copier.py to skip actual file writes
- [x] T047 [US4] Implement preview generator in src/operations/generator.py to show planned file changes
- [x] T048 [US4] Add MCP server summary to preview: list of servers to be configured
- [x] T049 [US4] Add environment variable summary to preview: required vs optional
- [x] T050 [US4] Add conflict detection to dry-run: show conflicts without attempting merge
- [x] T051 [US4] Format dry-run output with clear headers and file size estimates
- [x] T052 [US4] Ensure dry-run exits with appropriate code (0=ok, 3=conflict) without side effects

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T053 [P] Implement JSON Schema validator in src/validation/schema.py using jsonschema library
- [x] T054 [P] Add schema validation before writing .mcp.json in all workflows
- [x] T055 [P] Implement `claude-seed list` command in src/cli/main.py with --filter, --type, --json options
- [x] T056 [P] Add table formatting for list command output using basic string formatting
- [x] T057 [P] Implement environment variable support in src/cli/main.py: CLAUDE_REGISTRY_PATH, CLAUDE_SEED_LOG_LEVEL
- [ ] T058 [P] Add logging infrastructure in src/cli/main.py with DEBUG/INFO/WARN/ERROR levels (Optional)
- [ ] T059 [P] Create log directory ~/.claude-seed/logs/ and implement log file rotation (Optional)
- [x] T060 [P] Add comprehensive error messages for all failure modes per contracts/cli-commands.md
- [x] T061 [P] Implement graceful degradation: if questionary fails, fall back to input() prompts
- [x] T062 [P] Add path traversal prevention: reject paths containing ".."
- [ ] T063 Optimize registry loading: lazy-load metadata only for selected namespace (Optional)
- [ ] T064 Add performance logging: measure and log time for each phase (Optional)
- [ ] T065 Update quickstart.md with actual CLI usage examples and validation procedures (Optional)
- [ ] T066 Create example registry structure in tests/fixtures/mock_registry/ with sample items (Optional)
- [ ] T067 Document registry metadata schema in docs/registry-schema.md (Optional)
- [ ] T068 Add CLI help text and examples to all commands with --help flag (Already done via Click decorators)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P3)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Enhances US1 but independently testable
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Uses US1 infrastructure but independently testable

### Within Each User Story

- Dataclasses and models before services that use them (Phase 2 provides all models)
- Core algorithms (merge, resolve, copy) before CLI commands that orchestrate them
- Error handling and validation after core functionality
- Each story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T003, T004, T005)
- All dataclass creation tasks in Foundational can run in parallel (T006-T010)
- Within US1: T019 and T020 (selection UI), T021 (copier), T022-T023 (merger) can run in parallel
- Within US2: T031 and T032 (lock file operations) can run in parallel
- All Polish tasks marked [P] can run in parallel (T053-T062)

---

## Parallel Example: Foundational Phase

```bash
# Launch all model creation tasks together:
Task: "Create RegistryItem dataclass in src/registry/models.py"
Task: "Create Selection dataclass in src/selection/models.py"
Task: "Create Conflict dataclass in src/operations/models.py"
Task: "Create LockFile and LockItem dataclasses in src/operations/lockfile.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Verify init workflow works end-to-end

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Validate with quickstart.md (MVP!)
3. Add User Story 2 → Test independently → Validate reproducibility
4. Add User Story 3 → Test independently → Validate conflict detection
5. Add User Story 4 → Test independently → Validate dry-run preview
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (T019-T030)
   - Developer B: User Story 2 (T031-T038)
   - Developer C: User Story 3 (T039-T044)
   - Developer D: User Story 4 (T045-T052)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Phase 2 (Foundational) MUST be complete before ANY user story work
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Tests are OPTIONAL per Constitution Principle III - focus on implementation quality
