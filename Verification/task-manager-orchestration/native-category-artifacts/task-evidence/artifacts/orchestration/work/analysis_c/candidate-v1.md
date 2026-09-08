# Ticket-ordering analysis, candidate v1

Assignment `analysis_c` uses the boundary and full-example perspective for the complete complex-analysis problem. It is bound to baseline `793560a4186ffcac6675a147940798d9f8877ca1ac818b9651bc1513491da069`, Task `TASK-20260908-726896CC`, execution `ticket_validation_20260908`, generation 1. This is an analysis deliverable; implementation and final policy selection belong to later authorized work.

Order tickets by descending urgency. For equal urgency, retain their original relative input order. An equivalent ordering key is descending urgency followed by ascending original position. Ticket IDs identify records; they do not resolve urgency ties. Every valid input record appears once in the ordered result.

The inspected fixture contains all four records in this input order:

| Input position | ID | Urgency | Output position |
| --- | --- | --- | --- |
| 1 | t3 | 2 | 2 |
| 2 | t1 | 3 | 1 |
| 3 | t2 | 2 | 3 |
| 4 | t4 | 0 | 4 |

The complete ordered result is `[{"id":"t1","urgency":3},{"id":"t3","urgency":2},{"id":"t2","urgency":2},{"id":"t4","urgency":0}]`. Its exact output IDs are `t1,t3,t2,t4`. Urgency 3 comes first and urgency 0 comes last. Both middle tickets have urgency 2, so t3 stays before t2. Sorting tied IDs alphabetically would reverse that pair and violate the criterion.

Boundary reasoning supports the same rule. Empty input has an empty ordered result. A single valid ticket remains the sole record. When all urgencies are equal, the entire input order is retained. For the two endpoint urgencies, 3 precedes 0 regardless of their starting positions. Already ordered input needs no relative-order changes. These statements concern valid records and do not determine how invalid records are handled.

The invalid-input decision remains explicitly deferred. Both allowed policies can satisfy a subsequent, explicitly chosen interface:

| Permitted policy | Observable outcome | Consequence for the caller |
| --- | --- | --- |
| Raise an error for invalid input | The operation fails explicitly and returns no successful ordered result. | The caller must correct the invalid data or handle the failure before receiving results. This avoids partial-result handling. |
| Return valid records with an explicit rejected-record report | Valid records are ordered, and each rejected record is reported with its reason and a way to identify its input position. | The caller can use partial results but must inspect the report; silently dropping invalid records would violate this policy. The interface must define both outputs. |

This candidate does not choose either policy or infer a user preference. Exact invalid-record rules, error details, rejection-report shape and downstream handling must be settled with the selected coding baseline. The scenario describes a possible later strict-validation steering event; its description does not resolve this analysis baseline's open decision.

The fixture bytes were verified against SHA256 `3923fe6ee5e9c9cb40da4e53030be11844b3c9dc8bf22a620539576a163eea3d`. A transient Python standard-library check produced the exact four-ID result, preserved the two urgency-2 tickets' order, and left the parsed input snapshot unchanged. It also checked empty, singleton, all-equal and endpoint examples. These checks validate the analysis examples. No ticket-ordering module or production implementation was written or tested.

All three analysis criteria are covered: the ordering rule includes stable ties; the full verified example includes all four exact output IDs; and both permitted invalid-input policies remain compared and explicitly deferred. No sibling candidate was read. This version is ready for the assigned senior's synthesis and the manager's separate acceptance.
