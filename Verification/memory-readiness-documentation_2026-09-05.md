# Memory readiness documentation update

User request: ensure humans and AI agents in new and existing projects know
when semantic memory is not ready and the Cognee backend is inactive or
unverified, and ask whether to activate it. Keep the generic template
uninitialized. This update documents readiness and handoff behavior; it does not
enable models or change runtime/configuration behavior.

## Requirements and implementation plan

| Requirement | Observable acceptance | Planned change |
| --- | --- | --- |
| DOC-01 | Installation, verified exact/keyword memory, semantic setting and verified Cognee/model operation have distinct meanings. | Add explicit readiness notices and evidence checks to project and installation docs. |
| DOC-02 | Humans and incoming agents see the notice after setup and when first using existing project memory. | Route from root/template/product AGENTS and READMEs; include the notice in the generated project README and portable packaged consumer control guide. |
| DOC-03 | Disabled/unverified semantic memory prompts a clear activation-or-defer question; existing yes/later/decline is honored. | Require the handoff in source/active initializer instructions and all relevant setup guides. |
| DOC-04 | Existing projects report actual state; true flags and old receipts never imply readiness. | Document evidence-based status and the current configuration-migration gap; no invented activation command or receipt editing. |
| DOC-05 | The template remains an uninitialized reusable starter, with working direct/nested links and clear instructions for the real copy. | Update template documentation only; retain the same allowlist and initializer behavior. |
| DOC-06 | Existing configurations, runtime code, permissions, receipts, model state, Git setup and completed ledgers are preserved. | Use documentation/resource updates, reviewed source-to-active adoption, scoped checks and before/after comparisons. |

Execution order: inspect current state and routes; update independently owned
product and root/template documentation; review and adopt the two changed
initializer documentation files; validate generated consumer documentation and
links; record evidence and limitations. No managed Task, TRD or prior completed
plan is reopened for this ordinary documentation request.

The Director owns scope, root/template/initializer docs and final verification.
A bounded project-sub-agent updates only the Memory Service documentation and
its packaged control-guide resource. Both use the current filesystem-backed
role catalog and inherited model/reasoning. No reusable AGENTS/SOUL/ROLE source
or unrelated existing project receives an inferred bulk update.

## Verification

All six documentation requirements passed review and the relevant checks on
2026-09-05. The delivered change covers 20 documentation/adoption files, plus
this verification record.

| Requirement | Verified result |
| --- | --- |
| DOC-01 | Root, template, product and portable consumer guides distinguish installation, exact retrieval, semantic configuration and verified provider/model operation. The metadata check explicitly does not certify retrieval. |
| DOC-02 | Root/template/product AGENTS and README entry points link to the readiness instructions. Actual direct and nested project-document rendering preserved the notice and resolved links. The built wheel includes the portable consumer guide. |
| DOC-03 | Guides and source/active initializer instructions contain the explicit activation-or-defer question, preserve earlier yes/later/decline decisions, and prevent repeated prompts or treating silence as consent. |
| DOC-04 | The read-only inspection ran against the existing root, uninitialized product and a temporary prepared consumer. Documentation distinguishes false, true-but-unverified and missing/stale evidence. The existing-consumer configuration-migration limitation is explicit. |
| DOC-05 | Template documentation renders correctly for direct and nested destinations. The template still has no memory configuration or derived memory directory; its SOUL and ROLE are unchanged. |
| DOC-06 | Before/after hashes match for all nine protected configuration, permissions, initialization receipt, lockfile, runtime and governance files. Initializer code is unchanged; all nine source/active package files agree. Existing adoption history is retained with the two reviewed documentation revisions appended. |

The root's read-only inspection reported project `sys4ai-depot`, dataset
`sys4ai-depot-memory`, `semantic_enabled = false`, a matching initialization
receipt and an existing exact index. The receipt reports
`exact_index_initialized = true`, `provider_initialized = false` and
`models_activated = false`. That metadata check does not itself test retrieval.
The product checkout has `semantic_enabled = true` but no initialization receipt
or derived index: its live semantic/backend readiness remains unverified.

| Check | Result |
| --- | --- |
| Root tests | 28 passed |
| Template tests | 7 passed |
| Source initializer tests | 16 passed; 1 opt-in installed end-to-end case skipped |
| Active initializer tests | 16 passed; 1 opt-in installed end-to-end case skipped |
| Consumer bootstrap/resource tests, including the new wheel | 30 passed |
| Direct and nested generated documentation | Notices, handoff instructions and local links passed in both destinations |
| Active skill metadata | Valid |
| Changed documentation links and Git whitespace check | Passed |

The source and active initializer documentation is version 1.0.1. The new
immutable consumer artifact incorporates the portable guide; its
[artifact receipt](../Projects/Sys4AI-Memory-Service/dist/consumer/0.1.0/30ad0ccf05ea82ef87ab0ce59a1ca2271bc0ec16225b93fb0c272c779b8f5821/artifact.json)
records wheel SHA-256
`d043c02232e7d2d59b257ea61ac9c2af421d0fd9db3747f122ec0a4c64d9c474`.
Comparison with the previous consumer wheel found only the packaged control
README, package README metadata and wheel RECORD changed; no Python module
changed. The wheel's import/preparation check passed without installing it into
a live consumer. Root-owned consumer documentation was adopted separately.

Highest verification: reviewed documentation plus rendered and packaged
consumer handoffs and focused regression checks. No live conversational
activation, model download/startup, semantic retrieval, configuration migration,
new live project installation, Git setup or publication was performed. The
generic template and product checkout remain uninitialized. Existing immutable
wheels and unrelated project-owned copies are not automatically updated.
The documented existing-consumer migration capability gap remains unresolved;
this documentation update does not implement that capability.

Before snapshots, test output, rendered documents and machine-readable evidence
are retained under `/private/tmp/sys4ai-memory-readiness-docs/`, especially
`baseline.json`, `final-evidence.json`, `rendered-evidence.json` and the test logs.
The bounded documentation review also recorded
`/private/tmp/sys4ai-memory-readiness-docs-evidence.json`.
