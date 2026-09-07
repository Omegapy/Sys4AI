# Sys4AI project registry

The `depot/` directory contains factual inventory for the Sys4AI workspace.
[`projects.json`](./projects.json) lists known root and child projects, their
local paths, and observed Git and GitHub Pages state.

The registry does not copy or update files. It does not make a reusable source
authoritative over a project, and it does not grant permission to initialize a
repository, configure a remote, publish, deploy, or change a child's content.

The separate [template update mapping](./template-update.json) and
[update guide](./template-update.md) govern automatic publication of `*-depo`
changes into the template. They do not update existing product projects.

## Registry schema

Schema version 2 contains:

- `workspace_name` for the local workspace;
- one stable `id`, display `name`, relative `path`, and `kind` per project;
- `registered: true` to state that the entry is current inventory;
- observed `repository` status and remote; and
- observed `github_pages` status and URL.

Every path is relative to the Sys4AI root. Use `.` for the root. Child projects
belong beneath `Projects/`. Record only external state that has been observed;
use `not_initialized`, `not_configured`, and `null` rather than guessing.

## Current projects

| ID | Path | Kind | Repository |
| --- | --- | --- | --- |
| `sys4ai-depot` | `.` | Depot manager | Initialized |
| `sys4ai-template-project` | `Projects/Sys4AI-Template-Project` | Project template | Not initialized |

## Add or update an entry

For canonical project creation or an authorized clean manual copy, the
[init-new-project helper](../.agents/skills/init-new-project/SKILL.md) performs
this inventory update after specialization. It validates current schema and
identity, rereads the registry under a lock, rejects conflicting ID/path/hash
changes, and publishes one atomic update. Equivalent reruns add no duplicate.
The same inventory function serves `create` and `prepare-existing`.

For a separately requested inventory correction:

1. Confirm that the project directory exists and is the intended project.
2. Use a unique stable ID and the real root-relative path.
3. Inspect Git, remote, and publication state before recording it.
4. Edit only the exact registry entry.
5. Validate the JSON and confirm that every registered path exists.

Treat each child as independently owned. Repository status is `initialized`
only when the child has its own `.git` marker and Git reports that exact child
as the top-level. An ancestor Sys4AI repository is not the child's repository.
The Template has no independent Git marker; its status remains `not_initialized`.
Its files are tracked by the parent `Omegapy/Sys4AI` repository, as recorded in
its inventory notes. Other child projects remain excluded from that repository. Creating independent Git
history, remotes or publication state is a separate workflow and is not part
of initialization.

Registration is inventory maintenance only. Reusable material is authored in
the root source collections and automatically published into the mapped
template. Active root installations and product projects retain their own
copies; their adoption or refresh requires an exact scope and verification.
