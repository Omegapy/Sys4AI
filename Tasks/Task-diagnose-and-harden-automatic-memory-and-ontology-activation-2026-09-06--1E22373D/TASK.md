<!-- Generated from task.json revision 9. Do not edit directly. -->

# Task: Diagnose and harden automatic memory and ontology activation

## Identity

| Field | Value |
| --- | --- |
| Task ID | TASK-20260906-1E22373D |
| Status | cancelled |
| Created | 2026-09-06T14:14:36-06:00 |
| Updated | 2026-09-06T20:46:33-06:00 |
| Parent | TASK-20260906-A5CB956D |
| Revision | 9 |

## Description

Investigate why the Sys4AI root and project initialization left memory semantics, Cognee, ontology and combined context disabled or incomplete; fix the implementation, dependency installation, preserved-state migration and automatic enabling for the root and both new and existing project setup. Coordinate with the already active operational setup Task and verify actual installed services before claiming readiness.

## Definition of done

- Each observed activation failure and the historical semantic-disabled default has a source-backed diagnosis, a bounded correction or verified existing correction, and relevant regression evidence.
- The root has compatible installed memory and ontology runtimes, semantic memory enabled through a supported migration, and current source-backed exact, Cognee semantic, ontology, ontology-semantic and combined-context checks all pass.
- Canonical init-new-project create installs, configures, enables, synchronizes and verifies both systems automatically; a real isolated new-project run and an identical rerun prove this behavior.
- Canonical prepare-existing upgrades an initialized exact-only project and prepares an uninitialized existing project automatically, preserving identity, custom files, canonical sources, existing records/history and unrelated permissions; real isolated runs prove the behavior.
- Installation, provider, model, source-drift and interrupted-setup failures are explicit and recoverable, cannot report completed or ready prematurely, and have proportionate meaningful regression checks.
- Reusable source, active root initializer and mapped template assets and instructions agree on required operational readiness; the shipped artifacts and template checks pass.
- Final direct inspection, independent review, appropriate tests, preservation evidence and a durable diagnostic/handoff report cover every requirement without conflating package installation, source implementation and live root readiness.

## Current summary

Cancelled by explicit user instruction to close every open Task and stop the failed memory/ontology enabling attempt. No further implementation or testing is authorized for this attempt. Source, data, packages, model caches and evidence are retained. This cancellation does not claim the original definition of done was achieved.

## Blockers

None

## Open questions

None

## Next step

Task cancelled at user request. Do not continue this attempt; any future retry requires a new explicit user request.

## Latest Task Response

[RESP-0008](responses/Task-Response-0008-2026-09-06T20-46-33-06-00.md)
