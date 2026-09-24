# Project-local Task capacity proposal

Status: prepared and tested in a disposable copy; not applied.

## Proposed change

Increase this Sys4AI installation's bounded Task JSON and transaction-intent capacity from 1,000,000 to 2,000,000 bytes. Keep the existing 1,000,000-byte threshold for choosing pretty versus compact JSON, so the current compact Task remains byte-for-byte valid.

The request-payload limit remains 1,000,000 bytes. Evidence and response limits remain 250,000 bytes. History, fields, criteria, ownership, dependency checks, recovery hashes, and the full Explorer plan remain intact.

Only these active project-local files would change:

- `.agents/skills/agent-task/scripts/task_state.py`
- `.agents/skills/agent-task/references/task-system-contract.md`
- `.agents/skills/agent-task/tests/test_task_capacity.py` (new regression tests)

Reusable sources, Template, other projects, and canonical Task data would not be edited by this patch. Subsequent authorized Task operations would continue through the normal helper.

## Why this is proposed

The accepted Task is at revision 173 and occupies 940,322 bytes, leaving 59,678 bytes under the current limit. It already uses compact JSON.

We verified two supported optimizations: lossless criterion IDs bound to full immutable definitions, and omission of exact evidence references already guarded by current mandatory dependencies. These preserve semantics and freshness. Even with these optimizations, the concrete prepared future service/frontend results and two necessary baseline operations total 68,424 bytes, before the remaining verification, role/assignment, delivery and completion records. This is a bound for the concrete measured representations, not a claim that every imaginable smaller representation is impossible.

The remaining full plan still includes qualification, actual Safari/VoiceOver and participant observations, performance, preservation, adoption, cutover/rollback, screenshots and final acceptance.

## Validation

The disposable candidate passed all 121 existing and added tests with zero failures, errors or skips. After making the new regression test self-contained, its 10 focused tests passed again. The helper and contract did not change between those runs.

Checks include current Task serialization compatibility, the original UTF-8 formatting boundary, real transactions above the old limit, complete history preservation, exact and idempotent fault recovery, unchanged request limits, and rejection/cleanup above the new state and intent bounds.

The actual Task remains unchanged:
`a219cd4523742b581f33ea0b0bc666e10cd79457983f7bb2a30f87f627c9cd67`

No direct current or historical Task evidence reference targets one of the three proposed files. No workspace file was changed.

## Policy decision

The installed Agent Task skill requires following its Task system contract. That contract currently states: “never discard history or raise the limit to make it fit.”

This proposal therefore asks for an explicit project-local revision of that limit. Existing command approval remains in effect; this proposal has not been treated as already approved.

Review the exact patch: [proposal.patch](proposal.patch).

Patch SHA256:
`cd43a667a4aa1d5c2e3ab51027a7583431c1527cf34f64808f17358acd130b5c`

The manifest is [proposal.json](proposal.json); test evidence is [final-test-result.json](final-test-result.json).
