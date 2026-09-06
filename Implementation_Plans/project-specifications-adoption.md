# Project specifications adoption

Source: the user's 2026-09-05 request to adapt `SPECS-depo/SPECS.md` for the
depot root and each project under `Projects/`, with a reusable template and no
duplicated specifications in README or agent guidance.

## Requirements and acceptance

| ID | Required outcome | Work and evidence |
| --- | --- | --- |
| SPEC-01 | Each existing project root has an adapted, uppercase `SPECS.md`. | Inspect the depot, Template, Electronics and Memory Service; verify four files against current local sources. |
| SPEC-02 | Specifications match each project's environment, dependencies and exclusions. | Read project instructions, manifests, package metadata and `.gitignore`; distinguish requirements, installed tooling and declaration gaps. |
| SPEC-03 | Template specifications remain reusable. | Preserve generic product context and explicit specialization instructions; do not initialize the template. |
| SPEC-04 | README and AGENTS link to specifications without duplicating them. | Move technical specification sections, retain operational commands and authority contracts, and verify required-read/navigation links. |
| SPEC-05 | New projects retain the template's specification and valid links. | Update the initializer's starter allowlist and generated README in its source and active copies; exercise the existing asset-collection path in disposable fixtures. |
| SPEC-06 | Existing project-owned state is preserved. | Compare baseline hashes; preserve ignores, environments, manifests, registries, product code, historical records and unrelated edits. |

## Execution and ownership

The Director owns integration, the depot-root files, initializer compatibility,
affected contract checks and final acceptance. Independent project documentation
is delegated to the validated `project-sub-agent` role:

- `/root/template_specs`: only Template `SPECS.md`, `README.md`, `AGENTS.md`.
- `/root/electronics_specs`: only Electronics `SPECS.md`, `README.md`, `AGENTS.md`.
- `/root/memory_service_specs`: only Memory Service `SPECS.md`, `README.md`, `AGENTS.md`.

Role sources are `sub-agent-roles/project-sub-agent/AGENTS.md` and `ROLE.md`.
The role supports bounded documentation and verification; no specialized
hardware work or provider operation is required. Each child inherits the exact
Director model and reasoning effort. No nested delegation is authorized.

The initializer asset changes are necessary because its existing allowlist
omits `SPECS.md` and its generated README would otherwise repeat the relocated
requirements. Its implementation remains unchanged. Update relevant existing
contract checks for the new document locations, and append reviewed hashes to
the initializer adoption record without rewriting earlier revision entries.

The existing role-package documentation assertion also follows the new spec
location. Apply that test-only change to the reusable role-management package
and its four inspected project-local copies so future copies and current
projects use the same documentation contract. No role helper behavior changes.

## Verification and stopping condition

Reopen all changed documents. Check local links, duplicate specification
sections, whitespace, source/active initializer parity, starter collection and
the affected existing contract suites. Record actual results in
`Verification/project-specifications-adoption_2026-09-05.md`.

The baseline contains 1,147 source/document hashes and the original root README,
AGENTS and ignore files for each project. It is stored in
`/private/tmp/sys4ai-project-specs-rxi7d748/` for this change review.

Stop when all six requirements have direct evidence. Documentation adoption
does not install dependencies, initialize memory, register new memory sources,
alter Task/TRD lifecycle state, run hardware, or create/publish repositories.

## Completion

All six requirements passed the checks recorded in the verification report.
The Director reopened each project diff and specification, verified the copied
starter in both direct and nested destination layouts, and accepted the result.
Existing unrelated Electronics documentation/test-input issues are recorded
separately in that report; they do not prevent specification adoption.
