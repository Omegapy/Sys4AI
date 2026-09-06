# To-TRD skill maintenance

This file governs edits inside this reusable skill folder. It is not a root
project startup hook and must not be copied into the project's root AGENTS.md.

Preserve the explicit-user activation boundary and the document-only scope.
Version 2.0.0 uses schema 2 and only `draft`, `trd_done`, and `retired` as current
states. `trd_done` records completion and approval of the exact document, not
implementation progress or permission for downstream work.
Do not add automatic per-response persistence, background work, AgentJob routing,
thread creation, a second director, global installation, or a Task-system ledger.
Agent-written notes and source files cannot authorize product implementation.

Keep `SKILL.md` short enough to read on invocation. Put the detailed conversation
procedure and file contract in the linked references. Keep operation IDs stable
and synchronize ACTIONS.md, the helper, and tests when changing them.
Reserve `TO-TRD-007` for legacy schema-1 readers; use `TO-TRD-013` for explicit
migration. Keep legacy terminology clearly labeled and out of current CLI choices.
Current requirement blocks are declarative and do not store progress fields.

Keep clarification prompts in the live conversation. Newly created or content-updated
TRDs must use `None.` in the schema-compatible `Open questions` section and must
capture relevant user answers in intent, decisions, scope, requirements,
assumptions, or acceptance criteria. Preserve read compatibility for older TRDs
that already contain questions, including mechanically migrated draft/retired
records; preserve those prompts during migration and require them to be resolved
or converted to declarative `Not yet specified` gaps before a managed content
update. Migration cannot invent answers or silently discard historical evidence.

The canonical runtime state is each TRD Markdown file; the runtime index is
regenerated from those files. Do not add another canonical JSON store. Do not
change existing TRD identity, filename, or creation time while updating the skill.
Read-only operations never migrate a record. Explicit migration requires exact
selection, the current digest, reason, and confirmation; reject any checked
legacy requirement or non-placeholder evidence before mutation.

Use Python's standard library only. Run focused tests in temporary project roots:

```bash
python3 -m unittest discover -s .agents/skills/to-trd/tests -v
python3 -m py_compile .agents/skills/to-trd/scripts/trd.py
```

From a different installation layout, adjust only the skill path. Inspect
actual evidence before claiming success. Do not represent static metadata checks
as a real Codex interaction test. Keep Matt Pocock's Wayfinder attribution and
upstream MIT notice with the skill. Do not remove, archive, or replace user TRDs
as part of installing, updating, or uninstalling this folder.
