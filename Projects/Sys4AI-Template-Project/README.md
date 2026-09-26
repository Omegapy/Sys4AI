# Sys4AI Template Project

This directory is the governed starter for a new Sys4AI product project. It
provides a project-local soul, a generic Project Director, reusable sub-agent roles,
project-local Task and TRD skills, and the contracts that keep those systems
testable. It does not define the future product, repository remote, or GitHub
Pages site.

For project specifications, see [SPECS.md](./SPECS.md).

The template's [LICENSE](./LICENSE) routes code to [Apache 2.0](./LICENSE-CODE)
and documents to [CC BY 4.0](./LICENSE-DOCS). Both initialization routes include
the complete trio for projects without existing licensing. Existing project
license systems remain project-owned and are preserved as a whole.

This template is maintained from the parent's reusable `*-depo` sources through
the [automatic update pipeline](../../depot/template-update.md). Edit reusable
content in its mapped source collection. The template is the sole source of
starter assets for creation and missing assets in existing-project setup. Each
resulting product copy is project-local and receives no automatic updates.

## Start a new Sys4AI project

Use the depot's [init-new-project skill](../../SKILLS-depo/init-new-project/SKILL.md)
with the real product name, stable ID, purpose, and destination.
The `create` route specializes this Template's starter files, complete skill
and role packages, reference assets, and soul, then records factual inventory.

For a manual copy or a customized existing project, use the same helper's
`prepare-existing` route. It adopts missing assets while preserving customized
files and existing identity. Both routes record checked setup stages and source
hashes in `control_records/project-setup.json`; equivalent reruns avoid duplicate
registration. Runtime dependencies and environments are prepared separately for
the real product. Keep Git setup and publication separate.

Copy only reviewed static starter files; exclude environments, caches, Git
metadata, and derived state. Add product source, tests, and domain guidance
through the project's own authorized work.

Do not keep the template name for a product. Do not invent repository or Pages
values before they are configured and verified.

## Template and project-owned files

The template currently includes these project-local categories:

- `SOUL.md`
- `AGENTS.md` and `ROLE.md` template variants
- `LICENSE`, `LICENSE-CODE`, and `LICENSE-DOCS`
- the bounded `project-sub-agent` and confirmed `task-manager` role bundles
- a deterministic `Roles/INDEX.md` generated from those authoritative pairs
- complete shared skill packages under `.agents/skills/`
- the role-system and Task-system implementation contracts

The reusable root collections may contain similar source material, but matching
content creates no automatic relationship. This README, Task records, TRD
records, product code, credentials, build output, repository configuration, and
publication settings are also project-owned.

## Agent roles

The root [AGENTS.md](./AGENTS.md), [SOUL.md](./SOUL.md), and
[ROLE.md](./ROLE.md) define shared guidance and the generic Project Director.
Reusable roles live in [Roles](./Roles), with generated [navigation](./Roles/INDEX.md)
and one
`AGENTS.md` and one `ROLE.md` per role.

The Project Director uses the repository-local
[manage-subagent-roles skill](./.agents/skills/manage-subagent-roles/SKILL.md)
to inventory the live role catalog, select or create a suitable role, and
delegate bounded work through native Codex sub-agent orchestration.

Every team member retains the confirmed manager's exact model and reasoning
effort. Verify that inheritance separately from independent solver context.
The responsible Director reviews
and verifies child evidence before integration.

## Requirements and implementation

For non-trivial work:

1. Capture the user's intended outcome, constraints, exclusions, and acceptance
   criteria.
2. Create source-linked requirements.
3. Create a detailed implementation plan that maps each requirement to work and
   evidence.
4. Implement the complete authorized scope.
5. Test, verify every requirement, and validate the user-relevant workflow.

The explicit [To-TRD skill](./.agents/skills/to-trd/SKILL.md) can manage a Task
Requirement Document when the user invokes `$to-trd`. A TRD does not implement
its requirements or create Task state.

## Tasks

The project-local Task system keeps a durable work record that can continue in
a later Codex thread. A Task is a project objective with a stable ID; it is not
a Codex thread, native goal, or TRD. The user-facing
[Task skill](./.agents/skills/task/SKILL.md) routes explicit requests, and the
Project Director uses the internal
[Agent Task skill](./.agents/skills/agent-task/SKILL.md) to maintain state.

Use these prompts:

```text
$task new Name: <name>; Description: <objective>; Done when: <criteria>
$task continue <task-id-or-exact-name>
$task status
$task list
$task update <task-id> <approved change>
$task pause <task-id>
$task complete <task-id>
$task cancel <task-id>
$task reopen <completed-task-id>
```

Each Task lives directly under [Tasks](./Tasks). The canonical record is
`task.json`; `TASK.md` and `Tasks/INDEX.md` are generated views. Ordinary child agents
return evidence, while the Project Director owns Task state and final Task
Responses.

## Local verification

Run the focused contracts from this project root:

```bash
.venv/bin/python -m unittest discover -s .agents/skills/agent-task/tests -v
.venv/bin/python -m unittest discover -s .agents/skills/manage-subagent-roles/tests -v
.venv/bin/python -m unittest discover -s .agents/skills/to-trd/tests -v
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
```

These checks verify local package behavior. They do not prove that the template
has been specialized, published, or exercised in a live product environment.

## Task-manager execution

Authorized Task execution uses a real native manager distinct from the host.
Bootstrap reserves it, records its actual receipt and transfers the sole
canonical writer at activation. Generic work uses one worker; complex work uses
independent solvers and a distinct senior; extra-complex work also assigns one
reviewer per solver. Current passes and coherent manager acceptance precede
a dedicated implementation child when multi-solution work needs authorized changes.

Read the [orchestration contract](./.agents/skills/agent-task/references/orchestration-contract.md)
for actual helper payloads, version and recovery gates. Historical schema-1
Tasks remain readable; upgrade only an explicitly selected record. Role legacy
transition and index repair use the [role skill](./.agents/skills/manage-subagent-roles/SKILL.md).
New starter projects contain no active Task execution, native IDs or copied live
history. The depot root's automatic intake and inactivity closure are separate
local policies; this Template keeps its explicit selection policy.

## Project memory starter

The [memory skill](./.agents/skills/memory/SKILL.md), [record contracts](./reference-assets/MEMORY-depo/README.md),
[empty memory directory](./MEMORY/README.md) and [configuration](./memory.yaml)
provide portable project memory. The Template contains no learned records and
its identity remains neutral. Initializer edition `governance-starter-v8`
specializes a new project's memory identity, enables automatic capture and binds
its local Director. Setup reports that capture is on and asks whether to turn
it off. Existing choices, learned memory and older setup receipts are preserved. Direct Markdown and lexical lookup need no backend.
The optional local backend and model are provisioned through separate explicit
work; setup does not install or activate them. Frozen Task inputs and scoped
publication follow the memory skill's existing integration contracts.

## Learning starter

The [What Did You Learn skill](./.agents/skills/what-did-you-learn/SKILL.md) uses
the [module contracts](./reference-assets/LEARNING-depo/README.md) and the memory
skill's [shared completion checkpoint](./.agents/skills/memory/references/automatic-capture.md).
Ask "What did you learn?" for an evidence-based review, including a valid
no-durable-lesson result. The question alone permits no save or project change.
Automatic persistence follows the existing preference and current owner/grant;
capture off preserves explicit review and authorized save behavior.

Edition v7 and later supply this capability by default for new and first-prepared
projects. Existing prior-edition projects use the selected depot initializer's
`prepare-existing --adopt-module what-did-you-learn` route. Explicit
`--refresh-dependency memory` may refresh complete unchanged receipt-owned
dependencies; custom packages, project content and learned history remain
preserved. Ordinary reruns retain their original setup edition. The existing
setup receipt records module adoption and checked recovery. See the
[initializer guide](./.agents/skills/init-new-project/README.md) for exact usage.
This starter contains no learned records, active grant or runtime hooks.

## Ontology starter

The [ontology skill](./.agents/skills/ontology/SKILL.md), [profile](./reference-assets/ONTOLOGY-depo/profile.md)
and [neutral configuration](./ontology.yaml) provide locked core concepts with
empty local project and binding graphs under `ONTOLOGY/`. Initializer edition v8
specializes project ID, name, purpose, namespace and local Director authority.
Ontology operations use Python's standard library and do not require a service.

Earlier completed projects select `prepare-existing --adopt-module ontology`.
Explicit `--refresh-module ontology` accepts only complete unchanged receipt-owned
installations. Customized and incomplete installations stay whole; ordinary
reruns retain their original setup edition and locked imports. Use the initializer
`assess-ontology` route for static configuration/import/binding checks and the
installed ontology `health` command for semantic and source readiness. Canonical
publication still needs its exact current operation grant. The Template contains
no project definitions, instances, grants, generated wiki or runtime state.

## Project Knowledge Explorer starter

The Template includes the read-only Explorer package. Its presentation
configuration is neutral and cannot launch as the depot; a real project uses
its own ontology identity and selected configuration. Installation starts no
service and installs no runtime dependencies.

See [the Explorer specifications](./SPECS.md#project-knowledge-explorer-and-initialization-v13)
and [operations guide](./.agents/skills/ontology/references/explorer-operations.md)
for launch, configuration, session closure, and scoped existing-project adoption.
The former browser authoring workbench is retired; trusted proposal and
publication commands retain separate authority checks.

## Project Curator starter

The [Curator skill](./.agents/skills/curate/SKILL.md), [charter](./CURATOR.md),
[neutral configuration](./curator.yaml), [document ownership](./document-ownership.json)
and [application contract](./reference-assets/CURATION-depo/contract.json)
coordinate selected project maintenance through the existing owners. Four paired
Curator roles appear in the generated Roles index. The Template carries no live
Task, grant, queue history, project-specific knowledge, enabled schedule or service.

Initializer v10 binds destination identity while leaving runtime and standing
permissions disabled. Existing projects adopt Curator only through the explicit
initializer module route; their base setup, licensing, custom packages, role
provenance and capture preference remain project-owned. `$curate` status and
scoped review read metadata without model analysis or canonical writes. Exact
manual and automatic mutations share current owner and authorization gates.
Static/disposable checks do not establish native runtime or host-service readiness.
