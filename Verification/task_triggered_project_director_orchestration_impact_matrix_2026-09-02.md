# Task-triggered Project Director orchestration impact matrix

## Decision boundary

This matrix defines the complete source-only implementation write set for
`PLAN-20260902-2C15FED4`. It was prepared after the protected baseline and
before editing a reusable source. `Changed` means the artifact must receive an
implementation edit. `Added` means a new implementation artifact. `Unchanged`
means the inspected existing contract already satisfies the mapped need and
must retain its baseline bytes.

## Requirement-to-artifact matrix

| Requirement | Required outcome | Changed or added artifacts | Explicit unchanged disposition | Verification |
| --- | --- | --- | --- | --- |
| `REQ-001` | Explicit Task activation loads the established root Director. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | Installed `.agents` copies remain unchanged. | Root-resolution, role-read, and no-replacement scenarios |
| `REQ-002` | Define a project Task consistently. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | Agent Task schema remains unchanged because it already distinguishes canonical Task identity. | Task-meaning and state-separation assertions |
| `REQ-003` | Preserve end-to-end Director ownership. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | Agent Task helper remains unchanged; the root Director already owns its mutations. | Ownership and child-authority scenarios |
| `REQ-004` | Assess complexity, uncertainty, decomposition, risk, review, and evidence. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | No numeric-scoring helper is added. | Three-path classification scenarios |
| `REQ-005` | Perform simple low-risk work directly. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | No mandatory delegation setting is added. | Simple-direct scenario |
| `REQ-006` | Decompose suitable complex work into bounded contracts. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | Role templates remain unchanged because the Director delegation contract already contains the required fields. | Decomposed-complex scenario |
| `REQ-007` | Select the narrowest suitable role from a fresh catalog. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | Entire `SKILLS-depo/manage-subagent-roles/` package remains unchanged; its live inventory and task-profile contract already covers every delegated function. | Cross-package role-selection checks |
| `REQ-008` | Create a role only for a reusable role gap. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | Entire role-management package remains unchanged; it already distinguishes role, skill, tool, dependency, permission, and Director-owned gaps. | Existing-fit and capability-gap scenarios |
| `REQ-009` | Use two or more independent candidates for unresolved uncertainty. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | No fixed agent count or persistent solver registry is added. | Uncertain-adversarial scenario |
| `REQ-010` | Honor feasible user orchestration instructions. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | Role-management parser and metadata remain unchanged. | Feasible and constrained user-override scenarios |
| `REQ-011` | Give every formally reviewed candidate its own reviewer. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | Role-management package remains unchanged because reviewer selection uses the existing generic role workflow. | One-to-one reviewer mapping scenario |
| `REQ-012` | Return rejected candidates to the originating solver and review again. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | Agent Task schema remains unchanged; Task Responses can record the failure, requests, child ID, and new review. | Failed-review revision scenario |
| `REQ-013` | Assign a distinct senior synthesis agent after all required reviews pass. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | Role-management package remains unchanged because synthesizer selection uses the existing task profile and role catalog. | All-pass synthesis scenario |
| `REQ-014` | Recycle irreconcilable conflicts to every affected solver. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | No separate conflict ledger is added. | Fusion-conflict recycle scenario |
| `REQ-015` | Record exactly one case-by-case implementation owner. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | Agent Task schema remains unchanged; implementation ownership is stored in the current Task Response and summary. | Director-owner, senior-owner, missing-owner, and multiple-owner scenarios |
| `REQ-016` | Complete only after authorized performance and current direct evidence. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | All eight declared Agent Task source artifacts remain unchanged; its existing completion payload already requires criterion-by-criterion evidence. Generated cache state is classified separately below. | Incomplete-evidence and child-report-only rejection scenarios |
| `REQ-017` | Preserve a durable orchestration record. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | Agent Task contract, helper, templates, metadata, and tests remain unchanged because existing append-only Task Responses and canonical summary fields can represent every required event without schema migration. Generated cache state is classified separately below. | Record-field coverage and continuation reconstruction checks |
| `REQ-018` | Keep state systems and action authority separate. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | Both conditional packages and all active, template, registered-project, Git, publication, and deployment state remain unchanged. | State-boundary and authority-negative scenarios |
| `REQ-019` | Iterate only on material change and stop truthfully. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md`; orchestration test module | No retry counter or hidden state is added to either conditional package. | No-progress, missing-authority, missing-capability, runtime-limit, and irreducible-conflict scenarios |
| `REQ-020` | Change both required reusable source targets. | `SKILLS-depo/task/SKILL.md`; `ROLES-depo/project-director-ROLE.md` | `SKILLS-depo/task/agents/openai.yaml` remains unchanged because its explicit-only description and default prompt remain accurate. | Scoped diff and direct hash checks |
| `REQ-021` | Decide every Agent Task and role-management candidate impact before editing. | This impact matrix | All sixteen named conditional package files remain unchanged for the file-specific reasons below. | Unique contiguous requirement rows and reverse review |
| `REQ-022` | Preserve active copies and unrelated depot assets. | Verification report | Active `.agents` packages, root guidance, template project, registry, TRD, prior Task, unrelated reusable assets, and unmanaged plans retain baseline state. | Post-change hash comparison and scoped Git review |
| `REQ-023` | Validate changed sources and representative workflows. | `SKILLS-depo/task/tests/test_task_project_director_orchestration.py`; verification report | Existing conditional-package and root tests are run but not modified. | Structural validation, focused suites, scenario matrix, and final audit |

The table has exactly one row for each contiguous requirement from `REQ-001`
through `REQ-023`. Forward review maps every requirement to work or a protected
unchanged disposition. Reverse review maps every authorized changed or added
artifact to one or more requirements.

## Conditional Agent Task package dispositions

The current response payload already contains `work_completed`,
`verification_evidence`, `user_response_summary`, `current_summary`,
`next_step`, `blockers`, `open_questions`, `relevant_files`, lifecycle state,
and an optional thread reference. Those fields can durably record the selected
workflow, contracts, child IDs, reviewer mappings and outcomes, revision
cycles, synthesis result, implementation owner, blockers, and completion
evidence. A new schema or helper field would add migration risk without adding
required capability.

| Candidate file | Disposition | Requirement-linked reason |
| --- | --- | --- |
| `SKILLS-depo/agent-task/SKILL.md` | Unchanged | Existing Director-only mutation, response, verification, and completion rules satisfy `REQ-003`, `REQ-016` through `REQ-019`, and `REQ-021` through `REQ-023`. |
| `SKILLS-depo/agent-task/references/task-system-contract.md` | Unchanged | Existing canonical summary and append-only response contract represents every `REQ-017` orchestration event while preserving `REQ-018` state boundaries. |
| `SKILLS-depo/agent-task/scripts/task_state.py` | Unchanged | No schema, transaction, lifecycle, containment, privacy, or rendering behavior must change for `REQ-016` through `REQ-019`. |
| `SKILLS-depo/agent-task/assets/TASK.md.template` | Unchanged | Current summary, blockers, questions, next step, and latest-response link are sufficient continuation views for `REQ-017`. |
| `SKILLS-depo/agent-task/assets/Task-Response.md.template` | Unchanged | Existing response sections can hold concise orchestration decisions and evidence required by `REQ-017`. |
| `SKILLS-depo/agent-task/assets/INDEX.md.template` | Unchanged | Catalog indexing is unrelated to orchestration stages and already preserves Task identity under `REQ-018`. |
| `SKILLS-depo/agent-task/agents/openai.yaml` | Unchanged | Explicit-only internal workflow metadata remains accurate and does not affect `REQ-003` or `REQ-018`. |
| `SKILLS-depo/agent-task/tests/test_task_state.py` | Unchanged | Existing 52-test safety suite remains the compatibility oracle; source-orchestration behavior is tested in the new Task package module. |

Pre-existing `__pycache__` files are generated residue, not implementation
candidates. A direct-source diagnostic invoked the suite's explicit
`py_compile.compile()` check and regenerated the existing
`scripts/__pycache__/task_state.cpython-312.pyc`; the cache count remained two
and no new residue was created. All eight declared source artifacts retain
their baseline hashes. The installed Agent Task package, including its cache,
retains its complete baseline directory digest.

## Conditional role-management package dispositions

The current role-management contract already inventories the live filesystem,
builds the complete required task profile, selects the narrowest valid role,
creates a non-overwriting bundle only for a reusable role gap, checks skill and
tool availability separately, builds bounded delegation contracts, enforces
exact model and reasoning inheritance, and supervises or collects native child
results. Solver, reviewer, senior synthesis, and implementation-owner work are
functions passed through that generic workflow, not new role types.

| Candidate file | Disposition | Requirement-linked reason |
| --- | --- | --- |
| `SKILLS-depo/manage-subagent-roles/SKILL.md` | Unchanged | Existing inventory, selection, creation, spawn, supervision, and collection modes satisfy `REQ-007`, `REQ-008`, `REQ-010`, `REQ-011`, `REQ-013`, `REQ-017` through `REQ-019`, and `REQ-021` through `REQ-023`. |
| `SKILLS-depo/manage-subagent-roles/references/role-schema.md` | Unchanged | No new reusable role field is needed; orchestration function belongs in each task profile and delegation contract. |
| `SKILLS-depo/manage-subagent-roles/scripts/role_catalog.py` | Unchanged | Live inventory, validation, exact selection inputs, and no-overwrite creation behavior already meet the mapped requirements. |
| `SKILLS-depo/manage-subagent-roles/assets/role-bundle/AGENTS.md.template` | Unchanged | No new role bundle or instruction field is required. |
| `SKILLS-depo/manage-subagent-roles/assets/role-bundle/ROLE.md.template` | Unchanged | Solver, reviewer, synthesizer, and implementer are selected capabilities, not hard-coded role kinds. |
| `SKILLS-depo/manage-subagent-roles/agents/openai.yaml` | Unchanged | Current user-facing description already covers finding, creating, and assigning roles. |
| `SKILLS-depo/manage-subagent-roles/README.md` | Unchanged | Package installation and use are not changed by the orchestration contract. |
| `SKILLS-depo/manage-subagent-roles/tests/test_role_catalog.py` | Unchanged | Existing 50-test suite remains the role-catalog compatibility oracle; cross-package orchestration use is tested in the new Task package module. |

Pre-existing `__pycache__` files remain untouched generated residue.

## Authorized write set

Implementation source and evidence writes are confined to:

- `SKILLS-depo/task/SKILL.md`
- `ROLES-depo/project-director-ROLE.md`
- `SKILLS-depo/task/tests/test_task_project_director_orchestration.py`
- `Verification/task_triggered_project_director_orchestration_impact_matrix_2026-09-02.md`
- `Verification/task_triggered_project_director_orchestration_verification_2026-09-02.md`

Managed-plan projections and the selected project Task record may change only
through their deterministic helpers as separately authorized governance state.
Every other source artifact is outside the implementation write set. The one
regenerated pre-existing Agent Task cache file is classified above as a
verification side effect, not source implementation.
