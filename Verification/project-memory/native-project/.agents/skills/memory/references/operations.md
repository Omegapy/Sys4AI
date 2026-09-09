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
certificate inspection for an enabled backend. It never starts the vendor
runtime to discover availability. Missing or stale profiles report lexical
coverage and the actual limitation.

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
