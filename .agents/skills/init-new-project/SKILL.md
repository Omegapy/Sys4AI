---
name: init-new-project
description: Create or prepare a selected Sys4AI project using Template governance assets, preserved project content and factual registration.
metadata:
  version: 13.0.0
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
and role packages, and selected reference assets. The eleven required skills are
`agent-task`, `communication`, `init-new-project`, `manage-subagent-roles`, `task`,
`memory`, `ontology`, `to-implementation-plan`, `to-trd`, `what-did-you-learn` and
`curate`. The `project-sub-agent` and `task-manager` pairs and a validated `Roles/INDEX.md`
are required for new projects. The initializer reads the Template and does not refresh it.

New Curator installations enable bounded project-session maintenance. Setup
assessment is static and does not prove a live session. The reviewed
package inventory binds the current supported owner interfaces and retained
callers. Installing or assessing the package does not establish native runtime
operation; assessment reports runtime as not exercised.

The memory starters are `memory.yaml`, `MEMORY/README.md`, the complete memory
skill, and `reference-assets/MEMORY-depo/` contract assets. The Template config
has no project ID or name, publisher authorization, learned records or enabled
backend. New installation enables automatic capture and binds the local Director
to the destination's current SOUL/AGENTS/ROLE hashes and bounded memory paths.
Setup specializes `project.id` and `project.name`, retains project root `.`,
and uses the local `reference-assets/MEMORY-depo` contract path.
The memory helper validates the constrained JSON-compatible YAML configuration
without contacting or provisioning a backend. Nonempty Template memory and
missing required memory starter, skill or contract sources reject setup.

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

Existing customized `memory.yaml` bytes remain untouched, including a config in an older
format. Existing `MEMORY/`, `reference-assets/MEMORY-depo/`, and memory skill
collections remain intact as whole packages; setup does not add their missing
resources. A pristine `memory.yaml` in a manual Template copy is specialized during first
preparation, enabling capture and binding its own project authority. The receipt reports preservation instead of claiming that such
project-owned configuration is operational. Changing it is separate scoped
project work. Original complete memory inventories are retained for recovery;
completed reruns observe current edits without replacing those original hashes.

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

## Learning setup and selected adoption

New setup and first preparation require the complete local learning skill and
`reference-assets/LEARNING-depo/` contract inventory. Existing packages are
preserved whole and assessed with exact missing/incompatible-resource diagnostics.
For a first memory binding only, a missing stable completion link may be appended
to `AGENTS.md` before its destination-local authority hash is computed. Preserve
already-bound governance and configuration; report unavailable shared capability
when its route is incompatible.

An earlier completed setup receives learning only through an explicitly selected
`prepare-existing --adopt-module what-did-you-learn` request with the same exact
identity/destination arguments. Optional `--refresh-dependency memory` selects
whole memory skill and contract packages only when their full current inventory
matches completed receipt-owned evidence. Preserve custom/incomplete dependencies,
configuration, capture off and memory history. Missing empty capability may be
installed with new local provenance; do not rewrite the original setup contract.

Use `assess-learning --destination ABSOLUTE_PROJECT_PATH` for read-only current
capability. It separates manual/shared interfaces, actual capture choice,
publication binding/scope and optional backend status. Publication always needs
a current exact operation grant and owner checks. Backend status is never a
successful runtime check. Unknown resolver/configuration inspector bytes are
preserved without execution instead of being trusted for a read-only claim.

Module operations are nested in the existing receipt's `module_adoptions` with
frozen source/target hashes and archived earlier receipts. Finish a partial base
setup first. Resume a partial module with its exact module/dependency selection;
changed inputs or conflicting edits prevent replay. Ordinary reruns acquire no
new edition; equivalent completed module requests preserve later project edits
and verify current capability without an implicit package refresh.

## Ontology setup and selected adoption

Edition v8 adds the ontology skill, local contracts, locked core module, neutral
`ontology.yaml` and empty `ONTOLOGY/` project and binding graphs. Create and first
preparation specialize the saved project ID, name, purpose, unique namespace,
import locks and destination-local Director binding. The binding covers only
`ONTOLOGY/modules/project` and `ONTOLOGY/bindings`; exact operation grants remain
required for publication. Setup neither installs nor starts a runtime or service.

Use `assess-ontology --destination ABSOLUTE_PROJECT_PATH` for a read-only static
assessment of configuration, complete import hashes and current local authority.
It executes no copied project Python. `structural_readiness: available` and
`runtime: not-exercised` are separate facts; use the installed ontology `health`
command for semantic validation and source freshness. Copied files alone never
establish runtime readiness or publication authority.

An earlier completed receipt acquires ontology only through the exact selected
`prepare-existing --adopt-module ontology` request. Ordinary reruns retain their
base edition and locked versions. `prepare-existing --refresh-module ontology`
selects a new reviewed Template inventory for a previously receipt-owned ontology
installation; it may be combined with `--adopt-module ontology`. It does not
select a memory dependency refresh. Repeating the same source request verifies
current capability, while a changed Template source inventory creates a separate
hash-bound operation in `module_adoptions` and archives prior receipt bytes.

Treat `ontology.yaml`, `ONTOLOGY/`, the ontology skill and its contract package as
one installation. A customized, incomplete or incompatible existing installation
is preserved as a whole, with exact diagnostics and no partial merge. A complete
pristine manual Template copy may specialize its neutral config. Refresh requires
the complete file and directory inventory to equal prior receipt-owned evidence;
missing files, extra files and custom edits block replacement of the entire
installation. Existing ontology authority is retained on refresh. Existing
memory choices, learning, governance, Tasks, roles, licenses and project records
remain outside this operation. A partial ontology operation resumes only its
same module/refresh selection, frozen Template hashes and expected target bytes.

## Advanced ontology v9 and selected capability upgrades

New and first-prepared projects receive `ontology-advanced.yaml`, complete
advanced ontology contracts and interfaces, browser assets, pinned dependency
manifests, the eight guarded action families and a reusable Template updater.
All five advanced profiles start disabled. The companion gets its destination
project ID and a separately scoped destination-local publication binding.
No environment, dependency, model, backend process, service or guard bootstrap
is provisioned or enabled. Static capability installation, profile enablement,
current operation authorization, backend certification and observed runtime
behavior are reported separately in `ontology_advanced`.

The initializer's trusted static inventory requires the complete current
ontology, memory and initializer packages, including shipped tests, the
acceptance runner, local contracts and pinned dependency/model specifications.
The inventory is bound to the executing initializer's reviewed digest. Unknown
target Python is parsed for syntax without executing it. Only the known pure memory
configuration validators, learning resolver and role-index inspector may execute during assessment;
unknown customized inspectors are preserved and reported as unavailable.
Role inspection accepts only the reviewed current helper or its exact known
v1/v2 root-name variants; an ordinary rerun never grants custom helper execution.

Use `assess-ontology-advanced --destination ABSOLUTE_PROJECT_PATH` to inspect
capability and exact existing extension locks without executing project Python.
An installed capability with `runtime: not-exercised` is not a ready backend.
Existing configured profiles and certification may need separately selected
setup or recertification after code changes.

For a completed earlier setup, select
`prepare-existing --adopt-module ontology-advanced` with the exact existing
identity arguments. V1-v8 base editions and their original source/adoption
records remain unchanged. This route updates only complete verified
receipt-owned capability packages: ontology, memory, Task, TRD, plan, role and
initializer skill code, ontology reference contracts, and the selected updater
helper. It preserves `ontology.yaml`, existing `ontology-advanced.yaml`,
authored project/binding/extension graphs, locked core imports, proposals,
publication history, memory records/preferences, licensing and governance.
It never uses whole `ONTOLOGY/` equality as a reason to replace authored data.

A missing baseline ontology can be installed as an explicitly recorded neutral
prerequisite inside the same `module_adoptions` operation. Partial, customized,
missing receipt-owned or unowned incompatible packages are preserved and
refused before writing. Exact known source-equal packages may be retained
without overwriting them. An already enabled destination guard configuration
requires its exact selected adapter repair before a capability upgrade; setup
does not silently change guard bindings or disable enforcement.

Repeated selected adoption verifies the current result when the Template
inventory is unchanged. A newly selected Template capability inventory creates
a new exact operation while preserving the original base receipt history.
Partial operations resume only their original source inventory and recognized
pre/post bytes. Changed authored data, configuration, source packages or unknown
target edits stop replay and retain both the pending receipt and project work.
The existing setup receipt and guarded transaction entry points own this flow;
there is no second setup ledger.

## Default collaboration activation

Create and first preparation install and enable the complete collaboration
capability automatically. An ordinary selected `prepare-existing` also adopts a
missing capability for a previously completed setup. No adoption flag is required.
This additive `collaborate` operation uses the existing receipt's `module_adoptions`;
it preserves the original base edition, source hashes, archived receipts and
project identity. A supported current Task owner and the marked Task/Agent Task
collaboration instructions are required for enabled readiness.

An existing source-equal complete package is retained. Customized, incomplete or
unsupported packages and owner interfaces remain untouched and block readiness.
Missing instruction sections may be appended only to unchanged receipt-owned
Task guidance. Unknown project Python never executes during this assessment.
`assess-collaboration --destination ABSOLUTE_PROJECT_PATH` reports current static
installation, enabled readiness and exact diagnostics. Runtime is not exercised.

The manager still registers each Task policy and exact assignment grants. Setup
creates no board, Task, native binding, background service or idle-agent wakeup.
The automatic operation resumes through the same setup request after interruption;
its frozen source/target hashes reject changed sources or conflicting edits.
Reruns preserve base provenance and complete module identity, without refreshing
installed packages or replacing later project edits.

## Completion and receipts

The durable receipt is `control_records/project-setup.json`, schema version 1,
with setup contract `governance-starter-v11`. Edition v11 enables session maintenance
on installation; v10 preserves its inactive Curator defaults. Edition v9 adds neutral advanced capability; edition v8 adds ontology; edition v7 adds learning.
Memory remains supported for v5-v11 and capture for v6-v11. Edition v6 defaults automatic
capture on and binds the destination's own Director for reviewed memory writes.
The `memory_capture` result reports the actual current setting and readiness.
Edition v5 added memory starters and
records `specialized` identity/configuration assets separately from `adopted`
copies and `preserved-project-owned` files. `preserved_memory` records the
original complete config and collections; `current_memory` records the latest
observation. Missing resources inside an existing memory collection use
`skipped-existing-package`, retaining every Template source entry.

Editions v4, v5, v6, v7, v8 and v9 require the license trio
and records the original `preserved_licenses` inventory (empty when adopting
the trio) separately from `current_licenses` observed during verification.
Entries for absent companions use `skipped-existing-license`; every Template
license source remains in the receipt. Original markers must remain present;
ordinary content edits are observed without rewriting original hashes. During
interrupted asset adoption, licensing must still match the reviewed inventory.

Earlier `governance-starter-v5` receipts retain their original capture setting
and publisher binding; reruns do not silently upgrade them.
Earlier `governance-starter-v4` receipts retain the seven-skill licensing edition
without acquiring memory. Earlier `governance-starter-v3` receipts retain their original license-free
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
`static_health` records the selected setup edition or module, observation time,
input inventory versions, each required/preserved capability outcome, and
`runtime: not-exercised`. `static_ready` and `aggregate` describe this current
assessment. They never establish backend, model, guard or service operation.
An adopted or explicitly selected capability that fails a required static check
stops at `verification`, retains a partial receipt, and returns nonzero. Resolve
its recorded cause and repeat the exact request; copying success is insufficient.

Preserved customized capability may remain unavailable. In that case the base
asset/registration receipt can complete, with `preserved-unverified` diagnostics,
`static_ready: false`, `aggregate: degraded`, and CLI exit 1. Its completed base
receipt keeps later governed module adoption possible. Do not describe that
result as a complete healthy capability installation. Valid disabled publication
and capture-off choices remain disabled. CLI exit 0 requires a passing selected
static assessment; exit 2 retains the existing invalid/incomplete setup error
contract. Reruns use the receipt's recorded edition and original source inventory,
then assess current bytes; earlier completion evidence does not certify new edits.
The receipt retains source hashes and the original adoption hashes separately
from the hashes observed during the latest verification. A preserved or skipped
resource is identified explicitly; copied Template bytes are not claimed for it.
The receipt must account for every source destination in both directions:
adopted files match `owned_files`, preserved files match `preserved_files`, and
both maps match the source adoption hashes. Only explicitly skipped resources
inside an existing package, nonempty Task tree, or a v4/v5/v6/v7/v8/v9 preserved licensing
system may be absent from both maps.
Standalone starters and the required source inventory cannot be omitted.

After the helper returns `status: completed`, read `memory_capture` and tell the
user its actual setting. When `status: on`, say: "Memory automatic capture is on.
Would you like to turn it off?" Setup is already complete; do not wait for an
answer to enable it. Keep it on unless the user opts out. If they ask for off,
use the installed memory `set-capture off` command with the current config hash.
A preserved off preference remains off on reruns. If status is unavailable,
explain the preserved configuration/package limitation and complete any separately
authorized upgrade; never report capture ready just because a flag is true.
For the completion trigger, follow the memory skill's automatic-capture reference.

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

## Curator session installation and explicit existing-project adoption

New and first-prepared projects use `governance-starter-v11`. They receive
`CURATOR.md`, destination-specialized `curator.yaml`, enabled `curator-session.yaml`, protected
`document-ownership.json`, complete Curator/owner packages, current reference
contracts and four paired Curator roles. The existing role owner generates
`Roles/INDEX.md`. Repository/branch selection, runtime, standing entitlements,
autonomous writes, unattended schedules, external notifications, service and hook activation
remain disabled. Automatic memory capture retains the existing new-project
on/default notice and existing explicit opt-outs.

Earlier v1-v10 receipts retain their base edition and exact inventories. Ordinary
reruns do not acquire session maintenance or Curator or refresh an adopted Curator edition. For a selected
completed project, use `prepare-existing --adopt-module curator` with its
exact existing identity and destination. The existing receipt records the original
receipt hash/history, source manifest, complete package before/after inventories,
charter/configuration preservation, role index and current checks. No second
adoption store or canonical Task writer is created.

Adoption may add missing Curator files or refresh complete unchanged receipt-owned
owner packages. Customized, unknown or incomplete packages require selected repair;
existing charters/configuration/maps are preserved. Legacy role layouts require
the existing explicit role transition before adopting active `Roles/` pairs.
Authored knowledge, Tasks, project identity, licensing, capture choice, unrelated
roles and runtime state remain protected. An interrupted operation resumes only
with its original source bytes and exact recognized target pre/post bytes. Later
edits and changed sources hold recovery. Completed reruns verify current installed
state without refreshing new source editions implicitly.

Static assessment parses selected source and configuration; it executes no unknown
customized project Python. Installed, configured, authorized, compatible and
runtime-observed are distinct fields. Neutral capability can be statically
available while authorization and runtime observation remain false. Native,
service and optional backend/model checks require their separate selected gates.

`assess-curator --destination ABSOLUTE_PROJECT_PATH` is the read-only Curator
assessment entry. It reports installed, configured, authorized, compatible and
runtime-observed states separately, without executing unknown project Python.
`prepare-existing --adopt-module curator` is the preferred selected adoption
spelling; `project-curator` remains a compatible alias for the canonical module ID.

The affected-owner fixture tests use explicitly selected read-only depot sources
and an isolated, existing work directory. They do not require private release
snapshots or a special source-directory name and never choose a live source root
implicitly. Set `SYS4AI_CURATOR_TEST_SOURCE` to the real absolute selected depot
source root containing its packaged starter assets and registered Template;
set `SYS4AI_CURATOR_TEST_WORK` to a separate fixture directory (never that source
root or its ancestor). Only new temporary children of the work directory are
written. Run the selected interpreter with `PYTHONDONTWRITEBYTECODE=1` and
`PYTHONPATH` pointing to this package's `tests` directory:

```sh
python -m unittest test_curator_setup test_curator_adoption test_curator_recovery -v
```

The source root is copied for testing; its registry, Template and reusable
collections are read-only inputs. Earlier editions are explicitly reconstructed
from packaged baseline assets. Historical role helpers execute only after their
reconstructed bytes match the existing approved pin. These fixtures are not
original historical binaries. v1/v2 retain incompatible role layouts and require
the existing separately selected transition; tests never force migration or
relabel completed receipts to make Curator adoption succeed.

Selected v11 installations enable [bounded session maintenance](../curate/references/session-maintenance.md) immediately.
The Template remains neutral; explicit opt-outs and earlier setup receipts retain
their choices. The unattended scheduler, services and runtime installation remain
separate.

## Integrated Curator edition

New and first preparation select governance-starter-v12. This edition specializes
the Curator process and all function semantics after identity, session choice,
owner packages and Roles/INDEX.md settle. The Template retains empty active graphs,
null project identity, unbound authority and disabled session policy.

For a previously initialized project, select `prepare-existing --adopt-module
curator`. To refresh an earlier Curator installation explicitly add
`--refresh-module curator`; `project-curator` is the retained alias. An ordinary
rerun verifies its recorded edition. Original setup receipts and v1-v11 meanings
remain unchanged. Unchanged completed selections verify without new operations.

Compatible authored ontology uses an exact ontology-owner publication. A missing
grant leaves a resumable `curator_integration.preview` in the setup receipt. Supply
`--integration-grant-file` and optionally `--integration-proposal-file` on the same
request after exact review. API callers may supply a trusted current grant callback.
This route adds no installation, background AI, Git or unselected-project authority.
Static semantic success is separate from current runtime execution.
