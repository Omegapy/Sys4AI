# Ticket-ordering design B, candidate v2

This complete revision is produced by the same solver `/root/task_manager_validation/coding_b` for Task `TASK-20260908-726896CC`, execution `ticket_validation_20260908`, generation 1. It targets current baseline `acd7e5a4ae3da65dc15fe35a5e63e29865d64fdfd516a2ebf51d48bc61b7adee` under rebind packet `2d2127376d381d67f6fda17444ee3cdc9e73c6cb4981bfc3eff8484cb5468eb5`.

## Policy revision and attribution

Candidate v1 (`c20f8d2d2dd29d9cda4c727baef1cc1f14feedfcbd41735c7c6e4858ad6b0e03`) proposed the then-permitted rejection-report return. The identical shared conflict explanation `coding_conflict_v1.md` (`175219b33b2a880a3114a594e753792ac789292defd1fc9318dbc769816a68a7`) identifies its incompatibility with a batch exception from the same API. The host-relayed controlled-test steering `coordination/strict-policy-steering.json` (`6658c9280414b04f2ab89c2e001c6b7fc516ca6f56636cf2a2946e8ca2cddc65`) now explicitly selects strict `ValueError` behavior.

Accordingly, v2 replaces v1's report outcome and ordered valid-subset return. Every invalid batch raises `ValueError`, returns no partial result or report, and leaves the complete input unchanged. The earlier proposal was valid within its former baseline; it is superseded by this explicit test decision, not silently discarded or attributed to an unrecorded product preference. Complete diagnostic accounting, compound-defect examples, stable ordering, record identity and preservation checks remain useful and are retained. There is no optional mode or wrapper retaining the conflicting interface.

## Complete function contract

`order_tickets(records)` accepts a Python list of dictionaries. Each dictionary must contain a nonblank string `id` and an integer `urgency` in inclusive range 0..3. Check integer membership with `isinstance(value, int)` and explicitly exclude `isinstance(value, bool)` before checking range. Both True and False, floats, numeric strings, None, missing fields and out-of-range urgency are invalid. Do not coerce values.

IDs must be unique by exact raw string equality. Use whitespace stripping only to detect blank IDs; do not normalize or alter them. Case and surrounding spaces remain significant. Diagnose every occurrence of a duplicate usable nonblank string ID, including one whose urgency is independently invalid. Extra fields are retained without affecting ordering.

Every valid call returns a new list of the original record objects, exactly once each, sorted by descending urgency with ties in original input order. Input order, dictionaries and nested values remain unchanged. Empty input returns a distinct empty list. Record objects are intentionally shared with the result; this promises no mutation by the function, not isolation from a caller's later edits.

Every invalid call raises `ValueError` before result construction. A non-list container raises `ValueError('input_not_list')`. For a list, accumulate all independently detectable reasons per original zero-based position. Use these reason codes: `record_not_dict`, `id_missing`, `id_not_string`, `id_blank`, `id_duplicate`, `urgency_missing`, `urgency_not_integer`, and `urgency_out_of_range`. A non-dictionary element has only its record-type reason; an invalid urgency type is not also a range error. Within each dictionary, order ID reasons first, urgency reasons second, and duplicate reasons last. The proposed deterministic exception message is `invalid tickets: <position>:<comma-separated reasons>;...`, listing defective positions in ascending order. This preserves diagnostic coverage as exception text without returning a report or partial records.

## Algorithm and evidence

1. Reject a non-list container. For a list, allocate separate per-position reason lists and an ID-to-positions map.
2. Inspect all records without writes. Collect field defects and map every usable raw ID, even when another field is invalid. Mark every position in each duplicated ID group.
3. If any reasons exist, raise the single diagnostic `ValueError`. No accepted subset is sorted or returned.
4. Otherwise sort `(original_position, record)` pairs by `(-urgency, original_position)` and construct a fresh list of record references.

This preserves each valid input position exactly once, nonincreasing urgency and stable tie positions. Neither branch mutates input. Sorting takes O(n log n) time and O(n) extra storage, apart from ID character inspection and hashing. The design needs only the standard library.

The exact fixture `data/tickets.json`, SHA256 `3923fe6ee5e9c9cb40da4e53030be11844b3c9dc8bf22a620539576a163eea3d`, is `[{'id':'t3','urgency':2},{'id':'t1','urgency':3},{'id':'t2','urgency':2},{'id':'t4','urgency':0}]`. The new result has IDs `t1,t3,t2,t4` and urgencies `3,2,2,0`; the original stays in t3,t1,t2,t4 order. This retains the accepted `analysis_proposal_v1.md` ordering analysis, SHA256 `38a563ef628c0d052234931c71a459865f4a9b27886f242b3251423233cccb6f`; the later steering supplies its formerly deferred invalid-input decision.

For the compound invalid input `[{'id':'dup','urgency':True},{'id':'dup','urgency':3}]`, raise `ValueError('invalid tickets: 0:urgency_not_integer,id_duplicate;1:id_duplicate')`. Both duplicate positions and the independent boolean defect remain visible, and neither record is returned.

## Focused validation and handoff

The dedicated implementer should use standard-library `unittest` to cover the exact fixture, empty and singleton input, all urgency values 0..3, all-equal and mixed ties, already ordered input, both boolean values, -1 and 4, float/string/None urgency, missing fields, blank and wrong-type IDs, duplicates including compound defects, malformed records and non-list containers. Retain extra nested fields and exact raw ID semantics. For successful calls, assert result type, new-list identity, expected IDs, record-reference identity and full input preservation. For invalid calls, assert `ValueError`, diagnostic positions/reasons and an unchanged deep input snapshot and record identities after a valid prefix; ensure no normal partial result is returned.

A transient standard-library model ran 24 named checks of this revised specification. They passed, including exact diagnostics, both booleans after a valid prefix, compound defects, no partial result, fixture IDs, empty/boundary/tie behavior and preservation. Input and dependency hashes were verified against the current rebind packet. These are targeted design-model checks, not tests of a production module. The receipt lists their exact names and input hashes.

This candidate covers all current design criteria and explicitly resolves its former policy commitment under the authorized shared steering. Current individual review, senior synthesis and manager acceptance still remain separate gates. The implementation criterion belongs to the distinct dedicated implementer after exact acceptance; this solver has written no production code or ledger state.
