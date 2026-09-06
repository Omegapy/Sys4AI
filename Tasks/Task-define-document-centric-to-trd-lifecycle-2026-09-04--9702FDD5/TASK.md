<!-- Generated from task.json revision 8. Do not edit directly. -->

# Task: Define document-centric To-TRD lifecycle

## Identity

| Field | Value |
| --- | --- |
| Task ID | TASK-20260904-9702FDD5 |
| Status | completed |
| Created | 2026-09-04T12:40:31-06:00 |
| Updated | 2026-09-04T13:07:06-06:00 |
| Parent | None |
| Revision | 8 |

## Description

Define a governed redesign of the To-TRD lifecycle so it tracks the state of the TRD document itself rather than implementation of the requirements. Replace the current not_done semantics with a TRD-complete state, keep implementation progress in the separate implementation-plan and Task systems, establish migration and compatibility rules, and capture the result in a managed TRD without implementing the redesign.

## Definition of done

- The active and reusable To-TRD packages, helper lifecycle schema, tests, documentation, current TRD catalog, and To-Implementation-Plan handoff contract are inspected as current sources.
- The user confirms the exact canonical and user-facing lifecycle vocabulary, including the replacement for not_done and the meaning of draft, TRD completion, and retirement.
- The requirements define clear ownership boundaries: To-TRD tracks document completion, while implementation-plan and Task systems track planned and performed implementation work.
- The requirements define how existing TRD records, indexes, commands, tests, documentation, reusable and active packages, and downstream consumers migrate without silently corrupting state.
- A managed project-local TRD is created through the To-TRD helper with source-linked requirements, observable acceptance criteria, explicit exclusions, Open questions set to None, and no unresolved ambiguity disguised as downstream instructions.
- No To-TRD implementation, existing-record migration, dependency installation, destructive operation, Git action, publication, or deployment is performed under this requirements-definition Task.

## Current summary

TASK-20260904-9702FDD5 is complete. TRD-20260904-E2BADD07 revision 3 is the user-approved requirements baseline for a document-centric To-TRD lifecycle using draft, trd_done, and retired. Its legacy frontmatter remains draft by explicit user authorization until a separately planned and authorized implementation migrates it. No package implementation, existing-record migration, dependency installation, destructive operation, Git action, publication, or deployment occurred.

## Blockers

None

## Open questions

None

## Next step

None

## Latest Task Response

[RESP-0007](responses/Task-Response-0007-2026-09-04T13-07-06-06-00.md)
