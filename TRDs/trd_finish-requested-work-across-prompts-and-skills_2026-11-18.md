---
schema_version: 2
trd_id: "TRD-20261118-666F5516"
title: "Finish requested work across prompts and skills"
slug: "finish-requested-work-across-prompts-and-skills"
created_at: "2026-11-18T09:15:05-07:00"
updated_at: "2026-11-18T09:16:01-07:00"
status: "trd_done"
revision: 2
last_action_id: "TO-TRD-006"
status_reason: "The user explicitly approved the eight requirements in the presented revision 1."
---

# Task Requirement Document: Finish requested work across prompts and skills

## Destination

Give a Sys4AI user a completed, verified result when the agent can deliver it and a precise account of any work that genuinely depends on someone else. Apply this expectation to ordinary prompts, skills and bounded assignments in both the depot's reusable guidance and its active root.

## Captured user intent

- U1 — On November 18, 2026, the user described agents stopping midway, handing obvious choices back to the user and leaving work unfinished. The user wants agents to use evidence and judgment, finish the requested work and seek guidance when a real decision remains.
- U2 — The user requested the revised recommendations titled “Finish the requested work,” including recovery, partial blockers, explicit stops, ownership, a self-contained handoff and three ordinary-prompt checks.
- U3 — The user explicitly invoked To-TRD and asked for these recommendations to be implemented in the reusable depot folders and in the active Sys4AI root functionality files.

## Context and sources

- S1 — [GPT-6.2 task completion and writing guidance](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6.2-astra#task-completion), [Codex prompting guide](https://learn.chatgpt.com/guides/prompting-gpt-6-2-astra), and [TheAIGRID on testing with real work](https://www.youtube.com/watch?v=hx1wLU9fldA&t=1617s).
- S2 — [Root instructions](../AGENTS.md), [root Director](../ROLE.md), [reusable Director](../ROLES-depo/project-director-ROLE.md), the worker and specialist pairs in `ROLES-depo/` and `Roles/`, and the [Template update contract](../depot/template-update.md). The active root has project-specific copies.
- S3 — [Root soul](../SOUL.md), [reusable soul](../SOULS-depo/SOUL.md) and [communication skill](../SKILLS-depo/communication/SKILL.md). Existing sections cover missing evidence, recovery, stopping and final reporting.

## In scope

The reusable soul, relevant roles and communication skill, their mapped Template installation, and the corresponding depot-root instructions and necessary existing integrity checks or bindings. Qualification covers an obvious documented command, recovery after a failed check, and useful delivery with one source missing.

## Out of scope

Changes to ordinary product projects, activation or mutation of a managed Task, a new scheduler, changes to agent models or effort, external publication and changes to unrelated work. Existing explicit approval and stopping requirements continue to apply.

## Task requirements

### REQ-001 — Finish the requested outcome
- Requirement: An agent carries ordinary prompt requests and skill-driven assignments through the deliverable and any authorized verification needed to finish it.
- Source: U1, U2, U3 and S1.
- Acceptance: An advice request produces usable advice. A requested repair produces the repair and its relevant verification. The agent compares every requested result with what it can actually deliver before ending its turn.
- Acceptance: A remaining in-scope action the agent can take is carried out. The user receives an offer or instructions to act only when further action actually belongs to them.
- Depends on: None.

### REQ-002 — Resolve routine questions from evidence
- Requirement: The agent consults the conversation, project files, conventions, and direct observation before asking for guidance. It selects a clearly suitable authorized choice and discloses a material assumption.
- Source: U1, U2 and S1.
- Acceptance: With one documented project check command, the agent finds and runs it without asking the user which command to run.
- Acceptance: When available evidence leaves a consequential choice for the user, the agent asks the smallest question that settles it. A guess about consent cannot authorize a restricted action.
- Depends on: REQ-001

### REQ-003 — Recover from a failed attempt
- Requirement: The agent investigates a failed attempt and pursues an available, authorized recovery grounded in what the failure revealed.
- Source: U1, U2 and S1.
- Acceptance: When the first check on a repair fails and the cause is recoverable, the agent identifies the cause, corrects it, reruns the affected check and reports the observed outcome.
- Acceptance: An explicit request to pause or stop takes effect under the applicable ownership rules.
- Depends on: REQ-001

### REQ-004 — Continue work that is independent of a blocker
- Requirement: A missing input, permission, credential or safety fact pauses the work that depends on it. The agent completes other authorized work and requests only the outstanding input needed to resume.
- Source: U1, U2, S1 and S3.
- Acceptance: Given two sources for a review and only one accessible source, the response covers the accessible source, identifies the precise unsupported conclusion and states what would resolve it.
- Acceptance: The agent reports unmet criteria honestly and observes required permissions and skill-specific approval steps.
- Depends on: REQ-001, REQ-002

### REQ-005 — Assign and integrate observable results
- Requirement: The assigning Director defines an observable example of successful delivery. The worker owns its bounded deliverable through verification and the coordinator owns integration and the final result. An activated Task retains its sole confirmed manager.
- Source: U2, U3 and S2.
- Acceptance: A consequential assignment identifies something the recipient can inspect or try to accept the result. A worker supplies its evidence and any affected criterion. The responsible coordinator verifies the integrated outcome.
- Acceptance: An ordinary prompt can complete without activating a managed Task or creating a ledger record.
- Depends on: REQ-001, REQ-004

### REQ-006 — Resolve specialist scope and delegation
- Requirement: The documentation, knowledge, and improvement-maintenance Curator workers finish the portion they own and return additional work to their assigning manager.
- Source: U2, U3 and S2.
- Acceptance: Each specialist's paired instructions and role agree that the specialist does not delegate. When adjacent work needs a different assignment, the specialist identifies it to the manager and completes the authorized portion.
- Depends on: REQ-005

### REQ-007 — Make the final handoff self-contained
- Requirement: The final response identifies what was completed, what evidence supports it and which requested result, if any, remains open. Requested artifact-only formats continue to be respected.
- Source: U2, U3 and S1.
- Acceptance: A reader can determine the result and any material limitation without opening progress updates or reading a worker's shorthand.
- Acceptance: An outstanding authorized step within the current request is taken before a final handoff. Final text distinguishes completed checks from pending checks.
- Depends on: REQ-001, REQ-004

### REQ-008 — Deliver both reusable and active instructions
- Requirement: The completion rule belongs near the top of the reusable and active project souls. The corresponding Director, worker, specialist and communication instructions are available in the reusable sources, the mapped Template and the active depot root.
- Source: U2, U3 and S2.
- Acceptance: The Template updater reports current and each changed mapped copy matches its reusable source. The active root contains the required behavior and retains its project-local wording, Task intake policy, and ownership.
- Acceptance: Root and role instruction entry points continue to load the project soul. Current governance bindings and checks cover the adopted root bytes. Existing product projects, historical records and unrelated working edits are preserved.
- Depends on: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007

## Decisions

- The user delegated placement. Put the shared behavior immediately after Governing priority in the project soul. Root, Template and role instructions already require that read. Role files own assignment and handoff details. The communication skill owns presentation.
- “Finish” is measured against the requested deliverable. A recommendation request ends with usable recommendations. A request for a repair includes the authorized correction and its relevant check.
- Use the existing source-to-Template mapping and an explicit scoped adoption at the depot root. Preserve the historical release evidence while checking the current governing files. The exact phrasing, checks and compatible binding updates are bounded implementation choices.

## Open questions

None.

## Not yet specified

None.

## Assumptions

None.
