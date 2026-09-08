# init-new-project

This skill creates or prepares one selected project beneath its owning depot's
`Projects/` folder. The [skill contract](SKILL.md) defines scope and preservation.
The standard-library [helper](scripts/init_new_project.py) reads governance
starters only from the registered Template, specializes project identity,
maintains factual registration and verifies local files.

Both routes preserve existing project documents, packages, Tasks, configuration,
data and repository metadata. New projects receive seven complete skill packages
and the generic and task-manager roles with a generated index. The helper does not create an environment, install software
or contact a service. It uses Git only for read-only observations when a child
repository already exists.

The [receipt schema](assets/initialization-receipt.schema.json) defines schema-1
`governance-starter-v4` receipts at `control_records/project-setup.json`. Source
provenance, original adoption hashes and current observed hashes have separate
fields. Partial asset adoption resumes only against the same source inventory
and unchanged target bytes. Completed reruns preserve project edits and observe
current files and registration. Receipts from earlier setup tools are untouched.
Receipt validation binds every source adoption decision to the exact owned or
preserved file inventory. An omitted entry, changed adoption digest, contradictory
source decision or unsupported skipped starter rejects a rerun before mutation.

Version 6 adds the Template's `LICENSE`, `LICENSE-CODE`, and `LICENSE-DOCS` to
both setup routes through contract v4. Existing root license markers and license
directories preserve the whole project licensing system, including missing
companions. `preserved_licenses` records the original marker and tree hashes;
`current_licenses` records the latest observation. Skipped companions retain
their Template source entries with `skipped-existing-license`. The skill defines
recognized names and the boundary for licensing embedded only in other prose.
Earlier v1-v3 receipts remain valid with their original starter requirements.
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

The standard-library suite uses disposable depot fixtures. It exercises licensing
adoption, whole-system preservation, earlier receipt editions, create,
manual-copy preparation, existing customization, identity and registry conflicts,
source drift, symlink/hardlink rejection, atomic writes, interrupted recovery,
locking and reruns. CLI end-to-end checks run with isolated Python, no installed
site packages, and subprocess calls confined to read-only Git observations.
There are no dependency installs, downloads, model fixtures or external services.

Source editing, adoption into an active project and Template propagation remain
separate operations. Tests in an isolated fixture do not establish live watcher
health or authorize changes to other registered projects.
