# Maintenance during a project session

Selected new installations enable `curator-session.yaml` immediately. The neutral
Template keeps `enabled: false` and no project identity. Earlier setup editions
keep their receipt and installation choices; a missing session file means this
mode has not been adopted. An existing `enabled: false` choice always wins.
The separate `curator.yaml` unattended scheduler remains unchanged and disabled.

At the first assistant turn of an installed project session, and when returning
after interruption, run:

```bash
python .agents/skills/curate/scripts/curator.py session-start --project-root .
```

Use the project's selected Python interpreter. This command gathers current local
Git observations, reads existing delivery records and records a missed-session
signal when its observed input changes. It performs no model call or canonical
Task, memory, ontology or content write. It does not start a service or certify
that a live AI host is available. Existing delivery records remain pending across
sessions until the current owner records their completed outcome. Startup uses bounded changed-path metadata, including current file metadata and
committed changes since the queued predecessor. Large status listings are streamed
and hashed twice within one observation deadline, retaining only the selected
page. The result reports total rows, remaining coverage and stream bytes separately
from the retained-page limit; it never sends the full listing to the agent. It is never proof of complete
source validation or reconciliation. Read further pages with `--path-offset` and
the exact current `--snapshot`; changed observations require a fresh first page.

The live Director acts on eligible pending maintenance in the current session,
using existing owner APIs. Read-only triage creates no Task. Reuse the current
owning Task for dependent work; route a new actionable maintenance objective
through ordinary Task intake and the existing required role/team workflow. The
owner retains exact candidate and current-source checks. Preserve original user
work and avoid creating a second execution for an already-owned obligation.
Do not ask again merely because the installation's approved session policy is
active. Scope, actual ownership and explicit project choices still apply.

Use at most one admitted maintenance operation per checkpoint, two model calls,
30 seconds of maintenance work, 1,000,000 candidate bytes and three concurrent agent
slots. These are ceilings; fresh observed capacity and remaining session usage may
be lower. Preserve pending work on exhaustion or unavailable owners. A later
checkpoint may resume with fresh current-owner usage evidence; do not reset
usage to evade the session budget. A task needing a larger required team remains
pending for an explicitly selected execution rather than dropping required roles.

When no Task is active, the live Director may invoke the installed canonical
owner's normal CLI for an already authorized, bounded maintenance operation. Use
that owner's required current preview, binding, exact inputs and resulting receipt,
within the same session budget. A metadata signal does not create new authority.
Do not instantiate the Task-bound Application adapter by fabricating a Task or
reopening completed work. If the work itself requires Task intake, use the normal
project workflow for that objective; the adapter is not a reason to create one.

A depot that has no generic `project.json` uses its existing `curator.yaml` project
ID and canonical root for session identity. When `project.json` exists, it must
also match. This supports the existing depot layout without claiming generic
project setup or adding an identity file.

Embedding hosts use `curator_session.dispatch(application, action, request,
root=..., actor=..., observation=..., now=...)` for one exact selected automatic
operation. `observation` is the existing scheduler's fresh owner-evidence view,
with its policy digest taken from `curator_session.effective_policy(root)`, actual
usage and iteration counts, current runtime status and current evidence hashes.
The application retains its real actor/Task binding and fixed public owner
arguments. A request file or shell process supplies no native identity. The
current owner consumes the exact delivery only after a completed outcome and
an attributable canonical owner receipt; dispatch alone does not consume it.

Keep idle checks and routine successful maintenance quiet. Report actionable
changes, conflicts or decisions. The CLI's structured output is diagnostic data,
not a demand to announce every pending signal. Logs remain summary-first; query
registered handles for only the bounded details needed by current maintenance.

To opt out, set the project-owned `curator-session.yaml` `enabled` field to false.
No service, hook, unattended AI, external notification destination or runtime
installation is part of this session mode.

## Semantic context

The Curator ontology describes collection, owner evaluation and selected dispatch
as separate steps. Retained delivery means pending input, and dispatch alone does
not prove a completed owner outcome. Current-owner receipts determine consumption.
Session-off remains an explicit opt-out; no ontology record enables background AI.
