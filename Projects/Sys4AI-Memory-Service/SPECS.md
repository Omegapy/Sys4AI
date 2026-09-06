# Sys4AI Memory Service specifications

This project-local `SPECS.md` owns the product's technical baseline. Detailed
dependency, configuration, and interface contracts remain in the linked
sources below; extend those sources and this baseline as the product evolves.

## Product and service boundary

Sys4AI Memory Service is a local-first, agent-independent memory platform for
Sys4AI projects. It combines deterministic exact and lexical retrieval with a
replaceable semantic, graph, and temporal provider. Clients use provider-neutral
`sys4ai_memory` interfaces and must not depend on Cognee response shapes,
native tools, or storage files. The [developer guide](docs/operations/developer-guide.md)
owns the detailed layering, interface, retrieval, and lifecycle contracts.

Registered project sources remain authoritative. Tracked sources, schemas,
registries, profiles, policy, configuration, control records, and documentation
are canonical only according to their registered role. Indexes, caches,
provider databases, staging output, model artifacts, audit logs, receipts,
generations, and export candidates are generated local state.
`.sys4ai/memory/` and provider databases must remain disposable and rebuildable
from registered sources, schemas, profiles, and configuration.

General agents receive read and propose capabilities. Approval, promotion,
rebuild activation, import activation, mass deletion, and privacy erasure
require fresh canonical permission checks, a reviewed preview or staged
artifact, and a matching digest. Semantic memory never grants authority.

## Python environment and dependencies

Use Python 3.12 in the project-local `.venv/`, managed by `uv`. Run project
tools and Python-based skills with this environment's interpreter. The
[Python selector](.python-version), [dependency manifest](pyproject.toml), and
[lockfile](uv.lock) own the runtime selection, dependency constraints, and
resolved versions. The manifest separates core runtime libraries from the
optional `cognee` provider and `dev` tools; do not duplicate those lists here.

The installed project skill helpers use the Python standard library. Record
any added third-party skill dependency in the appropriate manifest group and
lockfile, with its skill and purpose documented here. The depot's PDF baseline
uses `PyMuPDF` for `pdf-pymupdf` inspection, text/image extraction, and rendering
through `pymupdf` or `fitz`. That skill is not installed locally and PyMuPDF is
not declared or installed in this product environment. If the PDF skill is
adopted, declare PyMuPDF as tooling before using it; it is not a core Memory
Service runtime requirement.

## Configuration and exclusions

The [configuration contract](config/README.md) owns capability, model, path,
permission, transport, and provider settings. The [decision register](docs/decisions/decision-register.md)
owns approved choices and deferrals. The [readiness procedure](docs/operations/memory-readiness-and-activation.md)
owns project-specific capability checks and the activation handoff.

Maintain the project-owned root [.gitignore](.gitignore), preserving its
product-specific exclusions for the virtual environment, generated memory and
provider state, model caches, build/test output, and local secrets. Do not
replace it wholesale with the depot's example. Keep it under version control
when a product repository is established through an authorized workflow.

## Documentation ownership

`AGENTS.md` requires reading this file. `README.md` provides the project entry
point, operational commands, and evidence status, with a plain link here for
specifications. Keep technical requirements here or in the detailed contracts
linked here; do not repeat them in those entry documents. The
[Makefile](Makefile) and [verification guide](docs/verification/README.md) own
the validation commands and release-evidence rules.
