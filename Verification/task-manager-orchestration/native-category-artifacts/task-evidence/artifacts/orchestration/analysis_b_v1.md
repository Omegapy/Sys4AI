# Ticket ordering analysis, candidate v1

Assignment: analysis_b. Perspective: invariant reasoning. This is a complete analysis of the common bounded problem. It does not implement the module or select an invalid-input policy.

The input is an ordered sequence of ticket records. For valid records, the result contains every input record exactly once, ordered by descending urgency. Equal urgency preserves the records' original input order. A new result list preserves the input sequence and record values. No additional tie breaker, including ticket ID, is authorized.

Four invariants make the ordering precise:

1. Conservation: output positions are a permutation of the input positions. No valid ticket is lost, duplicated, or silently filtered.
2. Urgency: for any earlier output record and later output record, the earlier urgency is at least the later urgency.
3. Stability: if two records have equal urgency, their relative order equals their original relative order.
4. Preservation: forming the output leaves the original list order and record values unchanged.

For valid input, these conditions determine a unique ordering of positions. Associate each record with its original zero-based position and compare the pair of negative urgency and original position in ascending order. The urgency component establishes descending priority; the position component resolves ties without using ticket content. This is an analytical construction, not a performed production implementation. It also avoids the error of reversing an ascending result, which could reverse tied records.

For the verified fixture, original positions are t3 at 0 with urgency 2, t1 at 1 with urgency 3, t2 at 2 with urgency 2, and t4 at 3 with urgency 0. The required output is:

| Output position | Ticket ID | Urgency | Original position |
| --- | --- | --- | --- |
| 0 | t1 | 3 | 1 |
| 1 | t3 | 2 | 0 |
| 2 | t2 | 2 | 2 |
| 3 | t4 | 0 | 3 |

Thus the complete output IDs are `t1,t3,t2,t4`. Urgency decreases as 3,2,2,0. The only tied pair, t3 and t2, retains original positions 0 before 2. All four records occur once. An inline standard-library check observed these invariants against the exact source fixture and confirmed that the fixture remained unchanged.

Boundary consequences follow directly from the invariants. Empty valid input yields an empty new list. A singleton retains its sole record. If all urgencies tie, output order equals input order. Already correctly ordered records keep their order. Urgency 0 remains valid and follows higher urgency; urgency 3 precedes lower urgency. The supplied scenario requires nonblank unique string IDs and integer urgency in 0..3, excluding booleans. Those validity constraints must not be silently relaxed by coercion, ID-based sorting, truncation, or silent omission.

The invalid-input behavior remains explicitly deferred. The two permitted options have different interfaces:

| Permitted policy | Observable behavior | Required explicit detail |
| --- | --- | --- |
| Raise an error | Reject an invalid batch, report the validation problem, and return no ordered result. Preserve the input. | The eventual proposal must define the exception type and useful validation diagnostics. |
| Return valid records with an explicit rejection report | Return the ordered valid subset together with an explicit report identifying rejected input positions and reasons. Preserve the input. | The eventual proposal must define the return shape and complete rejection accounting, including how duplicate IDs are treated. |

Under the report policy, conservation applies to valid accepted positions, and every original position must appear exactly once in either the accepted result or rejection accounting. Silent filtering satisfies neither permitted policy. Missing fields, wrong types, out-of-range urgencies, boolean urgency, blank IDs, and duplicate IDs need documented outcomes under whichever policy is subsequently selected.

Both options can meet the ordering and preservation rules. The first favors a single all-valid batch contract; the second permits partial processing and requires a richer result contract. This assignment provides no authority to choose either option or claim a user preference. The manager must carry this open decision into the later authorized design stage. The three present analysis criteria are satisfied while that decision remains open.

Evidence boundary: the exact fixture, packet, role pair, and shared baseline hashes were verified. The fixture calculation passed. Boundary statements and policy comparisons were inspected as analytical consequences; no production module, invalid-input implementation, integration suite, sibling candidate, or final Task acceptance was exercised here. The receipt records versioned source and artifact hashes.
