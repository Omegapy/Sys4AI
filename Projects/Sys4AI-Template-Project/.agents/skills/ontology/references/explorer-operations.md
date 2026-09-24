# Project Knowledge Explorer operations

Use the selected project's Python 3.12 and resolved project root:

```sh
.venv/bin/python -B .agents/skills/ontology/scripts/ontology.py --project-root "$PWD" explore --open
```

The foreground reader binds only loopback. Ctrl-C stops the owned service.
Launch uses the packaged assets and never installs, builds or activates optional
profiles. A stopped Python process must be launched locally again. The browser
cannot restart it. Keep bootstrap links and private session files out of logs,
version control and shared evidence. See [commands](commands.md) for optional
port/session selection, expiry, reconnection and the separate `explorer-health`
command. [BUILD.md](../explorer/BUILD.md) owns explicit package maintenance.

`ontology.yaml` owns project identity and permitted knowledge. Optional
`ontology-explorer.yaml` controls presentation only and must match that project
ID. Its closed schema is `reference-assets/ONTOLOGY-depo/schema/explorer-v1.json`.
An absent presentation file uses bounded defaults. The neutral Template has
`project_id: null` and intentionally reports `configuration_needed`; it is not a
running depot. The initializer retains its existing starter allowlist, so a new
project may use absent-file defaults. For explicit presentation, copy the
reference starter and set only its selected project's ID before launch. Existing
projects require an exact scoped package adoption; registration never updates
their installed files.

A missing bundle/schema/lock/notices reports `package_incomplete`. Reinstall the
exact reviewed complete package, or use the separately authorized build route.
Do not rebuild at startup or copy individual chunks from another build. Package
changes invalidate a running session; restart locally after the installation.
Data refresh only changes knowledge within unchanged executing package bytes.

The old `workbench` command is retired and returns `workbench_retired`; former
`--authority-file`, `--session-file` and `--port` arguments are rejected. Proposal,
publication, recovery and agent retrieval commands remain trusted local routes.
No old browser credentials migrate. Six old assets and the trusted helper import
names remain solely for historical setup compatibility; no current HTTP service
serves those assets. A retained enabled workbench profile is reported retired by
advanced health. Changing that project setting is a separate scoped operation.

Before adoption, retain exact preimages for changed code, runtime assets,
configuration and guard bindings. Stop the owned reader before restoring those
files. An enabled guard's updater/helper and successor adapter/bootstrap/config
must be changed together through public guard repair, with the companion config
last. Rollback restores only reviewed code/assets/configuration and current
valid guard bindings; it never restores old ontology, memory, proposals, Tasks,
receipts or publication history. Keep the Template watcher held until the owner
has approved the complete distribution state; restoring it can immediately apply
all pending source changes.

