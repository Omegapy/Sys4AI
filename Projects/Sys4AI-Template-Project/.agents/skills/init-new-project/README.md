# init-new-project

This skill creates or prepares one selected project beneath its owning depot's
`Projects/` folder. The [skill contract](SKILL.md) defines scope and preservation.
The standard-library [helper](scripts/init_new_project.py) reads governance
starters only from the registered Template, specializes project identity,
maintains factual registration and verifies local files.

Both routes preserve existing project documents, packages, Tasks, configuration,
data and repository metadata. New projects receive seven complete skill packages
and the generic role. The helper does not create an environment, install software
or contact a service. It uses Git only for read-only observations when a child
repository already exists.

The [receipt schema](assets/initialization-receipt.schema.json) defines schema-1
`governance-starter-v1` receipts at `control_records/project-setup.json`. Source
provenance, original adoption hashes and current observed hashes have separate
fields. Partial asset adoption resumes only against the same source inventory
and unchanged target bytes. Completed reruns preserve project edits and observe
current files and registration. Receipts from earlier setup tools are untouched.
Receipt validation binds every source adoption decision to the exact owned or
preserved file inventory. An omitted entry, changed adoption digest, contradictory
source decision or unsupported skipped starter rejects a rerun before mutation.

Version 3 removes the former principal, dataset and runtime-artifact CLI/API
options. It accepts schema-2 starter policy only, with no optional root files.

Run the focused tests using the depot's Python 3.12 interpreter:

```bash
PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 \
  .venv/bin/python -m unittest discover \
  -s SKILLS-depo/init-new-project/tests -v
```

The standard-library suite uses disposable depot fixtures. It exercises create,
manual-copy preparation, existing customization, identity and registry conflicts,
source drift, symlink/hardlink rejection, atomic writes, interrupted recovery,
locking and reruns. CLI end-to-end checks run with isolated Python, no installed
site packages, and subprocess calls confined to read-only Git observations.
There are no dependency installs, downloads, model fixtures or external services.

Source editing, adoption into an active project and Template propagation remain
separate operations. Tests in an isolated fixture do not establish live watcher
health or authorize changes to other registered projects.
