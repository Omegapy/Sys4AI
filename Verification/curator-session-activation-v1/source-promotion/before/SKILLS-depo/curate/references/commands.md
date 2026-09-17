# Command routes

Use the selected project interpreter and its installed `scripts/curator.py`.
`status --policy /absolute/project/curator.yaml` reports existing configuration and
pending metadata. `review --policy ... --scope path` restricts notices to the
requested paths; repeat scope for multiple paths. This standalone metadata view
reports `analysis_performed: false`. Neither invokes a model,
creates a Task or writes canonical state. `validate --policy ...` checks schema.

`update`, `correct`, `retry`, `pause` and `resume` accept `--policy` and an exact
`--selection` JSON file with operation ID, payload digest and payload. Standalone
commands return `held: authenticated_application_required` with a nonzero exit;
the file is not authority. The embedding host constructs `Application` with its
existing Broker or `None`, explicit `policy_path`, `accepted_operations`, `task_owner` and
`task_folder`. Candidate integration and product routes additionally select their
existing owner and exact reviewed arguments. Product helper modules are supplied
as `product_owners`, keyed by `memory_maintenance`, `ontology_build` or
`ontology_wiki`; `product_arguments` are keyed by exact selected operation ID. `Application.run` uses one route for
manual and automatic selections and retains actual owner results.

Pause and resume select existing Task stop, resume and lifecycle operations, with
runtime interruption/reconciliation handled by its existing owner. Application
status reads canonical Task state; it creates no separate pause record and does
not equate an interruption request with confirmed stopping.

For an explicit bounded source-ownership review, the selected host calls
`Application.review(affected_paths=paths, request=request, actor=actual_actor)` with
an accepted `target.classify` operation of permission class `analysis` and exact
payload `{"analysis":"source-ownership","paths":["selected/path"]}`. It reads
the exact selected source bytes, checks their ownership/section routing, and
returns source identities and classifications. The maximum is 50 distinct paths,
2 MB per source and the smaller of 8 MB or the accepted byte budget overall.
It issues no write grant and performs no canonical writes or model analysis.
Other analyses are not implied by this fixed analysis selection.

Status is observation, pending is unfinished obligation, unavailable means a
required current resource cannot be observed, and blocked means a known scope,
owner or authority conflict. Installed/inactive and selected/unverified are not
runtime-ready. An exact retry retains the original operation and journal while
using fresh authentic recovery transport. Aborted maintenance may be reconciled
and consumed while its products still require a separate subsequent rebuild.

`tick --selection /absolute/selected.json` computes due status for the exact policy
hash and existing scheduling state. It cannot activate native work on its own.
The operational `Application.tick` embedding receives an actual selected actor
(or an existing Broker callback) and
fresh host-selected usage/runtime evidence, then uses the same owner route. It
checks finite iterations, remaining budgets and unavailable-runtime holds; see
[scheduling](../../../CURATION-depo/scheduling.md). A standalone actor/session
wake bridge remains incomplete and is not synthesized from selection JSON.
See [conversation](conversation.md) for contextual selection and the unchanged
summary-first log commands in [SKILL.md](../SKILL.md).

The host can use `Application.log_context(handle)` for outgoing agent context.
It contains a bounded summary, the stable handle and query instructions. Use
`log.query` with `projection: events` for event metadata or `tool_output` for
ordinary text and detailed tool output. Full log files remain local; query
responses retain their configured byte, match and excerpt bounds.

## Fixed direct owner calls

Supply actual helper modules in `operation_owners` and exact JSON keyword
arguments in `operation_arguments[operation_id]`. The selected operation binds
`owner_arguments_sha256`, `payload_sha256`, `automatic` and its current
`task_binding` (`task_id`, `revision`, `execution_id`, `generation`). Call
`Application.run(action, request, actor=actual_current_actor, origin=origin)`.
The caller returns the actual owner result unchanged. A supplied Broker keeps
its existing callback route when no direct arguments are selected for that
operation. These embedding inputs are supplied by the current owner, not loaded
as authority from a model-written request file.

| Operation | Existing public owner | Exact selected keyword arguments |
| --- | --- | --- |
| `task.event` | `task_state.response_transaction` | `command: orchestrate`, `project_root`, `tasks_root`, `selector`, `expected_revision`, `raw_payload` |
| `task.response` | `task_state.response_transaction` | `command: record-response` or `pause`, `project_root`, `tasks_root`, `selector`, `expected_revision`, `raw_payload` |
| `task.recover` | `task_state.command_reconcile` | `project_root`, `tasks_root`, `selector`, `expected_revision`, `raw_payload` selecting the original `transaction` |
| `memory.publish` | `memory_publish.publish` | `root`, `payload`, `grant_file`, `actor` |
| `memory.recover` | `memory_recovery.recover` | `root`, `journal_path`, `grant_file`, `actor` |
| `ontology.publish` | `ontology_publication.publish` | `root`, `proposal`, `grant`, `expected_preview_sha256` |
| `ontology.recover` | `ontology_publication.recover` | `root`, `operation_id`, `grant` |
| `target.classify` | `curator_classification.classify_target` | `root`, `ownership`, `targets`, each with selected `identity` and byte `ranges` |

Task arguments must target the selected canonical root, Task ID and current
revision. Event and response actor/execution fields retain the actual current
writer. The complete Task `raw_payload`, memory `payload`, or ontology
`proposal` equals the selected request payload. Recovery retains its original
owner journal/operation through the exact selected owner arguments. Knowledge
owners receive their actual current owner-specific records; Application does
not replace or weaken those checks.

Pause/resume/retry/review may reach their documented owner transition from an
inactive stage while retaining exact current writer/version binding. Other direct
mutations require active/open execution. A paused Task does not accept new work.
Normal Task intake remains with the existing Task owner before Application is
constructed; these routes do not create a competing execution or new ledger.

## Ordinary controller-selection artifact

`validate_controller_selection(project_root, selection, catalog_owner=role_catalog)`
is read-only. The artifact has exactly `schema_version: 1`, `controller: curator`,
`project_id`, `project`, `charter`, `policy` and `role`. Project, charter and policy
are exact `{path, sha256}` references to `project.json`, `CURATOR.md` and
`curator.yaml`. Role is `{name, agents, role}` with exact current references to its
`Roles/<name>/AGENTS.md` and `ROLE.md`. The validator reopens the selected bytes,
checks prepared project identity and current policy, and resolves the role through
a fresh existing filesystem catalog. It does not create, reserve or activate work.

The owning host saves those exact selection bytes within its permitted evidence
scope and includes the artifact and returned source references in the normal
manager reservation's `source_refs` and context. Ordinary new Curator intake uses
Task schema 2/orchestration version 1, followed by the actual native manager
receipt, required reads and confirmed activation. A neutral policy can remain
inactive; this bounded execution selection enables no standing schedule or
permission. Existing version 2 records keep their original requirements and are
never relabelled or converted by this route.
