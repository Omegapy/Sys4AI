<!-- Generated from task.json revision 2. Do not edit directly. -->

# Task: Implement automatic Task intake and close-old-task lifecycle

## Identity

| Field | Value |
| --- | --- |
| Task ID | TASK-20260904-5D29651E |
| Status | completed |
| Created | 2026-09-04T17:36:19-06:00 |
| Updated | 2026-09-04T18:06:04-06:00 |
| Parent | None |
| Revision | 2 |

## Description

Update the active Sys4AI Task workflow and deterministic helper so explicit work intake reuses a matching active Task or creates a new one without a creation/reopen prompt, and closes inactive unfinished Tasks after 30 days with the distinct terminal status close-old-task. Preserve the generated index, canonical history, read-only routes, project ownership, and all unrelated work.

## Definition of done

- Task intake automatically returns the uniquely matched active Task or creates a new Task when no active match exists; completed or age-closed records remain historical and do not trigger a reopen-or-new confirmation.
- The helper supports close-old-task for nonterminal Tasks inactive for at least 30 days, records closure without completion claims, preserves responses and identity, and reports the terminal status in validation, index, list, show and counts.
- Explicit work intake performs the stale-Task policy through governed helper transactions; status, list, show, continue, validate and startup checks remain read-only, with meaningful lock, revision, ambiguity, time-boundary and partial-result tests.
- Root Task/Agent Task guidance, helper contract, metadata, applicable root instructions and proportionate regression tests agree with the new behavior and preserve separate project-local ownership.
- Targeted helper and root integration checks pass, a disposable end-to-end intake and stale-closure scenario is verified, and live Task projections validate with no unexpected changes to reusable source collections, child projects, managed plans or existing Task histories.

## Current summary

Automatic Task intake and 30-day close-old-task lifecycle are implemented and verified in the active Sys4AI workflow. The current policy implementation Task is complete. Highest verification level: runtime behavior observed in isolated fixtures and live Task intake. The separate Memory System implementation Task is awaiting its existing repository disposition; original native goal and managed plan were not marked complete.

## Blockers

None

## Open questions

None

## Next step

None

## Latest Task Response

[RESP-0001](responses/Task-Response-0001-2026-09-04T18-06-04-06-00.md)
