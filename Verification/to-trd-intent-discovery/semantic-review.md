# Discovery and coverage review

This is the implementing Director's static review of the final candidate. It is
not an independent interview or actual-host test. The [acceptance matrix](acceptance-matrix.md)
copies all 73 source criteria exactly and ties all 22 outcomes to files, plan
work, and classified evidence. No acceptance criterion was removed or waived.

## Control-flow review

| Cases | Written control reviewed | Result of static review |
| --- | --- | --- |
| C01, C14 | Entry section 3 and wayfinding readiness/incomplete-request sections require a material question, response end, actual answer, and no dependent synthesis/write. Variants have no future answer in the first prompt. | Covered in guidance and scenarios; actual pauses and fresh loading unexercised. |
| C02 | Answer propagation precedes further discovery and changes scope, isolation outcome, sources and acceptance. | Covered; helper fixture verifies prepared content updates, not model incorporation. |
| C03 | Consequence and settled prerequisites choose the next question; isolation removes the sharing branch. | Covered; no fixed interview length or questionnaire. Actual branch selection unexercised. |
| C04 | CSV resolves format only; ambiguous Yes resolves no alternative. | Covered; default recommendation, elapsed time, unrelated replies and tool results cannot create consent. |
| C05 | Inspect the readable fixture for current JSON, ask the user about desired format. | Covered; existing state cannot become approval of a redesign. Actual read-versus-ask behavior unexercised. |
| C06 | Applicable material areas determine fast-path readiness; draft-only output gets no approval prompt. | Covered; complete fixture has selection, fields, locality, overwrite, empty input and success conditions. |
| C07 | Explicit draft-now instruction interrupts discovery; known intent and declarative gaps are saved, including zero requirements. | Covered; the existing zero-requirement contract is retained. No intake prompt is stored as downstream work. |
| C08 | No-follow-up instruction wins; save authority is considered separately and approval questions also remain prohibited. | Covered; discussion/no-write, explicit incomplete draft and real host-instruction variants are distinguished. |
| C09 | Resume stays read-only until save; changed answers invalidate assumptions and questions. Retain continuing IDs and account for removed IDs. | Covered; named removal in the fixture cannot be recycled into a new unrelated outcome. |
| C10 | Review whether a declaration hides missing current-user intent, regardless of its heading or punctuation. | Covered; no helper heuristic added. Actual semantic discrimination unexercised. |
| C11 | Future-user dialog, research, quoted label and URL-query requirements retain their intended purpose under existing field rules. | Covered; no general ban on question language or punctuation. |
| C12 | Agent intent review, helper validation and approval of a presented unchanged document are separate. Content changes invalidate approval. | Covered; existing helper gate regressions pass. Real approval exchange unexercised. |
| C13 | Exact selector is read first; list/show/validate do not enter discovery or repair state. | Covered; helper read-only regressions pass, agent decisions unexercised. |

The new interaction examples illustrate a complete prompt, an actual turn end,
a selection answer that changes the requirement, a consequential overwrite
follow-up, and interrupted/forbidden questioning. They clearly label synthetic
turns and never attest to current-user approval.

## Bidirectional source and artifact review

The ten body headings and all requirement fields remain unchanged. New/current
Open questions remains `None.`; zero requirements, historical questions,
migration, exact hashes, state transitions and no-op behavior retain their
existing helper implementation. The source helper was not edited. Completion
diagnostics are structural, not claims of semantic readiness or user consent.

The example defines U03 as a synthetic clarification. Its filtered selection,
all-fields choice, overwrite refusal and empty-selection behavior reach actual
requirements and acceptance. Its two IDs and genuine dependency remain. In the
prepared update fixture U04 supersedes selection, updates scope and acceptance,
preserves REQ-002, and leaves no contradictory excluded-record acceptance. Every
replacement asserts an actual unique match. This verifies the stored fixture,
not that a model asked for or understood the answer.

All source edits map to approved plan work:

| Changed resource | Plan work | Purpose |
| --- | --- | --- |
| SKILL.md, agents/openai.yaml | TASK-005, TASK-010 | Discovery first, readiness, wait, answer propagation and version 2.2.0. |
| references/wayfinding.md | TASK-006, TASK-007 | Adaptive procedure, materiality, source/decision distinction, semantic review and save boundaries. |
| references/interaction-examples.md | TASK-007 | Four required contrasting synthetic interactions, plus the no-questions branch. |
| references/trd-contract.md, assets/trd-body-template.md | TASK-008 | Explain the discovery boundary while retaining artifact grammar. |
| assets/example-input.json | TASK-009 | Synthetic clarification changes the outcome and acceptance. |
| tests/test_trd.py | TASK-009, TASK-011 | Update dependent fixtures, resource/link checks and meaningful stored-answer assertions. |
| README.md, INDEX.md, AGENTS.md, ACTIONS.md | TASK-010 | Consistent operation/version/maintenance documentation and resource navigation. |
| tests/interaction-scenarios.md | TASK-003 | All C01–C14 inputs, separate turns, expected observations, write limits and source-criterion labels. |

No source file falls outside that manifest. The three protected package files
retain their baseline bytes. The mapping performs the Template copy; no direct
Template edit or active-root/product adoption occurs. The legacy Python suite
and live preservation audit provide compatibility evidence; they cannot stand
in for the still-required conversations.

## Remaining evidence

The matrix has 31 criteria explicitly requiring missing actual-host observations,
plus seven scenario-definition criteria whose definitions are complete but whose
cases remain unexecuted. Twelve criteria are reviewed at written-guidance level,
eight have package/helper evidence, nine have preservation evidence, two have
Template evidence, one conditional installed-copy refresh is not applicable to
this execution, and three have reporting evidence. These categories are evidence
types, not an aggregate completion score.

The external bundled YAML skill validator could not start because PyYAML is
absent; the package's own structural checks pass. No new dependency, runner,
agent, upstream source, schema, command, state or discovery database was added.
The [host protocol](host-protocol.md) and exact baseline/candidate copies are
ready, but the behavioral result remains incomplete.
