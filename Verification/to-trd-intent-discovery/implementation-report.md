# To-TRD intent-discovery implementation

Later authorized adoption: the root and Template now both match version 2.2.0.
See [the adoption report](adoption-report.md). The root-preservation statements
below describe the earlier source-implementation operation.

The planned source changes are delivered as **2.2.0** in
[SKILLS-depo/to-trd](../../SKILLS-depo/to-trd/SKILL.md), and the registered Template
contains the same 16 resources. **Full plan verification remains incomplete:
none of C01–C14 has been exercised in a separate manual Codex session.**

The entry and metadata now make understanding intent the first responsibility.
The procedure checks applicable material requirements, pauses after asking a
user-owned question, incorporates answers into affected requirements and
acceptance, handles partial and changed answers, preserves clear-request and
incomplete-draft paths, and obeys follow-up prohibitions. Semantic review keeps
unresolved intake out of requirements while preserving legitimate questions in
the intended deliverable. Exact-document approval remains a separate operation.

The package adds [synthetic examples](../../SKILLS-depo/to-trd/references/interaction-examples.md)
and [all 14 scenario definitions](../../SKILLS-depo/to-trd/tests/interaction-scenarios.md),
updates the contact-export example and its dependent regressions, aligns the
version and documentation, and preserves schema 2 and the helper API.

## Delivered evidence

| Check | Observed result |
| --- | --- |
| Baseline source suite | 46/46 passed before edits. |
| Final source suite | 46/46 passed using the source tests and helper. |
| Final Template suite | 46/46 passed using the Template's own tests and helper. |
| Syntax, JSON, package metadata and links | Passed; compiled output confined to disposable paths. |
| Protected helper, attribution and MIT notice | Byte-identical to baseline. |
| Source/Template parity | All 16 final resources match. |
| Template updater | Current, no pending work/conflicts/recovery; existing watcher observed ready with a fresh successful check. No manual apply or service-control action. |
| Preserved paths | All 24 plan-preserved paths unchanged; active root retains all 14 baseline resources. |
| Source coverage | All 22 requirements and 73 exact acceptance criteria audited; no waivers. |
| Actual-host/fresh-session cases | 0/14 executed; blocked pending a selected manual disposable Codex test task. |
| External skill YAML validator | Unable to start: PyYAML absent in both project and bundled runtimes. No installation performed; package-native metadata checks pass. |

The highest executed level is the complete package regression suite with direct
filesystem verification of mapped delivery. For the changed conversational
behavior, the highest level is static review. The rewritten instructions and
passing Python tests do not prove that the reported behavior is fixed.

## Exact scope and state

[Baseline](baseline.json) records Git HEAD
`947e0ea217eeb52369b33fd76d24079cea1d7e10`, the pre-existing mixed worktree,
source/root/Template package hashes and protected paths. This execution changed
11 existing source files and added two resources, listed in
[candidate-manifest.json](candidate-manifest.json). The
[baseline-to-candidate patch](source-changes.patch) excludes the earlier 2.1.0
changes. No new Git revision was created.

The source TRD remains **draft revision 1** with digest
`1467b2f536dfdf51f4af62a6c77bbfc8bdbe4b186f54e6af1045c41d7489476e`.
The canonical implementation plan remains **draft revision 2** with digest
`aad5246ce3df7d86be79a5c34d6e5977b7d819044e78842236473d688aea30dd`.
The user's current instruction authorized implementation of that exact plan;
it did not activate a separate Task or the named plan-tracking skill. The
[plan skill](../../.agents/skills/to-implementation-plan/SKILL.md) states:
"Do not create or mutate a managed plan without explicit activation." Its
canonical task rows therefore still say planned, although source work is
delivered here. This mismatch is reported, not silently synchronized. Read-only
plan validation reports current projections; root TRD validation is canonical-valid.

There was no active-root or ordinary-product refresh, global installation,
existing-TRD mutation, Task mutation, registry/root-governance edit, dependency
installation, agent launch, watcher installation/control, Git mutation or
external publication. Disposable candidate copies are evaluation fixtures, not
product adoption. Future-project creation and actual-host discovery were not tested.

## Work still required

TASK-004's baseline manual observations and TASK-014–TASK-019's actual candidate
loading, C01–C14 conversations and fresh-session verification remain incomplete.
The available workflow has no selected disposable test task. DEC-003 calls for
manual sessions and the plan excludes automatic task creation; the user has been
asked to identify the test task. No CLI process, evaluator or subagent was used
as a substitute, and no synthetic consent was claimed.

The [host protocol](host-protocol.md) provides exact ready baseline/candidate
paths and one-message-at-a-time instructions. Run the actual cases, retain
minimal visible evidence and any failures, make only supported targeted
corrections, rerun affected checks, and reconcile the
[acceptance matrix](acceptance-matrix.md). Full completion requires the missing
evidence or an explicit user-approved change to those requirements.

Details: [source verification](source-mechanical.md),
[semantic review](semantic-review.md), [host results](host-results.md),
[Template verification](template-verification.md), and
[preservation audit](preservation-audit.md).
