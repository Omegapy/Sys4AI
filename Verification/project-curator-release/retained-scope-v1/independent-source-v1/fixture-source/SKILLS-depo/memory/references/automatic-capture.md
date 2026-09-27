# Shared learning review and memory completion

<!-- sys4ai:learning-review-v1 -->

This is the single completion entry for memory and an installed compatible
What Did You Learn module. The module supplies learning judgment; this entry
coordinates the existing memory publication route. It also accepts explicit
review or save requests. Do not invoke the learning skill recursively or run
another capture after this procedure returns.

New memory installations enable `integration.automatic_capture` by default.
The setting is a JSON boolean (`true`/`false`); the setting command accepts
the user-facing words `on` and `off`. It controls the agent's workflow, not a
timer, filesystem watcher, transcript recorder, runtime hook or backend service.
These are explicit and instruction-based checkpoints, not guaranteed event
detection. A quiet period is not acceptance; an unavailable interruption or
compaction signal is an execution limit.

## Enter once with the actual mode and work boundary

Identify the real owning project, responsible Director or current confirmed
Task manager, relevant work unit, source versions and read/write scope. Reuse
an already completed checkpoint result for the same finding/evidence instead
of starting a second publication. Keep retry identity in the existing work
result or publication journal; add no new event ledger.

- Manual review: a bare "What did you learn?" question requests an evidence-based
  review only. Return supported lessons, applicability and limits or a valid
  no-durable-lesson result. The question alone permits no save or project edit,
  regardless of the automatic-capture setting.
- Explicit save: use normal reviewed `publish` or `supersede` authority. Capture
  off does not prevent this separately requested operation and is not toggled.
- Automatic checkpoint: check the actual current `capture-status`. Review at
  substantive completion, a settled accepted decision, clear material correction,
  significant observed failure or verified reusable success when likely to
  affect future work. Persist only when enabled, useful, supported and currently
  authorized. Off prohibits automatic persistence under either skill name.

Ordinary status, list, readiness, lookup and inspection-only requests remain
non-mutating. They publish no note, preserve no new draft file, maintain no
index, modify no configuration and activate no Task. The manual question is
not silently reclassified as a material-work checkpoint to permit a save.
Unsettled clarification remains pending; preserve concise attributed evidence
at a known handoff only within an already granted evidence/output scope.

For completion, the Director reviews after relevant verification and before
final handoff. In an explicit Task, the confirmed manager performs the same
checkpoint after its verification and before committing the terminal Task
response, while it still owns the execution. No user reminder is needed.

## Select the compatible review contract

For installed use, inspect this project's
`.agents/skills/what-did-you-learn/` and `reference-assets/LEARNING-depo/`.
The learning package's read-only `scripts/learning_contract.py` resolves exact
resources and declared memory interfaces without importing dependency code.
For source-only development, explicitly select the matching
`SKILLS-depo/what-did-you-learn/`, `LEARNING-depo/` and `SKILLS-depo/memory/`
layout under the same depot root. Do not silently substitute source assets for
an incomplete installed package or search another project's files.

When compatible capability is present, read the resolved module's `policy.md`
and `review-contract.md` directly. Perform its steps 1-5 once, coordinate step
6 through the guarded publication below, then finish its bounded steps 7-8.
The module does not call this entry again. Review precedes any publication.

If both learning packages are absent, retain memory-only behavior: inspect
current accepted notes and actual work evidence; select a useful new lesson,
accepted decision, verified result or observed failure with lasting value.
Skip duplicates, trivial conversation, temporary progress and unsupported
conclusions. Prepare the exact record with sources, applicability and limits
through the existing [evidence contract](evidence-and-lifecycle.md).
Do not manufacture a finding to satisfy the checkpoint.

If learning resources are partly present or incompatible, report the exact
resource/interface limitation. The supported memory-only workflow remains
available when its own dependencies and authority are valid; do not report the
learning module or a required learning deliverable as complete. Resolution is
read-only and never upgrades preserved packages, binds governance or installs
a service. Shared-checkpoint presence, actual capture setting, current
publication authority and optional backend readiness remain separate claims.

## One guarded publication

1. Compare accepted memory and current sources before creating a record. A
   duplicate or no-durable-lesson result completes the checkpoint with no write.
   Additional evidence is not automatically a new lesson. Review conflicting
   evidence through supported supersession/retraction; preserve the predecessor
   and actual prior versions. Semantic deduplication is the owner's review,
   while operation retry protection is the helper's responsibility.
2. Children return proposals in their assigned results. The owning Director or
   confirmed manager alone reviews final bytes, real source hashes and locators,
   truthful claims, applicability and limits. Discussion-only capture requires
   concise authorized local evidence; never invent an accepted decision, source
   hash, result receipt or Task origin. Follow [publication examples](publication-examples.md)
   and [operations](operations.md) to bind the actual reviewed payload, prior
   hashes, current config/authority and fresh observed native receipt. A current
   grant needs no redundant per-note user approval. A rejection never permits
   rewriting authority hashes, grants or configuration to make the write pass.
3. For an automatic save, use one fitting existing trigger:

   | Trigger | Actual meaning |
   | --- | --- |
   | `work-completed` | Substantive work has completed and its relevant checks ran; a verified reusable success can qualify here. |
   | `task-completed` | The confirmed manager has verified its Task and is at the checkpoint before the terminal response. |
   | `decision-recorded` | A substantive decision is actually accepted and supported by local design evidence. A correction qualifies only if it established that accepted decision. |
   | `failure-observed` | A significant failure or violated constraint was actually observed with appropriate result evidence. Its suspected cause may remain uncertain. |

   A finer event distinction belongs in body/evidence content. An unfinished
   correction is no accepted decision; a suspected defect is no observed failure.
   When no supported trigger fits, keep the review bounded and do not invent an
   event value. Use a later fitting checkpoint, or normal publication for an
   explicitly requested save. Invoke:

   ```text
   python .agents/skills/memory/scripts/memory.py --project-root ROOT capture PAYLOAD --trigger TRIGGER --grant-file GRANT --actor ACTOR
   ```

   The payload is the existing reviewed `publish` or `supersede` transaction.
   Explicit saves use that named command with the same payload/grant/actor
   contract instead of `capture`; a reviewed retraction uses `retract` under
   its own actual authority. No command, trigger or memory schema is added.
4. Reopen the returned publication receipt and canonical record and confirm
   exact or lexical retrieval before reporting a save. Repeated delivery reuses
   the same operation ID and exact payload. The durable journal reports which
   records committed; a partial error is not "nothing saved". Use memory-only
   recovery of that exact operation with a current grant, preserving human
   edits and actual commit status. Report an optional failure separately from
   accepted work; a required memory deliverable remains unmet. Recovery never
   reopens terminal Tasks, relaunches agents or replays committed Task events.

The initial Task manager reservation includes bounded `MEMORY/` publication
and `control_records/memory/` evidence scope when this checkpoint is assigned.
Use existing `fit.writes` and native activation gates. Do not add a learning
manager or a second canonical Task writer. Independent solver packets stay
frozen; new notes and sibling proposals do not enter them. Apply the existing
[Task integration](task-integration.md) gates to material new inputs.

## Preference and readiness

`capture-status` is read-only and returns the actual setting and configuration
SHA256. Only on an explicit user preference change, call:

```text
python .agents/skills/memory/scripts/memory.py --project-root ROOT set-capture off --expected-config-sha256 SHA256
```

Use `on` to restore capture. The helper changes only that boolean, rejects stale
configuration and pending recovery, and preserves notes and other settings.
Explicit user-requested publication remains available when capture is off.
Reads never toggle capture or update an index. Capture writes canonical Markdown
and its journal only. An enabled semantic backend needs its normal separately
authorized reindex after configuration or corpus changes; report that readiness
separately from canonical/exact/lexical retrieval.

After successful initialization, show the verified capture setting. When on,
say: "Memory automatic capture is on. Would you like to turn it off?" Initialization
is already complete; keep capture on unless the user opts out. Preserve an
existing off preference on reruns. An incompatible preserved installation needs
a scoped upgrade; never substitute an "on" readiness claim for that limitation.

### Curator completion coordination

Curator uses this same completion checkpoint and capture preference; it does not
create a parallel saver. Deduplicate by exact completion/objective/artifact/source
identity, coordinate the current Task owner and return only remaining obligations
for already-repaired findings. Capture off prevents equivalent automatic memory
or ontology persistence through Curator. Explicit correction retains its own
selected owner authority. Suspected causes remain bounded investigation and later
benefit stays unobserved until evidence exists.
