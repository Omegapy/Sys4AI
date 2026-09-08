# Ticket-ordering candidate A, version 3

This is the complete independent validation and interface proposal for assignment `coding_a`, Task `TASK-20260908-726896CC`, execution `ticket_validation_20260908`, generation 1. It revalidates strict rejection by raising `ValueError` for every invalid batch under the now-delivered host-authorized controlled-test steering. This authority is specific to the approved validation scenario; it does not assert a separately selected user product preference.

The current common coding baseline SHA256 is `acd7e5a4ae3da65dc15fe35a5e63e29865d64fdfd516a2ebf51d48bc61b7adee`. This candidate depends on the accepted ordering analysis at `Tasks/Task-native-ticket-orchestration-validation-2026-09-08--726896CC/artifacts/orchestration/analysis_proposal_v1.md`, SHA256 `38a563ef628c0d052234931c71a459865f4a9b27886f242b3251423233cccb6f`, and the exact `data/tickets.json` fixture, SHA256 `3923fe6ee5e9c9cb40da4e53030be11844b3c9dc8bf22a620539576a163eea3d`.

## Shared conflict disposition and current revalidation

I read the exact shared `policy_conflict` explanation in `coding_conflict_v1.md`, SHA256 `175219b33b2a880a3114a594e753792ac789292defd1fc9318dbc769816a68a7`, and the host-relayed decision in `coordination/strict-policy-steering.json`, SHA256 `6658c9280414b04f2ab89c2e001c6b7fc516ca6f56636cf2a2946e8ca2cddc65`. Raising an exception and normally returning a rejection report are incompatible commitments for the same invalid call. The steering now resolves that interface choice: every invalid batch raises `ValueError`, yields no partial result or rejection report, and leaves the complete input unchanged. Every valid call returns a new stable descending list.

My version-2 error-based design already meets that selected policy and is explicitly revalidated here against the revised baseline. For the conflict example with a valid `ok` record followed by boolean-urgency `bad`, this design requires `ValueError`, no normal return, and an unchanged complete input snapshot. The rejected-subset/report alternative and any mode or wrapper that preserves it are outside the current interface. Its diagnostic-accounting contribution remains visible in the shared explanation; complete rejection reporting is not imported into this strict API. The proposed first-invalid-index and reason diagnostics remain sufficient, with all existing validation and preservation criteria retained.

The accepted analysis still supplies ordering, invariants and the exact fixture. Its earlier policy deferral is resolved only by the current steering and baseline. There is no remaining policy conflict in this candidate. The original versions and their evidence are retained; this version must pass its assigned current review before further senior synthesis and manager acceptance.

## Correction of the initial controlled defect

Version 1 intentionally omitted boolean validation for the controlled review test. The assigned reviewer independently rejected it with mandatory finding `R-A-001`, findings SHA256 `a3a5df3e0b266344d89355382599fbaf4d91155134394189d38f4c769f1275f4`. Version 2 corrected that finding by explicitly excluding boolean urgency in validation and proposing negative tests for both `True` and `False`, including an invalid record after a valid prefix with unchanged input. Version 3 retains that correction unchanged. The prior candidates and receipts remain intact. The strict-error behavior is now revalidated against current steering; all other design choices remain unchanged. This current design awaits the same reviewer; it is not a production implementation or a manager acceptance.

## API and validation contract

The proposed API is `order_tickets(records)`. On valid input it returns a new Python list containing every original record exactly once, ordered by descending urgency with input order preserved for ties. It accepts a Python list of dictionary records. An empty list is valid. The function leaves the input list, its order, every dictionary, and every extra field unchanged.

Each record must contain `id` and `urgency`. An ID must be a string with at least one non-whitespace character; uniqueness uses the exact original string, with case and surrounding whitespace retained. There is no trimming, normalization, coercion, or ID-based tie breaking. Thus `"t1"` and `" t1 "` are distinct valid IDs, while `"   "` is invalid. Repeated references to one record with the same ID still violate uniqueness. Extra fields are allowed and retained without affecting order.

The contract requires integer urgency in the inclusive range 0 through 3, explicitly excluding booleans. The corrected predicate is `isinstance(urgency, int) and not isinstance(urgency, bool) and 0 <= urgency <= 3`. Both `True` and `False` therefore take the invalid-input path and raise `ValueError`; their integer-subclass behavior cannot make them valid urgency.

Invalid top-level shape, a non-dictionary record, missing required fields, a non-string or blank ID, a duplicate ID, a failed urgency type check, or urgency outside 0 through 3 raises `ValueError`. No successful result, partial result, rejected-subset return or rejection report is returned on failure. Validate the complete batch before constructing a successful ordered result. Report the first offending input index and field or record reason in input order, with top-level errors identifying `records`. Use concise diagnostics; message text is not a stable API requiring full-string test matches. Caller input stays unchanged on all handled validation failures.

## Algorithm and invariants

1. Require `isinstance(records, list)`; otherwise raise `ValueError` identifying `records`.
2. Create an empty set of seen IDs. Visit the input records in increasing zero-based position, reading without writing any record or input-list element.
3. Require each record to be a dictionary with both required keys. Check that its ID is a nonblank string and is absent from the seen-ID set. Add that exact ID to the local set.
4. Require `isinstance(record["urgency"], int) and not isinstance(record["urgency"], bool)` and inclusive range 0 through 3. Raise `ValueError` for any failed check, including either boolean value.
5. After every record passes, associate each original record with its input position. Sort those pairs by the ascending key `(-record["urgency"], original_position)`.
6. Build and return a new list from the records in that pair order. The empty input takes this same path and returns a distinct empty list.

The explicit position key makes tie behavior independent of ticket IDs. Every validated input position contributes one output position. Negated urgency puts 3 before 2 before 1 before 0; original position orders equal-urgency records. These properties give conservation, descending urgency and stable ties. The algorithm never sorts the caller's list in place or mutates dictionaries. Validation needs O(n) time and storage for ID uniqueness; comparison sorting takes O(n log n) time with O(n) additional storage. No third-party package is needed.

The result is a shallow list of the original record objects. The input-preservation guarantee concerns this function call; later caller mutation of a returned dictionary can also be visible through the original list because deep-copy isolation is outside this contract. Retaining those identities also preserves arbitrary extra fields without unnecessary copying or transformation.

## Exact fixture and proposed tests

The exact fixture, in input order, is `[{"id":"t3","urgency":2},{"id":"t1","urgency":3},{"id":"t2","urgency":2},{"id":"t4","urgency":0}]`. The expected new result is `[{"id":"t1","urgency":3},{"id":"t3","urgency":2},{"id":"t2","urgency":2},{"id":"t4","urgency":0}]`. Its IDs are `t1,t3,t2,t4`; all four appear once, with `t3` preceding `t2` despite their lexical ordering.

The dedicated implementer should use standard-library `unittest` and run `PYTHONDONTWRITEBYTECODE=1 <available interpreter> -m unittest`. The following are proposed behavioral cases, not a claim that a product test suite has run:

| Case | Required observation |
| --- | --- |
| Exact four-record fixture | IDs are exactly `t1,t3,t2,t4`, with all four original objects present once. |
| Empty input | Result equals `[]` and is a different list object from the input. |
| Singleton at 0 and singleton at 3 | The one record remains, in a new result list. |
| Mixed endpoints and all four urgency values | Urgencies are `3,2,1,0`; both inclusive endpoints are accepted. |
| All-equal urgency with nonalphabetic ID order | The entire original ID sequence remains unchanged. |
| Already ordered input | Value order remains correct, but the output list is distinct. |
| Input preservation and extra fields | A deep snapshot before the call equals the input after it; original list order and record identities are preserved. Extra nested fields remain intact and do not affect ordering. |
| Wrong outer shape | `None`, a tuple, a string and a dictionary each raise `ValueError`. |
| Malformed records | A `None` entry, scalar entry, missing ID and missing urgency each raise `ValueError`. |
| Invalid IDs | Numeric ID, empty ID, whitespace-only ID and an exact duplicate ID each raise `ValueError`. |
| Exact ID comparison | Distinct `"t1"` and `" t1 "` are accepted and retained verbatim. |
| Invalid urgency | Values `-1`, `4`, `1.0`, `"2"` and `None` each raise `ValueError`. |
| Boolean urgency | Test `True` and `False` separately as urgency values; each raises `ValueError`, returns no successful result, and leaves the input unchanged. |
| Boolean after a valid prefix | For each of `True` and `False`, place an invalid record after at least one valid record. Assert `ValueError`, no successful partial result, and complete equality to the input snapshot after the exception, including original order and dictionary values. |
| Failure after valid prefix | A later malformed record raises `ValueError`, returns no successful partial list, and leaves the complete input snapshot unchanged. |

Use `assertIsNot` for result-list identity, `assertEqual` for expected order and unchanged snapshots, and `assertRaises(ValueError)` for rejection. Preservation on failure must cover more than the first record so a prefix-processing mutation would be detected. These checks address observable behavior rather than private helper layout.

## Scope, coverage and current evidence

The design covers the whole function: the API and batch-error choice, descending stable ordering, list and record preservation, new-list and empty behavior, IDs and duplicate handling, ordinary urgency boundaries, extra fields, diagnostics, computational cost and meaningful test cases. The prior missing-boolean correction remains intact through explicit rejection and corresponding proposed tests; the assigned reviewer must verify the current candidate bytes. Dedicated implementation and executable product-suite verification are later gates owned by a distinct implementation child after manager acceptance; analysis is not performed code.

This solver read the current complete baseline, its exact shared conflict explanation, host steering and own prior candidate, and verified all six current baseline input hashes. The required role pair was reread and verified. A transient calculation over the exact fixture observed the required IDs, an unchanged deep input snapshot, a distinct result list and preserved record identities; predicate expressions rejected both booleans and accepted ordinary integer boundaries. These checks revalidate the unchanged design expressions under the current inputs. They do not implement or execute the proposed API or its product test suite. Initial sibling drafts were not inspected; the shared conflict explanation is now an explicitly authorized common input. No Task, role index, production file, configuration, package, Git, network or external state was changed. The complete current candidate is ready for the same reviewer.
