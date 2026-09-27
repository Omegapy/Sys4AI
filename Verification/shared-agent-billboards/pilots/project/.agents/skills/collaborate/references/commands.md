# Commands

Use the selected project's Python 3.12 interpreter and installed helper:

```sh
python .agents/skills/collaborate/scripts/collaborate.py \
  --project-root /absolute/project --task-path Tasks/SELECTED/task.json \
  --assignment ACTUAL_ASSIGNMENT --actor /actual/native/identity \
  --execution CURRENT_EXECUTION --generation 1 \
  --policy-path Tasks/SELECTED/artifacts/orchestration/POLICY.json \
  --policy-sha256 EXACT_SHA256 list --unread --items 20
```

All binding options are required; paths are project-relative except project-root.
The helper fills post identity from canonical assignment context. Policy must be
registered by the manager and exact-bound in participant input/context. Read-only
commands never create, start, repair or acknowledge work. Reopen Context after any
canonical Task change; delayed cached contexts fail current reads and writes.

Commands: post/reply; list/read/search/digest; acknowledge/handle/delivery; pending;
linked; validate; rebuild; snapshot; assess; proposal. List/read/search/digest share
one bounded filtered representation. `--subtask`, `--thread`, `--participant`,
`--type`, `--artifact`, `--phase`, `--search`, `--unread`, `--offset`, and `--items`
apply to board reads. Offset is pagination only; unread derives from exact receipts.
Remaining coverage is explicit. `rebuild` writes only own views/TASK-BILLBOARD.md.

Mutations take `--payload-file` in the actor's existing read or write scope. A post
payload has exactly the keys below. A reply uses reply_to, a correction supersedes.
References are exact path/sha256 objects, not arbitrary URLs or source commands.

```json
{"operation_id":"question1","thread_id":"clock_rule","reply_to":null,"supersedes":null,"subtask":"RESEARCH","type":"question","title":"Which time rule is assigned?","body":"The source gives x(n)=nL but no t(n). Is the proposed clock rule an assumption?","phase":"peer-exchange","visibility":"findings","recipients":["manager","solver_a"],"requested_response":"Identify the exact source or mark the clock rule proposed; stop after one evidence reply.","urgency":"routine","targets":[],"evidence":[],"limitations":["Question only; no established physics result."],"material":false}
```

Phase is read from the policy/current canonical gates. A predeclared independent
policy dynamically opens peer-exchange only when all current candidates resolve;
that release needs no input-changing phase rewrite. Reviewer first assessments
still seal unrelated findings/verdicts until their own current review exists.

For an independent/reviewer-first policy, operational posts must use exactly one
of the fixed titles Source unavailable, Tool unavailable, Clarification requested;
body `Operational notice; ask the current manager for the permitted clarification.`;
requested_response `Manager: assess the exact frozen source or tool issue at the next active checkpoint.`;
operation_id notice plus 1-8 digits; thread_id operations; empty limitations;
reply_to/supersedes null; material false; targets/evidence limited to pre-existing
frozen baseline inputs. Arbitrary authored text belongs to findings. Types finding,
challenge and proposal cannot use operational; reviewer versions use verdict.
Receipt prose and tool results remain sealed from other independent recipients.

Receipt payload: operation_id, mid, state, recipient (optional defaults actor),
evidence (optional), native_receipt (optional). State is delivery-attempt, notified,
failed, uncertain, acknowledged, handled, answered or deferred. Notified requires
`{"tool":"collaboration.send_message","native_id":"/actual/recipient","result":ACTUAL_RETURNED_RESULT}`.
The file is evidence of an actual caller-observed result; the helper does not
invoke or authenticate the tool. No receipt can create an assignment or wake it.

Pending payload is `{"recipient":"ASSIGNMENT"}`; response includes permitted
message ID, source reference, fixed bounded title summary, actual bound native
recipient, urgency, transport and wake:false. Failed/uncertain requests remain.
Linked payload has message_id and reference; both message and link must be readable.
Validation reports permitted current messages only, without hidden content counts.

Snapshot payload: operation_id, selected_ids, assessments (optional). It selects
exact immutable message references/targets and omitted visible coverage, at most
200 total references/250000 bytes, and copies no conversation. Only manager/senior
can snapshot in their own grants. Register its returned path/hash through the
existing Task artifact/input event at a meaningful boundary.

Assess payload: subtask and assessments. Each assessment has message_id, target,
disposition (addressed/rejected/obsolete/deferred), owner (current actor's assignment),
decision_kind (synthesis/acceptance/review/verification), decision_id, evidence and
reason. The reference must resolve to actual current canonical decision bytes;
invented or stale IDs fail. Senior may cite its own synthesis; manager may cite its
current decision/assigned-review/verification evidence. Deferred remains blocking.
Formal owners still inspect semantics and criteria: a supplied label is no proof.

Proposal payload: operation_id, owner_kind, thread_id, selected_ids, evidence,
suggested_change, validation, limitations. It produces a pending owner handoff;
see knowledge-and-maintenance.md. No knowledge or maintenance owner is invoked.

Errors expose a constant code only, never rejected content or private filenames.
The helper reports unsupported topology/leases/bindings and never repairs canonical
state or silently upgrades historical schemas. Version 1 has no delete command.
