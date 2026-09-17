# Operational regression investigation and proposed correction

Task: TASK-20260913-E83FCC98. Accepted plan: PLAN-20260913-64A6385B revision 1. Diagnostic rebind: canonical revision 30, `regression-rebind-v1.json`. This document proposes a correction; it does not authorize or claim its implementation.

The integrated root exceeds the existing full inference response bound and the existing SHACL worker time bound. The added Curator corpus is the observed trigger. No production, reusable source, Template, configuration, original implementation result, frozen manifest, or original root handoff was changed during this investigation.

## Observed evidence and limits

The manager's `operational-regression-v1.json` records the actual installed root failures: default full inference returns `output_limit` / `Worker output exceeded its bounded IPC channel`; full SHACL returns `timeout` / `Worker time budget expired`. The pre-integration baseline passed both. Current 48 competency checks pass, which does not establish these operational capabilities.

The selected current context is `257bfefabd4b8fcc05358172e4f0b3bb0a3bbe5cc0daf9fb867b94b5616f5ca0`. Its 412 records include 221 Curator records. All source statuses used by the structure accounting are current.

The diagnostic script `regression-v1/measure.py` called the existing installed public APIs and actual confined worker with only the two Curator canonical graph inputs replaced by empty graphs in read-only proposal overrides. All other selected records, rules, constraints and configured limits remained. This counterfactual is diagnostic scope, not current root health:

| Counterfactual probe | Observed result | Public elapsed time | Public JSON bytes |
| --- | --- | ---: | ---: |
| Full inference without the two Curator graphs | `ok`, complete, 253 proofs | 0.403 s | 654,053 |
| Full SHACL without the two Curator graphs | `conformant`, complete | 5.884 s | 30,803 |

The worker receipts confirm network denied and project files unreadable. Full receipts and summary are retained in `regression-v1/without-curator-infer.json`, `regression-v1/without-curator-validate.json`, and `regression-v1/counterfactual-summary.json`.

`regression-v1/structural_metrics.py` uses standard-library structure accounting and the pure reasoning implementation. It does not run RDFLib, pySHACL or other optional dependencies outside their confined worker. Its replay exactly matches the observed confined counterfactual for status, completeness, trust, inferred triples, proofs, conflicts and conclusions. The current-root accounting in `regression-v1/structural-metrics.json` finds:

- 596 named premises, 597 proof nodes, one inferred triple, zero negative assertions and zero conflicts.
- Full response content alone occupies 1,623,520 bytes with canonical formatting, or 1,377,629 bytes with compact formatting, before additional worker, version and public context fields. Both exceed the 1,048,576-byte bound.
- The proofs field alone is 587,048 formatted bytes and the corresponding provenance field is 915,265 bytes. Selected premise identifiers add 52,683 bytes. The dominant cost is repeated representation of the selected evidence, not runaway derivation.
- Generated SHACL has 412 record NodeShapes but only 35 distinct complete constraint sets. The retained group membership map covers all 412 original targets.

These findings establish the inference serialization cause. They establish SHACL corpus growth and repeated shape structure as a concrete optimization target; they do not establish how much pySHACL time is spent in each internal phase or prove an unimplemented optimization will pass the root time bound.

No limits should change: input 8,388,608 bytes / 50,000 triples; output 1,048,576 bytes / 500 rows; query 10 seconds; reasoning 30 seconds; 100,000 derived triples; 128 rounds; 10,000 proof nodes; two workers; RSS 536,870,912 bytes; guard 5 seconds; query depth 64.

## Proposed correction 1: an explicit full-closure diagnostic for health

Preserve default `infer` response and failure behavior. Do not remove its full proofs, filter them to derived conclusions, suppress provenance, silently select fewer premises, or change frozen replay/publication consumers. `ontology_advanced_packet.py` compares full proof results during replay; publication and inference-knowledge consumers depend on the existing proof contract. Compact JSON alone cannot solve this case.

Add a separately named `infer_diagnostic` public Python API, implemented as an explicitly validated diagnostic result mode of the existing confined inference operation. Keep default mode `full` and reject unknown modes. The diagnostic mode must execute the same selected premises and negative assertions through the same complete reasoning function, conflict detection and all resource limits. Compact only the finished result at the worker response boundary, before wire serialization. It must never change the reasoning inputs or discard a failure into a successful summary.

The diagnostic response should have a versioned schema and explicitly identify `result_mode: diagnostic`, `reasoning_scope: full_selected_closure`, and `proof_detail: counts_and_digests_only`. Retain status, complete, trusted, authority false, rule/profile identity, rounds, limit and diagnostics. Provide deterministic counts and SHA-256 digests for selected premise IDs, selected negative assertions, inferred triples, full proof nodes and conflicts, computed from the exact full result using the existing canonical byte encoding. Retain the existing context/snapshot and worker evidence. Summarize explicit goal outcomes only if bounded; do not let caller-provided goals escape the normal response bound. Do not include partial arrays under existing full-proof field names.

Expose a clear explanation that this proves execution of the full selected closure but does not deliver a complete proof export. Point users requiring proof detail to the existing exact `infer(..., premise_ids=[...], goals=[...])` route, with a warning that its result proves only the explicitly selected premise scope; a narrow query does not substitute for the full diagnostic. The selected premise set and context digest must make the scope inspectable. A full default inference call may still fail `output_limit`; report that truthfully as a full-detail export limitation.

Change only the operational inference health probe to call the explicit diagnostic API. Its returned probe evidence must name the diagnostic mode and full selected closure and state that full proof delivery was not tested by that probe. Preserve separately observed full-inference failures in the report. Static configuration readiness and operational closure execution remain separate. Publication, frozen packet replay, knowledge retrieval and other existing callers continue using default full inference.

Expected source scope: `SKILLS-depo/ontology/scripts/ontology_backend.py`, `ontology_standards.py`, `ontology_health.py`, one focused diagnostic test, and the existing source reasoning/command documentation describing this new distinction. Add a small dedicated pure diagnostic helper only if needed to keep the implementation reviewable. No CLI addition is required for health's internal API. Root adoption must be separately reviewed against the actual root predecessors.

## Proposed correction 2: group identical generated SHACL constraint sets

Within `shapes_for_records`, compute each record's complete generated property-constraint set with unchanged type closure, domain/range eligibility, cardinality and provenance requirements. Canonically key the entire set, then emit one deterministic NodeShape for each distinct set, with every original record retained as a `sh:targetNode`. Reuse existing property-shape and `sh:in` list caches. Do not group by record kind alone. Preserve distinctions including minCount zero, every maxCount, node kind, minimum length, exact membership lists, and all applicable inherited predicate constraints. Cache repeated type closure only with exact immutable selected inputs.

No semantic record, predicate, source requirement or target may disappear. NodeShape IDs may become deterministic group IDs; preserve focus-node findings and provide a deterministic membership mapping if source-shape consumers need to identify a former record shape. Extra authored shapes must remain intact. Preserve the supported-feature gate, no-import check, selected graph restrictions, inferred-evidence prohibition, malformed-shape rejection, meta-SHACL, inference none, advanced false, JS false, no imports, abort-on-first false, warning/info treatment and validation depth 32.

Expected source scope: `SKILLS-depo/ontology/scripts/ontology_shacl.py` plus focused equivalence/negative tests. First verify identical target-to-complete-constraint mappings before and after. The root accounting predicts 35 generated NodeShapes retaining 412 targets, but actual confined full-root validation within the unchanged 10-second budget is the acceptance gate. If it still times out, retain the failure and report it rather than claiming correction or increasing its budget.

## Mandatory implementation and adoption gates

1. Diagnostic equivalence: for bounded fixtures compare every reported count/digest with the corresponding actual full confined inference result, including an inferred chain, duplicate premises, explicit negatives and a positive/negative conflict. Full default output remains unchanged. A deliberately excessive default response still returns `output_limit`; the explicit diagnostic may succeed only when the full computation itself completes within its original limits.
2. Diagnostic rejecting controls: stale source/snapshot, disabled profile, invalid premise selection, unsupported result mode, timeout/cancellation, proof-node/round/derived-triple bounds, output bound and conflict/untrusted cases retain their existing rejection or incomplete semantics. Do not turn resource exhaustion or conflict into `ok`/trusted. Verify a premise subset is never labeled full project scope.
3. Health contract: operational health names its diagnostic scope and proof-delivery limitation, propagates diagnostic failures, leaves static assessment separate, and does not redirect publication, knowledge or frozen replay callers. Report both the bounded full-closure diagnostic and actual default full-inference result on the root.
4. SHACL equivalence: compare each original target's full constraint set to its grouped membership, with no omitted or added constraints. Test records that differ by one constraint or one eligible membership so they do not merge. Require all original targets and exact selected graph scope.
5. Confined SHACL negatives: wrong domain, wrong range, invalid binding entity, missing provenance, missing required metadata, wrong node kind, missing required value and too many values must produce violations focused on the exact edited target, including targets that share a group. Include malformed/unsupported extra shapes, forbidden imports/inferred scope and bounded failure controls. Preserve the existing SHACL and actual guard negative suite; do not change guard action acceptance.
6. Run the corrected full root corpus through the actual confined worker without changing any limits, weakening sandboxing, removing semantics or relabeling failures. Preserve raw results, timing, target count, context and bytes. Recheck all 48 competencies, scoped proof retrieval and relevant existing full-proof/replay contracts.
7. Propagate source changes to the neutral Template through its updater; verify current state and absence of root/project identity. Prepare a separate exact root source-to-installed manifest with actual predecessor preimages/hashes, current helper compatibility, and any required guard-repair selection. Host performs active-root adoption and current-root operational verification after source ownership stops. Keep the first implementation freeze immutable; emit a new correction freeze/result.

## Disposition

No correction has been implemented or performance-validated. This proposal preserves all current failure evidence and confines the proposed behavior change to an explicit health diagnostic and equivalent generated SHACL structure. The diagnostic assignment is complete and source writes remain stopped pending the manager's accepted correction and exact rebind.
