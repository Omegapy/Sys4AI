# Sys4AI Template Project

This directory is the governed starter for a new Sys4AI product project. It
provides a project-local soul, a generic Project Director, reusable sub-agent roles,
project-local Task and TRD skills, and the contracts that keep those systems
testable. It does not define the future product, repository remote, or GitHub
Pages site.

For project specifications, see [SPECS.md](./SPECS.md).

**Memory is not initialized in this template.** For a real project copied
manually, follow [Initialize memory in a copied project](./INIT_MEMORY.md).
The guide uses the depot's shared preparation helper and one direct
initialization command for the selected copy.

The software package is `sys4ai-memory-service`, maintained at
[Sys4AI-Memory-Service on GitHub](https://github.com/Omegapy/Sys4AI-Memory-Service).
Each real project installs its own copy and stores its own memory. The guide's
[package location and GitHub clone section](./INIT_MEMORY.md#package-location-and-github-clones)
explains local wheel installation, published dependencies, and what a recipient
must set up after cloning. Repository existence alone does not supply a package.

**After default setup in a real project, semantic memory is still not ready.**
Basic exact/keyword memory can work while semantic search is disabled and the
Cognee backend/models remain inactive. The guide tells both the human and AI
agent how to check the actual state, report it clearly, and ask whether to
activate semantic memory. Existing projects must check their current settings
and evidence rather than assume the default or treat an enabled flag as proof.

All files in this template are project-local. Reusable collections in the
parent Sys4AI workspace are optional inputs and do not update the template. A
future adoption or refresh must identify the exact source, destination, and
overwrite boundary, then run this project's local checks.

## Start a new Sys4AI project

Use the depot's [init-new-project skill](../../.agents/skills/init-new-project/SKILL.md)
with the real product name, stable ID, purpose, destination and memory owner.
Canonical creation specializes a clean starter, adopts the six current baseline
packages and soul, records factual inventory, installs the exact runtime and
initializes project-local memory in the same authorized run.

If the project was copied manually, use [INIT_MEMORY.md](./INIT_MEMORY.md).
Copy only the reviewed static starter files; exclude the template's development
environment, caches, Git metadata and derived state. The manual preparation
route preserves unrelated copied-project files and refreshes only the reviewed
baseline assets. Add product source, tests and domain guidance through the
project's own authorized work. Keep Git setup and publication separate.

Do not keep the template name for a product. Do not invent repository or Pages
values before they are configured and verified.

## Template and project-owned files

The template currently includes these project-local categories:

- `SOUL.md`
- `AGENTS.md` and `ROLE.md` template variants
- the generic `project-sub-agent` role bundle
- complete shared skill packages under `.agents/skills/`
- the role-system and Task-system implementation contracts

The reusable root collections may contain similar source material, but matching
content creates no automatic relationship. This README, Task records, TRD
records, product code, credentials, build output, repository configuration, and
publication settings are also project-owned.

## Agent roles

The root [AGENTS.md](./AGENTS.md), [SOUL.md](./SOUL.md), and
[ROLE.md](./ROLE.md) define shared guidance and the generic Project Director.
Reusable sub-agent roles live in [sub-agent-roles](./sub-agent-roles), with one
`AGENTS.md` and one `ROLE.md` per role.

The Project Director uses the repository-local
[manage-subagent-roles skill](./.agents/skills/manage-subagent-roles/SKILL.md)
to inventory the live role catalog, select or create a suitable role, and
delegate bounded work through native Codex sub-agent orchestration.

Every role-based child inherits the Director's exact model and reasoning effort.
A role changes instructions and scope, not model settings. The Director reviews
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
`task.json`; `TASK.md` and `Tasks/INDEX.md` are generated views. Child agents
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
