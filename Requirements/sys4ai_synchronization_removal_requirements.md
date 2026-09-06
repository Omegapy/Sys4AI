# Sys4AI synchronization removal requirements

## Document control

| Field | Value |
| --- | --- |
| Status | Implemented and verified on 2026-08-29 |
| Scope | Remove the Sys4AI synchronization capability and its project dependencies |
| Project root | `/Volumes/P-SSD/AngryOwl/Sys4AI` |
| Related plan | `Implementation_Plans/sys4ai_synchronization_removal_implementation_plan.md` |

## User intent and observed baseline

`U-001` - The user decided not to use the synchronization skill for now and
authorized its removal, including dependent processes and project-used files.
The user requested an implementation plan followed by implementation.

At baseline, the planned root skill package
`.agents/skills/sys4ai-project-sync/` did not exist. The underlying capability
existed as `tools/depot_sync.py`, `depot/manifest.json`, tests, operating
documentation, governance rules, and synchronization-specific requirements and
plans. The registered template project was present at
`Projects/Sys4AI-Template-Project/`, while the old synchronization registry
path omitted the `Projects/` prefix.

## Scope boundary

In scope:

- remove the complete local synchronization control and operating process;
- remove direct executable, configuration, test, duplicate-source, and
  synchronization-only documentation artifacts;
- remove active governance and template instructions that require or describe
  synchronization;
- keep the project registry as factual workspace inventory only; and
- verify the result against the live root and template project.

Out of scope:

- deleting reusable skills, active project-local skill installations, SOUL
  files, role bundles, Task data, TRDs, or the template project;
- creating a replacement copy, install, update, or propagation framework;
- changing the behavior of independent skills;
- committing, pushing, publishing, deploying, or changing remote systems; and
- changing unrelated pre-existing untracked files.

## Requirements

### Capability retirement

#### REM-001 - Retire the synchronization skill interface

- Requirement: The project must contain no installed, advertised, planned, or
  callable `sys4ai-project-sync` skill interface.
- Source: `U-001`; live skill inventory.
- Acceptance: No `sys4ai-project-sync` directory or active instruction remains,
  and the repository contract verifies its absence.

#### REM-002 - Remove the synchronization engine

- Requirement: Delete the Python copy engine and leave no project command that
  invokes it.
- Source: `U-001`; `tools/depot_sync.py`; current README commands.
- Acceptance: `tools/depot_sync.py` is absent and no active project file refers
  to the command.

#### REM-003 - Remove synchronization configuration

- Requirement: Delete the source-to-target manifest and remove its authority
  from the project.
- Source: `U-001`; `depot/manifest.json`; root governance.
- Acceptance: `depot/manifest.json` is absent, no active process loads it, and
  no active guidance treats a file copy as manifest-managed.

#### REM-004 - Remove dependent tests and operating processes

- Requirement: Delete the synchronization-only test suite and replace any
  repository checks that require synchronization with checks for the
  post-removal workspace contract.
- Source: `U-001`; `tests/test_depot_sync.py`;
  `tests/test_repository_contract.py`.
- Acceptance: The direct suite is absent, the repository suite does not import
  or execute the removed engine, and the updated suite passes.

#### REM-005 - Remove synchronization-only records and duplicate inputs

- Requirement: Delete active requirements, plans, verification records, and
  exact duplicate contract sources whose project purpose was to define, prove,
  or feed synchronization.
- Source: `U-001`; manifest inventory; SHA-256 comparison of contract copies.
- Acceptance: The exact retirement list in the implementation plan is absent;
  the independent root contract copies remain.

### Post-removal governance

#### GOV-001 - Remove synchronization duties from root governance

- Requirement: Root `AGENTS.md` and `ROLE.md` must govern the Sys4AI workspace
  without manifest precedence, managed-copy duties, apply operations, or
  synchronization completion gates.
- Source: `U-001`; current root governance.
- Acceptance: Both active files describe project-local ownership and factual
  workspace registration, retain the Project Director, Task, TRD, and role
  contracts, and contain no operational synchronization instruction.

#### GOV-002 - Reclassify reusable collections without automatic authority

- Requirement: `SKILLS-depo/`, `SOULS-depo/`, `AGENTS-depo/`, and
  `ROLES-depo/` must remain reusable collections, but they must not
  automatically govern or propagate to active project copies.
- Source: `U-001`; preservation boundary.
- Acceptance: Current documentation states that catalog entries and active
  project files are independent until a future explicit change is authorized.

#### REG-001 - Keep a factual project registry only

- Requirement: Preserve `depot/projects.json` as workspace inventory, remove
  synchronization-specific managed semantics, and record the template's real
  path.
- Source: Workspace identity; live filesystem observation.
- Acceptance: The registry uses the current schema documented in
  `depot/README.md`, lists existing paths, and grants no copying authority.

#### TMP-001 - Remove synchronization from the template project

- Requirement: Update the reusable template guidance and the current ignored
  template working tree so they no longer depend on a parent manifest or depot
  apply process.
- Source: `U-001`; current template `AGENTS.md` and `README.md`.
- Acceptance: Both template guidance copies describe project-local ownership,
  and the template remains usable with its current skills, SOUL, role, and
  contracts.

### Preservation and evidence

#### PRS-001 - Preserve independent project capabilities and data

- Requirement: Preserve reusable skill packages, installed root and template
  skills, SOUL files, role bundles, Task data, TRDs, project code, and project
  documentation unless a file is on the exact retirement list.
- Source: User's removal boundary; project safety rules.
- Acceptance: A before-and-after inventory confirms that these retained
  capabilities and data still exist, and their focused tests pass where
  available.

#### PRS-002 - Preserve unrelated worktree and external state

- Requirement: Do not change unrelated pre-existing untracked files, Git
  history, index state, remotes, publications, or deployments.
- Source: User scope; initial `git status`; project authority rules.
- Acceptance: Final status shows the same unrelated untracked paths, no file is
  staged, and no external action was performed.

#### VER-001 - Detect stale active dependencies

- Requirement: Search the complete active root and template surfaces for stale
  synchronization paths, commands, authority claims, and skill references.
- Source: `U-001`; bidirectional verification requirement.
- Acceptance: Only the removal requirements, implementation plan, verification
  record, unrelated examples, or clearly historical text may name the retired
  capability; no active process or instruction does.

#### VER-002 - Verify the integrated project

- Requirement: Run the updated repository contract and the independent Task,
  role-catalog, and To-TRD skill tests.
- Source: Project completion standard.
- Acceptance: Every selected suite passes with observed output, and any check
  not run is reported as unverified.

#### VER-003 - Audit requirements and changed artifacts in both directions

- Requirement: Map every requirement to implementation and evidence, and map
  every changed or removed artifact back to an authorized requirement.
- Source: Root requirements-to-verification workflow.
- Acceptance: The final plan and verification record contain complete forward
  and reverse traceability with no silent deferral.

## Completion standard

Completion requires every requirement above to have current evidence, every
retirement target to be absent, every preservation target to remain, the
selected test suites to pass, and the final root and ignored-template changes
to be reviewed. A future decision to restore synchronization is a separate
project and is not part of this removal.
