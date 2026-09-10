# To-TRD completion workflow repair

The user reported that To-TRD repeatedly remains in `draft` instead of reaching
`trd_done`. In this conversation, implementation choices were recorded as
requirements gaps even though the required outcomes could already support a plan.
The existing helper's 42 tests pass, including successful document approval.
The repair therefore addresses the capture and completion workflow and makes
the helper's existing completion gates visible.

## Requirements and bounded implementation plan

| ID | Required result and source | Work and acceptance |
| --- | --- | --- |
| FIX-001 | The user's reported design-versus-requirements confusion is resolved. | Update skill instructions, conversation guidance, and body-template guidance. Constrained implementation choices belong in Decisions; actual missing behavior, scope, acceptance, or authority remains a requirements gap. |
| FIX-002 | A settled capture has a clear route to `trd_done`. | Describe the saved-document review and approval step, accept unambiguous approval of the presented revision without making the user repeat a hash, and verify the persisted state. Explicit draft-only requests and read-only operations remain read-only with respect to lifecycle. |
| FIX-003 | The reason for a draft state is inspectable. | Add derived completion diagnostics to helper summaries and failed completion receipts, sharing the actual gate logic. Test ready, blocked, approved, retired, legacy, and stale-write behavior in temporary projects. |
| FIX-004 | Existing authority and document compatibility are preserved. | Keep schema 2, operation IDs, exact selectors, digest checks, explicit approval, migration controls, and current TRD bytes unchanged. Draft TRDs remain usable as unsettled planning sources. |
| FIX-005 | The reusable fix reaches the affected installation. | Edit only `SKILLS-depo/to-trd/`, copy the exact changed files into root `.agents/skills/to-trd/`, and check the existing template update pipeline. Preserve other project copies and unrelated working changes. |

The root Project Director owns implementation and final integration. The work
is authorized by the user's request to fix the skill. It does not create or
approve a managed TRD or implementation plan, reopen a completed Task, install
dependencies, or change Git or publication state.

The file boundary is the skill entrypoint, its maintenance guidance and README,
the two linked references, the body template, the helper, and focused tests.
The main risk is concealing a real requirement gap as a planning decision;
instructions and negative cases must preserve that boundary. The helper reports
structural eligibility only and does not infer meaning or user consent.

## Verification

Before editing, all 42 reusable-source tests passed. The template updater
reported `current`, with no additions, updates, deletions, or conflicts. Source,
root, and template skill files matched except for an ignored source `.DS_Store`.
A temporary SHA-256 baseline covers 819 existing tracked and untracked files.

The repaired skill is version 2.1.0. It retains schema 2 and all operation IDs.

| Check | Observed result |
| --- | --- |
| Reusable source To-TRD suite | 46 tests passed. |
| Root-installed To-TRD suite | 46 tests passed. |
| Template-installed To-TRD suite | 46 tests passed. |
| Root repository contract suite | 13 tests passed. |
| Skill Creator structural validator | Source, root, and template packages valid. |
| Python compilation | All six changed Python files compiled without writing bytecode. |
| Template update check | `current`; no additions, updates, deletions, or conflicts outstanding. |
| Package adoption | Eight changed files match across source, root, and template. |
| Root TRD catalog | Canonical documents valid; index current. |
| Preservation | Exactly 24 baseline files changed within the three skill copies; the other 795 baseline files retained their bytes. |

The new regression scenarios exercise all reported content blockers, read-only
diagnostics, rejection without approval, successful approval with implementation
choices left to planning, stale approval rejection after a revision, unresolved
authority, and retired/legacy states. Successful transitions are read back from
canonical files, with a current index and no product implementation artifacts.

## Requirement verification

| Requirement | Evidence and outcome |
| --- | --- |
| FIX-001 | The entrypoint, wayfinding reference, contract, and template distinguish requirements from constrained design choices. `test_planning_choices_allow_document_approval` passes; `test_completion_preserves_authority_gaps` retains the negative boundary. |
| FIX-002 | The entrypoint's Finish the document workflow requires the final review/approval handoff and immediate persisted transition when approval already applies. CLI tests verify `draft` to `trd_done`, readback, index consistency, and stale-hash rejection. |
| FIX-003 | `completion_blockers()` is shared by summaries and the transition gate. Tests confirm identical diagnostics on reads and failed approval, with no writes during inspection. |
| FIX-004 | Existing lifecycle, migration, identity, privacy, lock, no-op, and plan-handoff tests pass. Root TRDs, their index, Tasks, registry, and unrelated project files retain their baseline bytes. |
| FIX-005 | The exact eight-file root adoption was guarded by baseline hashes. The existing watcher synchronized the template, its check reports current, and all three copies pass their focused suite. Other product-project copies remain unchanged. |

## Verification limits

The highest verification level is targeted runtime tests through the helper CLI
in isolated projects, with the relevant repository contract suite passing.
Instruction changes were inspected against the reported conversation; a fresh
end-to-end Codex skill invocation was not exercised. No host discovery, future
project creation, dependency installation, Git write, or publication was performed.

The existing ontology TRD `TRD-20260905-236FDE55` remains draft revision 1 with
SHA-256 `fd8a825ee509e56de6d8ecfb4a71a0ca8bc941020da9de3a50c49a15e90cdd25`.
This skill repair neither rewrites its four recorded gaps nor treats the user's
repair request as approval of that document. Its current diagnostic correctly
identifies the persisted `Not yet specified` section. A subsequent authorized
document revision can classify those items using the repaired workflow.
