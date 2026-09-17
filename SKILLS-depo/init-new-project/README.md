# init-new-project

This skill creates or prepares one selected project beneath its owning depot's
`Projects/` folder. The [skill contract](SKILL.md) defines scope and preservation.
The standard-library [helper](scripts/init_new_project.py) reads governance
starters only from the registered Template, specializes project identity,
maintains factual registration and verifies local files.

Both routes preserve existing project documents, packages, Tasks, configuration,
data and repository metadata. New projects receive ten complete skill packages
and the generic and task-manager roles with a generated index. The helper does not create an environment, install software
or contact a service. It uses Git only for read-only observations when a child
repository already exists.

The [receipt schema](assets/initialization-receipt.schema.json) defines schema-1
`governance-starter-v9` receipts at `control_records/project-setup.json`. Source
provenance, original adoption hashes and current observed hashes have separate
fields. Partial asset adoption resumes only against the same source inventory
and unchanged target bytes. Completed reruns preserve project edits and observe
current files and registration. Receipts from earlier setup tools are untouched.
Receipt validation binds every source adoption decision to the exact owned or
preserved file inventory. An omitted entry, changed adoption digest, contradictory
source decision or unsupported skipped starter rejects a rerun before mutation.

Version 10 adds service-independent ontology through edition v8. The neutral
Template contains strict JSON configuration, empty project and binding graphs,
locked core imports and the complete ontology skill and contracts. New setup
specializes ID, name, purpose, namespace and a current destination-local Director
binding limited to ontology publication. No runtime is provisioned.

Select adoption for an older completed receipt with the existing identity inputs:

```bash
python3 .agents/skills/init-new-project/scripts/init_new_project.py \
  prepare-existing --destination /absolute/depot/Projects/Selected \
  --project-id selected --project-name Selected --purpose "Project purpose" \
  --adopt-module ontology
```

Select a later Template edition using `--refresh-module ontology` with the same
`prepare-existing` identity inputs. Exact source hashes, package versions and
before/after targets are frozen in a nested receipt operation. The original base
edition is retained. An unchanged source request is idempotent; new sources need
an explicitly selected refresh. Recovery rejects changed inputs or conflicting
target bytes before publication.

The v8 `ontology` route preserves the configuration, canonical tree, skill and
contract collection as one installation if any existing part is custom, incomplete or incompatible.
Only a complete unchanged receipt-owned installation can be refreshed. A pristine
manual Template copy specializes its config during first preparation. Current
ontology publication bindings and memory preferences are retained; this route
never refreshes learning or memory or rewrites existing governance.

Read current static capability with:

```bash
python3 .agents/skills/init-new-project/scripts/init_new_project.py \
  assess-ontology --destination /absolute/depot/Projects/Selected
```

The initializer checks configuration, exact import hashes and local authority
without executing copied Python. It reports structural readiness separately from
`runtime: not-exercised` and the still-required operation grant. Run the installed
ontology `health` command to inspect semantic validation and source freshness.

Version 9 adds the `what-did-you-learn` module through contract v7. Memory
features remain explicit for v5-v9 and automatic capture for v6-v9. New projects
and first preparation receive the complete thin skill and five declared assets
under `reference-assets/LEARNING-depo/`. The source manifest, local references,
supported memory interfaces and shared completion route must pass preflight.
Existing custom module and memory packages remain whole. An incomplete preserved
capability is reported with its exact resource diagnostics.

Inspect current capability without changing files or contacting a backend:

```bash
python3 .agents/skills/init-new-project/scripts/init_new_project.py \
  assess-learning --destination /absolute/depot/Projects/Selected
```

The result separates `manual_review`, `shared_automatic_checkpoint`, the actual
capture preference, current Director binding and `authorized_publication`.
`requires-current-operation-grant` means the memory helper must still check the
exact operation, actor, configured path scope and current Task owner. It is not
an authorization to save. Backend status is `disabled` or
`configured-not-verified`; setup never initializes or contacts one. The three
pure resolver/configuration inspectors are pinned to this initializer's reviewed
version. Unknown customized inspector bytes remain untouched and are rejected
before execution; other compatible project resources may remain customized.

For an exact project whose completed receipt predates learning, select adoption:

```bash
python3 .agents/skills/init-new-project/scripts/init_new_project.py \
  prepare-existing --destination /absolute/depot/Projects/Selected \
  --project-id selected --project-name Selected --purpose "Project purpose" \
  --adopt-module what-did-you-learn
```

Add `--refresh-dependency memory` only when explicitly selecting a complete
memory skill and contract-package refresh. The helper refreshes an existing
package only when its entire file and directory inventory matches completed
receipt-owned provenance. It removes only retired owned resources. A customized
or incomplete dependency stays whole and receives a precise scoped-adoption
requirement; matching filenames never establish ownership. Existing `memory.yaml`,
capture off, notes, grants, history and backend data remain project-owned.
A pre-memory project can receive the selected empty memory capability and its
own initial authority. If needed, the minimal stable completion link is appended
to its governing instructions before that first local hash binding. An existing
binding is preserved, including any incompatible completion route.

Selected operations live in `module_adoptions` inside the existing receipt.
They retain the original base contract, source/owned/preserved inventories and
content-addressed receipt history. Each records module/version identity, exact
Template sources, package decisions, frozen before/after hashes, target scope,
checks and current capability. Partial operation status remains inside that
entry; a failed CLI result also distinguishes `base_setup_status`.
Recover unfinished base setup before adoption. Recover an interrupted module
with the exact same module and dependency arguments, frozen Template inputs and
expected before/after target bytes. Source drift, conflicting edits or active
project/Template locks refuse unsafe continuation. Completed repeated module
requests verify current files and capability, preserve subsequent project edits,
perform no implicit refresh and add no registration. Ordinary setup reruns keep
the original edition and do not discover a new module.

Version 8 enables automatic memory capture by default through contract v6, for
new projects and the first memory installation into an existing project. It
binds the destination Director to its actual governing files and reports
`memory_capture.status`, `message`, and `opt_out_question` after successful setup.
The agent must tell the user capture is on and ask whether to turn it off,
without delaying initialization. Existing off choices and old receipt editions
survive reruns. Incompatible preserved packages are reported as unavailable.

Version 7 added an empty memory capability through contract v5. It requires
`memory.yaml`, `MEMORY/README.md`, the memory skill and the complete
`reference-assets/MEMORY-depo/` package. Only the new config's project ID and
name are specialized; project root `.` and relative contract/state paths remain
local, and the backend remains disabled. Source validation rejects a populated
Template memory tree or incomplete required assets. The receipt distinguishes
`specialized` configuration/identity from copied `adopted` files and preserved
files. Registration grants no memory publication or cross-project access.

Existing configuration bytes and complete memory collections remain
project-owned, including custom notes, unrecognized config formats and missing
package resources. Original hashes are recorded in `preserved_memory`; current
observations are recorded in `current_memory`. Interrupted adoption requires
the complete reviewed inventory to remain unchanged. A completed rerun permits
ordinary content edits while retaining original evidence. An existing config,
when customized or from an older incompatible edition, is preserved and is
not falsely certified as operational. A pristine manual copy of the current
Template configuration is specialized on first preparation. Backend installation, configuration
adoption and changes to an existing publisher binding remain separate scoped
project work. New v6 installations receive their own bounded binding.

Version 6 adds the Template's `LICENSE`, `LICENSE-CODE`, and `LICENSE-DOCS` to
both setup routes through contract v4. Existing root license markers and license
directories preserve the whole project licensing system, including missing
companions. `preserved_licenses` records the original marker and tree hashes;
`current_licenses` records the latest observation. Skipped companions retain
their Template source entries with `skipped-existing-license`. The skill defines
recognized names and the boundary for licensing embedded only in other prose.
Earlier v1-v5 receipts remain valid with their original starter requirements;
v4 retains the license trio, and none of them acquires the v5 memory edition.
Completed reruns do not adopt the new license edition or change past evidence.

Version 5 adopts exactly spelled `Roles/` and validates each destination index
using frozen role helper bytes without copying runtime locks or transition
receipts. Existing `governance-starter-v1` (`sub-agent-roles/`) and
`governance-starter-v2` (lowercase `roles/`) receipts retain their original
contract, paths and adoption hashes. Directory-entry inspection prevents
case-insensitive lookup from silently merging or splitting role collections.
A version-2 rerun after an explicit role-helper case rename validates the
completed proof and directory identity, records its digest separately, and
reports current hashes at `Roles/` paths. It does not invent historical paths or
change old evidence. Missing, pending, changed or wrong-root proof rejects the
rerun before writes. Finish an interrupted asset stage using its recorded
Template edition before the rename; completed asset stages can resume remaining
setup after the proven rename. Current helper adoption and reindexing are part
of that separate reviewed migration, never implicit setup actions.
A fresh prepare-existing request with legacy roles or an incompatible role
helper stops before writes and identifies the required explicit transition.
A completed copy-first transition is accepted with its retained legacy directory
only after the strict receipt, old and active bytes, current index and role helper
are verified. Missing, incomplete, corrupt or conflicting transition evidence
blocks preparation before starter writes. Existing current role collections and
their additional files are preserved.

Version 3 removed the former principal, dataset and runtime-artifact CLI/API
options. It accepts schema-2 starter policy only, with no optional root files.

Run the focused tests using the depot's Python 3.12 interpreter:

```bash
PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 \
  .venv/bin/python -m unittest discover \
  -s SKILLS-depo/init-new-project/tests -v
```

The standard-library suite uses disposable depot fixtures. It exercises memory
identity/path specialization, empty starters, complete memory preservation,
missing memory sources, on/off capture, post-setup notices, v1-v9 receipt recovery, selected module recovery, licensing
adoption, whole-system preservation, earlier receipt editions, create,
manual-copy preparation, existing customization, identity and registry conflicts,
source drift, symlink/hardlink rejection, atomic writes, interrupted recovery,
locking and reruns. CLI end-to-end checks run with isolated Python, no installed
site packages, and subprocess calls confined to read-only Git observations.
There are no dependency installs, downloads, model fixtures or external services.

Source editing, adoption into an active project and Template propagation remain
separate operations. Tests in an isolated fixture do not establish live watcher
health or authorize changes to other registered projects.

## Advanced ontology initializer v9

The current helper verifies complete capability packages and shipped tests
against `assets/static-capability-v1.json`, whose digest is pinned in its trusted
static inspector. It checks profile/requirement locks, local identity and
publication bindings, and parses unknown target Python without executing it. New source
delivery requires this complete inventory; reruns retain the original receipt's
edition and source inventory. Known pure configuration validators remain pinned;
unknown copied inspectors are preserved without execution. Role-index inspection
likewise pins the reviewed current helper and exact v1/v2 root-name variants.

Results include `static_health`, `static_ready` and `aggregate`. A failed required
adopted/selected capability retains a partial verification stage and returns
exit 2. A preserved custom capability gap may retain completed base assets and
registration so later scoped adoption remains possible, while reporting
`preserved-unverified`, `static_ready: false`, `aggregate: degraded`, and exit 1.
Exit 0 means the selected static assessment passed. All these results retain
`runtime: not-exercised`; setup never starts, installs or certifies a runtime.
Disabled publication and capture-off choices remain unchanged.

`test_static_readiness.py` covers these completion boundaries, missing test/health
resources, lock changes, manual/deep paths, exact recovery and earlier editions.
The installed ontology tests support `SYS4AI_STANDARDS_PYTHON` and
`SYS4AI_SEMANTIC_ACCEPTANCE_ROOT` for separately selected existing runtimes;
depot-only fixture factories use explicit `SYS4AI_TEST_DEPOT_ROOT` when absent
from the selected owner. `ontology/tests/acceptance_runner.py` requires the
reviewed identity inventory and fails missing or skipped selected coverage.

Initializer 11.0.0 uses `governance-starter-v9` for new and first-prepared
projects. The advanced companion specializes the destination identity and
publication binding. Standards, inference, semantic retrieval, guards and the
workbench remain disabled. Setup copies capability and manifests; it performs
no dependency/model installation, certification, service startup or guard
bootstrap. The result separates installed capability, enabled flags, current
operation grants and unexercised runtime state.

Use `assess-ontology-advanced --destination PATH` for a read-only static check.
Use `prepare-existing --adopt-module ontology-advanced` with the existing
identity arguments for an explicit capability upgrade. Earlier base editions
stay unchanged. The operation refreshes complete unchanged receipt-owned code
packages and contracts while preserving authored ontology, import locks,
configurations, durable proposals, memory choices, licensing and governance.
Unknown customized or missing packages fail before writing with diagnostics.
An earlier project without ontology can receive a recorded neutral prerequisite
in the same module operation. Guard-enabled destinations require their selected
adapter repair before code refresh.

The existing `module_adoptions` collection retains exact source inventories,
prior receipt archives, expected target bytes and protected authored-data
inventories. Interrupted upgrades resume only recognized pre/post state. New
source files, conflicting target edits or changed protected data block replay.
Completed equivalent requests observe current project state without overwriting
later edits. This differs from the v8 whole-installation `--refresh-module
ontology` route, which retains its original semantics.

Focused acceptance is in `test_advanced_ontology_setup.py`,
`test_advanced_ontology_adoption.py` and `test_advanced_ontology_recovery.py`.
The complete initializer suite also checks earlier editions, licenses, memory,
learning, roles, CLI boundaries and recovery. All fixtures use disposable
registered depots; they do not update the real Template or projects.

Selected v11 installations enable [bounded session maintenance](../curate/references/session-maintenance.md) immediately.
The Template remains neutral; explicit opt-outs and earlier setup receipts retain
their choices. The unattended scheduler, services and runtime installation remain
separate.
