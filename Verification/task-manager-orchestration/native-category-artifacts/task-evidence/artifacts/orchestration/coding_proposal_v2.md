# Ticket-ordering implementation proposal, version 2

This is the coherent current proposal for Task `TASK-20260908-726896CC`, execution `ticket_validation_20260908`, generation 1, baseline `acd7e5a4ae3da65dc15fe35a5e63e29865d64fdfd516a2ebf51d48bc61b7adee`. The authorized controlled-test steering resolves `policy_conflict`: every invalid batch raises `ValueError`, returns no partial result or rejection report, and leaves the complete input unchanged. Both original solvers addressed the same conflict, and both current candidates passed their original assigned reviewers. This proposal awaits the manager's exact acceptance and a distinct dedicated implementer.

## Function contract

Implement `order_tickets(records)` in `ticket_ordering.py` using the Python standard library. `records` must be a Python list of dictionary records. Every record must have an `id` and `urgency`. An ID must be a nonblank string unique by exact string equality; use whitespace stripping only to detect blankness. Keep case and surrounding spaces unchanged. Repeated references with one ID are duplicates. Do not normalize, coerce or use IDs to break ties.

Urgency must satisfy `isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 3`. Explicitly reject both `True` and `False`, wrong types, missing values and out-of-range integers. Extra fields are allowed, retained unchanged and do not influence ordering.

Every valid call returns a new list containing each original record object exactly once, sorted by descending urgency with original input order preserved within ties. Empty input returns a distinct empty list. The function never changes the caller's list, list order, dictionaries or nested values, on success or validation failure. The result shares original record objects; later caller edits are outside this no-mutation-during-call guarantee.

Every invalid top-level container, record shape, required field, ID, duplicate or urgency raises `ValueError` before constructing or returning an ordered result. There is no accepted-subset return, report object, optional mode or wrapper.

## Algorithm and diagnostic choice

1. Require a list; otherwise raise `ValueError` with a concise reason identifying `records`.
2. Keep a local set of seen raw IDs. Visit records in increasing zero-based position without writing to input. Require a dictionary and both required keys, then a nonblank string ID absent from the set, then the urgency predicate above. A failed check raises `ValueError` identifying that record position and a relevant field or record reason. A missing required key is reported before field-value validation at that position. After a record validates, add its exact ID to the local set.
3. Only after all records validate, associate each record with its original input position. Sort newly allocated pairs by ascending `(-urgency, original_position)` and return a new list of their original record references. Never sort the caller's list in place.

This proposal selects A's first-error diagnostic approach. It reports the first defective record in traversal order; full exception wording is not a public compatibility contract. B instead proposes collecting every defect, diagnosing all occurrences of duplicated IDs and formatting a deterministic aggregate exception. That contribution is explicitly omitted because the current criteria require reliable rejection and preservation, not complete diagnostic enumeration or an exact message protocol. The first-error design uses fewer structures and stops at the first known invalid condition. The tradeoff is less diagnostic coverage per call; callers may encounter another defect after correcting the first. B's compound-defect examples remain rejection-and-preservation tests, without assertions for every diagnostic reason. Neither current candidate is represented as already agreeing with this synthesis choice.

Each valid position contributes one result position. Negative urgency gives descending order, and original position preserves ties independently of IDs. The local set enforces uniqueness. Reading input and constructing separate output structures preserves it. Comparison sorting uses O(n log n) time and O(n) extra storage, apart from ID character inspection and hashing; no new dependency or global state is needed.

## Required verification

The exact input fixture is `[{"id":"t3","urgency":2},{"id":"t1","urgency":3},{"id":"t2","urgency":2},{"id":"t4","urgency":0}]`. Its SHA256 is `3923fe6ee5e9c9cb40da4e53030be11844b3c9dc8bf22a620539576a163eea3d`. The required result IDs are `t1,t3,t2,t4`, with urgencies `3,2,2,0`; the original remains `t3,t1,t2,t4`.

Use discoverable standard-library `unittest` tests. Fixed expected results must establish order, rather than using the implementation's sorting expression to compute test expectations.

| Cases | Required observations |
| --- | --- |
| Exact four-record fixture | All four expected IDs in order, distinct result list, each exact original record object once, unchanged full input snapshot and original positions. |
| Empty, singleton at 0 and 3, all four urgency values | Fresh lists, unchanged records and correct descending endpoints. |
| All-equal IDs `z,a,m`, mixed ties, already ordered input | Original relative tie order retained; ID spelling never breaks ties; result remains a new list. |
| Extra nested fields and IDs `x`, `X`, ` x ` | Full values and record identities preserved; raw IDs remain distinct and unchanged; extras do not change order. |
| Non-list containers and malformed records | `None`, tuple, string, mapping or scalar containers, and non-dictionary entries raise `ValueError`. Missing `id` and missing `urgency` raise `ValueError`. |
| Invalid IDs and duplicates | Non-string, empty, whitespace-only and exact duplicate IDs raise `ValueError`; repeated references with the same ID also reject. |
| Invalid urgency | Each of `True`, `False`, -1, 4, a float, numeric string and `None` raises `ValueError`. Test both booleans separately and after a valid prefix. |
| Later invalid and compound-defect records | Malformed, duplicate and boolean cases after a valid prefix raise `ValueError` without any normal partial result. Preserve the complete deep input snapshot, original order and record identities. A compound duplicate/boolean example also rejects; complete diagnostic enumeration is not required. |
| Diagnostic meaning | Representative top-level errors identify `records`; representative record errors identify the first defective zero-based position and relevant field/reason. Avoid full-string message assertions. |

After exact acceptance, the dedicated implementer may write only `ticket_ordering.py`, tests and `implementation-evidence` within this disposable project. Provide test discovery support within `tests` if needed, and run `PYTHONDONTWRITEBYTECODE=1 /Volumes/P-SSD/AngryOwl/Sys4AI/.venv/bin/python -m unittest` from the project root. Record the exact command, observed result and artifact hashes, then directly exercise the fixture, empty input and invalid-input preservation. A design defect returns to the manager instead of changing the accepted interface silently. Preserve the fixture, context, role and skill files, and all other protected state.

## Source dispositions and readiness

| Exact current candidate | Candidate SHA256 | Exact current passing review | Retained contribution |
| --- | --- | --- | --- |
| `coding_a_c3` / `coding_a_v3` | `13655a83e362d3cb02bc81f407ffe7d0ce03a1a0c7734dd47f467b811665e4d3` | `review_a_v3`, `5a286092a641aad5d98d7bb2c24029de10450bcf9d37609b1dbfc7eb4c411076` | Complete strict API, first-error validation, stable positional construction, boolean correction and failure-after-prefix checks. |
| `coding_b_c2` / `coding_b_v2` | `5c7f2146a68b57d15e0d2a7a7cc69e6c878a52bbf517e9f0e09db495a6accc89` | `review_b_v2`, `838ac622eef6b1b730e796bdc49d82a78aca054e3c5d1314232c0bd1dfb20656` | Explicit authorized replacement of the old report interface, identity and nested-preservation rules, compound-defect and raw-ID tests, validation-before-result construction. |

The shared conflict SHA256 is `175219b33b2a880a3114a594e753792ac789292defd1fc9318dbc769816a68a7` and the authorized steering SHA256 is `6658c9280414b04f2ab89c2e001c6b7fc516ca6f56636cf2a2946e8ca2cddc65`. The accepted analysis at `analysis_proposal_v1.md`, SHA256 `38a563ef628c0d052234931c71a459865f4a9b27886f242b3251423233cccb6f`, supplies ordering and invariants; its earlier policy deferral is resolved by this current steering. The decision is authority for this controlled validation scenario, not a separately inferred product preference.

`policy_conflict` is resolved and no design issue remains unresolved. All current design criteria have an explicit implementation and verification path. Performed implementation, passing production tests, manager acceptance and final Task completion remain separate required gates. The senior rechecked exact source and review bindings and independently checked seven ordering examples plus validity expressions. Those checks support the specification and do not claim an executed production function. `synthesis-v2.json` records all required difference dispositions and exact versions. The original conflict artifacts are preserved.
