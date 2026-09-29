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

The active [skill directory](./.agents/skills/) contains the installed project
packages. Their `SKILL.md` files own their usage
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

## Project memory

The root owns portable Markdown records in `MEMORY/` and its `memory.yaml`
configuration under identity `sys4ai-depot`. Adopted contracts live at
`reference-assets/MEMORY-depo/`; reusable sources remain in `MEMORY-depo/` and
`SKILLS-depo/memory/`. General retrieval permits README, docs and research; it
excludes child projects, Tasks, roles, reusable assets and private/runtime paths.

The memory core and Task/role integration retain Python 3.12 standard-library
independence. Configuration/frontmatter use a documented JSON subset of YAML.
`requirements-memory.txt` declares the existing optional PyMuPDF extraction
dependency. The pinned Basic Memory pilot uses `.venv-memory-pilot` and the
memory skill's separate backend requirements/profile; the root `.venv` is
preserved. Setup and ordinary reads provision no packages, models or services.

The [state-path contract](./.agents/skills/memory/references/state-paths.md)
separates derived products from durable backend configuration and maintenance
recovery. The [integration contract](./.agents/skills/memory/references/task-integration.md)
uses existing Task artifacts and inputs without a schema change. Initializer
edition `governance-starter-v5` supplies empty project memory; v1-v4 receipts,
root intake/closure policy and existing product content retain their semantics.
Semantic use is controlled by current configuration and the exact local pilot
certification. Inspect `memory.py --project-root . health` for current readiness.

Automatic memory capture defaults on in initializer edition `governance-starter-v6`.
The completion workflow and explicit on/off command are defined in the memory
skill's [automatic-capture reference](./.agents/skills/memory/references/automatic-capture.md).
New installations receive destination-local Director authority. Setup reports
the actual setting and offers off after completion; existing choices and earlier
receipt editions are preserved.

## Learning module and initialization v7

`LEARNING-depo/` owns the version 1.0.0 policy, review contract, compatibility
manifest and lesson-body assets. The thin `what-did-you-learn` skill uses the
existing memory completion reference, storage schema, four capture triggers,
publication and recovery operations. Adopted contracts live at
`reference-assets/LEARNING-depo/`. No learned records or runtime state belong
in the reusable module or Template.

Initializer 9.0.0 uses `governance-starter-v7` for new and first-prepared projects.
Memory editions remain v5-v7 and automatic capture v6-v7. Explicit
`prepare-existing --adopt-module what-did-you-learn` extends the existing setup
receipt's `module_adoptions`; it retains the original base edition and archived
provenance. `--refresh-dependency memory` selects complete unchanged receipt-owned
dependencies only. Current project content, memory choices, records and existing
bound governance remain preserved. A first memory binding may add its missing
stable completion link before hashing destination-local authority.

The read-only learning resolver and initializer assessment use Python 3.12's
standard library. The initializer binds its three pure inspectors to reviewed
hashes and rejects unknown customized inspector code before execution. Static
interfaces, actual capture choice, current binding, operation-specific grants
and backend status are separate checks. Initialization provisions no runtime,
service, model or dependency. Follow the installed
[initializer contract](./.agents/skills/init-new-project/SKILL.md) and
[learning entry](./.agents/skills/what-did-you-learn/SKILL.md) for usage.

## Ontology first release and initialization v8

`ONTOLOGY-depo/` owns the compact local JSON-LD profile, trusted vendored context,
core module 1.0.0, publication contract and neutral starter. The installed ontology
skill adopts `SKILLS-depo/ontology/`; `reference-assets/ONTOLOGY-depo/` holds the
selected contracts. Canonical project content belongs in `ONTOLOGY/modules/`
and `ONTOLOGY/bindings/`, with explicit identity and import locks in `ontology.yaml`.
Stable shared IDs use `urn:sys4ai:ontology:core:` and project IDs use
`urn:sys4ai:ontology:project:<project-id>:`.

Parsing, validation, lexical lookup, typed traversal, source verification and
wiki generation use Python 3.12's standard library. The profile supports its
manifested keys only; it does not resolve remote contexts or provide general
JSON-LD/RDF reasoning. Retrieval defaults to 2 hops and 20 results, with limits
of 8 hops, 100 results and 32,000 UTF-8 bytes. Reads neither repair generated
state nor publish canonical records.

Compile and wiki builds record exact input versions. Derived graph/index/link
outputs live under `.sys4ai/ontology/`; generated Markdown lives under
`ONTOLOGY/WIKI/`. Reviewed publication intents, immutable receipts and bounded
recovery records under `control_records/ontology/` are durable. Ontology authority
is separate from memory grants, Task ownership and capability discovery.

The ontology-owned memory adapter uses current installed read interfaces and
derived sidecars; memory schema v1, corpus, backend and capture settings retain
their existing semantics. Frozen ontology packets use existing Task artifact,
baseline and assignment references, with the same 250,000-byte and 200-reference
limits. Ontology operations create no Task and assign no role.

Initializer edition `governance-starter-v8` specializes a neutral ontology for new
and first-prepared projects. Selected ontology adoption or refresh extends the
existing setup receipt without relabeling earlier editions or overwriting
customized packages. Setup installs no dependency, service, model or product
runtime. The [ontology contract](./ONTOLOGY-depo/profile.md) and
[command reference](./.agents/skills/ontology/references/commands.md) define the
supported operations; [release evidence](./Verification/ontology-first-release/RELEASE.md)
records actual verification.

## Ontology second release and initialization v9

The first-release core and memory/Task schemas retain their existing versions.
`ontology-advanced.yaml` is a separately versioned companion for selected local
standards, inference, semantic, guard, and workbench profiles. Approved extension
documents live in `ONTOLOGY/extensions/`; proposal revisions, reviews, imports,
and publication receipts remain durable under ontology-owned paths.

The standards profile pins RDFLib 7.6.0, pySHACL 0.40.1, and their complete lock in
`.venv-ontology-standards`. It confines workers on the verified Darwin host and
separates asserted, inferred, derived, and external graphs. Its finite rule
profile supports declared type and property semantics; it does not claim full
OWL 2 RL. Read-only SPARQL supports SELECT, ASK, CONSTRUCT, and the documented
DESCRIBE profile. Ordinary reads neither install dependencies nor refresh state.
The depot defines GeneratedWikiPage as an Artifact subtype and identifies its
generated ontology wiki index as an instance; the inferred Artifact type is a
derived conclusion, while the class declaration and source binding stay authored.

Semantic retrieval uses a separately selected local model and environment,
`.venv-ontology-semantic`, with exact model/package/index inputs. Similarity
ranking does not establish identity, truth, approval, or execution authority.
Frozen advanced packets retain the existing Task artifact path/hash interface
and limits. Initial solvers share identical selected bytes and cannot retrieve
new live facts, proposals, models, or documents through that packet.

The second release originally exposed proposal, validation, publication, and
guarded helper interfaces through a loopback browser workbench. That browser
authoring service is now retired. Trusted agent/CLI routes retain their separate
authority checks. Guards cover the declared ontology, memory,
Task, TRD, plan, role, Template, and setup dispatch paths. Current authority and
exact inputs are checked separately from semantic conformance. Direct filesystem
edits and unintegrated host tools are outside that dispatch coverage.

Initializer `governance-starter-v9` supplies neutral advanced profiles without
runtime activation. Earlier receipt editions remain distinct; explicit
`ontology-advanced` adoption uses exact previews and the existing receipt/recovery
model. The Template updater distributes source assets only to its registered
Template. Root adoption is separately manifested; no ordinary product is updated.
See the [advanced contract](./ONTOLOGY-depo/advanced-profile.md),
[operations](./.agents/skills/ontology/references/commands.md), and
[second-release evidence](./Verification/ontology-second-release/RELEASE.md).

## Project Knowledge Explorer and initialization v13

The current browser interface is the read-only Project Knowledge Explorer.
Its installed `explore --open` command serves the reviewed local frontend on
`127.0.0.1` for one server-selected project root. Overview, Terms, Processes,
and Map read canonical knowledge and permitted sources; the browser grants no
authoring or execution authority. Core reads require Python 3.12 and packaged
assets, without activating optional advanced profiles or installing dependencies.

`ontology-explorer.yaml` controls presentation only and must match the project's
identity in `ontology.yaml`. The root uses `sys4ai-depot`; the Template's null
presentation identity stays neutral. An explicitly selected destination may use
the documented absent-file defaults or specialize its presentation configuration.
Existing projects need scoped adoption; neither registration nor Template updates
replace their local packages.

The reading session has no automatic deadline. The Close reading session action
revokes its cookie and request token; service stop or package replacement also
invalidates the session. Closing a tab alone does not revoke it. The one-use
bootstrap still expires after 60 seconds, and pagination cursors retain their
bounded lifetime. Host, Origin, session, CSRF, source confinement, request budgets,
and read-only dispatch remain enforced. Reload can resume an existing session
against the same live service.

Initializer edition `governance-starter-v13` carries the Explorer's static
capability inventory. Earlier setup receipts retain their original editions and
ownership. Setup installs static assets; it starts no reader and provisions no
product environment. [Explorer operations](./.agents/skills/ontology/references/explorer-operations.md)
owns launch and adoption procedures, [the contract](./SKILLS-depo/ontology/references/explorer-contract.md)
owns the wire and resource rules, and [BUILD.md](./.agents/skills/ontology/explorer/BUILD.md)
owns explicit builds. Current package identity is recorded in
[the runtime manifest](./.agents/skills/ontology/explorer/assets/manifest.json).
The original full-release verification remains incomplete under the user's
testing-stop instruction; historical evidence is not upgraded by this documentation.

## Shared agent billboards and collaboration release

The reusable [collaborate skill](./SKILLS-depo/collaborate/SKILL.md) supplies
Task-governed collaboration through immutable participant posts, scoped reads,
reply/correction links, bounded derived views and exact owner snapshots.
Participants use an existing native assignment and a registered manager policy;
posting grants no Task lifecycle, publication or external-action authority.
The common filesystem and actor bindings are cooperative checks, without OS
authentication or raw-filesystem confinement. Initial candidates and assigned
first reviews remain sealed until their independence gates pass.

An immutable collaboration post retains its author, Task/subtask, version,
visibility and source references. A collaboration reading receipt acknowledges
one exact message version; it establishes reported reading rather than independent
comprehension or incorporation. A recipient-observed notification receipt uses
receipt schema 2 for actual addressed-mailbox observation, independently of reading.
Empty sender API returns remain unconfirmed. Message/policy schemas remain 1;
current readers explicitly support receipt schemas 1 and 2.

Material collaboration evidence identifies an affected exact candidate/version.
Current owners assess all material message types; affected reviews, synthesis and
acceptance must pass the existing invalidation and revalidation gates. A
collaboration owner snapshot binds selected visible posts, objections and exact
versions for the responsible senior/manager. It grants no new decision authority.
A pending collaboration knowledge proposal identifies evidence for memory,
ontology or Curator review. A post, reply, acknowledgement or accepted discussion
does not publish knowledge or run maintenance; each system retains its own owner
and publication grant.

PLAN-20260926-40C61316 revision 1 was implemented in completed
TASK-20260926-7F3F57E1, revision 56. The [release evidence](./Verification/shared-agent-billboards/RELEASE.md)
maps 63 requirements and 17 plan tasks. Verification includes focused deterministic
checks, actual governed generic/extra-complex pilots and one original baseline,
scoped aggregation, 53 checked source-to-Template mappings and two disposable
package adoptions. Both original comparison cases met the same semantic criteria;
the single descriptive pair establishes no performance or quality advantage.

The reusable source, neutral Template and depot root now contain the complete
capability. The root installation is enabled through exact package inventory,
reviewed depot-v1 Task-owner compatibility and default Task/Agent Task
collaboration instructions. Its read-only `health` assessment passes. The existing
root Task helper, all canonical Task records, role pairs and root governance
remain preserved; version 1 compatibility grants no version 2 native broker proof.

The current initializer automatically enables collaboration on create and first
prepare-existing, and adds missing capability to the selected earlier completed
setup through its existing module adoption transaction. Base receipt editions,
identity, history, configurations and project-owned content remain preserved.
A complete reviewed package, one whole exact owner profile and default instruction
markers are required. Customized, incomplete or unsupported package/guidance/owner
combinations block enabled readiness without execution or overwrite. Reruns are
idempotent; interrupted collaboration adoption resumes the same frozen operation.
No other registered product is refreshed implicitly.

Static-ready installation enables the default working habit. Each Task manager
still verifies common-store topology, registers its scoped policy, binds exact
baseline/current inputs and supplies participant grants before dispatch. Required
read checkpoints, independent candidate/first-review seals, material owner
assessment and input-before-wake gates remain in force. Setup starts no service,
installs no dependency/model, creates no Task and provides no automatic idle wake.

[Enablement verification](./Verification/collaboration-enablement-20260927/RESULT.md)
covers actual root static preflight, current owner gates, scoped depot-v1 exchange,
initializer create/prepare/earlier-receipt/recovery/idempotence/conflict cases and
exact Source/Template/root adoption. Confined receipts and injected failures are
deterministic evidence. Historical generic V1/extra-complex V2 native results and
current package deterministic/adoption checks remain distinct; this enablement
performs no new native pilot and claims no performance or quality advantage.
See [commands](./.agents/skills/collaborate/references/commands.md),
[Task integration](./.agents/skills/collaborate/references/task-integration.md) and
[knowledge proposals](./.agents/skills/collaborate/references/knowledge-and-maintenance.md).
