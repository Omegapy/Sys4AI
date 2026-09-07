# Maintain reusable sources and the project template

Edit, add and remove reusable skills and guidance in the root `*-depo`
collections. The update engine publishes these files into
`Projects/Sys4AI-Template-Project/`. Both `create` and `prepare-existing` read
their starter assets exclusively from that template.

The active Sys4AI root and existing product projects keep their own copies.
Only the template receives automatic updates. The project registry remains
factual inventory and does not control the update mapping.

## Where files go

[`template-update.json`](./template-update.json) owns the exact mappings.

| Reusable source | Template destination |
| --- | --- |
| Valid packages in `SKILLS-depo/` | `.agents/skills/`, including added skills and the initializer |
| `SOULS-depo/SOUL.md` | `SOUL.md` |
| `AGENTS-depo/project-template-AGENTS.md` | `AGENTS.md` |
| `ROLES-depo/project-director-ROLE.md` | `ROLE.md` |
| Generic sub-agent role pair in `ROLES-depo/` | `sub-agent-roles/project-sub-agent/` |
| `SPECS-depo/project-template-SPECS.md` | `SPECS.md` |
| `SPECS-depo/project-template.gitignore` | `.gitignore` |
| `SPECS-depo/project-template-README.md` and `template-tests/` | Template overview and its local contract test |
| Initializer policy and README renderer | `.template/`, also retained in its skill package |
| Other regular files in the remaining `*-depo` collections | `reference-assets/<collection>/`, preserving their relative paths |

`overrides` place a file at its active template path instead of the default
reference location. `mirrors` add a second destination. Add an explicit mapping
when new guidance should become an active root file or role bundle. New skills
are discovered automatically without adding a mapping. Retain a complete skill
package with valid metadata before publishing it. The six governance skills
remain required dependencies; extra skills can be added and removed.

The Template's schema-2 policy selects static starter files and bounded trees.
Skill and role trees are discovered dynamically. `.template/` controls are read
by the initializer, while project identity and README content are specialized.
Transient files, environments, repository history, credentials, model files,
and generated data are excluded. Product dependencies are prepared separately.
Every explicit override or mirror must refer to a current source file.

## Check or update now

Run from the Sys4AI root:

```bash
.venv/bin/python tools/template_update.py check
.venv/bin/python tools/template_update.py apply
```

`check` is read-only. Exit 0 means current, exit 1 means an update is needed,
and exit 2 reports invalid input, a conflict, a busy lock or recovery work.
`apply` validates and publishes an update; a current template causes no rewrite.
Read its JSON result rather than inferring success from file timestamps.

First adoption accepts absent targets and byte-identical existing files. Later
updates compare each managed destination with its recorded hash. A customized
destination is a conflict. Unrelated template files remain untouched. Deletion
only removes previously managed bytes; removal of required governance or an
entire recorded source collection stops the update. A detached external drive
is unavailable input, never a request to delete files.

Sources are checked again before publication. The updater takes an exclusive
advisory lock and initialization takes a shared lock while copying assets.
Atomic file replacement and local recovery state protect interrupted updates;
inspect the reported recovery condition before retrying. Do not edit a success
receipt, discard a lock, or force an overwrite to hide a conflict.

## Retire a source collection

Normal updates reject a missing recorded collection so a detached drive cannot
look like an instruction to delete managed files. An intentional retirement
uses an exact collection name and the SHA-256 of the current raw
`.sys4ai/template-update/state.json` file. Preserve a verified recovery copy and
stop this checkout's watcher before changing the coordinated source set.

Remove the selected source collection and all of its mappings. Keep the depot
root, Template, and every other recorded collection present. Preview and apply
with the same reviewed digest:

```text
.venv/bin/python tools/template_update.py check --retire-collection COLLECTION --expected-state-sha256 DIGEST
.venv/bin/python tools/template_update.py apply --retire-collection COLLECTION --expected-state-sha256 DIGEST
```

These placeholders must be replaced by an exact recorded collection and a
fresh raw-file digest. The preview lists the retired destinations and the full
update. Customized or already missing deletion targets, stale state, another
missing collection, remapped retired destinations, and pending transactions
block a new retirement. The helper records approved retirement in its normal
pending transaction and publishes successor state; do not edit state by hand.

After an interrupted apply, run ordinary `apply` without retirement flags.
The pending record binds the approved collection and original digest and
checks both the source collection and destination bytes before recovery.
After success, normal `check` must be current with no pending transaction.
Restore the watcher only after the retained sources and Template pass checks.

## Automatic filesystem updates on macOS

The local watcher scans nested source and template paths once per second. It
waits for two quiet seconds before calling the update engine. It also retries
periodically so an interrupted or missed observation can recover. Changes
normally appear a few seconds after editing stops; invalid or conflicting input
keeps the prior template and records the error.

The watcher runs under the logged-in user's launch agent, independently of
Codex and Git commits. This follows Apple's
[launch agent model](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html).
Recursive content checks supplement event timing rather than relying on a
single lossy filesystem notification.

```bash
.venv/bin/python tools/template_watch.py install
.venv/bin/python tools/template_watch.py status
.venv/bin/python tools/template_watch.py uninstall
```

`install` creates and starts this checkout's user launch agent. Its label
includes a hash of the real checkout path so other checkouts stay independent.
`status` distinguishes a loaded service from a ready watcher, reports stale
checks, and shows the most recent engine result. On a removable drive, macOS
may ask to let Python access removable volumes. Approve that system prompt to
enable this watcher; a running process with no successful check is not ready.
`uninstall` stops that watcher and removes its launch agent; it preserves update
history and template content. Reinstall after moving the checkout. A Git clone
does not install a host service automatically.

For a foreground watcher, use:

```bash
.venv/bin/python tools/template_watch.py watch
```

Local hashes, recovery records and watcher status live beneath
`.sys4ai/template-update/` at the depot root and are excluded from Git. Launch
diagnostic logs live under `~/Library/Logs/Sys4AI/<service-label>/`, so macOS can
open them before accessing the removable volume. They are separate from
`.sys4ai/memory/`. A watcher error needs inspection of its JSON
status and the conflicting source/destination; it is not evidence that the
template is current. No Git commit, push, project-memory refresh or model
activation is performed by these commands.
