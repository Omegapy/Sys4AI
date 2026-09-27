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

The licensing starters are `LICENSE`, `LICENSE-CODE`, and `LICENSE-DOCS`.
They define the Apache 2.0 code / CC BY 4.0 document split and default
attribution. Setup contracts `governance-starter-v4` and `governance-starter-v5` adopt the complete trio
when no existing root license markers are present. It preserves existing
licensing as a whole, records original and observed marker hashes separately,
and skips missing companions. Earlier setup editions retain their own source
requirements; a rerun does not adopt a later licensing edition. Follow the
initializer skill for recognized markers and explicit adoption boundaries.

Setup does not define a product runtime or configure a repository. Product
implementation, dependency installation, Git setup, and publication are
separate project work. Existing independent project state remains project-owned.

## Git exclusions

Keep the existing root [.gitignore](./.gitignore) as a starter asset and track it
when the real project's repository is configured. It excludes virtual
environments, generated caches, local secrets and Task runtime files. Preserve those protections when specializing the project.
Review inherited path-specific rules, including `/Projects/*`, against the real
product's layout rather than replacing its exclusions with depot defaults.

## Task and role storage

The Task helper preserves schema-1 history and adds a versioned orchestration
extension for enabled records. Task state, role definitions, native execution
and managed document lifecycles stay separate. Current role definitions use
paired files under `Roles/` with a destination-generated `Roles/INDEX.md`.
The role mutation helper uses Python standard-library POSIX advisory locking;
unsupported hosts must report the missing capability rather than bypass it.
No database, queue service, memory/ontology backend or new production package
is required by orchestration.

Use the installed Task and role contracts for current commands, exact writer
and version checks, index repair, selected legacy transition and recovery.
Initializer starter data excludes native handles, live execution and role
transition runtime receipts. Existing customized projects require their own
reviewed adoption; registration and read-only inspection do not migrate them.

## Project memory runtime

The memory core, Task integration and lexical source lookup use Python 3.12's
standard library. `memory.yaml` and record frontmatter accept a documented JSON
object subset of YAML; no general YAML parser is imported by governance helpers.
Canonical notes live only in `MEMORY/`, with adopted contracts under
`reference-assets/MEMORY-depo/`. Configuration and canonical records remain
trackable; the Template starts empty with neutral identity and backend disabled.

Optional PDF extraction is declared in the memory skill's
`requirements-extraction.txt`. The pinned Basic Memory local pilot has a separate
`requirements-backend-pilot.txt`, immutable model profile and runtime. Neither is
installed by initialization or lookup. The backend's ordinary CLI/MCP writers
are not canonical publication tools; the guarded adapter uses derived products
and exact result revalidation. A failed compatibility gate retains lexical use.

The memory [state-path contract](./.agents/skills/memory/references/state-paths.md)
distinguishes rebuildable projection, normalization, index and model products
from durable backend configuration and pending maintenance journals. Never
classify the whole `.sys4ai` directory as disposable. Setup edition v6 selects
the empty capability, defaults automatic capture on and binds the destination
Director to its local governance. It records copied, specialized or preserved
assets and reports the setting with an opt-out after completion. Existing
choices and v1-v5 receipt editions retain their original adoption evidence.

## Learning capability

Initializer edition v7 adds the complete `what-did-you-learn` skill and
`reference-assets/LEARNING-depo/` resources. Memory remains supported for v5-v8
and automatic capture for v6-v8. The module supplies learning review and
improvement disposition through the existing memory completion reference;
record schema, publication, retrieval and recovery remain owned by memory.
Canonical learned records remain project-local in `MEMORY/`.

Selected prior-edition adoption uses `prepare-existing --adopt-module
what-did-you-learn`. Optional `--refresh-dependency memory` requires a complete
unchanged receipt-owned dependency package. The existing setup receipt gains
validated `module_adoptions`, preserving its original base fields and
content-hashed history. Existing configuration, capture off, bound governance,
customizations and notes remain intact. First memory binding may add its missing
stable completion link before local authority hashes are computed.

The standard-library read-only assessment separates interface capability,
capture preference, current binding, required operation grants and optional
backend status. Unknown customized inspectors are preserved without execution.
No setup or lookup installs a backend, starts a service, records transcripts,
adds runtime hooks or provisions a model. Inspect the installed learning and
initializer contracts for supported commands and exact recovery boundaries.

## Ontology starter and initialization v8

Initializer 10.0.0 uses `governance-starter-v8` for new and first-prepared projects.
The [ontology contract](./reference-assets/ONTOLOGY-depo/profile.md) defines a
strict JSON-LD subset with pinned local contexts and versioned core imports.
Canonical project graphs and bindings live under `ONTOLOGY/`; `ontology.yaml`
configures the local project. Python 3.12 standard-library helpers provide core
validation, lookup and explicit generated outputs without an ontology service.
Generated `.sys4ai/ontology/` and `ONTOLOGY/WIKI/` paths are separate from durable
`control_records/ontology/` publication and recovery records.

Setup specializes the saved project identity, namespace and local Director
binding. The initializer statically verifies declaration/import integrity and
current binding without executing customized project code. Semantic/source
readiness is inspected by the installed ontology `health` command; setup grants
no operation-specific publication authority. Existing receipts retain their
original edition. Explicit ontology adoption and receipt-owned refresh use the
[initializer contract](./.agents/skills/init-new-project/SKILL.md), preserving
existing memory, learning, governance, Tasks, roles, licensing and project data.

## Curator capability and initialization v10

The current starter edition is `governance-starter-v10`; earlier v1-v9 setup
receipts keep their original edition and recorded ownership. Curator adds its
charter, inactive destination configuration, protected ownership map, complete
skill/reference package and four paired roles. Existing role discovery owns the
generated index. Source distribution installs no service, hook, environment,
model, queue, credentials or live entitlement and copies no project knowledge.

Curator status/review are read-only. Current Task intake/continuation can consult
existing scoped Curator notices; unrelated work proceeds silently. Exact manual
and automatic operations use the same Application route and original owner APIs.
Fixed direct calls bind the actual current Task, manager, root, revision and exact
selected arguments. Existing Broker callbacks retain their supported route and
every owner still performs its own checks. Separate
authority covers integration, canonical knowledge, governance, dependencies and
runtime effects. Installed capability is not activation; selected native and
host proof remains required. Explicit existing-project adoption uses the one
setup receipt, retains licensing/capture/custom roles and preserves partial
recovery and later edits without implicit refresh on completed reruns.

New ordinary Curator executions use Task schema 2 with orchestration version 1.
The read-only `validate_controller_selection` helper validates a versioned
selection artifact against the prepared project, selected charter and policy,
and current filesystem role catalog. Its exact bytes and source references enter
the normal manager reservation's `source_refs` and context. Actual reservation,
native launch receipt, required reads and confirmed activation remain mandatory;
the selection artifact itself creates no Task or standing runtime permission.
Existing orchestration version 2 records retain their original Broker and native
protocol requirements and are never converted by ordinary selection. Static-ready
setup remains installed-inactive and establishes no native or callback readiness.
