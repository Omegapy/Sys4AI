# Project specifications (template)

Keep this file as `SPECS.md` in each project's root. Specialize it for the real
product's runtime, dependencies and file exclusions as those choices are made.
Keep technical specifications here and link to them from `README.md` and
`AGENTS.md`. The existing implementation contracts and memory setup guide retain
their own detailed requirements and procedures.

## Python environment

Use a project-local Python 3 virtual environment at `.venv/` for Python-based
skills and project tools. Install their dependencies into that environment.
For the Memory System preparation route, use a Python version compatible with
the selected immutable runtime. The selected artifact's package metadata owns that version requirement.

This template checkout may have a `.venv` for local checks. It is ignored and is
never a starter asset. For a new Memory System consumer, let the shared
initializer create the copied project's own `.venv` at its final path. Do not
copy, move or precreate a different environment for that preparation route.
Follow [INIT_MEMORY.md](./INIT_MEMORY.md) for the setup procedure.

After preparation, activate the real project's environment:

### macOS and Linux

```bash
source .venv/bin/activate
```

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

Confirm the prepared project's interpreter and installed package:

```bash
python --version
python -c "import importlib.metadata as metadata; print(metadata.version('sys4ai-memory-service'))"
```

Leave it with `deactivate`.

## Skill and runtime dependencies

| Dependency | Use in a project created from this starter |
| --- | --- |
| Python standard library | The bundled Task, role-catalog, implementation-plan and To-TRD helpers require no third-party Python packages. |
| `PyMuPDF` | Required PDF-work library from the depot specification. The `pdf-pymupdf` skill uses it for PDF inspection, text and image extraction, and page rendering through `pymupdf` or `fitz`. That skill is not one of this template's embedded packages. |
| `sys4ai-memory-service` | Installed into a real copied project's environment by the shared preparation route in [INIT_MEMORY.md](./INIT_MEMORY.md). The selected artifact and its dependency lock determine its packages and versions. |

The starter currently has no `requirements.txt` or `pyproject.toml`. When
specializing a real project, declare `PyMuPDF` and any other third-party skill
dependencies in a tracked `requirements.txt` or the product's dependency
manifest. Keep version constraints in that manifest and update this table when
a skill adds a dependency. A template's development environment does not
provision any future copy; verify its own dependencies before using a skill.

## Git exclusions

Keep the existing root [.gitignore](./.gitignore) as a starter asset and track it
when the real project's repository is configured. It excludes virtual
environments, generated caches, local secrets, Task runtime files and derived
memory state. Preserve those protections when specializing the project.
Review inherited path-specific rules, including `/Projects/*`, against the real
product's layout rather than replacing its exclusions with depot defaults.
