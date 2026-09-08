# Sys4AI depot specifications

This file owns the technical specifications for the Sys4AI depot root. It is
adapted from [the reusable specification](./SPECS-depo/SPECS.md). Product
projects keep their own root `SPECS.md`; this file describes the depot.

## Python environment and dependencies

Use Python 3.12 in this root's `.venv/`. Run Python helpers with
`.venv/bin/python`. Do not copy or move another project's environment here.

| Component | Dependency specification |
| --- | --- |
| Task, role, document and project-initialization helpers | Python standard library. |
| Template update engine and macOS watcher | Python standard library, including POSIX advisory locks; macOS `launchd` manages the local watcher. |
| `pdf-pymupdf` skill | `PyMuPDF`, providing `pymupdf` and `fitz`. The skill is available through the personal skill catalog, separately from the depot's installed skill packages. |

The root currently has no `requirements.txt` or `pyproject.toml`. PyMuPDF is
installed in its environment but has no root dependency declaration. When
adding a root manifest, record skill dependencies there and keep version
constraints there rather than duplicating them in prose. Installing a package
and recording a reproducible dependency are separate steps.

Inspect the selected interpreter and package manager with:

```bash
.venv/bin/python --version
.venv/bin/python -m pip --version
```

The active [skill directory](./.agents/skills/) contains `agent-task`,
`communication`, `init-new-project`, `manage-subagent-roles`, `task`,
`to-implementation-plan` and `to-trd`. Their `SKILL.md` files own their usage
contracts; [SKILLS-depo](./SKILLS-depo/) owns separate reusable sources.

## Git exclusions

The root's existing [.gitignore](./.gitignore) owns the exclusion rules for
local environments, generated files, caches, secrets and independent child
working trees. Preserve its project-specific rules. The reusable copy in
`SPECS-depo/` is a source for later adoption, not a replacement for this file.

## Template update pipeline

Reusable assets are authored in the `*-depo` collections. The
[mapping](./depot/template-update.json) and
[update guide](./depot/template-update.md) define their automatic publication
into the template. Only that template supplies project-initialization assets.
Update state and recovery data belong in `.sys4ai/template-update/`.
Host logs belong in `~/Library/Logs/Sys4AI/`. The watcher is a local
user launch agent; a clone requires its own explicit watcher installation.

`LICENSES-depo/` supplies `LICENSE`, `LICENSE-CODE` (Apache 2.0), and
`LICENSE-DOCS` (CC BY 4.0) through explicit Template root mappings. The active
root adopts the same trio. [The licensing guide](./LICENSES-depo/README.md)
records provenance, attribution, scope, and project ownership boundaries.

## Project initialization

Both `init-new-project create` and `prepare-existing` copy reviewed governance
assets from the registered Template, specialize project identity, and maintain
factual project registration. They preserve customized project files and
existing independent state. The helpers use the Python standard library and
read-only Git observations. They do not provision a product runtime.

The setup receipt at `control_records/project-setup.json` records source hashes,
asset adoption, registration, and verification. A partial operation must resume
through the helper's checked same-request flow. Product dependencies, virtual
environments, Git initialization, and publication are separate project work.
Setup contract `governance-starter-v4` includes the complete license trio and
records preserved project licensing separately. Earlier receipt editions keep
their original source requirements and do not acquire licenses on a rerun.

## Documentation ownership

Keep technical requirements here. `README.md` provides navigation and usage;
`AGENTS.md` requires reading this file and owns agent instructions. Link to the
existing skill and operational contracts instead of repeating their contents.

## Task orchestration and role storage

Task and role helpers use Python standard-library filesystem transactions,
SHA256 evidence and the existing Task ledger. Role mutation uses POSIX advisory
locking; no database, external orchestration framework or retired memory service
is required. Native tools supply real agent control and inheritance evidence.
The root intake policy remains separate from generic Template behavior.
