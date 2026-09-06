# Memory control records for Sys4AI depot

These are project-owned canonical control files for `sys4ai-depot`, dataset
`sys4ai-depot-memory`. The explicit caller `sys4ai-depot-director` owns the bounded
initialization, synchronization and read grants. These grants confer no
approval, deletion, cross-project access, publication or general source-write
authority. Source-registration authority is a separate preparation option and
uses the existing reviewed registration operation.

Preparation writes configuration and validates its complete reference closure.
It does not initialize storage, import a native provider, start a server, or
load or download a model. Run the installed runtime's `init-memory` command
with this project's identity and caller to initialize exact storage. Both the
new-project and manual-template procedures use this preparation API and the
same direct initializer. The root adoption route may use its reviewed
initialization operation after the same preparation.

The default `base@1` profile supports exact and lexical recall. The packaged
software-engineering profile is optional; semantic models and graph behavior
remain deferred until explicitly configured and authorized. Its A3 behavior
references require a trusted profile-source authority assignment.

## Readiness handoff for the human and AI agent

The prepared default is `semantic_enabled = false`: semantic memory is not
ready and this preparation has not activated the Cognee backend. Exact memory
finds identifiers and keywords; semantic memory finds related meaning using
the backend and models. Installation, exact initialization and verified
semantic retrieval are separate states. Inspect this project's current state
before using those labels, because an existing project may have changed its
configuration or completed activation since preparation.

At installation handoff, when taking over memory work, and before semantic use:

1. Read `config/memory.toml` and the normal project handoff for previous
   activation decisions. Validate the configuration with this project's
   installed runtime. Missing or invalid configuration means readiness is
   unknown, not ready.
2. Inspect `control_records/memory/runtime-installation.json` if present for
   installation provenance. Inspect the initialization receipt under the
   configured local data directory. It must match the current project ID,
   dataset ID and configuration fingerprint. An absent or stale receipt does
   not prove that memory or the backend is ready.
3. Distinguish the initialization fields: `exact_index_initialized = true`
   records storage creation; `provider_initialized = false` in a matching
   receipt records that Cognee was not activated by initialization. A true
   provider field records a past initialization, not current model readiness.
   The current initializer writes `models_activated = false`; do not edit it.
4. Check current sync and source-backed exact/keyword retrieval evidence before
   calling exact memory working. Semantic readiness also needs approved models
   and successful real semantic sync/recall in this project, with actual
   provider participation, cited canonical sources and project isolation.
   A true flag, `health` response, other project's test or exact fallback is
   insufficient. Retain the configuration fingerprint, versions, date and
   verification result in the normal handoff.

This read-only command, run from the project root, reports configuration and
receipt metadata without importing Cognee, starting services or downloading
models. It does not exercise retrieval or certify readiness:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -I - <<'PY'
import json
from pathlib import Path
from sys4ai_memory.configuration import load_configuration
from sys4ai_memory.util import resolve_within

root = Path.cwd().resolve()
loaded = load_configuration(root / "config/memory.toml", trusted_project_root=root)
memory = loaded.configuration.memory
relative = (loaded.resolved_paths["local_data"] / "receipts/initialization.json").relative_to(root)
path = resolve_within(root, relative, must_exist=False)
receipt = json.loads(path.read_text()) if path.is_file() else None
if receipt is not None and not isinstance(receipt, dict):
    raise ValueError("Invalid initialization receipt; readiness is unknown")
matching = bool(receipt and receipt.get("project_id") == memory.project_id
                and receipt.get("dataset_id") == memory.provider.cognee.dataset
                and receipt.get("configuration_fingerprint") == loaded.fingerprint)
print(json.dumps({
    "project_id": memory.project_id,
    "dataset_id": memory.provider.cognee.dataset,
    "configuration_fingerprint": loaded.fingerprint,
    "semantic_enabled": memory.models.semantic_enabled,
    "receipt_matches_configuration": matching,
    "exact_index_file_present": loaded.resolved_paths["exact_index"].is_file(),
    "receipt_flags": {key: receipt.get(key) if receipt else None for key in
                      ("exact_index_initialized", "provider_initialized", "models_activated")},
    "retrieval_verified_by_this_check": False,
}, indent=2))
PY
```

If the runtime is missing or this check fails, report the missing/invalid
evidence; do not initialize memory as an inspection shortcut. Interpret receipt
flags only when the receipt matches. A matching receipt still needs current
functional checks. Do not copy configuration contents or secrets into reports.

When exact retrieval has been verified and the matching receipt confirms the
default inactive backend, tell the human:

> Exact/keyword memory is working. Semantic memory is disabled and is not ready;
> the Cognee backend has not been activated for this project.

If exact retrieval has not been checked, say so. If semantic configuration is
enabled but verification is missing, report "Semantic memory is configured;
current semantic and Cognee readiness are unverified." Do not report an
inactive backend when its state is unknown.

Unless the user has already decided, ask:

> Would you like me to configure and activate semantic memory and the Cognee
> backend for this project now, or keep exact/keyword memory for now?

Record yes, later or decline in the normal project handoff, with the observed
state and next action for the human and future agents. Honor existing authority
without asking again. Later or decline preserves the current configuration;
no answer leaves the choice undecided. Give any first-use notice briefly,
continue unrelated work and do not repeat the question on every startup.

## If activation is requested

Inspect this project's installed artifact, approved local model profiles,
source exclusions, permissions and private model/cache paths. Any required
provider dependencies, model resources or local process startup must fit the
authorized scope. Prepare the proposed settings and verification steps; Git,
publication and cross-project changes remain separate.

For a project with no initialized or partial derived store, validate its chosen
profiles and use its authorized initialization route: the installed
`sys4ai-memory` supports `init preview` then `init apply --impact-digest` with
the reviewed digest and current identity/permission, or `init-memory` for an
authorized direct bootstrap. After initialization, sync reviewed sources and
verify actual semantic retrieval, exact retrieval and isolation. Provider
initialization alone is not semantic verification.

For an already initialized exact-only project, stop before changing live
settings: configuration changes invalidate the fingerprint-bound initialization
and sync receipts. The current runtime has no general installed command that
migrates an existing exact-only consumer to semantic memory. After a yes
decision, prepare a bounded migration/reinitialization proposal that preserves
canonical sources and the current working state, and report the missing
supported migration path as the next implementation action. Do not invent an
`activate` command, edit/delete success receipts, wipe the memory directory or
rerun initialization expecting it to accept a changed fingerprint. If state is
partial or unfamiliar, inspect and plan recovery before any activation.

All generated indexes, provider databases, caches, logs, model caches and
initialization receipts belong below `.sys4ai/memory/`. They are disposable and
ignored. An initialization receipt is created by the shared initializer only
after actual storage initialization succeeds; this directory contains no
pre-filled success receipt.

Later files and folders remain excluded unless reviewed source registration
admits them. Registering a folder cannot raise its authority or authorize
writes, installs, Git operations or external action.
