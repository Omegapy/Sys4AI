# Native delivery

Pending requests are reconstructed from durable posts and recipient-specific
successful native notification receipts. The sender's active session invokes the
existing native send_message API and records its actual recipient and returned
result. Failed/uncertain results remain pending; repeated identical operations
preserve one result. A returned receipt is cooperative evidence, not an authenticated
transport acknowledgement, comprehension proof or native lifecycle observation.

Use bounded digest at the four working checkpoints. For manager blockers, attempt
notice at the next available active-session control opportunity. Routine requests
never call followup_task or launch an idle agent. Waiting outside a session creates
no polling service. An interrupted session reopens existing immutable files and
reconciles pending delivery rather than republishing posts or replacing assignments.

Material change is a separate owner workflow: observe stopped/completed, queue
exact packet with send_message, commit assignment.inputs using that actual
receipt, then followup_task. Unchanged continuation uses assignment.resume first.
Record actual native observations for pilot proof. Synthetic deterministic tests
cannot establish native isolation, delivery, idle behavior or interruption recovery.

Native transport also protects future full-history forks. While any required
initial candidate or assigned first-review gate is closed, pending requests
withhold substantive titles, semantic message IDs and source paths even from
manager-directed notifications. Only the validated closed fixed operational
vocabulary can be prepared for native delivery. Withheld contributions remain
durable and become eligible after exact canonical release; their counts are not
reported as permitted coverage. This transport restriction does not broaden
board visibility or grant permission to load sibling findings manually before
an independent fork. Generic/component workflows without those gates retain
ordinary permitted delivery.

An empty send_message result {} and null provide equally weak return evidence.
Do not label a new sender-owned notified receipt from either return; record the
actual raw result with delivery-attempt/uncertain evidence instead. Historical
schema 1 notified records stay readable with their original state and raw result,
but derived notification_confirmation marks empty returns unconfirmed and pending
remains retryable. No receipt can invent fields that the native tool did not return.

When the addressed recipient actually observes the exact immutable notice in its
native mailbox, it can publish its own schema 2 notified receipt independently of
reading. Use the existing delivery command with a granted payload file:

```json
{"operation_id":"observed_notice1","mid":"AUTHOR.MESSAGE","state":"notified","recipient":"CURRENT_RECIPIENT","evidence":"Observed this exact message ID/hash in the native mailbox notice; identify the real observation context concisely.","native_receipt":null,"receipt_version":2}
```

The helper checks current assignment/native binding, addressed recipient, exact
message version and active write lease. Nonblank observation text is an attributed
recipient assertion and needs known actual mailbox evidence; it is not an
authenticated transport proof. Notify alone changes neither reported_reading nor
unread. A separate acknowledged receipt is required for reported reading. Different
recipients remain independent, identical operation/payload retries return the same
file/hash, and conflicting reuse fails. Version 2 receipt readers are required;
Task/message/policy/native-protocol versions and stored version 1 bytes are unchanged.
