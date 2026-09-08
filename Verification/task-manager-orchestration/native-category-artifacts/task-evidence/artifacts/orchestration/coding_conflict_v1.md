# Shared coding interface conflict, version 1

Both current candidates pass their assigned individual design reviews under baseline `85a4b04b6d818bcd4284d9cdfc677123a0f0627238b728d4f668d18f44f098e8`. They agree on valid-input ordering and preservation, but make incompatible commitments for invalid calls to the same `order_tickets(records)` API. This controlled synthesis conflict requires the bounded host decision below. It is not a new mandatory defect in either reviewed design.

| Current candidate | Exact SHA256 | Current passing review | Invalid-input commitment |
| --- | --- | --- | --- |
| `coding_a_c2` / `coding_a_v2` | `71136dfcfe79fc38bd7319cac2e1a2dfceb13fa2ad4931bda5276be9b0c2d565` | `review_a_v2`, `ce79426e4c6c22ea88f087735227c97ca99b428fa674a76b6d65b227bae7a981` | Raise `ValueError` for the invalid batch; return no partial list or rejection report. |
| `coding_b_c1` / `coding_b_v1` | `c20f8d2d2dd29d9cda4c727baef1cc1f14feedfcbd41735c7c6e4858ad6b0e03` | `review_b_v1`, `622e86d819edf03239fdbe033fb2299ba525f1f4fa3d8749a263e34502a54056` | Return a tagged rejection-report dictionary with the ordered accepted subset and complete rejection reasons. |

For `[{"id":"ok","urgency":3},{"id":"bad","urgency":true}]` expressed as JSON, the second urgency becomes Python `True` and is invalid in both designs. A specifies `ValueError` with no normal return. B specifies a `rejection_report` with `ok` in `accepted`, position 1 rejected for `urgency_not_integer`, and no container error. These are source-derived expected outcomes, not executed production behavior. One call cannot satisfy both normal-return and exception commitments. A new mode, wrapper or mixed policy would require a further interface decision and is outside this synthesis authority.

Should order_tickets reject every invalid batch with ValueError and no returned partial result, or return an explicit rejection report with the ordered valid subset and complete rejection reasons?

Both designs retain a new list for every valid call, descending urgency, original-position ties, raw nonblank unique string IDs, integer urgency 0..3 excluding booleans, no coercion, unchanged input and nested fields, original record identities, extra fields that do not affect order, and the exact fixture result `t1,t3,t2,t4`. A contributes clear batch-failure diagnostics and preservation checks after a valid prefix. B contributes complete diagnostic accounting and compound-defect examples. Keep these contributions visible; policy-dependent behavior must be revised explicitly after the decision.

The distinction between an exception and a report is a public interface difference, not terminology. The current evidence supports each allowed design individually; it does not establish a user preference or an implemented function. A's prior boolean omission is corrected in the exact current candidate and its current review has no mandatory findings. No valid requirement or opposing commitment is silently discarded. Full dispositions for complementary, terminology, scope, evidence and exclusive differences are in `conflict-details-v1.json`.

The manager must deliver this same exact versioned conflict explanation and authorized revised baseline to both originating solvers. Each returns a revised or explicitly revalidated current candidate; both assigned reviewers must pass those current versions before further senior synthesis. The described future strict policy remains prospective until that handoff. This senior does not select it, accept a proposal, write production code or mutate canonical state.
