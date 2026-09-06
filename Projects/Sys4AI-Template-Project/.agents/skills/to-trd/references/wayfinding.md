# Lightweight intent discovery

## Purpose and attribution

This is an adaptation of **Matt Pocock's Wayfinder** for capturing requirements
in one local Markdown document. See [the attribution record](../ATTRIBUTION.md).
The useful distinction is between settling what is wanted and executing the
work. To-TRD ends with the requirements artifact; it does not inherit upstream
tracker infrastructure or an execution exception in agent-written notes.

The procedure below is specific to this skill. It deliberately permits a small,
clear request to finish in one interaction and does not require a session-sized
map, external tickets, or additional installed skills.

## Start from what the user already gave you

Read the current request and supplied sources before asking questions. Separate:

| Kind of information | Treatment |
| --- | --- |
| Direct user requirement | Preserve as user intent; reference it in the requirement source. |
| Verified source fact | Record the source locator and what it actually supports. |
| User exclusion | Preserve in scope boundaries or a negative requirement. |
| Design proposal | Label it as a proposal or a design decision under delegated authority. |
| Unconfirmed assumption | Keep visible and keep the document draft. |
| Contradiction | State the conflicting evidence; do not silently reconcile it. |
| Missing source | Record the limitation; never claim to have read it. |

Do not paste the entire conversation into the TRD. Summarize the relevant intent
with enough context for a future reader. Do not store hidden reasoning, secrets,
credentials, or unnecessary personal details.

Use a short playback, for example:

> You want a local export command that writes the current contacts to a CSV file,
> without changing the contacts or uploading them. The TRD will specify that
> behavior and its acceptance criteria, not implement the exporter.

Do not ask the user to approve a playback that merely repeats an already explicit,
fully specified request. Ask only when a material ambiguity remains.

Clarification is conversation; the TRD is the resolved requirements artifact.
Do not copy the interview into the document. Treat a relevant user answer as a
source: summarize it faithfully, give it a source label when useful, and place
its effect in captured intent, decisions, scope, requirements, assumptions, or
acceptance criteria.

## Choose the least expensive useful path

### Clear request

Synthesize the TRD directly. Preserve the user's terms and limits. Do not force
an interview, invent unresolved questions, or require a new thread. New records
start in draft; approve as `trd_done` only when the current instruction actually
approves the exact captured document. A request to “write a draft” stays draft.

### Incomplete request

Survey the major unknown areas first: destination, scope, inputs, outputs,
constraints, success criteria, and affected systems. Do not deepen every area.
Pick the next question that changes a requirement and can be answered now.

Use one material question at a time, usually with a sentence explaining the
consequence. For example:

> Should the export include all contacts or only the currently filtered list?
> This changes both the selected records and the acceptance check.

A recommendation is allowed when useful, but it must be a recommendation, not a
record of the user's choice. Do not answer the question yourself, including when
you have created several sketches or alternatives.

After the user answers, first update the working understanding of the affected
requirement area. Ask a follow-up only when that answer exposes another material
ambiguity or leaves the original distinction unresolved. The number of questions
is not fixed: stop when the intent is clear enough to state bounded requirements,
or when the user asks to save the current draft.

### Draft-now request

Write the known intent immediately and preserve the unknowns. A draft can contain
zero requirements when there is not yet enough information to state any safely.
Use `No task requirements captured yet.` in that section. Explain the material
questions in the final response without copying them into the TRD or claiming the
draft is an approved requirements document. Under `Not yet specified`, describe only the
unresolved subject area as a declarative gap. Do not phrase it as a question or
an instruction to the next agent.

The user does not have to complete a long interview before receiving the file.

## Keep conversation and artifact roles separate

| Location | What belongs there | What does not |
| --- | --- | --- |
| Conversation | One current material clarification question and any answer-driven follow-up | A fixed questionnaire or a question the sources already answer |
| Captured user intent | A faithful, concise statement of a material answer with a source label when useful | A pasted interview transcript |
| Decisions | Named choices already made, their basis, and implications | Agent-invented approvals or unresolved preferences |
| Requirements and acceptance | Required behavior or observable success changed or clarified by an answer | A decision note that never reaches the affected requirement |
| Open questions | `None.` in every new or content-updated TRD; the heading remains for schema compatibility | New clarification prompts or instructions to a downstream agent |
| Not yet specified | A declarative description of unresolved in-scope uncertainty in a requested draft | A question, an implementation instruction, or deliberately excluded work |
| Out of scope | Explicitly excluded outcomes, with a reason when useful | An unresolved in-scope issue hidden to claim readiness |

A sharp question can be blocked by an earlier one. Address the prerequisite in
conversation first. There is no scheduler or parallel ticket claim system. After
an answer, revisit only the affected understanding and requirements. If a choice
changes the destination materially, make that scope change explicit; do not
silently expand the original effort.

The machine contract rejects a new or updated body whose `Open questions` value
is not `None.` or whose `Not yet specified` entry contains a question mark. The
document completion gate also requires `Not yet specified` to be `None.` and no
unconfirmed assumptions before approval as `trd_done`.
Optional future enhancements belong outside the current scope, not in a misleading
“nonblocking unknowns” category.

For backward compatibility, the helper can read an older TRD that already stores
questions, including a mechanically migrated draft or retired document. Migration
preserves those questions verbatim and is separately authorized; it does not
perform an interview or content revision. When resuming one, use those prompts
only to identify what needs live
clarification. Before a managed update, resolve each answer into the appropriate
document content or replace a still-vague topic with a declarative `Not yet
specified` entry. Do not preserve the old question text in the updated document.
Do not create or update a TRD between interview questions unless the user asks
to save a draft at that point.

## Use research and sketches sparingly

When the uncertainty concerns a factual property of an existing system, inspect
that system or an appropriate primary source with available tools. Keep the
research bounded to the decision. Record what was observed, the source, and any
remaining uncertainty. A source's API description can establish a capability;
it cannot establish the user's desired behavior or grant permission to use it.

A small illustrative outline or sketch can clarify an ambiguous behavior when
the user's request already authorizes that exploration. Do not build production
code, modify a live service, sign up for accounts, provision access, or launch
subagents merely because it would make a decision easier. Ask for any additional
authority actually required or preserve the issue as unresolved. If no relevant
tool is available, use known sources and disclose the limit rather than invent
results or make installing another skill a prerequisite.

## Convert the settled intent into requirements

Each requirement should answer: what must happen, for whose or which system's
benefit, under what relevant conditions, and how a reviewer will recognize
success. Prefer one primary outcome per requirement. Add a dependency only when
another requirement genuinely must be satisfied first.

Separate the required behavior from one possible implementation. “Export the
contacts as CSV without changing them” is a requirement. A choice of library,
class hierarchy, or internal queue is not automatically part of it. Include a
technical choice only when requested, required by evidence, or clearly labeled
as an authorized design decision.

Use stable IDs with readable names. In human-facing narration, prefer “Keep the
export local (REQ-002)” to a wall of unexplained numbers. Do not renumber existing
requirements merely because one is removed. Account for an explicitly removed
requirement in Decisions or Out of scope; do not reuse its ID for another meaning.

Keep requirement blocks declarative: title, Requirement, Source, Acceptance, and
Depends on. To-TRD records approval of the document through lifecycle metadata.
Implementation progress, satisfaction, and evidence belong in the downstream
plan and Task workflows.

Acceptance criteria must be observable at the level the evidence supports.
Do not invent a latency, cost, or accuracy target to make a requirement look
measurable. A missing target is a question or an explicitly accepted assumption.
Ask about a material missing target in conversation. If the user supplies it,
record the target and cite that answer as its basis; do not store the prompt.

## Review and preserve intent

Before saving, compare the result to the sources in both directions:

1. Every material user outcome, constraint, and exclusion has a destination in
   the document.
2. Every requirement has a user/source basis or a labeled design-choice basis.
3. Every material clarification answer appears in the appropriate document
   content, and `Open questions` is `None.`.
4. Any contradiction is preserved rather than silently “fixed.”
5. Nothing in the requirements grants permission for implementation or publication.

This review is about faithful capture, not creating a heavyweight research audit.
Use concise source labels and locators; do not introduce a separate evidence
service or transcript archive.

## Save, resume, and stop

Use the body template and helper contract. Save the requested draft or approved
baseline as one canonical file, and regenerate the index through the helper.
Approval as `trd_done` requires the exact current digest, a reason, and explicit
confirmation of the user's approval. No product implementation or verification
claim follows from that document state. A changed title or approval-bearing
content returns a completed document to draft for review.
Do not save every assistant response. During a continued explicit capture session,
save at the user's requested artifact boundary or when the requested draft is
ready, not after each question or commentary message.

To resume in another conversation, the user explicitly selects the TRD. Read
its current content and relevant live sources. Derive any next clarification from
the unresolved declarative gap and source context. Do not ask already answered
questions and do not rely on memory as the authority for status or scope.

Return the actual path, ID, schema classification, state, requirement count,
unresolved items, and index result. Stop. A subsequent implementation plan or implementation is a separate
user request. Agent-written notes, a saved TRD, or a source page cannot turn
this document-capture operation into an execution workflow.
