---
name: init-new-project
description: Create or prepare a selected Sys4AI project using Template governance assets, preserved project content and factual registration.
metadata:
  version: 6.0.0
---

# Initialize a Sys4AI project

Use the [helper](scripts/init_new_project.py) for authorized project creation or
preparation. An explanation or assessment request remains read-only. Both routes
adopt governance starter assets, specialize identity, register the project and
verify the resulting local files. Obtain the real destination, stable project
ID, name and purpose from the user's request or existing project identity.
Never place credentials in those inputs.

## Scope and ownership

The helper discovers its owning depot from its installation under
`SKILLS-depo/init-new-project/` or a registered project's
`.agents/skills/init-new-project/`. Destinations remain beneath that depot's
`Projects/` folder. The registered Template cannot be a destination. Overlapping
registrations, traversal, symbolic links, aliased files and identity collisions
are rejected. There is no caller-controlled depot or Template override.

Every starter input comes from the registered `Sys4AI-Template-Project`: its
schema-2 `.template/baseline-assets.json`, README renderer, soul, complete skill
and role packages, and selected reference assets. The seven required skills are
`agent-task`, `communication`, `init-new-project`, `manage-subagent-roles`, `task`,
`to-implementation-plan` and `to-trd`. The `project-sub-agent` and `task-manager` pairs and a validated `Roles/INDEX.md`
are required for new projects. The initializer reads the Template and does not refresh it.

The three required licensing starters are `LICENSE`, `LICENSE-CODE`, and
`LICENSE-DOCS`. They retain the Template's Apache 2.0 / CC BY 4.0 split and
default attribution. For a selected existing project, inspect its licensing
before setup. The helper recognizes root `LICENSE`/`LICENCE` (including
`LICENSES/`), `COPYING`, `COPYRIGHT`, and `UNLICENSE`, case-insensitively and
with dot, underscore, or hyphen suffixes. It preserves that entire system and
skips absent companions. If licensing exists only in other prose or metadata,
resolve that project-specific adoption before invoking setup. Do not infer
relicensing authority from registration or the presence of a template.

Existing project identity, README, specifications, skills, roles, Tasks,
configuration, data and registry metadata remain project-owned. Missing starter
assets may be added. Existing packages remain intact as a whole, including
custom resources and missing resources; do not combine editions automatically.
An existing `Roles/` collection is preserved as a whole. A missing role index
is generated from its actual pairs, including invalid-role diagnostics; an
existing index that differs requires explicit reindex before setup. An existing
lowercase `roles/` collection requires the role helper's explicit case-rename
preview/apply and compatible helper adoption before new setup. Directory-entry
inspection rejects wrong casing and dual collections even on case-insensitive
volumes. Setup never performs that migration or creates a second collection. A legacy
`sub-agent-roles/` tree or incompatible existing role helper requires a reviewed
transition before adopting new starters. A completed copy-first transition may
retain its legacy directory. Preparation verifies its strict receipt, retained
source hashes, current active pairs and index, and compatible role helper before
accepting that evidence. Both directories existing alone is insufficient. A pristine Template README in a manual copy is specialized. A customized README
is preserved. Existing `project.json` bytes and additional fields are preserved;
its project ID and relative destination must agree with the request, and its
existing display name and purpose take precedence.

## Run setup

Use the depot's Python interpreter and explicit values:

```text
python scripts/init_new_project.py create|prepare-existing
  --destination ABSOLUTE_PROJECT_PATH
  --project-id STABLE_PROJECT_ID
  --project-name PROJECT_NAME
  --purpose PRODUCT_CONTEXT
```

Use `create` for an absent or empty destination, or to resume its recorded setup.
Use `prepare-existing` for a selected existing directory or a manual Template
copy. The helper requires Python 3.12 and uses its standard library. Git is used
only to observe an existing child repository. Dependency installation, model
preparation, service startup, Git creation, publication and deployment are
separately scoped work.

Version 3 deliberately removes the former `--principal-id`, `--dataset-id` and
`--artifact-receipt` arguments and their Python API parameters. They are rejected,
not ignored. The starter policy has no optional root guide or runtime bundle.

## Completion and receipts

The durable receipt is `control_records/project-setup.json`, schema version 1,
with setup contract `governance-starter-v4`. Version 4 requires the license trio
and records the original `preserved_licenses` inventory (empty when adopting
the trio) separately from `current_licenses` observed during verification.
Entries for absent companions use `skipped-existing-license`; every Template
license source remains in the receipt. Original markers must remain present;
ordinary content edits are observed without rewriting original hashes. During
interrupted asset adoption, licensing must still match the reviewed inventory.

Earlier `governance-starter-v3` receipts retain their original license-free
starter requirement and `Roles/` layout. Earlier `governance-starter-v1`
and `governance-starter-v2` contracts retain their original `sub-agent-roles/`
and lowercase `roles/` source and adoption evidence. Reruns never convert their
contract. A version-2 rerun after an authorized rename requires the completed
`.sys4ai/roles-case-rename.json` proof and a compatible current helper. It records
that proof separately and observes hashes under the actual `Roles/` paths in
`current_files`; original source, destination and adoption hashes remain intact.
Its stages are `assets`,
`registration` and `verification`. A completed result contains all three stages
and passed checks for project identity, project files and factual registration.
The receipt retains source hashes and the original adoption hashes separately
from the hashes observed during the latest verification. A preserved or skipped
resource is identified explicitly; copied Template bytes are not claimed for it.
The receipt must account for every source destination in both directions:
adopted files match `owned_files`, preserved files match `preserved_files`, and
both maps match the source adoption hashes. Only explicitly skipped resources
inside an existing package, nonempty Task tree, or a v4 preserved licensing
system may be absent from both maps.
Standalone starters and the required source inventory cannot be omitted.

Reinspect the result and affected files before reporting completion. State the
actual checks performed and any unresolved conflict. The receipt establishes
local starter setup, not readiness of future project software. Existing setup
records at other paths and project-specific configuration or data are preserved.
Prior receipts from this helper are retained under
`control_records/project-setup-history/` by content hash.

## Reruns and recovery

An equivalent rerun verifies current files and registration. It preserves normal
project edits and existing registry metadata, adds no duplicate registration and
does not adopt a later Template edition. An incomplete asset stage retains its
exact source inventory and before/after hashes. A retry accepts already-published
bytes, publishes remaining unchanged targets and rejects conflicting edits or
changed Template input. Once asset adoption has completed, remaining stages can
resume without the original Template edition.

Finish any interrupted lowercase asset stage against its recorded Template
edition before the case rename. A partial operation whose asset stage already
completed can resume registration and verification after the proven rename.
Missing, pending, wrong-root or changed proof refuses a rerun before mutation;
the receipt is never relabeled to bypass recovery.

A partial result identifies the failed stage and the saved receipt. Resolve the
reported cause and repeat the same request. Preserve working project files;
never delete a receipt to evade an identity or ownership conflict. Per-project
and registry advisory locks reject live competing writers and release after
process exit. The shared Template lock prevents adoption during an updater
transaction and is released after asset adoption.

See [README.md](README.md) for verification commands and boundaries.
