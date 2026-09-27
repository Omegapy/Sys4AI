# Task collaboration contract version 1

The board is one logical join of immutable participant files. It is communication
evidence, not a second ledger. Canonical Task categories, baselines, assignments,
reviews, acceptance, implementation targets and completion retain their existing
owners. A done-post, vote, alleged approval, answered thread or acknowledgement
has no decision authority. Candidate and reviewer originals remain preserved.

## Binding and storage

A manager publishes a policy through artifact.register and includes the registered
path/hash in applicable baseline.inputs and assignment.context. The helper reads
the actual strict Task validator, current native receipts, role-read evidence and
exact policy bytes. It accepts schema 2 orchestration versions 1 and 2 without
migration; version 2 retains protected live native-context checks. Legacy schema
1 remains readable by its own Task helper, but cannot post without explicit upgrade.

The policy has exactly version, project, task, execution, generation, manager,
participants, subtasks, bounds and topology. Project is the selected absolute
root. Each participant maps to namespace and subtask_id. Namespace ends in
collaboration beneath that assignment's expressly granted path. Generic workers
and implementers use a Task-specific Evidence/TASK_ID/work/ASSIGNMENT directory
outside protected canonical Tasks/, expressly named in baseline and fit grants;
only selected owner snapshots are then registered into Task evidence. Solver, reviewer
and senior namespaces remain under their existing work/ASSIGNMENT_ID directory.
Readers need an existing canonical read grant covering each author namespace;
a policy cannot enlarge that grant. The manager's policy and snapshot namespaces
must also be expressly granted. Independent outputs never use a shared mutable file.

Policy subtask entries have phase, audience, independent_first_pass,
reviewer_first_pass and exchange_stop. Phase is independent, peer-exchange,
review, component or integration. Audience contains current assignment IDs.
Exchange_stop is a concrete bounded question/phase/evidence stopping condition.
Bounds default to record_bytes 65536, output_bytes 32768 and page_items 20; values
may be reduced or configured within 250000, 32768 and 200 respectively. Existing
Task JSON 2000000-byte, evidence 250000-byte and 200-reference limits remain.
Topology is common-store-cooperative. Other stores/transports are unsupported.

Each namespace contains messages/, receipts/, snapshots/, proposals/ and views/.
Only the owning assignment writes there. A regular JSON file contains payload
and sha256, the digest of canonical UTF-8 JSON payload. Atomic exclusive hard-link
publication follows a complete temporary file, file fsync and directory fsync.
Temporary files are ignored. Collision never overwrites; identical payload-bound
operation retries return the original. Directory-relative O_NOFOLLOW reads and
writes reject traversal and symlinks. Platform inability fails closed. Stable
operation IDs name complete immutable files; no shared array, journal or index
is written. Durability precedes notification. Pending delivery is reconstructed
from messages minus successful per-recipient delivery receipts after a crash.

## Contributions and visibility

Message types are note, question, finding, challenge, blocker, help-request,
change-notice and proposal. Honest questions and speculative notes need no proof.
The envelope contains version, project, task, execution, generation, assignment,
native_id, policy_sha256, operation_id, message_id, thread_id, reply_to,
supersedes, subtask, type, title, body, phase, visibility, recipients,
requested_response, urgency, targets, evidence, limitations and material.
Identity is filled from the current assignment, not accepted from post text.
References use exact path/hash objects. Material findings, challenges, blockers
and change notices require an exact target. Requested_response states the help
question/contribution/stopping condition. Urgency is routine or blocker and
confers no wakeup authority. Unknown fields and versions fail closed.

Visibility is operational, findings or verdict. Findings include substantive
reasoning, interpretations, assumptions and candidate conclusions even when
posted as a note. Verdict includes reviewer conclusions. Operational notices use the closed fixed vocabulary, numeric IDs and frozen
baseline references in commands.md for independent/reviewer-first policies.
Arbitrary authored prose stays findings. Every envelope field is checked, so
operational text cannot mechanically bypass the seal. Receipt prose/tool results
are similarly sealed from other independent recipients. Outside this closed
vocabulary, semantic truth and runtime context discipline remain owner duties.

Filter before titles, bodies, previews, counts, search, digest, notifications,
views, memory-selection snapshots or linked artifacts enter recipient context.
Addressed recipients and author can read only within current scope. Manager
access follows its current explicit read scope. With independent_first_pass,
sibling findings wait for candidate_set to resolve every current frozen solver
slot and exact preserved bytes. Reviewers receive their assigned candidate only;
other findings/verdicts wait until their own exact first review is recorded.
A reviewer verdict remains sealed from other reviewers until those recipients'
first assessments are recorded. A policy phase or a post's claim never proves a
gate. Peer exchange opens only after preserved candidates. Material changes
recheck current inputs and gates and reseal affected conclusions if necessary.
Direct linked content is returned only after both the message and canonical
reader grant pass; no raw-path escape or unfiltered preview exists.

Filters support subtask, thread, participant, message type, affected artifact and
phase, plus literal search and unread. Results are bounded with visible total,
returned, remaining and exact source hashes. Counts include only eligible messages.
Unread is current eligible exact versions minus recipient acknowledgement or
handled/answered/deferred receipts, never a global cursor. Releasing an earlier
sealed message makes it unread even after later messages were handled. Read/list/
search/digest/validate do not acknowledge or mutate files. Explicit rebuild writes
only the reader's authorized derived Markdown, never Task projections.

Replies point to a readable original in the same thread. Corrections are new
messages with supersedes and preserve the original bytes. Supersedes must retain
the originating author and thread. An original material objection stays relevant
until its exact current owner evidence assesses it; a correction does not erase
history. Do not represent an old-version challenge as proof about a later target.

## Receipts, decisions and privacy

Per-recipient immutable receipts distinguish delivery-attempt, notified, failed,
uncertain, acknowledged, handled, answered and deferred. Receipt reference binds
exact message ID/hash and current recipient. Notified requires a recorded actual
native send_message result; persistence cannot imply delivery. Acknowledged means
reported reading only, not comprehension or incorporation. Thread answered and
deferred states are attributed communication evidence, not formal resolution.

The active authorized owner prepares permitted pending requests, uses native
send_message and records actual results. Routine delivery never wakes idle
participants. At the next available active-session control opportunity, attempt
manager blocker notice; outside authorized sessions retain pending state. Material
rebind requires observed stop/completion, exact send_message packet, committed
assignment.inputs then followup_task. Unchanged resume retains assignment.resume.
No helper performs native invocation, launch, polling or lifecycle writes.

Selected snapshots identify exact messages, targets, hashes, included coverage
and omitted visible coverage within existing limits. A manager/senior assesses
material objections at review, synthesis, acceptance and completion boundaries.
Unresolved or only informally closed current objections block unsupported gates.
Attributable owner dispositions cite exact target, evidence and current canonical
decision reference; defer remains unresolved. Harmless speculative or obsolete
posts have no universal veto. Canonical candidate/review/synthesis/acceptance checks
invalidate only dependent evidence on changed bytes/versions, retaining history.

Exclude credentials, unnecessary personal data, hidden reasoning and full
transcripts. A small known-secret/control-character validator rejects obvious
credential formats with constant diagnostics; it cannot detect every secret or
judge all personal data. Authors and owners must inspect content. No rejected
payload appears in errors. No retention deletion is supplied; unresolved threads,
referenced decision evidence and preserved candidate history remain intact.
