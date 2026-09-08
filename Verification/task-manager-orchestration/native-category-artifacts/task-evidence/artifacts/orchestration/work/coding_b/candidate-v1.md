# Ticket-ordering design B, candidate v1

This is the complete independent design for `coding_b`, Task `TASK-20260908-726896CC`, execution `ticket_validation_20260908`, generation 1. The current coding baseline SHA256 is `85a4b04b6d818bcd4284d9cdfc677123a0f0627238b728d4f668d18f44f098e8`. It is an analysis artifact for review and later synthesis; no production function has been implemented.

The design selects the initially permitted explicit rejection-report policy. Every valid call to `order_tickets(records)` returns a new sorted list. An invalid call returns a separate tagged rejection-report dictionary, never an ordinary successful list and never silent omission. This proposal makes that policy commitment for synthesis without treating described future strict-policy steering as current authority.

## API and validity

`records` is a Python list of dictionary records. Each record must contain `id` and `urgency`. IDs must be strings with at least one non-whitespace character and must be unique by exact string equality. Whitespace is checked for blankness but is neither removed nor normalized. Matching is case-sensitive: `x`, `X`, and ` x ` are distinct nonblank IDs. Every occurrence of a duplicated otherwise nonblank string ID is rejected, including its first occurrence. Duplicate detection includes a record whose other fields are invalid, so changing urgency cannot hide an ID collision.

Urgency must satisfy `isinstance(value, int)` and must not satisfy `isinstance(value, bool)`, then lie within the inclusive range 0 through 3. Both `True` and `False` are invalid. Floats such as 2.0, strings such as "2", `None`, missing urgency, and values -1 or 4 are invalid. Nothing is coerced. Additional record fields are retained without affecting order.

A valid result is a newly allocated list containing each original record object once, ordered by descending urgency and stable original input position within ties. No record or nested value is altered. A deep copy is unnecessary; the function guarantees no mutation during the call, not independent ownership against later caller edits to shared record objects. A successful empty call returns a distinct empty list.

For invalid input, the separate dictionary has exactly these public fields:

| Field | Meaning |
| --- | --- |
| `kind` | The literal string `rejection_report`; the outcome is distinguishable from every successful list. |
| `accepted` | A new list of all records with no validation reasons, ordered by descending urgency and original position. It is an explicitly reported partial result. |
| `rejected` | A list in ascending input-position order of objects with `position` and `reasons`. Positions are zero-based. Every rejected position appears exactly once, with every independently detectable reason. |
| `input_errors` | Empty for list inputs. For a non-list container, exactly `['input_not_list']`, with empty `accepted` and `rejected` lists because no valid positional input domain exists. |

Reason codes are `record_not_dict`, `id_missing`, `id_not_string`, `id_blank`, `id_duplicate`, `urgency_missing`, `urgency_not_integer`, and `urgency_out_of_range`. A non-dictionary record has only `record_not_dict`; its fields cannot be inspected. Dictionary records accumulate applicable ID and urgency reasons, followed by `id_duplicate` when present. An invalid urgency type yields `urgency_not_integer`, not an additional range reason. This keeps diagnostics deterministic and meaningful. A caller can branch on a successful list versus the explicit report; it must never mistake a report's accepted subset for whole-batch success.

## Algorithm and preservation

1. If the top-level value is not a list, return the container rejection report.
2. Allocate one reason list per original position and a map from usable nonblank raw string IDs to all their positions. Inspect every dictionary's ID and urgency without changing it. Record all independent field reasons. Add every usable string ID to the map even when that record has another defect.
3. Mark every member of each ID group containing more than one position with `id_duplicate`. Rejecting all occurrences avoids an arbitrary first-wins choice and accounts for every collision.
4. Form `(original_position, record)` pairs only for positions with no reasons. Sort these pairs by ascending `(-urgency, original_position)` and construct a new list of their record references. The input-position component explicitly preserves stable ties without using IDs as tie-breakers.
5. If every position is valid, return the new list. Otherwise return the tagged report with this ordered accepted subset, each rejected position and all its reasons, and no list-level errors.

For each list input, every original position belongs to exactly one of accepted or rejected accounting. No rejected position is passed to the urgency sort. Accepted urgency never increases, and equal-urgency positions stay in original order. Input order, object values, extra fields and nested values remain unchanged on both successful and rejected outcomes. The map, diagnostics and result structures are separate allocations. A comparison-based implementation uses O(n log n) time and O(n) extra storage, apart from the characters inspected for blankness and string hashing. No package dependency or global state is needed.

## Exact dependencies and example

The accepted analysis is `Tasks/Task-native-ticket-orchestration-validation-2026-09-08--726896CC/artifacts/orchestration/analysis_proposal_v1.md`, SHA256 `38a563ef628c0d052234931c71a459865f4a9b27886f242b3251423233cccb6f`. It establishes descending urgency, positional stability, preservation, and the deferred initial invalid-input alternatives. This proposal retains those ordering invariants and supplies one of the explicitly permitted interfaces.

The fixture `data/tickets.json`, SHA256 `3923fe6ee5e9c9cb40da4e53030be11844b3c9dc8bf22a620539576a163eea3d`, is exactly `[{'id':'t3','urgency':2},{'id':'t1','urgency':3},{'id':'t2','urgency':2},{'id':'t4','urgency':0}]`. It is entirely valid, so the result is a new list with IDs `t1,t3,t2,t4` and urgencies `3,2,2,0`. The two urgency-2 tickets retain t3 before t2. All four records survive exactly once; the fixture itself remains in t3,t1,t2,t4 order.

For an invalid example, positions containing `{'id':'dup','urgency':True}` and `{'id':'dup','urgency':3}` both enter rejection accounting. Position 0 has `urgency_not_integer` and `id_duplicate`; position 1 has `id_duplicate`. The report's accepted list is empty. No booleans are accepted as integers and no duplicate is silently preferred.

## Meaningful tests for the dedicated implementation

Use standard-library `unittest` after exact manager acceptance. Compare both values and relevant identities, using a deep input snapshot before each call to expose nested mutation. Do not infer preservation merely from ordered IDs.

| Coverage | Observable checks |
| --- | --- |
| Exact four-record fixture | Successful list; IDs t1,t3,t2,t4; urgency 3,2,2,0; each record once; original input and objects unchanged; result is a different list. |
| Empty and singleton | New empty list and new single-record list, including identity checks. |
| Endpoints and all valid urgency values | 0,1,2,3 accepted; 3 precedes 0. -1 and 4 rejected with range reasons. |
| Stable ties | All-equal IDs z,a,m retain z,a,m; mixed ties retain original positions. Already sorted input retains order in a new list. |
| Boolean and wrong urgency types | True and False rejected explicitly; 2.0, "2", and None yield type reasons. Missing urgency has its own reason. |
| ID validity | Missing, non-string, empty, and whitespace-only IDs rejected. Exact raw duplicate IDs reject every occurrence. Case and surrounding spaces are retained as specified. |
| Malformed records and multiple defects | None, scalar, list, and string records are reported by position. Dictionaries missing both fields or carrying two bad fields include every applicable reason. |
| Duplicate plus other defect | Boolean urgency on one duplicate does not hide the duplicate group; all affected positions and independent reasons appear. |
| Report accounting | Valid subset is sorted stably; accepted and rejected positions are disjoint and exhaust the input; report kind and complete deterministic reason lists are asserted. All-invalid input returns a report with an empty accepted list. |
| Container rejection | None, mapping, tuple, string, and numeric top-level values return `input_not_list`, with no invented rejected positions. |
| Extra fields and preservation | Nested extra fields survive unchanged; returned record references match the originals; successful and invalid calls leave deep snapshots and input order unchanged. |

A transient standard-library model of this proposal executed 24 named specification checks, including the exact fixture, empty input, boundaries, both booleans, malformed inputs, all-duplicate rejection, combined defects, full report accounting, stable valid subsets, raw ID semantics, and nested extra-field preservation. Each check asserted expected IDs, exact expected rejection reasons when applicable, distinct result-list identity, input equality with a deep snapshot, and descending accepted urgency. List-input checks also checked record-reference preservation; rejection checks checked complete disjoint positional accounting. These are targeted checks of the design model, not tests of a production module or evidence of manager acceptance. Exact names are in receipt-v1.json.

## Coverage and handoff

The API and algorithm cover valid stable order, new lists, preservation, all ID constraints, integer urgency excluding booleans, empty input and explicit invalid outcomes. The tests cover all four fixture IDs and required boundaries. Candidate files remain inside the assignment workspace, and no code or protected source is changed. Implementation-required criterion completion is left to the distinct dedicated implementer after the manager accepts one coherent current proposal; this candidate cannot establish it. The remaining synthesis decision is which currently permitted invalid-input interface to accept. No unseen candidate, future user preference or unperformed runtime implementation is asserted.
