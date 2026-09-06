# Sys4AI depot specifications

This file owns the technical specifications for the Sys4AI depot root. It is
adapted from [the reusable specification](./SPECS-depo/SPECS.md). Product
projects keep their own root `SPECS.md`; this file describes the depot.

## Python environment and dependencies

Use Python 3.12 in this root's `.venv/`. Run Python helpers with
`.venv/bin/python`; run the installed memory command with
`.venv/bin/sys4ai-memory`. The installed Memory Service requires Python
`>=3.12,<3.13`. Do not copy or move another project's environment here.

| Component | Dependency specification |
| --- | --- |
| Task, role, document and project-initialization helpers | Python standard library. |
| `pdf-pymupdf` skill | `PyMuPDF`, providing `pymupdf` and `fitz`. The skill is available through the personal skill catalog, separately from the depot's installed skill packages. |
| Memory runtime | Installed `sys4ai-memory-service` consumer wheel. Exact package origin, version and dependency profile belong to the [installation record](./control_records/memory/runtime-installation.json); product dependency constraints belong to its [manifest](./Projects/Sys4AI-Memory-Service/pyproject.toml). |

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

## Project memory

The root consumes the installed Memory Service package. Its
[configuration](./config/memory.toml) identifies project `sys4ai-depot`, dataset
`sys4ai-depot-memory`, default profile `base@1`, and currently disables semantic
memory. Canonical configuration, permissions, registries and profiles remain
project-owned. Derived indexes, receipts, logs and caches belong beneath
`.sys4ai/memory/`.

The depot's adoption used `init preview` followed by digest-bound `init apply`;
new and manually prepared projects use the shared `init-memory` route.
Installation and configuration are not evidence of current retrieval or model
readiness. Follow the [memory control guide](./control_records/memory/README.md)
and [readiness procedure](./Projects/Sys4AI-Memory-Service/docs/operations/memory-readiness-and-activation.md)
for checks and the existing activation-decision handoff.

The [source registration policy](./control_records/memory/source-registration-policy.md)
owns memory source boundaries and registration procedures. Specification
adoption does not register or synchronize new files into memory.

## Documentation ownership

Keep technical requirements here. `README.md` provides navigation and usage;
`AGENTS.md` requires reading this file and owns agent instructions. Link to the
existing skill and operational contracts instead of repeating their contents.
