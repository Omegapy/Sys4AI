# Ticket-ordering analysis, candidate 1

Assignment `analysis_a` uses the stable ordering construction perspective. This is a complete analysis of the current problem, provided for manager acceptance. Baseline SHA256 is `793560a4186ffcac6675a147940798d9f8877ca1ac818b9651bc1513491da069`; fixture SHA256 is `3923fe6ee5e9c9cb40da4e53030be11844b3c9dc8bf22a620539576a163eea3d`.

Order tickets by descending urgency. For equal urgency, preserve the order of their positions in the input. A direct construction attaches each ticket's original zero-based position, orders by the pair (negative urgency, original position) in ascending order, then returns the tickets without the positions. The first component puts larger urgency first; the second makes an earlier input position precede a later one within each equal-urgency group. IDs do not break ties. Each valid input occurrence contributes exactly once, so the ordering neither loses nor duplicates tickets.

The verified fixture has the following positions and resulting order.

| Output position | ID | Urgency | Original position |
| --- | --- | --- | --- |
| 1 | t1 | 3 | 1 |
| 2 | t3 | 2 | 0 |
| 3 | t2 | 2 | 2 |
| 4 | t4 | 0 | 3 |

The exact output IDs are `t1,t3,t2,t4`. In particular, `t3` remains before `t2` because both have urgency 2 and `t3` occurs first in the input. The resulting record sequence is `[{"id":"t1","urgency":3},{"id":"t3","urgency":2},{"id":"t2","urgency":2},{"id":"t4","urgency":0}]`.

For eventual implementation, constructing a separate result list preserves the original list order and contents. The analysis does not require a deep copy of ticket records or authorize later mutation of them. Empty input gives an empty result; a single valid ticket stays unchanged; an all-equal-urgency input keeps its entire original order. Urgency 0 is included after higher values, as the fixture demonstrates. A standard comparison-based ordering of the decorated records has O(n log n) time and O(n) additional storage. This construction is an analysis, not implemented production code.

The invalid-input policy remains explicitly deferred. The scenario's coding stage requires nonblank unique string IDs and integer urgency in 0..3, excluding booleans. These validation constraints do not select what the public interface does when validation fails. Both following policies remain permitted proposals at this stage.

| Permitted policy | Behavior and tradeoff |
| --- | --- |
| Error on invalid input | Reject the operation with an explicit error and leave the input untouched. The caller receives no successful ordered result for a mixed valid/invalid batch and must correct the input before retrying. An exception type and diagnostic contract still need acceptance. |
| Valid results with an explicit rejection report | Order the valid subset and return an explicit report identifying rejected records and their reasons. This supports partial progress, but requires an accepted result/report interface and a defined treatment of cases such as duplicate IDs. Silent dropping is excluded. |

Neither policy is chosen here, and neither is attributed to user preference. The later authorized design decision must fix the invalid-record behavior and public return/error contract before implementation. The ordering rule applies to all accepted valid records under either policy, with stable ties relative to their original input positions.

Verification used the existing Python interpreter for an in-memory calculation from the exact fixture bytes. The full output, descending order, tie order, input snapshot preservation, empty input, singleton input and an all-equal-urgency example passed. Packet, baseline, scenario and selected role digests matched the supplied references. Manual review confirmed all three current baseline criteria are represented. No implementation, invalid-input runtime behavior, senior synthesis or manager acceptance is claimed.
