# Project specifications

Keep this file as `SPECS.md` in the project root, alongside `AGENTS.md` and
`README.md`. It owns the project's technical specifications. Extend it as the
project evolves.

## Python environment

Use a project-local Python 3 virtual environment at `.venv/`. Run Python-based
skills and project tools with that environment's interpreter, and install their
dependencies into the same environment.

## Skill dependencies

Record third-party Python libraries required by the project's skills in a
tracked `requirements.txt`, or the project's existing dependency manifest.
Keep version constraints in that manifest; use this section to explain which
skill needs each library. Update both when a skill adds a dependency.

The initial required library is:

| Python package | Skill | Purpose |
| --- | --- | --- |
| `PyMuPDF` | `pdf-pymupdf` | PDF inspection, text and image extraction, and page rendering. Provides the `pymupdf` and `fitz` imports. |

## Git exclusions

Keep a tracked `.gitignore` in the project root. Start from the
[companion `.gitignore`](./.gitignore), copied from the Sys4AI depot root.
Review its depot-specific path rules when adopting it into another project and
preserve that project's existing exclusions. Keep the virtual environment,
generated caches, and local secrets out of Git.

## Documentation links

`AGENTS.md` must include this required read:

> Read [SPECS.md](./SPECS.md) before performing project work.

`README.md` should provide this navigation link:

> For project specifications, see [SPECS.md](./SPECS.md).

Keep specification requirements here. Link to this file from other documents
without restating or summarizing those requirements.
