# Automatic project memory capture

Source: user's request to enable automatic capture now, default it on when
creating or preparing projects, and disclose the setting with an opt-out after
successful initialization. Direct implementation and tests; no sub-agents.

| Requirement | Implementation | Verification |
| --- | --- | --- |
| R1: Support on/off with on as the new-install default | Boolean schema/core, starter, current root config | Both values validate; non-booleans fail |
| R2: Capture useful findings automatically at work completion | Agent completion instructions and a checked capture command sharing publication safeguards | Enabled capture, disabled no-write, retry, stale evidence and authority tests |
| R3: Enable new-project and first memory adoption into existing projects | Initializer v6, project-local Director binding and completion status | Both routes, preserved governing files, distinct project scopes |
| R4: Disclose on and offer off after completed setup | Structured completion notice and mandatory skill handoff | Actual completed output; no misleading on notice for incompatible preserved installs |
| R5: Honor opt-out and preserve history | Exact-version setting command; old receipt editions and existing packages retained | Off survives rerun; v5 and earlier receipts remain their edition; notes unchanged |
| R6: Adopt source, Template and active root consistently | Source-first edits, checked Template update, scoped root adoption | Source/root/Template parity and affected suites |

Automatic means an agent completion workflow: after substantive work, an accepted
decision, or an observed failure, the responsible Director/manager evaluates
durable evidence and captures useful new knowledge before its final handoff.
No note is required for trivial/inspection-only work, duplicate findings, or
unsupported claims. Reads stay read-only. This is not a background service.
Existing product projects are not bulk-modified. Git publication is separate.
