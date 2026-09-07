# Project specifications (template)

Keep this file as `SPECS.md` in each project's root. Specialize it for the real
product's runtime, dependencies and file exclusions as those choices are made.
Keep technical specifications here and link to them from `README.md` and
`AGENTS.md`. The existing implementation contracts retain their own detailed
requirements and procedures.

## Python environment

Use a project-local Python 3 virtual environment at `.venv/` for Python-based
skills and project tools. Install their dependencies into that environment.
The bundled governance and project-setup helpers use the Python standard library.
Use Python 3.12 for the depot's documented checks.

This Template checkout may have a `.venv` for local checks. It is ignored and
is never a starter asset. A copied project's environment is prepared separately
at its final path when the product needs one. Do not copy or move an installed
environment from another project.

After creating a real project's environment, activate it with
`source .venv/bin/activate` on macOS/Linux or `.venv\Scripts\Activate.ps1`
in Windows PowerShell. Check `python --version`; leave it with `deactivate`.

## Skill and runtime dependencies

| Dependency | Use in a project created from this starter |
| --- | --- |
| Python standard library | The bundled Task, role-catalog, implementation-plan, To-TRD and project-setup helpers require no third-party Python packages. |
| `PyMuPDF` | Required PDF-work library from the depot specification. The `pdf-pymupdf` skill uses it for PDF inspection, text and image extraction, and page rendering through `pymupdf` or `fitz`. That skill is not one of this template's embedded packages. |

The project root currently has no `requirements.txt` or `pyproject.toml`. When
specializing a real project, declare `PyMuPDF` and any other third-party skill
dependencies in a tracked `requirements.txt` or the product's dependency
manifest. Keep version constraints in that manifest and update this table when
a skill adds a dependency. A template's development environment does not
provision any future copy; verify its own dependencies before using a skill.

## Governance setup

The depot's `init-new-project` helper reads starter assets only from the
registered Template. Its `create` and `prepare-existing` routes specialize
identity, adopt complete governance packages, preserve customized content, and
maintain factual project registration. Setup records source hashes and checked
stages in the project-owned `control_records/project-setup.json` receipt.
Equivalent reruns preserve identity and avoid duplicate registration.

Setup does not define a product runtime or configure a repository. Product
implementation, dependency installation, Git setup, and publication are
separate project work. Existing independent project state remains project-owned.

## Git exclusions

Keep the existing root [.gitignore](./.gitignore) as a starter asset and track it
when the real project's repository is configured. It excludes virtual
environments, generated caches, local secrets and Task runtime files. Preserve those protections when specializing the project.
Review inherited path-specific rules, including `/Projects/*`, against the real
product's layout rather than replacing its exclusions with depot defaults.
