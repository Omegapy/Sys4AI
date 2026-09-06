# Initialize memory in a real copied project

**This template is not initialized. Keep it uninitialized.** This guide applies
to a separately selected product copy under this Sys4AI depot's `Projects/`
folder. Do not run initialization against the template directory.

For normal project creation, use the depot's
[init-new-project skill](../../.agents/skills/init-new-project/SKILL.md). Its
`create` route completes preparation and direct memory initialization in one
authorized run. The procedure below covers a clean project that was copied
manually.

## Readiness notice for humans and AI agents

Installing the runtime or completing the default project setup does not make
semantic memory ready. After a successful default initialization and exact recall
check, the handoff is:

> Basic exact/keyword memory is working. Semantic memory is not ready:
> semantic search is disabled, and the Cognee backend and models have not
> been activated for this project.

A merely prepared copy still needs exact-memory initialization and verification.
This notice describes the default. For an existing project, inspect its actual
state; some projects already request semantic operation. Report missing or stale
evidence as unverified instead of claiming the backend is active or inactive.

The agent must tell the human user and leave the same status for the next
project agent in the normal project handoff. Read the real project's
`config/memory.toml`, `control_records/memory/runtime-installation.json` and
matching `.sys4ai/memory/receipts/initialization.json`. Report:

| Check | What it establishes |
| --- | --- |
| Installed package and project identity | Which runtime is installed for this project |
| Exact initialization plus current sync/recall evidence | Whether exact/keyword memory works |
| `semantic_enabled` and resolved model profiles | Whether semantic use is requested and configured |
| Matching provider receipt and current successful semantic operation | Whether Cognee and the model path actually work for this project |

An old receipt, another project's successful test, installed model files or a
true flag alone cannot establish current semantic readiness. Preserve working
exact memory when semantic activation is pending.

If semantic memory is disabled or unverified and no previous decision settles
it, ask the user:

> Would you like me to configure and activate semantic memory and the Cognee
> backend for this project now, or keep exact/keyword memory for now?

Honor an already explicit activation request. Record yes/later/decline in the
normal project handoff without creating a new policy or treating silence as
approval. On later/decline, retain the readiness notice and continue other work;
do not repeat the question every turn. Ask again when the user requests it or
the recorded activation conditions materially change.

For yes, identify the real project and selected local models, explain any model
downloads/services and resource needs, then follow the
[Memory Service readiness and activation guide](../Sys4AI-Memory-Service/docs/operations/memory-readiness-and-activation.md).
The real project's `control_records/memory/README.md` contains a portable
handoff checklist even when the original depot is unavailable. Installation
authority alone does not authorize new model/backend activation.

For an already initialized project, changing configuration can invalidate its
receipt. The current installed workflow has no general configuration-migration
activation command. Report that capability gap and arrange the required scoped
migration work before modifying working configuration. Do not edit/delete the
success receipt, rerun the project initializer over owned files, or claim that
setting `semantic_enabled = true` completes activation. The template remains
uninitialized throughout this process.

## Select the copy and establish its scope

Identify the real project name, stable lowercase project ID, destination,
product purpose and memory-owner principal. Use the user's existing instruction
when it already authorizes preparation, local dependency installation and
memory initialization for that project. Copying the template alone does not
provide that authority; clarify only a missing decision or action boundary.
Git setup, remotes, publication, servers and model activation stay separate.

Create the copy at its final path, preferably a direct `Projects/<name>` child.
Copy only the static starter files in the
[reviewed allowlist](../../SKILLS-depo/init-new-project/assets/baseline-assets.json):
root `AGENTS.md`, `ROLE.md`, `.gitignore`, `README.md`, the generic sub-agent role
bundle, the two static implementation contracts, an empty `Tasks/INDEX.md`, and
this guide. If a manual copy already contains the six baseline packages and
`SOUL.md`, the shared preparation helper inspects them before adoption.

Never copy Git directories, Git gitfiles, `.gitmodules`, history, `.venv`,
`.ruff_cache`, other caches, `.DS_Store`, bytecode, `.sys4ai`, provider databases,
models, logs, credentials or old project records. This template checkout may
have development tools such as `.venv` and `.ruff_cache`; they are excluded
transient files, not starter content. An existing copy containing such runtime
state needs a separate ownership review. Do not delete it automatically.

## Use the shared preparation route

Run the following from the **Sys4AI depot root**, replacing every example value
with the selected copy's real identity and absolute paths:

```bash
.venv/bin/python .agents/skills/init-new-project/scripts/init_new_project.py prepare-existing \
  --destination "/absolute/path/to/Sys4AI/Projects/YourProject" \
  --project-id your-project-id \
  --project-name "Your project name" \
  --purpose "The product purpose, intended users and scope." \
  --principal-id your-memory-owner \
  --artifact-receipt "/absolute/path/to/Sys4AI/Projects/Sys4AI-Memory-Service/dist/consumer/VERSION/SOURCE_MANIFEST_HASH/artifact.json"
```

Use the exact immutable artifact receipt produced by the registered
[Memory Service builder](../Sys4AI-Memory-Service/tools/build_consumer_artifact.py).
If `--artifact-receipt` is omitted, the shared helper invokes that builder for
the registered product. It verifies the wheel hash and locked dependencies;
do not edit an artifact receipt or use an editable sibling-source installation.

The helper performs the same preparation used by canonical creation:

1. Validate the destination, identity, sources and factual depot registry.
2. Specialize `README.md` and `project.json` with the supplied product context.
3. Adopt exactly `agent-task`, `communication`, `manage-subagent-roles`, `task`,
   `to-implementation-plan` and `to-trd` from the current
   [SKILLS-depo sources](../../SKILLS-depo/), plus
   [SOULS-depo/SOUL.md](../../SOULS-depo/SOUL.md). Do not assume the template's
   embedded copies equal current depot versions. Source and destination hashes
   record the reviewed adoption; later source changes do not update this copy.
4. Register the actual project path and identity through the shared atomic
   registry operation. Registration records inventory and observed repository
   state; it does not set up Git or infer an ancestor repository as this project.
5. Install the exact wheel into the copy's own `.venv` at its final path. Never
   move an installed environment or reuse the template's environment.
6. Call the installed Memory Service's common preparation procedure to create
   canonical configuration, registries, profiles, schemas and permissions, and
   append the required ignore protections.

The route does not recopy the project tree. It preserves unrelated files and
replaces baseline files only when they match the inspected template or source
copies. Project-customized conflicts stop for a separate, exact review.

## Run one direct initialization command

Successful preparation returns `status: prepared`, a `next_command` argument
list and its shell-quoted `next_command_shell` equivalent. Inspect the recorded
project path, project ID, dataset ID, principal, package version and wheel hash.
Execute that returned **direct `init-memory` command once** for the authorized
copy. Use the shared installed command; do not implement another bootstrap path
or import Cognee directly. There is no preview command or intermediate approval
pause in this manual route.

The common initializer validates the configured project boundary and canonical
resources before writing derived memory. Its receipt distinguishes exact-index
initialization from semantic-provider or model activation. The baseline enables
exact retrieval; semantic capabilities and model downloads are deferred.

Preparation writes these project-owned files and runtime references:

| Output | Meaning |
| --- | --- |
| `project.json`, `README.md` | Actual product identity and context |
| `.agents/skills/`, `SOUL.md` | Six reviewed baseline packages and soul |
| `.venv/` | This project's installed immutable runtime |
| `control_records/project-initialization.json` | Preparation stages, adopted hashes and factual registration |
| `control_records/memory/runtime-installation.json` | Installed version, wheel hash and package origin |
| `config/memory.toml`, `registries/`, `profiles/`, `schemas/memory/`, `control_records/memory/` | Canonical project-local Memory System resources |

Direct initialization creates `.sys4ai/memory/`, including the exact index and
`receipts/initialization.json`; subsequent operations keep audit records and
other derived state inside that boundary. The preparation record still describes
preparation. Read the separate initialization receipt for the actual initialized
state. No credential values belong in either record.

## Verify functional memory

From the **real copied project's root**, use its installed executable and the
same identity returned by preparation. Replace the example values below:

```bash
memory_command=(
  .venv/bin/sys4ai-memory
  --project-root "/absolute/path/to/Sys4AI/Projects/YourProject"
  --project-id your-project-id
  --dataset-id your-project-id-memory
  --principal-id your-memory-owner
  --agent-type project-initializer
  --run-id manual-verification
)
"${memory_command[@]}" sync --idempotency-key manual-first-sync
"${memory_command[@]}" recall your-project-id --mode exact
```

Require successful JSON responses, zero synchronization failures and nonempty
exact results citing this project's sources. Reopen the cited canonical file,
such as the specialized `README.md`, and confirm the real identity and purpose.
Directories alone do not establish usable memory. Keep the configuration,
permissions, namespace and dataset local to this project.

## Conflicts, reruns and recovery

An equivalent `prepare-existing` rerun verifies existing assets, registry and
runtime without duplicate adoption or installation. It does not silently take
newer source versions or rerun initialization. A changed destination, package,
identity or project-owned file requires a separate review.

A partial result reports completed stages, the failed stage and the exact owned
state. Inspect `control_records/project-initialization.json` before repeating
the same command to resume. Preserve unrelated files and do not substitute
another project ID, artifact or destination during recovery. If the returned
direct initialization fails, inspect its structured result and local receipt;
after resolving the reported cause, retry the same identity and idempotency key.
Do not delete state or activate models as an improvised repair.

Keep this generic template unchanged by those product operations. Its absence
of project-specific memory configuration and derived state is checked by
[the template contract tests](../Sys4AI-Template-Project/tests/test_template_contract.py).
