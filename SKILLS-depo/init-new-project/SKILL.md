---
name: init-new-project
description: Create a new project beneath this Sys4AI depot's Projects folder from its registered template, or prepare an explicitly selected clean manual copy, with the six baseline skills and isolated local memory.
metadata:
  version: 1.0.1
---

# Initialize a Sys4AI project

Use the deterministic [helper](scripts/init_new_project.py) for a user-authorized
project creation or manual preparation. A request to explain or plan this process
is read-only. Automatic skill discovery does not itself authorize file changes.

Obtain the real destination, stable project ID, project name, product purpose,
and memory owner principal from the user's request or established context. A
missing product decision is a reason to clarify; an already authorized creation
does not need another confirmation. Keep credentials out of all these inputs.

The helper determines the depot from its own installation under
`SKILLS-depo/init-new-project/` or `.agents/skills/init-new-project/` and validates
`depot/projects.json`. In the Sys4AI workspace this constrains destinations to
`/Volumes/P-SSD/AngryOwl/Sys4AI/Projects/`. There is no external depot or template
override. It rejects source projects, overlapping registrations, traversal,
symlinks, ID collisions and occupied creation destinations before publication.

The fixed sources are:

- Template: `Projects/Sys4AI-Template-Project/`, registered as
  `sys4ai-template-project` with kind `project-template`.
- Exactly six complete packages from `SKILLS-depo/`: `agent-task`,
  `communication`, `manage-subagent-roles`, `task`, `to-implementation-plan`,
  and `to-trd`.
- Soul: `SOULS-depo/SOUL.md`.
- Runtime: the immutable consumer wheel built by the registered
  `Projects/Sys4AI-Memory-Service/tools/build_consumer_artifact.py`.

The [allowlist](assets/baseline-assets.json) supplies only static starter
guidance, the generic role bundle, two workflow contracts and an empty Task
index. It includes the template's `INIT_MEMORY.md` when present. Template Git
directories/gitfiles, environments, old work, caches, model files, derived memory
and unknown files are never copied. The README and `project.json` receive the
actual project identity. Local links in the copied manual guide are rebased to
the same depot assets for deeper destinations; the receipt keeps both original
source and specialized destination hashes. Future depot assets remain optional
project adoptions.

## Canonical creation

Run the installed helper with the depot's Python 3.12 environment. Use explicit
arguments rather than assembling shell text from the user's values:

```text
python scripts/init_new_project.py create
  --destination ABSOLUTE_PROJECT_PATH
  --project-id lowercase-hyphenated-id
  --project-name PROJECT_NAME
  --purpose PRODUCT_CONTEXT
  --principal-id MEMORY_OWNER
  [--artifact-receipt EXACT_RECORDED_ARTIFACT_JSON]
```

An explicit artifact receipt must be beneath this depot's registered Memory
Service `dist/consumer/`. Without that argument, the approved builder creates a
versioned local artifact. Building and installing the isolated runtime are part
of the requested canonical creation; Git, remotes, publication, credentials,
network services and semantic model activation have separate authority.

One execution specializes the project, adopts the reviewed assets, records its
factual registration, installs the exact non-editable wheel in the final
destination's `.venv`, invokes installed
`python -I -m sys4ai_memory.bootstrap prepare`, and calls installed
`sys4ai-memory ... init-memory` directly once. The common Memory Service code
owns configuration validation and initialization. Do not reproduce it or import
Cognee from this skill. The same execution synchronizes registered sources and
verifies exact recall from a separate installed process.

Read the JSON result. Success means `status: completed`, with the actual wheel
hash, version, installation origin, project/dataset IDs, source/destination
hashes, checks and functional memory evidence. The final receipt is
`.sys4ai/memory/receipts/project-initialization.json`; its durable operation
record is `control_records/project-initialization.json`. Exact retrieval is
initialized. Semantic provider/model activation is explicitly deferred. A
`completed` creation result does not mean semantic memory is ready. Give the
readiness handoff below before closing the conversation.

## Manual copied-project preparation

Use `prepare-existing` with the same identity arguments only after the user
selects and authorizes the real clean copied project. It uses the same identity,
asset, registry, installer and canonical-memory preparation functions. It never
recopies the tree. Existing baseline files may be replaced only when they match
the inspected template or current source; customized conflicts stop first.
Unrelated project files remain intact.

The result is `status: prepared`, with `next_command` as an exact argv list and
`next_command_shell` for a human terminal. Execute that one direct `init-memory`
command under the user's manual initialization authority, then use the installed
`sync` and `recall --mode exact` commands to check functional memory. A prepared
receipt does not claim initialization. The generic template remains uninitialized.

## Required readiness handoff to the user and the project agent

After installation, preparation, initialization, or a readiness check in an
existing project, read that project's current `config/memory.toml`, installed
package metadata and matching initialization receipt. Distinguish installation,
verified exact/keyword memory, the semantic setting, and verified Cognee/model
operation. Missing or stale evidence means unknown/unverified. A true setting
or a successful creation receipt alone is not proof of semantic readiness.

For the default successfully initialized consumer, state plainly:

> Basic exact/keyword memory is working. Semantic memory is not ready:
> semantic search is disabled, and the Cognee backend and models have not
> been activated for this project.

For a merely prepared project, say that exact memory still needs initialization
and verification. For an existing project, report its observed state instead of
repeating the default notice. Always include the next step and point both the
human and incoming project agent to `INIT_MEMORY.md` and
`control_records/memory/README.md` in that project.

When semantic/backend readiness is disabled or unverified and the user has not
already decided, ask:

> Would you like me to configure and activate semantic memory and the Cognee
> backend for this project now, or keep exact/keyword memory for now?

Honor an existing activation instruction without asking again. Record a yes,
later or decline in the normal project handoff/work record; an unanswered
question is not consent. Keep a deferred choice visible without repeating the
question on every turn or blocking unrelated work. Never activate models as a
side effect of this notice or rerun.

If activation is requested, inspect the project's supported activation path and
model prerequisites first. For already initialized projects, a configuration
change can invalidate the initialization receipt. Do not prescribe a bare
boolean flip, delete/edit receipts, or invent an activation command. Use the
documented project activation procedure and report a missing migration capability
as a concrete blocker while preserving working exact memory.

## Reruns and recovery

An identical completed or prepared rerun verifies saved asset/configuration
hashes, registry identity and installed wheel bytes. It performs no duplicate
registration, asset refresh, installation or memory operation. Later source edits
do not change project-owned copies. Refreshing those copies is a separate action.

A partial result reports the failed stage, completed stages, observed owned
files and environment/memory presence. Inspect the operation record and repeat
the identical command to resume. A lock indicates an active or interrupted
coordinated operation; inspect its ownership and process state before separate
recovery. Never delete unrelated work, silently accept source drift, rewrite a
customized conflict, or claim that a directory proves functional memory.

See [README.md](README.md) for the package's verification commands and evidence
limits. Source publication and active skill adoption are separate operations.
