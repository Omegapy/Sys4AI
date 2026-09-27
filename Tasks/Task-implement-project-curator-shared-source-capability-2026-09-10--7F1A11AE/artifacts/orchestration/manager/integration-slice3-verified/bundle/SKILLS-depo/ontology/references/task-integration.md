# Frozen ontology in an existing Task

Ontology adds no Task schema field, event, scheduler, activation route, team
rule or writer. The current confirmed manager uses the installed Agent Task
helper to inspect ownership and register evidence through existing interfaces.
Reading an ontology or constructing a candidate packet creates no Task.

Before the first independent initial solver launches, call
`ontology_packet.build_packet(root, task_path=..., execution_id=...,
generation=..., actor=..., concept_ids=[...], allowed_sources=[...])`.
`concept_ids=[]` creates an explicit empty semantic packet; `query` may replace
the selection. The helper inspects the actual canonical Task with the installed
`task_state.py ... show` command and requires the active confirmed manager,
execution, generation, role-read receipt and writer. Wrong owners fail closed.

Selected records include immediate typed relationships, their predicates and
endpoints, replacements, and relevant bindings. Definitions, aliases, constraints,
fact classifications, source references and module/config/helper versions are
frozen. Canonical source files for selected records and exact permitted sources
are externally version-bound. The complete initial snapshot is informational:
an unrelated file change cannot expand the selected record set. A selected
canonical source, permitted document, module manifest, config or helper change
requires reassessment and is never silently substituted.

Additional `allowed_sources` have exactly `{path, sha256}` and must be selected
ontology allowlist files. Those exact source texts may supply frozen operational
excerpts. Solver/reviewer/synthesis/proposal write scopes, artifacts, copied
artifact hashes and current orchestration work products cannot seed a packet.
These are cooperative tool restrictions, not an operating-system sandbox.

The defaults allow at most 100 selected context records, 250,000 UTF-8 bytes per
packet and 200 exact references. An oversized selection fails and must be
narrowed. `freeze_packet(root, packet, output, actor=...)` reinspects the current
manager and unchanged Task version, validates exact inputs, and writes only a
new immutable JSON file inside the manager's granted output scope. It returns
`{path, sha256}`; the packet has no self-referential complete-file hash.

Supply that file to the existing `artifact.register` event with the actual
manager assignment as producer. Use its registered immutable artifact reference
in `baseline.inputs` and every initial solver assignment's `context`, including
queued solvers. `validate_assignment(root, registered_ref, task_path=...,
assignment_id=...)` checks the real current Task helper result, registration,
manager producer, execution, generation, baseline digest, round and equal solver
references. The host/manager separately verifies native context independence and
unchanged inherited model settings; ontology does not manufacture those receipts.

Further retrieval uses `search_packet(root, exact_ref, query)` or global CLI
`--packet-file PATH --packet-sha256 SHA` before the query command. Only packet
records are searched. A new concept in an unrelated canonical file or a new
memory record cannot enter silently. Mixed historical retrieval additionally
requires a separately frozen memory packet and uses its installed memory API.

`assess_change(old_packet, new_packet, reason)` is read-only and reports affected
meanings, version changes and required manager actions. An immaterial assessment
retains its reason without automatic restart. A material revision requires
current owners to be observed stopped/completed, an explicit revision reason,
existing subtask baseline revision, native `send_message` delivery of exact
references, `assignment.inputs` with the real message receipt, then
`followup_task`. Repeat affected review, synthesis, acceptance and implementation
gates. Creating revised packet bytes performs none of those Task events.

Deterministic helper fixtures use synthetic native receipts and are labeled as
such. They demonstrate interface compatibility. Real manager/solver delivery,
context independence and later-change isolation require separate observed native
execution evidence before being claimed.
## Advanced packet version 2

Set `advanced: true` in an explicit `freeze-packet` selection. Use
`graph_selection`, `inference_goals`, `extension_ids` and `semantic_queries` to
select additional context. The same current manager, execution, generation,
write-scope and artifact registration checks apply. The base compact records
remain v1; the packet wrapper is explicitly version 2, so a legacy reader
rejects it instead of silently interpreting advanced facts as assertions.

Inference includes only selected record and extension-statement premises,
selected negative evidence, finite rules, proofs, graph selection and exact
versions. Frozen reads replay the pure finite rules over captured premises to
validate proof consistency. They do not invoke a live backend or import new
ontology definitions. Changed selected inputs or contracts report stale state.

Semantic packet selection captures exact query vectors and the selected matrix
with model/index/source versions. Subsequent semantic queries support those
captured query strings only; other searches use the permitted frozen lexical
records. No live embedding, index refresh, new document, draft proposal, sibling
candidate or historical memory enters a frozen packet. Documentation used by
the index must also be explicitly selected as a permitted packet source.

The existing manager-controlled `assess_change` result reports material changes
to advanced context. Reconcile affected owners, revise the existing subtask
baseline, deliver exact revised references, and repeat the affected review and
acceptance gates. Current action guards retain their own current context; they
cannot replace a solver packet. Memory packets and memory publication authority
keep their original semantics.
