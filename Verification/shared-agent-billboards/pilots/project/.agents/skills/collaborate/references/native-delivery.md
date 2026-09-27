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
