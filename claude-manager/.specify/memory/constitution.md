<!--
Sync Impact Report:
- Version: 0.0.0 → 1.0.0
- Rationale: Initial constitution establishment for SpecKit framework
- Modified principles: All principles newly defined
- Added sections: All sections (initial creation)
- Removed sections: None
- Templates status:
  ✅ plan-template.md - Constitution Check section aligns with principles
  ✅ spec-template.md - User story prioritization aligns with Principle I
  ✅ tasks-template.md - Task organization aligns with Principles I & IV
- Follow-up TODOs: None - all placeholders filled
- Created: 2025-10-25
-->

# SpecKit Constitution

## Core Principles

### I. User Story Independence

Every user story MUST be independently testable and deliverable. Each story represents a complete vertical slice of functionality that:

- Can be developed, tested, and deployed without dependencies on other stories
- Delivers measurable user value when implemented alone
- Serves as a viable MVP increment
- Has clear priority ordering (P1, P2, P3, etc.) based on business value

**Rationale**: Independent stories enable parallel development, incremental delivery, and early validation of high-priority features. This reduces risk and accelerates time-to-value.

### II. Specification Primacy

Product requirements MUST be captured as technology-agnostic specifications focusing on WHAT users need and WHY, never HOW to implement.

Specifications must:

- Be written for business stakeholders, not developers
- Contain no implementation details (languages, frameworks, databases, APIs)
- Define measurable, testable success criteria
- Make informed guesses with documented assumptions rather than leaving excessive gaps
- Limit clarification requests to maximum 3 critical questions per feature

**Rationale**: Clear separation between requirements (spec) and implementation (plan/tasks) enables better decision-making, reduces rework, and allows technical choices to evolve independently of business needs.

### III. Test-Optional Development

Tests are OPTIONAL and MUST be written only when explicitly requested in the feature specification.

When tests are required:

- They MUST be written FIRST (TDD: red-green-refactor)
- They MUST fail before implementation begins
- Contract tests validate external interfaces
- Integration tests validate user journeys
- Unit tests are lowest priority (added only if explicitly requested)

**Rationale**: Not all projects need comprehensive test coverage. Forcing tests on every feature creates unnecessary overhead. When tests are needed, TDD ensures they're meaningful and catch regressions.

### IV. Parallel-First Design

Feature designs MUST maximize opportunities for parallel execution:

- Tasks marked [P] have no dependencies and can run concurrently
- Different user stories can be worked on in parallel
- After foundational phase completes, all user stories become parallelizable
- Templates and commands must support concurrent multi-developer workflows

**Rationale**: Parallel execution dramatically reduces development time and resource utilization. Forcing sequential thinking creates artificial bottlenecks.

### V. Constitutional Compliance

All specifications, plans, and tasks MUST pass Constitution Check gates before implementation:

- Phase 0: Check before research begins
- Phase 1: Re-check after design completes
- Any violations MUST be explicitly justified in Complexity Tracking section
- Unjustified violations block progression to next phase

**Rationale**: Constitution ensures consistent quality standards and prevents complexity creep. Explicit justification for violations maintains accountability.

## Workflow Constraints

### Mandatory Phases

Every feature MUST progress through these phases in order:

1. **Specification** (`/speckit.specify`): Create technology-agnostic requirements
2. **Clarification** (`/speckit.clarify`) [OPTIONAL]: Resolve ambiguities if needed
3. **Planning** (`/speckit.plan`): Design technical approach with Constitution Check
4. **Task Generation** (`/speckit.tasks`): Break down into executable tasks
5. **Implementation** (`/speckit.implement`): Execute tasks in dependency order
6. **Analysis** (`/speckit.analyze`) [OPTIONAL]: Validate cross-artifact consistency

### Specification Quality Gates

Specifications MUST NOT proceed to planning until they meet these criteria:

- No implementation details present
- All [NEEDS CLARIFICATION] markers resolved (max 3 allowed initially)
- Functional requirements are testable and unambiguous
- Success criteria are measurable and technology-agnostic
- User scenarios cover primary flows with acceptance criteria
- Edge cases identified
- Scope clearly bounded

### Planning Quality Gates

Plans MUST NOT proceed to task generation until they meet these criteria:

- Constitution Check completed and all violations justified
- Technical Context section fully populated (no NEEDS CLARIFICATION markers)
- Project structure selected and documented
- Research artifacts created (research.md, data-model.md if applicable)
- Contract definitions created for all external interfaces
- Quickstart validation guide created

## Development Standards

### File Organization

- Specifications: `specs/[###-feature-name]/spec.md`
- Plans: `specs/[###-feature-name]/plan.md`
- Tasks: `specs/[###-feature-name]/tasks.md`
- Research: `specs/[###-feature-name]/research.md`
- Contracts: `specs/[###-feature-name]/contracts/`
- Checklists: `specs/[###-feature-name]/checklists/`

### Branch Naming

- Pattern: `[###]-[feature-name]` (e.g., `001-user-auth`, `042-payment-gateway`)
- Number must be unique and sequential across all features
- Short name must be 2-4 words in kebab-case
- Branch creation MUST check remote, local, and specs directories for existing numbers

### Task Formatting

- Format: `[ID] [P?] [Story] Description`
- [P] indicates parallelizable tasks (different files, no dependencies)
- [Story] links task to specific user story (US1, US2, US3, etc.)
- Description MUST include exact file paths
- Tasks organized by phase: Setup → Foundational → User Story phases → Polish

### Foundational Phase Discipline

The Foundational phase MUST complete entirely before ANY user story work begins:

- Contains ONLY infrastructure that ALL user stories depend on
- Examples: Database schema, auth framework, API routing, base models
- Marked with checkpoint: "Foundation ready - user story implementation can now begin in parallel"
- User stories CANNOT add foundational dependencies retroactively

**Rationale**: Clear separation between shared infrastructure and feature work prevents false dependencies and enables true parallel development.

## Governance

### Amendment Process

Constitution amendments require:

1. Version bump following semantic versioning:
   - MAJOR: Backward incompatible principle removals or redefinitions
   - MINOR: New principle/section added or materially expanded guidance
   - PATCH: Clarifications, wording refinements, non-semantic changes

2. Sync Impact Report documenting:
   - Modified principles
   - Affected templates
   - Follow-up actions required

3. Template updates to maintain consistency:
   - `.specify/templates/plan-template.md` (Constitution Check section)
   - `.specify/templates/spec-template.md` (scope/requirements alignment)
   - `.specify/templates/tasks-template.md` (task categorization)
   - `.claude/commands/*.md` (command workflows)

### Complexity Justification

When Constitution Check identifies violations, justification MUST include:

- What constraint is violated (e.g., "4th library project")
- Why it's needed for this specific feature
- What simpler alternative was rejected and why

Unjustified complexity blocks progression to implementation.

### Compliance Review

Constitution compliance is verified at multiple checkpoints:

- Specification phase: Quality checklist validation
- Planning phase: Constitution Check gate (twice: before research, after design)
- Analysis phase: Cross-artifact consistency validation

All `/speckit.*` commands MUST enforce constitutional requirements relevant to their phase.

**Version**: 1.0.0 | **Ratified**: 2025-10-25 | **Last Amended**: 2025-10-25
