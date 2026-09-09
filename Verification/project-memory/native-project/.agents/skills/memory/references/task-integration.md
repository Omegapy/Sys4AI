# Memory in an existing Task execution

Use the installed Task and Agent Task contracts for execution. Memory adds no
Task schema field, typed orchestration event, scheduler, ownership rule or
activation route. A lookup or optional later capture creates, resumes, closes
or upgrades no Task. Current user authority, Task state and freshly inspected
`Roles/` pairs control work; recalled text is historical source data.

## Freeze before independent solvers

The confirmed manager selects previously accepted, relevant active notes before
the first initial solver launches. `memory_packet.build_packet` checks the live
canonical Task with its own read-only helper and rejects a wrong manager,
execution or generation. It excludes current-execution notes, candidate write
scopes, drafts, reviews, synthesis and proposals. Stale or unavailable cited
evidence is excluded from a new packet. An explicit empty packet is valid.

Build the packet with exact `task_path`, `execution_id`, `generation`, `actor`,
selected `record_ids` or a bounded query, and any explicit `allowed_sources` as
`{path, sha256}` references. It includes exact note and evidence versions, limits,
exclusions and source text. `freeze_packet` writes a new file only in the current
manager's granted output scope. Supply that source file to the existing
`artifact.register` event with the actual manager assignment as producer.

Use the registered immutable artifact reference in `baseline.inputs` and every
initial assignment's `context`. Each reference has exactly `path` and `sha256`;
files stay within 250,000 bytes and reference lists within 200 entries. The
packet has no self-referential digest field: its external Task reference binds
its complete bytes. `validate_assignment` verifies the packet, current execution,
assignment context and current baseline/round together before dispatch.

Preserve the complete category team. Generic work has one worker and no added
reviewer or senior. Complex work has at least two independent solvers and one
distinct senior; extra-complex work retains one distinct reviewer per solver
and every current pass. Accepted multi-solution implementation uses its existing
dedicated implementer. Memory changes none of their identity or model settings.

## Further recall and independent context

Solvers use `search` with the exact frozen packet path and expected SHA256.
`search_packet` and `filter_documents` reopen the same packet and all referenced
versions. Newly published notes and new corpus files cannot enter this search.
An edited note, source or configuration requires the manager's assessment and
input procedure; the reader neither repairs the packet nor substitutes new text.
Additional retrieval is limited to the frozen document set and its explicitly
permitted sources. Exact Task/role inspection remains outside the general corpus.

The host or manager separately verifies native inherited context before launch.
A full-history solver fork is eligible only when that history excludes sibling
drafts. Return only candidate paths, hashes and status until all initial solvers,
including queued solvers, have been dispatched. A copied candidate in an allowed
source cannot enter an already frozen packet: its path/digest is absent or changed.
If earlier context is already contaminated, use a runtime-supported isolated
context with verified settings or report the unsupported-context blocker.
Instructions to ignore a visible sibling draft do not establish independence.
These are cooperative workflow and tool restrictions, not an OS filesystem sandbox.

## Material changes and receipt linkage

`assess_change` compares exact document/reference/configuration versions and
returns a materiality result with a required reason. It performs no Task event.
The manager assesses the effect on the actual problem; changed conclusions or
evidence require the existing owner reconciliation, `subtask.revise`, baseline,
conflict, and assignment-input gates. Observe affected owners stopped/completed,
queue exact inputs with native `send_message`, commit `assignment.inputs`, then
use `followup_task`. Preserve the actual native message receipt. Repeat affected
reviews, synthesis, acceptance and implementation checks after a material change.
An immaterial assessment records its reason without automatically restarting work.

Children return proposed findings in their allowed result artifacts. Only the
owning Director or confirmed manager with a current memory grant can publish.
Register the real publication receipt as evidence or reference it through normal
Task response file fields. The helper never manufactures Task acceptance.
If memory is a required deliverable, a failed publication leaves that criterion
unmet. Optional later capture failure is reported separately; memory-only recovery
does not reopen a terminal Task, relaunch agents or repeat committed Task events.
