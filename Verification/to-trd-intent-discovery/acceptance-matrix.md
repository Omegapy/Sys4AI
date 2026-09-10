# Source acceptance matrix

All 22 requirements and 73 acceptance criteria below are exact copies from the untouched source TRD, checked against canonical plan revision 2. Each A-number denotes source order, not a new schema. Written guidance and scenario definitions do not prove actual model behavior. No criterion has an authorized waiver. Actual-host gaps prevent full implementation completion.

## REQ-001 — Make understanding intent the entry-point responsibility

Outcome: The to-trd entry point and agent metadata must describe intent discovery as the primary responsibility and TRD writing as the synthesis of understood intent, within the existing project role.

Responsible files: [SKILL.md](../../SKILLS-depo/to-trd/SKILL.md), [agents/openai.yaml](../../SKILLS-depo/to-trd/agents/openai.yaml). Plan work: TASK-005, TASK-010, TASK-013, TASK-014, TASK-022.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-001.A1 | SKILL.md and agents/openai.yaml consistently describe inspecting the request, resolving material ambiguity, and deriving requirements before document approval. | Verified in written guidance; live behavior unexercised | [Semantic review](semantic-review.md) |
| REQ-001.A2 | The package retains the name to-trd, Task Requirement Document terminology, TRP as an alias, and explicit invocation without introducing a new agent identity or mandatory subagent. | Verified in written guidance; live behavior unexercised | [Semantic review](semantic-review.md) |

## REQ-002 — Use an explicit readiness check before ordinary synthesis

Outcome: Ordinary synthesis must proceed only when applicable material requirement areas are understood from the request, inspected facts, actual user answers, or explicit delegation.

Responsible files: [SKILL.md](../../SKILLS-depo/to-trd/SKILL.md), [references/wayfinding.md](../../SKILLS-depo/to-trd/references/wayfinding.md). Plan work: TASK-003, TASK-005, TASK-006, TASK-013, TASK-015, TASK-016, TASK-022.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-002.A1 | The check considers outcome, beneficiary and use, current state and change, scope and exclusions, inputs and outputs and behavior, constraints and authority, observable success, and consequential edge cases. | Verified in written guidance; live behavior unexercised | [Semantic review](semantic-review.md) |
| REQ-002.A2 | A gap is material when alternative answers change the required outcome, scope, interface, constraints, acceptance, or action authority; a bounded implementation choice does not become a requirement gap. | Verified in written guidance; live behavior unexercised | [Semantic review](semantic-review.md) |
| REQ-002.A3 | A fully specified request takes the fast path without a compulsory questionnaire, numeric readiness score, or repeated confirmation; the ability to invent a plausible document does not establish readiness. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |

## REQ-003 — Separate discoverable facts from user-owned decisions

Outcome: Discovery must inspect relevant available sources for factual gaps and use the conversation for unresolved desired behavior, priorities, tradeoffs, and authority.

Responsible files: [references/wayfinding.md](../../SKILLS-depo/to-trd/references/wayfinding.md), [tests/interaction-scenarios.md](../../SKILLS-depo/to-trd/tests/interaction-scenarios.md). Plan work: TASK-006, TASK-013, TASK-015, TASK-022.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-003.A1 | A fixture establishing the current format is inspected without asking the user to restate it; that fact is not treated as approval to preserve the format in a redesign. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-003.A2 | Source facts, user intent, design proposals, explicit delegation, assumptions, and contradictions remain distinguishable; unavailable evidence is reported without invented research or a required new plugin. | Verified in written guidance; live behavior unexercised | [Semantic review](semantic-review.md) |

## REQ-004 — Pause after asking for a material user decision

Outcome: When a material intake decision belongs to the user, the agent must ask one focused question with its consequence and wait for the actual answer before dependent synthesis or writing.

Responsible files: [SKILL.md](../../SKILLS-depo/to-trd/SKILL.md), [references/wayfinding.md](../../SKILLS-depo/to-trd/references/wayfinding.md). Plan work: TASK-003, TASK-004, TASK-005, TASK-006, TASK-007, TASK-013, TASK-015, TASK-019, TASK-022.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-004.A1 | An ambiguous first capture produces a live clarification question and ends the response without a TRD write or a presented completed baseline in that turn. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-004.A2 | Silence, elapsed time, a preselected recommendation, a tool result, and an unrelated reply do not settle the decision or authorize a write. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-004.A3 | Discovery resumes from the actual answer or an explicit user instruction changing the requested mode, subject to higher-priority host instructions. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |

## REQ-005 — Sequence clarification by consequence and dependency

Outcome: The interview must adapt one material question at a time to settled prerequisites and the latest answer, preserving only the decisions that the user actually resolves.

Responsible files: [references/wayfinding.md](../../SKILLS-depo/to-trd/references/wayfinding.md), [tests/interaction-scenarios.md](../../SKILLS-depo/to-trd/tests/interaction-scenarios.md). Plan work: TASK-003, TASK-005, TASK-006, TASK-007, TASK-013, TASK-015, TASK-022.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-005.A1 | The agent surveys the major requirement areas, addresses outcome and scope first when unresolved, and selects a useful answerable question without imposing a fixed interview length. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-005.A2 | A dependent question is asked only after its prerequisite is settled and only if it remains relevant. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-005.A3 | A partial answer or ambiguous agreement resolves only its clear portion; the remaining material distinction receives a focused follow-up without repeating settled questions. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |

## REQ-006 — Propagate answers and changed intent into the requirements

Outcome: Each material clarification must update all affected intent, scope, constraints, decisions, requirements, and acceptance criteria before further discovery or synthesis.

Responsible files: [references/wayfinding.md](../../SKILLS-depo/to-trd/references/wayfinding.md), [tests/test_trd.py](../../SKILLS-depo/to-trd/tests/test_trd.py). Plan work: TASK-003, TASK-005, TASK-006, TASK-007, TASK-009, TASK-013, TASK-015, TASK-019, TASK-022.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-006.A1 | A clarification specifying one project and no sharing appears in scope and the relevant requirement and acceptance, with contradictory cross-project behavior removed. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-006.A2 | A changed answer invalidates dependent assumptions and obsolete interview branches; recording the answer only in Decisions while leaving affected behavior vague does not satisfy this requirement. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-006.A3 | Revisions preserve IDs where requirement meaning remains and explicitly account for removed requirements without reusing their IDs for unrelated outcomes. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |

## REQ-007 — Keep understanding review separate from validation and approval

Outcome: The workflow must distinguish the agent's review of understood intent, mechanical validation of the document, and the user's approval of the exact document revision.

Responsible files: [SKILL.md](../../SKILLS-depo/to-trd/SKILL.md), [references/trd-contract.md](../../SKILLS-depo/to-trd/references/trd-contract.md). Plan work: TASK-003, TASK-005, TASK-006, TASK-007, TASK-008, TASK-013, TASK-016, TASK-018, TASK-022.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-007.A1 | After substantial clarification, the agent briefly summarizes consequential outcome, scope, choices, exclusions, and success conditions, seeking confirmation only where interpretation still needs it. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-007.A2 | Agreement with an intent summary does not approve an unseen TRD, and helper validation does not establish semantic understanding or consent. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-007.A3 | Fully specified or already confirmed intent does not trigger a redundant understanding-approval exchange. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |

## REQ-008 — Respect each operation's document-write boundary

Outcome: Capture, resume, content revision, read-only inspection, and lifecycle operations must retain their existing activation and write boundaries.

Responsible files: [ACTIONS.md](../../SKILLS-depo/to-trd/ACTIONS.md), [tests/test_trd.py](../../SKILLS-depo/to-trd/tests/test_trd.py). Plan work: TASK-003, TASK-004, TASK-005, TASK-006, TASK-008, TASK-010, TASK-013, TASK-015, TASK-016, TASK-018, TASK-022.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-008.A1 | New capture can write at the authorized synthesis boundary; a resumed draft remains read-only until explicit save, and discovery does not persist after every question or answer. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-008.A2 | List, show, and validate do not start an interview, rewrite documents, migrate records, repair the index, or change lifecycle state. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-008.A3 | An exact existing-document selector is resolved and read before revision; supplied documents and agent-written notes cannot grant additional execution authority. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |

## REQ-009 — Honor an explicit incomplete-draft request

Outcome: An explicit request to save the current draft must produce an honest draft containing known intent, safely supportable requirements, and declarative material gaps.

Responsible files: [references/wayfinding.md](../../SKILLS-depo/to-trd/references/wayfinding.md), [references/interaction-examples.md](../../SKILLS-depo/to-trd/references/interaction-examples.md). Plan work: TASK-003, TASK-005, TASK-006, TASK-007, TASK-008, TASK-013, TASK-016, TASK-022.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-009.A1 | The agent can stop discovery and save immediately when requested, including zero requirements when none can safely be stated. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-009.A2 | Not yet specified describes unresolved in-scope matters declaratively; Open questions remains None., and the document contains no pasted interview transcript or delegated intake prompts. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-009.A3 | The record remains draft, contains no fabricated answers or accepted assumptions, and is not presented as a settled baseline. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |

## REQ-010 — Handle a prohibition on follow-up questions honestly

Outcome: When the user or a higher-priority host instruction forbids follow-up questions, missing material intent must remain visible without violating that constraint.

Responsible files: [SKILL.md](../../SKILLS-depo/to-trd/SKILL.md), [references/wayfinding.md](../../SKILLS-depo/to-trd/references/wayfinding.md). Plan work: TASK-003, TASK-005, TASK-006, TASK-013, TASK-016, TASK-022.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-010.A1 | The agent asks no prohibited question, invents no answer, and reports the resulting limit on understanding. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-010.A2 | An incomplete artifact is saved only if the current request authorizes that artifact; a follow-up restriction alone does not establish a complete requirements baseline. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |

## REQ-011 — Produce bounded requirements with traceable sources

Outcome: Every generated requirement must express one bounded outcome, identify its supporting source or explicitly authorized design basis, and define observable acceptance with genuine dependencies.

Responsible files: [references/wayfinding.md](../../SKILLS-depo/to-trd/references/wayfinding.md), [assets/example-input.json](../../SKILLS-depo/to-trd/assets/example-input.json). Plan work: TASK-003, TASK-006, TASK-007, TASK-008, TASK-009, TASK-013, TASK-015, TASK-017, TASK-022.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-011.A1 | Source labels resolve to meaningful statements or locators that support the requirement; synthetic examples are not attributed to the real user. | Verified in written guidance; live behavior unexercised | [Semantic review](semantic-review.md) |
| REQ-011.A2 | Both review directions are covered: every material outcome, clarification, constraint, and exclusion has a document location, and every normative requirement has justified support. | Verified in written guidance; live behavior unexercised | [Semantic review](semantic-review.md) |
| REQ-011.A3 | Negative requirements, stable IDs, and acceptance remain explicit; no unsupported technology, numeric target, approval, or assumption is invented merely to fill the template. | Verified in written guidance; live behavior unexercised | [Semantic review](semantic-review.md) |

## REQ-012 — Recognize unresolved intake decisions by meaning

Outcome: The pre-save agent review must prevent unresolved decisions needed to understand the current task from being disguised as implementation requirements, acceptance criteria, or decisions.

Responsible files: [references/wayfinding.md](../../SKILLS-depo/to-trd/references/wayfinding.md), [tests/interaction-scenarios.md](../../SKILLS-depo/to-trd/tests/interaction-scenarios.md). Plan work: TASK-003, TASK-006, TASK-008, TASK-013, TASK-017, TASK-022.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-012.A1 | Statements assigning the next agent to determine the intended selection, confirm the desired output, or decide which user workflow was intended are recognized as unresolved intake work. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-012.A2 | Rewording a question as a declaration does not make ordinary synthesis ready. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-012.A3 | Legitimate deliverable behavior that asks its future user a question, requested research questions, quoted labels, and URL query strings are not rejected merely for containing question language or punctuation. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |

## REQ-013 — Align the package guidance and interaction examples

Outcome: The source package must provide one consistent discovery procedure across its entry file, references, metadata, template, example, and maintenance documentation.

Responsible files: [INDEX.md](../../SKILLS-depo/to-trd/INDEX.md), [tests/test_trd.py](../../SKILLS-depo/to-trd/tests/test_trd.py). Plan work: TASK-005, TASK-006, TASK-007, TASK-008, TASK-009, TASK-010, TASK-011, TASK-012, TASK-013, TASK-019, TASK-021, TASK-022.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-013.A1 | SKILL.md contains the critical readiness, pause, and answer-propagation rules; references/wayfinding.md supplies the detailed procedure without a contradictory competing flow. | Verified in written guidance; live behavior unexercised | [Semantic review](semantic-review.md) |
| REQ-013.A2 | New references/interaction-examples.md covers the clear fast path, ambiguous request with a real pause, answer-driven follow-up, and requested incomplete draft, and is linked from the discovery reference and package index. | Verified in written guidance; live behavior unexercised | [Semantic review](semantic-review.md) |
| REQ-013.A3 | The template preserves its contract without becoming an interview checklist; the valid synthetic example adds a clarification source that changes an actual requirement and acceptance, with affected fixtures aligned. | Package/helper checks passed; no conversational claim | [Source checks](source-mechanical.md); [Template checks](template-verification.md) |
| REQ-013.A4 | README.md, INDEX.md, AGENTS.md, ACTIONS.md, and references/trd-contract.md accurately describe the same operations, write boundaries, verification limits, and source-maintenance paths. | Verified in written guidance; live behavior unexercised | [Semantic review](semantic-review.md) |

## REQ-014 — Preserve schema, storage, and historical compatibility

Outcome: The discovery repair must preserve schema 2, the current helper API and operation IDs, project-local storage, and the existing compatibility and safe-write contracts.

Responsible files: [references/trd-contract.md](../../SKILLS-depo/to-trd/references/trd-contract.md), [scripts/trd.py](../../SKILLS-depo/to-trd/scripts/trd.py). Plan work: TASK-001, TASK-002, TASK-008, TASK-010, TASK-011, TASK-012, TASK-013, TASK-018, TASK-021, TASK-022, TASK-024.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-014.A1 | The schema headings, requirement fields, frontmatter, draft/trd_done/retired states, canonical Markdown records, generated index, immutable identities, and hash-checked helper writes remain compatible. | Package/helper checks passed; no conversational claim | [Source checks](source-mechanical.md); [Template checks](template-verification.md) |
| REQ-014.A2 | New and content-updated TRDs keep Open questions as None.; existing read and explicit-migration behavior for historical questions and evidence is preserved. | Package/helper checks passed; no conversational claim | [Source checks](source-mechanical.md); [Template checks](template-verification.md) |
| REQ-014.A3 | No new schema field, status, CLI subcommand, persisted interview database, or second canonical store is introduced merely to record discovery. | Verified within this repair boundary | [Preservation audit](preservation-audit.md); [baseline](baseline.json) |
| REQ-014.A4 | Existing TRDs are not silently rewritten, renamed, migrated, retired, or deleted as a side effect of package maintenance. | Verified within this repair boundary | [Preservation audit](preservation-audit.md); [baseline](baseline.json) |

## REQ-015 — Preserve exact-revision approval and current diagnostics

Outcome: Document completion must retain the current 2.1.0 approval workflow and truthful structural completion diagnostics.

Responsible files: [SKILL.md](../../SKILLS-depo/to-trd/SKILL.md), [tests/test_trd.py](../../SKILLS-depo/to-trd/tests/test_trd.py). Plan work: TASK-001, TASK-002, TASK-003, TASK-005, TASK-008, TASK-010, TASK-011, TASK-012, TASK-013, TASK-016, TASK-018, TASK-021, TASK-022, TASK-024.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-015.A1 | New records remain draft until the user explicitly approves the presented unchanged revision; the agent uses the current hash, reason, and confirmation, then reads back trd_done. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-015.A2 | Approval requires at least one valid requirement, empty unresolved sections, and no unconfirmed assumptions; approval-bearing content changes return an approved document to draft. | Package/helper checks passed; no conversational claim | [Source checks](source-mechanical.md); [Template checks](template-verification.md) |
| REQ-015.A3 | completion.content_ready, blockers, and next_action remain derived from the actual gate and are described as structural diagnostics, without semantic-understanding claims or keyword exemptions. | Package/helper checks passed; no conversational claim | [Source checks](source-mechanical.md); [Template checks](template-verification.md) |
| REQ-015.A4 | A normal settled capture presents the document and asks for approval only when missing; a draft-only request or read-only inquiry does not initiate that exchange. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-015.A5 | Document approval grants no planning, implementation, migration, installation, Git, publication, deployment, or external-action authority. | Verified within this repair boundary | [Preservation audit](preservation-audit.md); [baseline](baseline.json) |

## REQ-016 — Verify the source helper and changed contracts

Outcome: Mechanical verification of a reusable package change must exercise the source copy being changed and retain existing helper regressions.

Responsible files: [README.md](../../SKILLS-depo/to-trd/README.md), [tests/test_trd.py](../../SKILLS-depo/to-trd/tests/test_trd.py). Plan work: TASK-002, TASK-009, TASK-010, TASK-011, TASK-012, TASK-013, TASK-021, TASK-022, TASK-023.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-016.A1 | Maintenance commands target SKILLS-depo/to-trd/tests and SKILLS-depo/to-trd/scripts/trd.py using the repository's existing Python environment. | Package/helper checks passed; no conversational claim | [Source checks](source-mechanical.md); [Template checks](template-verification.md) |
| REQ-016.A2 | Changed contracts, example fixtures, or optional diagnostics receive proportionate focused checks; unchanged installed-copy tests do not stand in for verification of changed source files. | Package/helper checks passed; no conversational claim | [Source checks](source-mechanical.md); [Template checks](template-verification.md) |
| REQ-016.A3 | Storage and syntax results are reported accurately, with generated caches kept out of deliverables; prepared document-body tests are not called live interviews. | Package/helper checks passed; no conversational claim | [Source checks](source-mechanical.md); [Template checks](template-verification.md) |

## REQ-017 — Define the complete conversational acceptance set

Outcome: New tests/interaction-scenarios.md must define the report's C01–C14 cases with synthetic inputs, expected visible behavior, and prohibited writes where applicable.

Responsible files: [tests/interaction-scenarios.md](../../SKILLS-depo/to-trd/tests/interaction-scenarios.md), [references/interaction-examples.md](../../SKILLS-depo/to-trd/references/interaction-examples.md). Plan work: TASK-003, TASK-004, TASK-011, TASK-012, TASK-013, TASK-014, TASK-015, TASK-016, TASK-017, TASK-018, TASK-019, TASK-022.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-017.A1 | C01 requires an ambiguous first-turn question and real pause with no write; C02 requires the actual answer to change isolation requirements and acceptance. | Scenario defined and statically reviewed; not executed | [Semantic review](semantic-review.md); [host results](host-results.md) |
| REQ-017.A2 | C03 covers prerequisite-dependent questioning; C04 covers partial answers and ambiguous agreement without invented consent. | Scenario defined and statically reviewed; not executed | [Semantic review](semantic-review.md); [host results](host-results.md) |
| REQ-017.A3 | C05 covers inspection of a source-resolvable fact; C06 covers a fully specified fast path that writes only within authority and remains draft until approval. | Scenario defined and statically reviewed; not executed | [Semantic review](semantic-review.md); [host results](host-results.md) |
| REQ-017.A4 | C07 covers an explicitly requested incomplete draft, including zero requirements; C08 covers missing intent when questions are prohibited. | Scenario defined and statically reviewed; not executed | [Semantic review](semantic-review.md); [host results](host-results.md) |
| REQ-017.A5 | C09 covers changed intent, affected acceptance, stable IDs, and accounted removals; C10 detects unresolved intake work hidden in declarative wording. | Scenario defined and statically reviewed; not executed | [Semantic review](semantic-review.md); [host results](host-results.md) |
| REQ-017.A6 | C11 preserves legitimate question content in the intended deliverable; C12 separates intent agreement from exact-document approval and implementation authority. | Scenario defined and statically reviewed; not executed | [Semantic review](semantic-review.md); [host results](host-results.md) |
| REQ-017.A7 | C13 verifies read-only operations; C14 verifies the deliberately selected candidate package and its resources in a fresh target-host session. | Scenario defined and statically reviewed; not executed | [Semantic review](semantic-review.md); [host results](host-results.md) |

## REQ-018 — Verify the discovery behavior in actual conversations

Outcome: Behavioral verification must exercise the candidate skill with sequences of user messages and distinguish executed interaction evidence from static checks.

Responsible files: [tests/interaction-scenarios.md](../../SKILLS-depo/to-trd/tests/interaction-scenarios.md). Plan work: TASK-003, TASK-004, TASK-013, TASK-014, TASK-015, TASK-016, TASK-017, TASK-018, TASK-019, TASK-021, TASK-022, TASK-023.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-018.A1 | At minimum, the actual target host exercises an ambiguous first turn, answer-driven revision, the clear fast path, an explicit incomplete draft, and exact-document approval. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-018.A2 | The ambiguous case is repeated with differently worded requests, and a critical ambiguous case is exercised in a fresh session loading the deliberately selected candidate entry and resources. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-018.A3 | Tests use disposable project roots and synthetic facts; evidence records the loaded skill path, version and hashes, relevant host instructions, available model configuration, minimal visible exchanges, write calls, and final artifact. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-018.A4 | Manual host exercises or an available conversation evaluator are acceptable, with the actual mode and unexecuted cases identified; synthetic test answers are never treated as real user approval. | Incomplete: actual-host observation required | [Host results](host-results.md); [helper checks](source-mechanical.md) are supporting evidence only |
| REQ-018.A5 | Evidence excludes hidden reasoning, credentials, unrelated conversations, and unnecessary raw logs. | Verified within this repair boundary | [Preservation audit](preservation-audit.md); [baseline](baseline.json) |

## REQ-019 — Keep reusable maintenance within the source-to-Template boundary

Outcome: The reusable repair must be authored in SKILLS-depo/to-trd/ and follow the existing checked mapping into the registered Sys4AI Template.

Responsible files: [README.md](../../SKILLS-depo/to-trd/README.md), [AGENTS.md](../../SKILLS-depo/to-trd/AGENTS.md). Plan work: TASK-001, TASK-010, TASK-013, TASK-020, TASK-021, TASK-022, TASK-023, TASK-024.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-019.A1 | Before future implementation, the current package, applicable guidance, mappings, and destination state are reinspected instead of relying on the report's reviewed snapshot. | Verified within this repair boundary | [Preservation audit](preservation-audit.md); [baseline](baseline.json) |
| REQ-019.A2 | Mapped Template updates use the existing template-update workflow and are checked against the source; no direct edit to a mapped Template copy or automatic product-project propagation is inferred. | Checked mapping and byte comparison passed | [Template update](template-update.md); [Template checks](template-verification.md) |
| REQ-019.A3 | Verification reports the actual check result and any conflict or recovery state; watcher installation, running status, and host readiness are not inferred from a mapping or matching version. | Checked mapping and byte comparison passed | [Template update](template-update.md); [Template checks](template-verification.md) |

## REQ-020 — Preserve project-local installations and unrelated state

Outcome: Active root and ordinary product-project installations must remain project-local, with any later adoption limited to separately authorized exact destinations and overwrite boundaries.

Responsible files: [README.md](../../SKILLS-depo/to-trd/README.md), [AGENTS.md](../../SKILLS-depo/to-trd/AGENTS.md). Plan work: TASK-001, TASK-004, TASK-010, TASK-013, TASK-014, TASK-019, TASK-020, TASK-021, TASK-022, TASK-023, TASK-024.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-020.A1 | An installed-copy refresh, if separately authorized, inspects source and destination guidance and content, preserves local changes, defines the exact file set, and verifies the resulting package. | No installed-copy refresh performed; conditional path unexercised | [Preservation audit](preservation-audit.md) |
| REQ-020.A2 | No bulk child-project refresh, global install, root-governance change to force invocation, or unrelated Task, memory, registry, or TRD mutation accompanies the repair. | Verified within this repair boundary | [Preservation audit](preservation-audit.md); [baseline](baseline.json) |
| REQ-020.A3 | Disposable evaluation of the candidate and the mapped Template path are distinguished from adoption into the active root or product projects; source verification alone is not reported as installed-host verification. | Verified within this repair boundary | [Preservation audit](preservation-audit.md); [baseline](baseline.json) |

## REQ-021 — Keep the adaptation self-contained and preserve provenance

Outcome: The revised package must remain a lightweight self-contained adaptation with accurate attribution and versioning.

Responsible files: [ATTRIBUTION.md](../../SKILLS-depo/to-trd/ATTRIBUTION.md), [licenses/wayfinder-MIT.txt](../../SKILLS-depo/to-trd/licenses/wayfinder-MIT.txt), [SKILL.md](../../SKILLS-depo/to-trd/SKILL.md). Plan work: TASK-002, TASK-005, TASK-010, TASK-011, TASK-012, TASK-013, TASK-021, TASK-022, TASK-023, TASK-024.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-021.A1 | The package retains Matt Pocock's Wayfinder attribution and MIT notice, adds provenance only for newly adapted material actually inspected, and does not present unverified upstream claims as current facts. | Verified within this repair boundary | [Preservation audit](preservation-audit.md); [baseline](baseline.json) |
| REQ-021.A2 | The repair does not require an upstream Wayfinder or companion-skill installation, tickets, research branches, mandatory agents, or one-ticket-per-session machinery. | Verified within this repair boundary | [Preservation audit](preservation-audit.md); [baseline](baseline.json) |
| REQ-021.A3 | The package version increment follows repository practice while document schema 2 remains unchanged. | Verified in written guidance; live behavior unexercised | [Semantic review](semantic-review.md) |

## REQ-022 — Report the actual verification and adoption level

Outcome: The final report for a separately authorized implementation must identify the delivered changes and the highest verification level actually supported by evidence.

Responsible files: [README.md](../../SKILLS-depo/to-trd/README.md), [AGENTS.md](../../SKILLS-depo/to-trd/AGENTS.md). Plan work: TASK-001, TASK-004, TASK-010, TASK-013, TASK-019, TASK-022, TASK-023, TASK-024.

| Criterion | Exact source acceptance | Evidence status | Current evidence |
| --- | --- | --- | --- |
| REQ-022.A1 | The report names changed files, the source revision, helper checks and their results, conversational cases actually executed, fresh-host evidence, and separately authorized installed-copy changes. | Report delivered with explicit incomplete evidence | [Implementation report](implementation-report.md) |
| REQ-022.A2 | It distinguishes static checks, helper tests, live interaction behavior, host integration, and unexercised behavior, including any remaining failure or limitation. | Report delivered with explicit incomplete evidence | [Implementation report](implementation-report.md) |
| REQ-022.A3 | It does not claim that the original behavioral problem is fixed solely because instructions were rewritten, versions match, or Python tests pass. | Report delivered with explicit incomplete evidence | [Implementation report](implementation-report.md) |
