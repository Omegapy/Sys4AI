---
schema_version: 2
trd_id: "TRD-20260926-5A1422F9"
title: "Shared agent billboards with Task-governed collaboration"
slug: "shared-agent-billboards-with-task-governed-collaboration"
created_at: "2026-09-26T09:37:56-06:00"
updated_at: "2026-09-26T10:12:59-06:00"
status: "trd_done"
revision: 2
last_action_id: "TO-TRD-006"
status_reason: "The user explicitly approved the presented unchanged revision 1 as the completed requirements document."
---

# Task Requirement Document: Shared agent billboards with Task-governed collaboration

## Destination

Add a reusable shared-billboard capability to the Sys4AI framework so assigned agents can exchange questions, findings, concerns, and suggestions directly while preserving independent analysis and the existing Task system's execution authority.

## Captured user intent

The user's recommendation requests shared working awareness between formal handoffs, with one logical board per Task and a scoped project overview. Participants contribute directly without case-by-case discussion approval. Posting, delivery, acknowledgement, and an answered thread do not change assignments, requirements, accepted solutions, scientific claim status, or completion.

The intended workflow preserves an independent first pass, then permits bounded peer exchange, candidate revision, applicable assigned review, senior synthesis, and manager acceptance. Different implementation components may share interfaces immediately under their selected policy. File-backed immutable contributions, reliable bounded notification, read checkpoints, honest scope/isolation limits, and selected promotion through existing knowledge and maintenance owners form the first capability. Controlled native pilots and comparative quality evidence precede broader adoption. This capture is a requirements document; it starts no implementation, Task execution, adoption, or publication.

## Context and sources

The requirement sources below use the user's supplied section numbers. They identify the actual recommendation rather than treating it as a verified implementation or a grant to execute its future work.

- U00: The opening recommendation and 'What I examined' distinguish the Sys4AI framework from the Aether-Flow research repository and separate discussion from execution authority.
- U01: Section 1, 'Preserve what already works', preserves the three category teams, effective settings, native identities, and changed-input controls.
- U02: Section 2 separates discussion, canonical Task decisions, and durable memory/ontology knowledge.
- U03: Section 3 requires shared Task threads, filters, scoped project aggregation, and ledger-derived status.
- U04: Section 4 preserves first-pass solver and reviewer independence while allowing bounded exchange and component-specific policies.
- U05: Section 5 defines broad task-relevant contributions, message types, identity/version metadata, references, evidence limits, and corrections.
- U06: Section 6 requires checkpoints, proactive peer-impact notices, bounded help, and preserved disagreement.
- U07: Section 7 separates delivery/acknowledgement/handling from comprehension, review, acceptance, and completion.
- U08: Section 8 requires durable publication before retryable notifications, truthful native resumption, and no unattended AI.
- U09: Section 9 proposes immutable structured files, participant namespaces, a Python helper, generated views, bounded canonical evidence, protected file operations, and explicit sharing across worktrees.
- U10: Section 10 requires filtering before context exposure, release-aware unread tracking, exact target versions, honest enforcement claims, and data/authority/privacy separation.
- U11: Section 11 links selected verified lessons to memory and recurring issues to existing Curator owners without duplicating either system.
- U12: Section 12 supplies a hypothetical research-assumption challenge, not an installed role or established physics claim.
- U13: Section 13 requests a separate collaborate-like capability, staged contract/helper/habit/pilot integration, explicit schema compatibility, and depot/Template/adoption boundaries.
- U14: Section 14 supplies ten failure-case acceptance scenarios and a same-settings comparison of outcome quality and communication cost.

Current local inspection establishes the following constraints. Local HEAD is ebc9fb164a4de9d359efd76f371163546017898b, matching the commit cited in the supplied review; this is not a check of remote main. The working tree already contains unrelated untracked artifacts. No supplied historical execution record was rerun as a live collaboration test.

- C01: ../AGENTS.md, ../SOUL.md, and ../ROLE.md establish depot ownership, bounded authority, categories, exact source/adoption boundaries, and verification discipline.
- C02: ../.agents/skills/task/SKILL.md, ../.agents/skills/agent-task/SKILL.md, and ../.agents/skills/agent-task/references/orchestration-contract.md establish the canonical writer, category teams, exact candidate eligibility, current assignment scopes, artifact registration, and native material-input sequence.
- C03: ../.agents/skills/memory/references/task-integration.md establishes frozen identical initial memory packets, exclusion of current-run drafts/proposals, and separate knowledge publication authority.
- C04: ../.agents/skills/agent-task/scripts/task_state.py defines MAX_JSON_BYTES = 2_000_000 and strict unsupported-field rejection; the orchestration contract defines bounded immutable artifact/input interfaces.
- C05: ../SPECS.md selects root Python 3.12 in .venv and the existing standard-library Task/role/document helpers.
- C06: ../.agents/skills/curate/references/session-maintenance.md and ../curator-session.yaml require bounded active-session owner routing and preservation of pending work, with unattended background AI disabled.
- C07: ../depot/template-update.json and ../depot/template-update.md identify the registered neutral Template and checked reusable-source distribution; active root and ordinary products do not automatically adopt source changes.
- C08: ../.agents/skills/to-trd/SKILL.md and its storage contract require document-only capture, exact-revision approval, and separation from implementation progress.
- C09: ../.agents/skills/ontology/SKILL.md separates proposals, accepted review, and exact authorized ontology publication; a memory grant supplies no ontology authority.

The recommendation's Aether-Flow README assessment and September 19 saved planning-Task example are attributed historical context. This capture does not establish an active Aether-Flow installation or repeat that repository inspection. Microsoft, AWS, and SQLite guidance is mentioned without precise source links in the supplied text. Those external factual assertions, including the SQLite patch claim, are not independently verified or used as required technology/version choices in this baseline. Durable-post/retry semantics are required directly by U08. SQLite is outside the first implementation scope.

## In scope

The future capability comprises the collaboration contract and separate reusable skill/helper; immutable Task-local contributions and receipts; permitted reading, replies, filtering, release-aware unread handling and explicit acknowledgement; bounded retryable native delivery; generated Task and project views; source-level manager/worker/Task habits; scoped evidence snapshots; existing knowledge/Curator routing; compatibility design; checked neutral Template distribution; controlled disposable or otherwise explicitly authorized pilot installations; failure-case and native verification; and comparable-workflow quality/cost assessment.

The present operation creates only this managed requirements document and regenerates its TRDs index. Future active-root or product adoption must have its own exact authorized boundary. Project-wide aggregation remains required for the full capability, with the user's task-local pilot prerequisite rather than silent deferral.

## Out of scope

- Replacing the Task framework with unrestricted group chat or another execution/approval ledger.
- Giving each agent a separate conceptual discussion board or requiring shared edits to one mutable discussion file.
- New traffic-management agents, message brokers, external infrastructure, continuous model polling, or unattended AI execution.
- SQLite or another database in the first implementation; any later index must remain rebuildable and needs separately scoped requirements and current platform/version validation.
- Using Git commits as real-time messaging, or performing Git publication, external messaging, deployment, purchases, dependency installation, or service provisioning under this capture.
- Automatically adopting reusable changes into the active depot root, registered products, unregistered children, or Aether-Flow; changing the project registry merely because an illustrative repository is named.
- Automatic publication of all posts into memory or ontology, automatic maintenance execution, changed scientific claims, or hidden expansion of assignments and tools.
- Physics conclusions or claims that illustrative research perspectives are installed roles.

## Task requirements

### REQ-001 - Contribute without case-by-case approval
- Requirement: Let assigned participants post any task-relevant question, observation, concern, suggestion, or speculative idea directly within their existing scope and permitted visibility, without permission for each contribution.
- Source: U00, U02, U05 - decentralized discussion with explicit authority.
- Acceptance: A participant can post and reply within its granted namespace without a manager relaying or approving each sentence; a speculative note or honest question needs no evidence but identifies its uncertainty.
- Acceptance: Posting neither changes assignments, accepted solutions, project requirements, scientific claim status, write scope, nor authority to use tools or perform external actions.
- Depends on: None.

### REQ-002 - Keep execution decisions in the Task ledger
- Requirement: Keep assignments, baselines, formal reviews, acceptance, implementation targets, and completion under their existing Task owners and canonical ledger; billboard content is communication evidence.
- Source: U02, U03, U07 - discussion, decisions, knowledge, and status remain distinct.
- Source: C02 - installed Task and orchestration contracts.
- Acceptance: An 'I am done' post, an alleged approval, a popular answer, or a closed thread cannot establish a canonical decision or completion; decision displays resolve to the current Task record.
- Acceptance: Workers cannot mutate task.json, Task Responses, or Task projections through the billboard; TASK.md and Tasks/INDEX.md retain their generated-view roles.
- Depends on: REQ-001

### REQ-003 - Preserve category teams and native identities
- Requirement: Preserve generic, complex, and extra-complex team structures, separate required native identities, identical effective model and reasoning effort, frozen required teams, and controlled changes to inputs.
- Source: U01, U06 - existing coordination machinery and category limits.
- Source: C01, C02 - root ROLE.md and installed Task contracts.
- Acceptance: Generic work retains one accountable worker including authorized implementation; complex work retains at least two independent full-problem solvers and a distinct senior, without a new mandatory reviewer stage; extra-complex work retains a distinct assigned reviewer per solver and every current pass before synthesis.
- Acceptance: The manager remains distinct from team functions; authorized multi-solution implementation retains its distinct dedicated implementer; communication does not add roles, shrink teams, bypass gates, or change settings.
- Depends on: REQ-002

### REQ-004 - Provide one logical shared board per Task
- Requirement: Provide one shared logical Task board with threads associated with subtasks, artifacts, and questions, combining participant-owned contributions rather than requiring navigation through individual diaries.
- Source: U03 - task boards and shared working awareness.
- Acceptance: Permitted readers can follow a thread across multiple participants, see replies and stable references, and identify discoveries, unanswered requests, disputed assumptions or interfaces, and changes since their last checkpoint.
- Depends on: REQ-001

### REQ-005 - Filter task discussion
- Requirement: Support scoped filtering by subtask, thread, participant, message type, affected artifact, and collaboration phase.
- Source: U03 - required task-board filters.
- Acceptance: Each listed filter returns only matching authorized posts; filtering or searching cannot reveal hidden titles, bodies, previews, counts that disclose protected conclusions, or linked content.
- Depends on: REQ-004

### REQ-006 - Generate a project-wide overview
- Requirement: Provide a concise generated project overview of relevant unresolved blockers, cross-task concerns, requested decisions, and maintenance proposals from underlying boards and current Task state.
- Source: U03 - generated project aggregation rather than a second management database.
- Acceptance: Every overview entry traces to its source post or canonical Task reference; displayed Task completion comes from the ledger; rebuilding changes neither source posts nor Task state.
- Acceptance: Director and Curator access follows their existing scopes; sub-agents receive only material permitted by their project, assignment, and independence restrictions.
- Depends on: REQ-002, REQ-004, REQ-005

### REQ-007 - Select collaboration policy per subtask and phase
- Requirement: Select and bind an explicit collaboration and visibility policy for each participating subtask and phase instead of imposing universal isolation or unrestricted sharing.
- Source: U04 - independent analysis and component collaboration need different policies.
- Acceptance: The current policy identifies permitted recipients, sealed content, release conditions, and peer-exchange boundaries; its binding is available to the affected assignments.
- Acceptance: Agents implementing distinct authorized components can exchange interface information immediately when the selected policy allows it; independent solvers retain their separate first pass.
- Depends on: REQ-003, REQ-004

### REQ-008 - Seal initial solver findings
- Requirement: Preserve identical frozen initial problem inputs and prevent sibling solvers from receiving substantive candidate findings until all required independent submissions are preserved and recorded.
- Source: U04, U10, U11 - independent first pass and contamination prevention.
- Source: C02, C03 - initial solver and frozen memory contracts.
- Acceptance: Solvers may publish within their authorized output namespace during the first pass, but sibling conclusions remain unavailable through posts, notifications, summaries, search, overview, memory retrieval, and inherited context.
- Acceptance: The release gate refers to the complete required candidate set and exact preserved versions; queued solvers cannot inherit earlier siblings' drafts.
- Depends on: REQ-007

### REQ-009 - Share nonrevealing operational notices
- Requirement: Allow operational notices and clarification requests during independent work only when they do not reveal candidate reasoning or conclusions.
- Source: U04 - missing files, unavailable tools, and clarifications can be shared.
- Acceptance: A missing-source or tool-unavailability notice reaches its authorized recipients during the first pass; a notice containing a substantive candidate conclusion remains sealed or receives a permitted nonrevealing notification.
- Depends on: REQ-008

### REQ-010 - Distribute material clarifications consistently
- Requirement: Route a clarification that materially changes the assigned problem through the manager and distribute the same versioned update to every affected solver through the existing input-binding gates.
- Source: U04, U08 - shared material clarification and native lifecycle sequencing.
- Source: C02 - assignment.inputs and reconciliation.
- Acceptance: The update identifies its exact baseline, affected assignments, packet version and delivery evidence; no solver receives a private material change while its siblings retain an older problem.
- Acceptance: Posting the clarification leaves the authorized baseline unchanged until its owner records the change and binds the affected inputs.
- Depends on: REQ-002, REQ-008, REQ-009

### REQ-011 - Open bounded direct peer exchange
- Requirement: After preserving independent candidates, open a defined peer-exchange window for direct targeted questions, evidence challenges, missing assumptions, and reconciliation proposals within existing assignments.
- Source: U04, U06 - independent first pass, peer exchange, revision, review, synthesis, acceptance.
- Acceptance: Participants reply directly without manager relay; the window has a defined phase and stopping condition, and original independent candidates remain available alongside attributed later revisions.
- Acceptance: Discussion informs candidate revision before the applicable review and synthesis gates; it does not itself accept a revised result or require repeated unchanged discussion.
- Depends on: REQ-008

### REQ-012 - Preserve the assigned reviewer's first assessment
- Requirement: For extra-complex work, give each assigned reviewer the exact candidate, criteria, and permitted evidence and record its independent first assessment before exposing other participants' verdicts.
- Source: U04 - independent assigned review followed by consideration of further objections.
- Source: C02 - one-to-one current reviewer mapping.
- Acceptance: Other verdicts cannot reach the reviewer before its first assessment through content, summaries, notifications, or inherited context; subsequent consideration records whether additional objections change the result.
- Acceptance: Peer discussion never substitutes for the assigned review, and changed candidates require the applicable current assigned review before synthesis.
- Depends on: REQ-003, REQ-007, REQ-011

### REQ-013 - Require participant reading checkpoints
- Requirement: Require participants to inspect permitted unread discussion before starting or resuming work, before relying on a shared interface, before submitting a candidate revision, and before final handoff.
- Source: U06 - work checkpoints rather than continuous polling.
- Acceptance: Updated working contracts and live evidence show the applicable checks and resulting bounded incorporation or escalation; no always-on polling loop or unnecessary model wakeup is required.
- Acceptance: Checkpoint reads remain distinct from explicit acknowledgement and cannot silently change assigned inputs or write ownership.
- Depends on: REQ-007

### REQ-014 - Require prompt notices affecting peers
- Requirement: Require proactive posting when a discovered assumption conflict, source correction, interface change, failed check, reusable result, or dependency problem is likely to affect another assignment.
- Source: U06 - reveal affected work before final reports.
- Acceptance: In a pilot where a participant discovers an affected dependency or inconsistent interface, it posts the exact affected artifact and relevant limitation while peers can still act within the authorized workflow, rather than withholding the finding until final handoff.
- Depends on: REQ-001, REQ-013

### REQ-015 - Bound help requests to existing assignments
- Requirement: Require help requests to identify an exact question, relevant artifact, requested contribution, and stopping condition; allow peer answers within existing assignments and route new substantive work to the manager.
- Source: U06 - bounded help and generic-category preservation.
- Acceptance: A peer can provide an in-scope answer directly; a request needing a new assignment, additional ungranted tools, or another agent receives manager routing without an automatic launch or scope expansion.
- Acceptance: Generic participation cannot create a second solver, reviewer, senior, or implementation worker.
- Depends on: REQ-003, REQ-011

### REQ-016 - Preserve objections in synthesis
- Requirement: Provide the senior with unresolved material objections as well as every eligible current candidate, and require explicit dispositions for resolved, rejected, and remaining objections.
- Source: U06 - preserve disagreement and reject voting or hidden omission.
- Source: C02 - senior synthesis eligibility and dispositions.
- Acceptance: The synthesis cites objection and artifact versions, explains evidence for its dispositions, and retains remaining limitations; popularity, voting, concatenation, or omission of opposing commitments does not establish a coherent accepted proposal.
- Depends on: REQ-002, REQ-003, REQ-011

### REQ-017 - Check material threads before acceptance and completion
- Requirement: Require the manager to assess unresolved material threads before acceptance and completion and resolve their effect through existing decision owners and eligibility gates.
- Source: U06, U07, U14 - no silently overlooked material objection.
- Acceptance: A material objection affecting current criteria prevents an unsupported acceptance or completion until addressed or rejected with attributable evidence; harmless or obsolete posts do not create an unbounded veto.
- Acceptance: A deferred material issue remains visible with its responsible owner and effect on criteria; a thread closure alone cannot clear a formal blocker.
- Depends on: REQ-002, REQ-016

### REQ-018 - Support a small contribution vocabulary
- Requirement: Support note, question, finding, challenge, blocker, help-request, change-notice, and proposal types, retaining a general note type for informal task-relevant contributions.
- Source: U05 - small structured envelope without formal-report burden.
- Acceptance: Each listed type can be submitted and read; an honest question or speculative note is valid without mandatory proof, while a supported finding can link evidence and state its limitations.
- Depends on: REQ-001

### REQ-019 - Bind contributor identity to current assignments
- Requirement: Populate and validate project, Task, execution, generation, author assignment, and native identity from current assignment context wherever possible, rather than trusting self-asserted authority.
- Source: U05, U09, U10 - identity, generation checks, and honest actor guarantees.
- Source: C02 - real native receipts and cooperative actor checks.
- Acceptance: Accepted contributions identify an eligible actual assignment and native participant; mismatched project, actor, assignment or generation is rejected or kept explicitly historical without becoming current evidence.
- Acceptance: Identity metadata documents its verified binding and remaining cooperative limitations rather than claiming OS authentication.
- Depends on: REQ-002

### REQ-020 - Keep stable message and thread references
- Requirement: Give every contribution a stable message ID and schema version with thread ID, optional reply reference, message type, title, and body.
- Source: U05 - stable envelope, threads and compatibility.
- Acceptance: A reply resolves to its referenced authorized contribution and thread; IDs remain stable across rebuilt views; missing, malformed, incompatible, or cross-scope references receive explicit bounded errors.
- Depends on: REQ-018, REQ-019

### REQ-021 - Declare visibility and intended audience
- Requirement: Record the applicable visibility and collaboration phase, intended recipients or relevant roles, requested response, and urgency in a contribution's envelope.
- Source: U05, U08 - targeted communication without universal broadcast.
- Acceptance: The helper validates audience and phase against the current policy; a targeted post reaches only eligible recipients; an urgency label requests attention but grants no authority or automatic wakeup.
- Depends on: REQ-007, REQ-019, REQ-020

### REQ-022 - Bind discussion to exact evidence and versions
- Requirement: Allow baseline, candidate, artifact, evidence, and limitation references, and require material findings or challenges to identify their exact target versions.
- Source: U05, U10 - evidence limitations and version-specific challenges.
- Acceptance: A material challenge against candidate version 1 remains attributable to that version and is not represented as verified against version 3; supported facts, interpretation, speculation, and missing evidence are distinguishable.
- Depends on: REQ-020

### REQ-023 - Correct posts without rewriting them
- Requirement: Keep published contributions immutable and publish corrections as new contributions carrying a supersedes reference when applicable.
- Source: U05, U09 - correction references and immutable publication.
- Acceptance: A correction preserves the original bytes, identity, and hash, identifies its predecessor, and is visible as the current correction only to authorized readers; conflicting reuse of an existing ID cannot overwrite it.
- Depends on: REQ-020, REQ-022

### REQ-024 - Separate handling state from result status
- Requirement: Track availability, actual notification, explicit acknowledgement, and addressed or deferred handling independently of Task lifecycle, review, verification, and acceptance.
- Source: U07 - communication state is not work status.
- Acceptance: A displayed handling state has attributable communication evidence and cannot count as result acceptance, comprehension, implementation, or completion; notified is not inferred from persistence alone.
- Depends on: REQ-002, REQ-020

### REQ-025 - Record acknowledgements per recipient
- Requirement: Keep explicit acknowledgement separately for each recipient and distinguish reported reading from delivery, comprehension, and incorporation.
- Source: U07 - per-recipient acknowledgements and truthful receipt semantics.
- Acceptance: One recipient's acknowledgement leaves others pending; a plain read does not acknowledge; an acknowledgement states only that the recipient reported reading the referenced version, without proving understanding.
- Depends on: REQ-024

### REQ-026 - Keep discussion closure distinct from owner resolution
- Requirement: Allow an author or relevant participant to close an answered discussion while reserving material-blocker resolution and solution acceptance for the existing responsible owner.
- Source: U07 - discussion answered, candidate revision pending; canonical acceptance references.
- Acceptance: Views can represent an answered question with candidate revision still pending and a manager-accepted change with its canonical reference; closing a question does not resolve a formal blocker or accept a change.
- Depends on: REQ-017, REQ-024

### REQ-027 - Persist contributions before notifications
- Requirement: Durably publish a contribution before attempting delivery and keep retryable pending delivery records when notification fails.
- Source: U08 - saved posts, transactional-outbox principle, crash recovery.
- Acceptance: A failure or crash between publication and notification preserves the post and an inspectable or reconstructible pending delivery; reconciliation can retry without losing the contribution or pretending it was delivered.
- Depends on: REQ-019, REQ-023, REQ-024

### REQ-028 - Deliver bounded checkpoint digests
- Requirement: Notify eligible recipients using a message ID, permitted bounded summary, and evidence reference; provide routine information in bounded checkpoint digests and notify the current manager promptly about a material blocker during an authorized active session.
- Source: U08 - bounded digests, prompt manager attention, no idle-agent broadcast wakeups.
- Acceptance: A digest respects visibility and configured output bounds and surfaces remaining unread coverage; blocker delivery is attempted at the next available active-session control opportunity and retains pending status if unsuccessful.
- Acceptance: Routine posts do not automatically wake every idle agent; outside authorized sessions, pending communication waits for the next legitimate checkpoint without unattended AI execution.
- Depends on: REQ-021, REQ-027

### REQ-029 - Respect native input and resumption gates
- Requirement: Use existing native-agent controls for notification while retaining stop, reconciliation, exact input binding, and resumption gates for material changes.
- Source: U08 - native messaging is not a write-scope or input change.
- Source: C02 - installed same-ID lifecycle sequence.
- Acceptance: For a material same-ID change, the manager observes the assignment stopped or completed, queues the exact packet with send_message, commits assignment.inputs with the actual receipt, then uses followup_task; active owners are stopped and reconciled before rebind.
- Acceptance: Unchanged-input idle continuation retains its existing assignment.resume gate; delivery or acknowledgement alone cannot wake a writer, renew a revoked assignment, or change its accepted target.
- Depends on: REQ-010, REQ-027, REQ-028

### REQ-030 - Make submission and delivery retries idempotent
- Requirement: Use stable operation IDs and payload binding so retrying the same logical submission or notification is harmless without duplicate contributions, assignments, or actions.
- Source: U08, U14 - missed and duplicate delivery.
- Acceptance: A same-operation same-payload retry returns the original logical result; a conflicting payload reuse is rejected; repeated notification neither creates another assignment nor claims a second contribution.
- Depends on: REQ-023, REQ-027

### REQ-031 - Reject stale execution and generation contributions
- Requirement: Check execution and generation freshness on publishing and consuming current communication and retain superseded content only as clearly identified permitted history.
- Source: U05, U09, U14 - prevent mixing superseded or unrelated work.
- Acceptance: A delayed old-generation post or receipt cannot alter current instructions, acknowledgements, eligibility, or decisions; views and evidence selection identify the applicable generation and historical limits.
- Depends on: REQ-019, REQ-029

### REQ-032 - Use participant-owned immutable file storage
- Requirement: Start with structured immutable message and receipt files, a small Python helper, existing native messaging, and generated Markdown views in explicitly granted participant namespaces within the selected Task's evidence area.
- Source: U09, U13 - file-backed first implementation and proposed Task-local arrangement.
- Source: C02, C05 - present write scopes and Python 3.12 environment.
- Acceptance: Concurrent participants publish into separate namespaces without editing a common JSON array, Markdown document, or index; the logical board joins the permitted source records.
- Acceptance: No writer acquires a new path merely by adopting the proposed layout; baseline and assignment scopes or reviewed compatibility changes explicitly grant the required paths.
- Depends on: REQ-004, REQ-019, REQ-023

### REQ-033 - Protect file publication and reads
- Requirement: Provide atomic publication, collision rejection, path confinement, bounded file and response sizes, content hashes, and generation checks; readers ignore incomplete temporary files.
- Source: U09 - required file-handling protections.
- Acceptance: Simultaneous publication preserves complete source files; ID/path collisions, traversal, symlink escapes, oversized records, corrupt hashes, and stale generation requests fail without outside or partial state changes.
- Acceptance: An incomplete temporary file is never presented as a published post; configured bounds and any truncated coverage are explicit.
- Depends on: REQ-031, REQ-032

### REQ-034 - Keep inspection and rebuilding nonmutating
- Requirement: Keep list, read, search, validation, and inspection read-only; explicit projection rebuilding may update only generated views and must not rewrite posts, acknowledge messages, mutate Tasks, or launch work.
- Source: U09, U14 - read-only inspection and generated-view boundaries.
- Acceptance: Before/after comparison shows unchanged canonical posts, receipts, Task state, assignments, and acknowledgements after inspection; explicit rebuilding changes only its authorized projection outputs and starts no agent or owner operation.
- Depends on: REQ-005, REQ-006, REQ-025, REQ-033

### REQ-035 - Keep casual traffic outside canonical Task JSON
- Requirement: Store individual contributions and receipts as communication evidence and use bounded snapshots or selected evidence manifests at meaningful decision boundaries through existing artifact mechanisms.
- Source: U09 - avoid per-post and per-acknowledgement Task events.
- Source: C02, C04 - artifact registration and canonical size/strict field constraints.
- Acceptance: Casual posting and acknowledgement do not append canonical Task events; manager-selected snapshots bind exact source versions and hashes, and canonical decisions reference the selected evidence without copying full conversations.
- Acceptance: The design preserves the current 2,000,000-byte Task JSON cap and existing artifact/input bounds unless a separately reviewed compatible change is required; snapshots report their selection and omitted coverage.
- Depends on: REQ-002, REQ-022, REQ-024, REQ-032

### REQ-036 - Verify shared access across execution environments
- Requirement: Verify an authorized common store or explicit transport before treating participants in separate worktrees or isolated filesystems as sharing a board.
- Source: U09 - paths are not automatically shared; Git is not real-time transport.
- Acceptance: A supported topology demonstrates that eligible participants can read the same referenced source bytes through the authorized store or transport; unavailable sharing is reported as a blocker or unsupported topology.
- Acceptance: The system does not use Git commits as real-time messaging and does not create infrastructure or transport authority from a directory name.
- Depends on: REQ-032, REQ-033

### REQ-037 - Filter before content enters agent context
- Requirement: Enforce project, assignment, phase, and independence visibility before any post body, title, preview, search result, digest, notification, overview item, or linked content enters a recipient's context.
- Source: U03, U04, U10 - visibility must precede exposure.
- Acceptance: Negative tests and native evidence demonstrate that restricted conclusions cannot reach recipients through any supported reading or delivery path; an instruction to ignore already-exposed content is not isolation evidence.
- Depends on: REQ-005, REQ-006, REQ-008, REQ-012, REQ-021, REQ-028

### REQ-038 - Surface newly released unread posts
- Requirement: Track unread eligibility so a sealed contribution released in a later phase becomes unread for eligible recipients even when they previously advanced past later-visible messages.
- Source: U10 - a global read-through cursor can skip newly released posts.
- Acceptance: A recipient reads permitted later messages while an earlier post is sealed; releasing that post surfaces it at the next permitted checkpoint until explicitly handled, without duplicating existing acknowledgement or exposing it early.
- Depends on: REQ-013, REQ-025, REQ-037

### REQ-039 - Reassess material version changes through existing gates
- Requirement: Assess source, baseline, candidate, dependency, or conflict changes against their exact affected versions and rerun the existing gates whose inputs materially changed.
- Source: U04, U10, U14 - scoped freshness and eligibility revalidation.
- Source: C02 - changed bytes invalidate dependent review, synthesis, acceptance, and targets.
- Acceptance: A material candidate change makes affected current review and acceptance evidence ineligible and halts an obsolete implementation target until revalidated; prior records remain historical.
- Acceptance: Unaffected evidence is preserved when its inputs remain valid; an ordinary speculative post does not itself revise a baseline or force an entire Task restart.
- Depends on: REQ-002, REQ-012, REQ-022, REQ-029, REQ-035

### REQ-040 - Report actual isolation guarantees
- Requirement: Distinguish cooperative actor/visibility checks from OS authentication, filesystem confinement, and verified runtime context isolation; report unavailable guarantees and contamination honestly.
- Source: U09, U10 - enforceable isolation and cooperative checks.
- Source: C02 - present protocol limitations.
- Acceptance: The supported runtime declares and verifies its actual enforcement boundaries, including inherited context; a run lacking required isolation evidence or exposed to sibling conclusions is not labeled independently solved.
- Acceptance: A shared filesystem that remains readable outside the helper is documented as a limitation unless separate confinement actually closes that route.
- Depends on: REQ-008, REQ-012, REQ-036, REQ-037

### REQ-041 - Treat messages as data without inherited authority
- Requirement: Treat post text, quoted instructions, and claims of approval as data to verify against their governing records, without granting new tools, write scope, scientific status, publication rights, or execution authority.
- Source: U02, U10 - discussion is not authority.
- Acceptance: A post claiming Director approval or containing a command cannot trigger protected actions unless the existing current authority and decision records independently support them; referenced sources retain their provenance and claim limits.
- Depends on: REQ-002, REQ-019, REQ-039

### REQ-042 - Keep stored discussion concise and private
- Requirement: Exclude credentials, unnecessary personal data, hidden reasoning, and full transcripts; store concise explanations, actionable questions, evidence references, and limitations.
- Source: U09, U10 - privacy and evidence limits.
- Source: C01, C02 - current storage and reporting rules.
- Acceptance: Contracts, helper validation where feasible, and reviewed pilot artifacts avoid prohibited content; unknown secret patterns are not falsely described as comprehensively detected, and a rejected post cannot leak through diagnostics or previews.
- Depends on: REQ-020, REQ-033, REQ-041

### REQ-043 - Promote selected verified lessons through memory owners
- Requirement: At completion, let the current authorized owner examine useful resolved threads with other verified evidence and propose reusable memory findings through the existing publication route.
- Source: U02, U11 - selected knowledge promotion without automatic post capture.
- Source: C03 - frozen memory packet and separate publication authority.
- Acceptance: A useful resolved thread can support an evidence-linked proposal, but a post never publishes memory automatically; the owner retains verification, privacy, grant, and source-version checks.
- Acceptance: Current-run posts, drafts, reviews, and proposals cannot enter initial solvers' frozen context through memory; no duplicate memory store or changed capture preference is introduced.
- Depends on: REQ-002, REQ-008, REQ-022, REQ-042

### REQ-044 - Route maintenance proposals to the existing Curator
- Requirement: Let relevant recurring issues produce linked maintenance proposals for the existing Curator process, preserving source thread, affected artifacts, suggested correction, and expected validation.
- Source: U03, U11 - observation and owner routing without a competing queue.
- Source: C06 - bounded session maintenance and existing canonical owners.
- Acceptance: The Director and authorized Curator can inspect relevant activity and route a proposal through existing owners; observation creates no new Task queue, duplicate execution, competing active-Task writer, or unattended AI.
- Acceptance: Unavailable owners leave proposals pending with truthful status; the proposal itself does not modify project policy or protected content.
- Depends on: REQ-006, REQ-017, REQ-022, REQ-041

### REQ-045 - Demonstrate research claim discipline
- Requirement: Include a representative research scenario in which independent candidates are followed by an assumption challenge, evidence-linked reply, permitted revision, applicable review, senior disposition, and manager decision.
- Source: U12 - hypothetical Aether-Flow example of a missing clock-rule assumption.
- Acceptance: The scenario preserves initial candidate versions and the objection, distinguishes a proposed assumption from an assigned source fact or established derivation, and shows that only the authorized workflow changes the accepted conclusion.
- Acceptance: Illustrative perspectives are not claimed as installed physics roles; no Aether-Flow deployment, ontology change, or validated physics result is inferred from the example.
- Depends on: REQ-008, REQ-011, REQ-012, REQ-016, REQ-017, REQ-041

### REQ-046 - Package a separate collaboration capability
- Requirement: Provide a separate reusable collaboration skill and helper for posting, scoped reads, replies, explicit acknowledgements, delivery bookkeeping, bounded digests, generated views, and validation.
- Source: U13 - a collaborate-like skill instead of overloading human-facing communication.
- Acceptance: The skill exposes the stated communication operations and their scope/visibility contracts while the communication skill retains its writing role; it neither selects scientific conclusions, assigns new work, nor accepts results.
- Depends on: REQ-018, REQ-020, REQ-025, REQ-028, REQ-034, REQ-041

### REQ-047 - Define the contract before runtime adoption
- Requirement: Define a versioned collaboration contract covering message types, author scope, visibility phases, thread handling, delivery, retention, and links to canonical decisions before adopting the helper or revised working habits.
- Source: U13 - explicit contract and staged integration.
- Acceptance: The contract resolves supported behavior, correction and receipt handling, bounded output, retention of referenced evidence and preserved candidate history, and phase transitions without assigning present user-intent discovery to a later agent.
- Acceptance: Any retention operation has an explicit authorized boundary and cannot silently erase current unresolved material threads or evidence needed for retained decisions.
- Depends on: REQ-023, REQ-026, REQ-027, REQ-035, REQ-046

### REQ-048 - Preserve strict schema compatibility
- Requirement: Use existing artifact and input events where sufficient; any necessary Task schema, event, or write-scope extension needs explicit versioning, compatibility, validation, and migration design.
- Source: U09, U13 - strict unsupported-field rejection and no casual event additions.
- Source: C02, C04 - current schemas and validation.
- Acceptance: The proposed integration identifies every changed contract and proves supported historical records retain their meaning; unknown fields and versions still fail closed.
- Acceptance: No inspected or historical record is silently upgraded, and a new namespace or phase field is not inserted into canonical Task data without its reviewed version contract.
- Depends on: REQ-002, REQ-032, REQ-035, REQ-047

### REQ-049 - Distribute reusable sources through the Template pipeline
- Requirement: Author reusable skill, role, working-contract, and related integration changes in their appropriate depot sources and distribute only through the established checked Template pipeline.
- Source: U13 - reusable changes belong in depot sources.
- Source: C01, C07 - source ownership, mapping, and preservation rules.
- Acceptance: An exact source/destination manifest and pipeline check demonstrate complete mapped assets in the neutral Template without direct editing of mapped copies or overwriting customized unrelated content; no task posts, native identities, populated records, or runtime state enter starter assets.
- Depends on: REQ-046, REQ-047, REQ-048

### REQ-050 - Require explicit project-local adoption
- Requirement: Require exact source, destination, file set, overwrite boundary, preservation rules, and destination checks for active-root or product-project adoption; registration and source equality confer no adoption authority.
- Source: U00, U13 - framework/research repository distinction and explicit adoption.
- Source: C01, C07 - depot and product ownership boundaries.
- Acceptance: An adoption preview identifies the selected project and changes; all unselected roots and product files remain unchanged, including Aether-Flow unless separately selected.
- Acceptance: Template distribution or a successful disposable pilot does not claim root activation, future-project runtime behavior, service installation, Git publication, or external deployment.
- Depends on: REQ-036, REQ-049

### REQ-051 - Prove concurrent posting preserves every contribution
- Requirement: Exercise concurrent publication against the shared file-backed board without shared-file overwrites.
- Source: U14 - concurrent posting acceptance case.
- Acceptance: Independent writers publish simultaneously; every successful operation has exactly one complete, hash-valid immutable contribution, and a colliding ID or path leaves the original intact.
- Depends on: REQ-030, REQ-032, REQ-033

### REQ-052 - Prove retry and crash recovery
- Requirement: Exercise duplicate submission and notification and a crash after publication before delivery.
- Source: U14 - duplicate contribution, duplicate action, and crash acceptance cases.
- Acceptance: Repeated identical operations preserve one logical contribution and no duplicate assignment/action; conflicting operation reuse is rejected.
- Acceptance: After the crash, the published source survives and pending notification is reconciled with truthful receipts without republishing or losing the post.
- Depends on: REQ-027, REQ-030, REQ-033

### REQ-053 - Prove stale generations cannot become current
- Requirement: Exercise late messages and receipts from a prior execution or generation.
- Source: U14 - old execution generation acceptance case.
- Acceptance: Late content and delivery records fail current eligibility checks and cannot affect current inputs, acknowledgement, acceptance, or overview status; permitted historical inspection retains its explicit version label.
- Depends on: REQ-031, REQ-034

### REQ-054 - Prove solver and reviewer isolation across all routes
- Requirement: Exercise initial-solver and first-review isolation against bodies, titles, previews, search, digests, notifications, overview, memory retrieval, linked artifacts, and inherited context.
- Source: U04, U10, U14 - independence acceptance cases.
- Acceptance: Restricted conclusions and verdicts remain absent from recipient inputs until their exact release gate; native evidence verifies supported runtime context independence rather than relying solely on synthetic receipts.
- Acceptance: A released previously sealed message becomes unread even after other messages were consumed; unavailable enforcement is reported and the run is not certified independent.
- Depends on: REQ-008, REQ-012, REQ-037, REQ-038, REQ-040, REQ-043

### REQ-055 - Prove material changes invalidate affected evidence
- Requirement: Exercise a material change to a candidate or assigned source after a current review or acceptance.
- Source: U14 - material candidate change acceptance case.
- Acceptance: Affected review, synthesis, acceptance and implementation targets become ineligible until the applicable owner records current revalidation; unrelated unchanged evidence and prior version history remain intact.
- Depends on: REQ-022, REQ-029, REQ-039

### REQ-056 - Prove idle delivery and interruption recovery
- Requirement: Exercise an idle recipient and an interruption/recovery cycle using actual native lifecycle evidence.
- Source: U08, U13, U14 - idle recipient, controlled pilot, interruption and recovery.
- Acceptance: Persistence, delivery, reported reading, comprehension, and resumed work remain separately evidenced; routine notification does not wake idle agents; pending messages survive interruption.
- Acceptance: A material resumption follows observed stopping, exact packet delivery, assignment.inputs commit, and followup_task; no duplicate launch or assignment is inferred from a missing or uncertain notification.
- Depends on: REQ-025, REQ-027, REQ-029, REQ-030, REQ-031

### REQ-057 - Prove inspection cannot start or acknowledge work
- Requirement: Exercise list, read, search, validation, and explicit generated-view rebuild boundaries.
- Source: U14 - read-only inspection acceptance case.
- Acceptance: Inspection preserves source posts, receipts, acknowledgement state, canonical Task bytes, and assignments and starts no work; an explicit rebuild changes only authorized derived views and retains source hashes.
- Depends on: REQ-034

### REQ-058 - Prove unauthorized scope is denied
- Requirement: Exercise cross-project, cross-assignment, traversal, symlink, forged-identity, unauthorized read/write, and protected-generation access attempts.
- Source: U09, U10, U14 - confinement and unauthorized access acceptance cases.
- Acceptance: Each attempt is denied without outside state changes or restricted content in errors, titles, previews, notifications, or search; tests identify any unsupported topology or cooperative-only guarantee.
- Depends on: REQ-019, REQ-031, REQ-033, REQ-037, REQ-040, REQ-042

### REQ-059 - Prove objections affect final gates
- Requirement: Exercise an unresolved material objection and an informally answered or closed thread that still affects current criteria.
- Source: U07, U14 - unresolved material objection acceptance case.
- Acceptance: Acceptance and completion cannot silently overlook the objection; the senior and manager dispositions cite its exact target and evidence; discussion closure or multiple agreeing replies cannot count as verification.
- Depends on: REQ-016, REQ-017, REQ-026, REQ-039

### REQ-060 - Run staged controlled native pilots
- Requirement: Demonstrate task-local behavior in a simple generic Task and a multi-solver Task after contract, helper, and working-habit integration; add project aggregation after task-local behavior is demonstrated and before broader adoption.
- Source: U13, U14 - controlled simple and multi-solver pilots before broader adoption.
- Acceptance: Authorized controlled pilots record actual native identities, settings, source versions, phase transitions, direct exchanges, current decisions, interruption recovery, and integrated output; required assigned-review behavior is separately exercised where applicable.
- Acceptance: A truthful release record separates deterministic helper tests, synthetic fixtures, native observations, and end-to-end evidence; an unexercised pilot, reviewer route, aggregation, or consumer adoption remains incomplete rather than reported passed.
- Depends on: REQ-003, REQ-006, REQ-012, REQ-013, REQ-014, REQ-045, REQ-047, REQ-048, REQ-050, REQ-051, REQ-052, REQ-053, REQ-054, REQ-055, REQ-056, REQ-057, REQ-058, REQ-059

### REQ-061 - Compare collaboration quality and cost
- Requirement: Compare the existing and billboard-enabled workflows on comparable tasks with the same model settings and comparable resource budgets, measuring useful outcomes and communication cost.
- Source: U14 - quality comparison and message count is not success.
- Acceptance: The comparison records task/criteria comparability, effective settings, budgets, earlier contradiction detection, late dependency discovery, reuse of relevant findings, final criteria satisfaction, recovery context, and communication resource cost.
- Acceptance: Observed differences and limitations are reported without inventing performance thresholds or treating message count as a success metric; unsupported improvement claims are excluded.
- Depends on: REQ-060

### REQ-062 - Route ontology corrections through their existing owner
- Requirement: Allow selected discussion to support proposed ontology corrections while keeping ontology publication and scientific claim status under the existing authorized project owners.
- Source: U02, U10, U11 - discussion can propose knowledge changes but cannot publish them.
- Source: C09 - ontology proposals, exact review, and separate publication grant.
- Acceptance: A correction proposal retains its source thread, exact evidence and limitations and uses the existing ontology proposal/review route; posting or accepting a discussion answer cannot publish an ontology record.
- Acceptance: Publication requires the current separate ontology authority and exact source/target checks; neither a memory grant nor a Task/billboard receipt establishes a scientific claim or permission to change it.
- Depends on: REQ-002, REQ-022, REQ-041, REQ-043

## Decisions

- The supplied recommendation is the requirements input, not authorization to implement it. This document preserves proposed future behavior and exclusions without claiming the capability exists or that tests or pilots have run.
- 'Collaborate' is the user's suggested capability name. The final package name, command spelling, envelope optionality, exact file layout, phase representation, bounds, digest/cursor algorithms, delivery transport, and retention mechanics are implementation choices constrained by the observable requirements. The proposed execution/generation/assignment storage tree is illustrative; existing assignment write scopes must be respected or explicitly extended through a reviewed compatible contract.
- The initial storage requirement is structured immutable files, a small Python helper, existing native messaging, and generated Markdown. It creates no new database or broker dependency. The root uses its selected Python 3.12 environment; consumer compatibility and runtime support remain explicit verified constraints rather than inferred from the developer's machine.
- Existing canonical event/artifact/input mechanisms are preferred. Any demonstrated insufficiency must lead to an explicit versioned compatibility design; strict schema validation and historical meaning cannot be weakened to admit new fields informally.
- Operational availability means visibility to eligible recipients under the current phase policy. It does not release sealed candidate findings early. Prompt material-blocker notification is attempted during an authorized active session; unavailable delivery remains pending. No numerical latency, benchmark improvement, or resource target is invented.
- The required staging is contract, helper and tests, working habits, controlled task-local native pilot, then project aggregation and broader adoption. This preserves the user's prerequisites without creating an implementation plan or starting those stages.
- Pilot write locations must be disposable controlled roots or separately selected authorized installations. Active-root and product adoption remain distinct future operations requiring exact manifests; the Aether-Flow example grants no installation or scientific authority.
- Full communication receipts are not Task decisions. Meaningful owner decisions cite bounded exact evidence snapshots. Formal freshness and invalidation are assessed by current owners against changed inputs, not by message popularity, thread closure, or a speculative post alone.
- The comparison must report comparable criteria, identical effective model settings, resource budgets, actual outcome measurements, and limitations. Message count and unsupported improvement claims cannot establish success.

The ten U14 acceptance cases map to: concurrent posting (REQ-051); duplicate submission/notification (REQ-052); crash after publication (REQ-052); old generation (REQ-053); initial-solver isolation (REQ-054); material candidate change (REQ-055); idle recipient (REQ-056); read-only inspection (REQ-057); unauthorized scope (REQ-058); unresolved material objection (REQ-059). Native pilot and quality/cost comparison are REQ-060 and REQ-061. Earlier behavioral requirements define each expected result; the scenario requirements require evidence of those results.

## Open questions

None.

## Not yet specified

None.

## Assumptions

None.
