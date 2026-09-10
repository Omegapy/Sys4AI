# Memory operations

Every CLI invocation requires `--project-root` with an explicit real path.
Outputs are JSON. A failure reports a code and bounded diagnostic metadata;
sensitive source contents are not copied into the error.

| Operation | Write boundary | Required authority |
| --- | --- | --- |
| `read PATH` | None | One owning project and canonical record path |
| `search QUERY` | None | Active project corpus or exact frozen packet |
| `validate [PATH]` | None | Current config and selected canonical records |
| `health` | None | Explicit project; absent config is reported |
| `propose INPUT` | Stdout draft; optional granted result file | Draft content; saving uses bounded output grant |
| `publish PAYLOAD` | One canonical record plus durable journal | Current scoped Director/manager grant |
| `supersede PAYLOAD` | Exact predecessor/successor records and journal | Same, with all expected versions |
| `retract PAYLOAD` | Existing record lifecycle and journal | Same, retaining content and reason |
| `redact PAYLOAD` | Selected record and managed transaction copies | Explicit privacy-redaction grant |
| `recover JOURNAL` | Only accepted memory transaction | Current recovery grant for original payload digest |
| `reindex` | Only classified rebuildable state and maintenance receipts | Explicit checked maintenance grant |

Inspection never changes config, mtimes, Tasks, roles, cache state or package
availability. `health` uses the dedicated adapter's standard-library
certificate inspection for an enabled backend by default. The explicit
operational level adds the bounded read described below. Missing or stale
profiles report lexical coverage and the actual limitation.

For proposals, children can return the helper's draft content directly through
their authorized result artifacts. This does not require a canonical publisher
grant and does not put the proposal in shared recall. An optional helper-owned
file save is a distinct scoped write. Canonical `MEMORY/` is never a proposal
output directory.

Public readers use direct canonical bytes; source/extraction/backend modules
are imported only for the explicitly selected command. A backend outage does
not change the user's task, select another project, provision a runtime, or
substitute a new backend. Search with `--packet-file` also requires the exact
reviewed `--packet-sha256`; it never guesses a frozen baseline's digest.

Use the [publication examples](publication-examples.md) to construct reviewed
operations. Maintenance and Task packets use the same checked actor/scope
boundary while retaining their distinct file formats and Task lifecycle.

Automatic completion workflows use `capture PAYLOAD --trigger TRIGGER` with the
same grant and actor as `publish`/`supersede`. It checks the current setting,
skips without writes when off, and retains publication and recovery safeguards.
`capture-status` is read-only. `set-capture on|off --expected-config-sha256 HASH`
is the explicit user preference operation; it changes only that configuration
boolean. See [automatic capture](automatic-capture.md) for checkpoints and notices.

## Scoped health and completion

Health result version 2 adds `assessment`, `aggregate`, `ready`, and
`health_schema_version: 2`; `status` mirrors `aggregate`. Existing record counts,
backend details and diagnostics remain available. `assessment.input_versions`
aliases `assessment.inputs`, `assessment.components` aliases the top-level
components, and `assessment.project` identifies the selected id/root.
`failed_required` lists failed required components. Exit 0 means the exact selected
assessment is ready, exit 1 means a completed non-ready assessment (including
absent configuration), and exit 2 means invalid request/configuration or an
assessment failure. JSON delivery alone no longer implies success.

`validate` reports record/evidence validity separately from current verification.
Informational historical-applicability diagnostics remain visible and do not
invalidate qualified historical evidence. Warning/error and unknown diagnostic
severities fail validation. `verified_current_records` counts only active records
whose observed verification applies to current inputs.

`health --scope selected|canonical --level static|operational` defaults to
`selected/static`. Canonical configuration, records and active evidence are always
required. Selected scope additionally checks already built projection/index
products and an enabled semantic backend. A backend with `enabled: true` and
`semantic_enabled: false` is explicitly `enabled_lexical_only`; the semantic
runtime is unselected and is required only by explicit `--require backend`. Completed maintenance provenance keeps
a previously built product required even if it is later removed. Explicit
`--require canonical|evidence|projection|index|backend` (repeatable) can require a
never-built component. Unknown names fail. `--format text` provides a concise
summary with the same exit contract; JSON is the default.

Static backend health checks existing profile, certificate, projection, index,
model bytes and runtime presence without starting the vendor runtime. Explicit
operational health runs a fixed hybrid read of at most one result in the existing
local worker, with a 30-second deadline, then rechecks the certificate. It starts
no service, writes no database and installs or downloads nothing. Successful
semantic retrieval does not establish guarded write-dispatch coverage; the result
labels that dispatch as unexercised.

Publication and capture return the immutable canonical commit boundary separately
from `current_readiness`. A completed publication can have pending projection or
index maintenance. Retrying the exact operation preserves the original receipt
and reevaluates current dependencies; observation times can change. The explicit
`reindex-payload` / reviewed `reindex` route refreshes only granted memory state.
Ontology memory-link and semantic refresh remain their owning module's separately
scoped operations. Publication does not inherit those grants.

After reindex commits, its receipt retains that completed product boundary even
when a required operational probe fails. The command then reports
`maintenance_pending`, `committed: true`, `ready: false`, and a next operation.
Interrupted pre-commit work continues through `backend-recover` with the original
exact payload and a current grant. A completed receipt is historical operation
evidence, not reusable proof that today's dependencies are current.
