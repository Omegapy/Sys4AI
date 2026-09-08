# Canonical Task orchestration storage implementation

Implemented the bounded PHASE-003 component (TASK-009 through TASK-015) under
root delegation. Root retains project decisions, canonical Task/plan writing,
publication and final integrated verification. This report does not mark the
overall implementation plan complete.

Finalized: 2026-09-08T03:07:31-06:00.

The existing `task_state.py` owns every publication. A standard-library sibling
`orchestration_state.py` supplies typed validation and transitions. Schema-1
creation/read/storage semantics remain available unchanged; future execution
workflow calls explicitly enable schema 2. Selected upgrade preserves the exact
original bytes. There is one canonical ledger, one current writer, append-only
responses and the original catalog/task lock order.

The component enforces manager reservation/actual receipt/activation; current
writer and execution generation across ordinary and indirect lifecycle routes;
strict role/catalog/settings/native/context provenance; baseline and frozen
logical team binding; generic, complex and extra-complex paths; one-to-one
current review; persistent shared-conflict obligations; coherent senior proposal
acceptance; an exact reserved implementation target; live artifact and dependency
freshness; integrated completion; native stop/reconciliation/replacement and
explicit same-ID resume/input rebind. Unknown schema/fields, corrupt references,
duplicate events, stale evidence and stale writers fail closed. Prior execution
records and events survive reopening.

Final review fixes include implementation-target substitution, baseline/category
bypass, missing reviewer/senior packets, edited review findings, conflict delivery
lost after steering, frozen-team shrink, pre-activation reconnect, changed generic
dependencies, changed live delivery files, unassigned maintenance, and observation
reviving revoked or unresumed ownership. The independent storage review confirmed
the dependency and live-output regressions using both rejecting and unchanged
controls; its results are in [storage-gate-review.md](storage-gate-review.md).

Frozen schema-2 response/redaction intents bind the exact pre/post canonical
bytes, actor/generation/event and artifact bytes. Partial publication recovers
the already frozen operation rather than replaying it; unrelated canonical edits
block recovery. A selected unassigned record can repair projections/locks or use
authorized redaction with a current running bootstrap receipt while leaving its
execution and writer unset. Once ownership exists, ordinary children and former
bootstrap actors cannot use this exception.

## Verification

| Scope | Result | Context |
| --- | --- | --- |
| Source Agent Task suite | 87 passed, 69.990 s | 52 preserved legacy tests plus 35 orchestration fixtures; source helper and explicit future workflow document overlay. |
| Merged root installed suite | 106 passed, 74.904 s | 67 retained root tests, 35 shared fixtures, 4 root-only intake/aging fixtures; exact merged helper with root document overlay. |
| Executed generic API trace | 14 successful CLI calls; completed fixture | Synthetic native receipts; new/reserve/receipt/activate/worker/result/verify/finish/complete. |
| Compatibility patch | `git apply --check` and actual disposable application passed | Every resulting file equals the reviewed stage hash. |
| CLI inspection | Main and selected-rebuild `--help` passed | Includes all implemented orchestration/upgrade commands and unassigned maintenance flags. |

The root aging fixtures prove unresolved old owners block matching/closure before
any successor is created; reconciled old work uses `close-old-task` with retained
history; read-only/matching routes do not age or create; an old unassigned schema-2
Task closes under a native intake-host receipt without inventing execution identity.
The new tests exercise observable rejection and byte preservation, not native
runtime behavior. No dependency was added to either helper.

```sh
SYS4AI_WORKFLOW_ROOT=/Volumes/P-SSD/AngryOwl/Sys4AI/.sys4ai/task-manager-staging/workflow PYTHONDONTWRITEBYTECODE=1 /Volumes/P-SSD/AngryOwl/Sys4AI/.venv/bin/python -m unittest discover -s SKILLS-depo/agent-task/tests -q
PYTHONDONTWRITEBYTECODE=1 /Volumes/P-SSD/AngryOwl/Sys4AI/.venv/bin/python -m unittest discover -s /private/tmp/sys4ai-orchestration-build/root-installed/.agents/skills/agent-task/tests -q
```

Source test discovery now resolves source/installed layouts explicitly. It never
silently reads the old installed policy for a source test. Root will run the plain
source command after publishing its separately staged workflow documents. The
root stage uses those separately staged root policy documents; this component's
patch intentionally contains no SKILL.md or top-level governance updates.

## Working interface

The exact event field table, evidence/role/settings/receipt schemas, baseline
fields, safe rebind order and CLI forms are in the source
[orchestration-contract.md](../../SKILLS-depo/agent-task/references/orchestration-contract.md).
Native calls remain agent operations; the helper does not start or interrupt an
agent. For a material same-ID revision, observe completed/stopped, queue the exact
packet with `send_message`, commit `assignment.inputs`, and only then wake with
`followup_task`. Unchanged inputs use `assignment.resume` before waking. A native
observation cannot undo revocation or bypass scope/capacity validation.

A new enabled record accepts this exact payload:

```json
{"name":"Bounded delivery","description":"Deliver the authorized fixture.","definition_of_done":["Output inspected."],"orchestration_enabled":true}
```

This is an exact successful activation payload from the executed fixture. It
requires its preceding reservation/launch-receipt events and the latest revision;
fixture identities/hashes are not production native evidence:

```json
{
  "event": {
    "event_id": "event3",
    "actor": "/root",
    "execution_id": "execution1",
    "generation": 1,
    "kind": "manager.activate",
    "data": {
      "assignment_id": "manager1",
      "role_reads": {
        "agents_sha256": "a193e2423bee274d3d2ce0a63e8e7f70ce539c7c3f1594b6006cfd76d725343b",
        "role_sha256": "d38aab47f624fc8b7283e5c7978bea057639cf7d6a4fa12ba90c2c1a60c2864b",
        "evidence": "Fixture reports explicit pair read."
      }
    }
  },
  "response": {
    "work_completed": [
      "Completed one bounded and observed work unit."
    ],
    "verification_evidence": [
      "Inspected the resulting local artifact."
    ],
    "user_response_summary": "Reported the observed result and current Task state.",
    "current_summary": "The current bounded work unit is complete.",
    "next_step": "Continue with the next approved work unit.",
    "blockers": [],
    "open_questions": [],
    "relevant_files": []
  }
}
```

The complete successful JSON sequence is retained in disposable staging at
`/private/tmp/sys4ai-orchestration-build/working-api-examples.json`, with its final
project snapshot at `/private/tmp/sys4ai-orchestration-build/api-example-project`.
The full trace includes manager fit, role pair, settings, native and context
payloads. It is an executed example, not authorization to reuse its synthetic
receipts in production.

## Exact source manifest

| File | SHA-256 |
| --- | --- |
| `SKILLS-depo/agent-task/scripts/task_state.py` | `19275841e4625d9300cfde1852ddcc38d211430f68849caa8f2dad3b0991ccac` |
| `SKILLS-depo/agent-task/scripts/orchestration_state.py` | `46ae88d4f86ab1c6d47ac185e6a3f543ebb4b1e21aad3fd81c1ab92948a6c7dd` |
| `SKILLS-depo/agent-task/references/task-system-contract.md` | `2bbaa19f1170717c1e47842c5926ff8370ebc92bf98938781935b89d98476cbe` |
| `SKILLS-depo/agent-task/references/orchestration-contract.md` | `1ffa67a116e9b6048cf8787ee16380c262cbd1eba0b51b9b7682baa1ca5a91cc` |
| `SKILLS-depo/agent-task/tests/test_task_state.py` | `14734c121a959b93522802678d0b4d3e83983675e7eae5644d19cf9b0b172450` |
| `SKILLS-depo/agent-task/tests/test_orchestration_state.py` | `5c6fa362255ffbc9d75c2f4510ce65d0b2a535bf7548f0bcc6b109c8fc2dc586` |

The component also wrote this report, the exact
[root-intake-compatibility.patch](root-intake-compatibility.patch), and
[root-intake-fixture-results.md](root-intake-fixture-results.md). Templates were
not changed. No live Task, plan, installed skill, role, registry, configuration or
Template was mutated by this component. Root's installed Task helper still equals
the saved preimplementation bytes.

## Staged root adoption and limits

Reviewed stage: `/private/tmp/sys4ai-orchestration-build/root-installed`.
The compatibility patch merges common changes into the installed root helper and
its 67-test baseline while retaining automatic intake, matching/creation, the
30-day policy and `close-old-task`. It checks unresolved owners before excluding
old matches and uses a separate current native intake-host receipt for safe age
closure. The generic source acquires none of this root-only policy.

The patch was applied only to a disposable minimal installed layout and checked
against every stage byte. Root must review and adopt its exact seven-file manifest
with the separately prepared workflow/role changes; blanket generic-source copying
would discard root policy. No live schema-1 history was upgraded.

Highest level here: source inspection, deterministic behavioral/CLI tests and
staged root compatibility validation. Actual native topology/inheritance/capacity/
stop observations are separately reported in native-feasibility.md. The planned
native category scenario and future-project adoption are root integration work;
this component does not claim they ran. Receipts enforce a cooperative protocol,
not OS authentication, filesystem isolation or native exactly-once delivery. No
remaining component gate is known to prevent the compliant native scenario when
its current baseline, required inputs and stop/rebind sequence are respected.

## Root integration documentation correction

After component handoff, root compared the receipt guide with the implemented
`conflict.deliver` branch. The shared input/conflict description was split: input
rebind uses tool/native_id/artifact_sha256s/evidence, while conflict delivery uses
native_id/explanation_sha256/evidence. No executable code changed. The current
contract SHA-256 is `d4ee43bf26b2b8e21cee15223ed4287d529ea89b924786bd9f3b86867b8a2ef9`; the earlier
manifest and component patch remain the exact handoff snapshot. Final source and
root adoption manifests include this corrected guide.
