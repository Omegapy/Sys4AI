# Ticket-ordering analysis, synthesis v1

This proposal covers the complete current complex-analysis baseline for Task `TASK-20260908-726896CC`, execution `ticket_validation_20260908`, generation 1. It is ready for separate manager acceptance. The analysis makes no implementation or invalid-input policy choice.

Order every valid input ticket by descending urgency, preserving its original relative input order within each equal-urgency group. Ticket IDs do not break ties. Associate each record with its original zero-based input position, order the pairs by ascending `(negative urgency, original position)`, and read the records from those ordered pairs. This analytical construction produces the required order without changing the original list or record values. A separate result list is sufficient; a deep copy of records is not required by this analysis.

Four invariants describe the result: each valid input position appears exactly once; urgency never increases across the result; equal-urgency positions retain their input order; and the input list and record values remain unchanged. These invariants determine a unique order of valid input positions. Reversing a complete ascending result or sorting tied IDs can violate stability. A standard comparison-based realization of the construction can use O(n log n) time and O(n) additional storage. This statement is a design analysis, not a measured production implementation.

The exact fixture is `[{'id':'t3','urgency':2},{'id':'t1','urgency':3},{'id':'t2','urgency':2},{'id':'t4','urgency':0}]` in that input order. Its SHA256 is `3923fe6ee5e9c9cb40da4e53030be11844b3c9dc8bf22a620539576a163eea3d`.

| Output position, one-based | Ticket ID | Urgency | Original input position, zero-based |
| --- | --- | --- | --- |
| 1 | t1 | 3 | 1 |
| 2 | t3 | 2 | 0 |
| 3 | t2 | 2 | 2 |
| 4 | t4 | 0 | 3 |

The exact output IDs are `t1,t3,t2,t4`. The full result is `[{"id":"t1","urgency":3},{"id":"t3","urgency":2},{"id":"t2","urgency":2},{"id":"t4","urgency":0}]`. All four records appear once. The two urgency-2 records retain t3 before t2. Urgency 0 is included after higher urgency.

Empty valid input yields an empty new list. A singleton remains the sole record. An all-equal input keeps its complete input order. Already correctly ordered input keeps its relative order. For the endpoint values, 3 precedes 0 regardless of their original positions. A transient standard-library calculation independently checked these five boundary examples and the exact fixture, including conservation, descending order, tie stability, an unchanged input snapshot and a distinct result list.

The invalid-input decision stays explicitly deferred. The scenario states the later coding stage's validity constraints: nonblank unique string IDs and integer urgency in 0..3, excluding booleans. Those constraints do not determine the invalid-input return or error contract.

| Permitted policy, still deferred | Observable behavior | Decision needed before implementation |
| --- | --- | --- |
| Raise an explicit error | Reject an invalid batch, leave the input unchanged and return no successful ordered result. The caller corrects the data or handles the failure. | Specify the exception and diagnostic contract. |
| Return valid records with an explicit rejection report | Order the accepted subset, preserve stable ties by original input positions, leave the input unchanged and account explicitly for rejected positions and reasons. The caller can process partial results and must inspect the report. | Specify the return/report interface, duplicate-ID handling and complete accounting of every original position. |

Silent omission satisfies neither policy. Under a report policy, every original position must occur exactly once in either the accepted result or rejection accounting; conservation of the ordered subset refers to accepted valid positions. Missing fields, wrong types, out-of-range or boolean urgency, blank IDs and duplicate IDs need defined outcomes under the selected policy. Coercion and ID-based tie breaking are not established requirements.

The two policies make incompatible eventual interface commitments if both are treated as mandatory for one call, but the current analysis requires their comparison and deferral. The candidates agree on that scope. The scenario's described future steering does not select a policy for this baseline. No user preference, exception choice or report shape is inferred here. There is no unresolved conflict preventing this analysis deliverable; the explicitly deferred interface decision must be resolved in a later authorized coding baseline.

Source attribution is version-specific:

| Registered candidate | Version | Exact SHA256 | Retained contribution |
| --- | --- | --- | --- |
| analysis_a_v1 | v1 | 73ab17594aa57ec3466b331562c2f7f791a7e4b54a47c0e771cae72d507cee4f | Ordering construction, original-position tie handling, full record sequence, distinct result-list and complexity explanation. |
| analysis_b_v1 | v1 | c761201d2e8a0dc516c40ae1711b587e1831cab4d81d6403c53db0cad51f2b46 | Conservation, urgency, stability and preservation invariants; unique positional ordering; reversal risk; accepted/rejected position accounting. |
| analysis_c_v1 | v1 | 9c1003a67784cf391db1cfd3ded94f30009b0195e0cc459b0257068687e99cae | Full-fixture and endpoint explanation, boundary coverage, ID tie-break counterexample, and separation of current analysis from possible later steering. |

Each candidate addresses the complete problem. Repeated ordering statements, repeated tables and repeated policy comparisons are consolidated above; no competing substantive ordering rule or mandatory finding is discarded. The source tables use different zero-based or one-based presentation conventions. This proposal labels both conventions explicitly and preserves the same ticket sequence. All three current candidate versions and the common baseline were rehashed before synthesis. The senior independently recalculated the examples rather than treating candidate claims as proof of an executed implementation.

The common baseline SHA256 is `793560a4186ffcac6675a147940798d9f8877ca1ac818b9651bc1513491da069`. Current criterion coverage is complete: the opening rule and invariants specify descending urgency with stable ties; the table and full result give all four exact output IDs; and the policy comparison preserves explicit deferral without inventing preference. Source paths, digest checks, dispositions and the senior's observed checks are recorded in the accompanying synthesis and receipt JSON files.

Verification reached targeted checks of analysis examples plus static source and output checks. No product module, invalid-input implementation, integration suite, final Task completion or manager acceptance was performed by this senior.
