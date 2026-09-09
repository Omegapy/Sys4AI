# Automatic capture at work completion

New memory installations enable `integration.automatic_capture` by default.
The setting is a JSON boolean (`true`/`false`); the setting command accepts
the user-facing words `on` and `off`. It controls the agent's completion workflow,
not a timer, filesystem watcher, transcript recorder, or backend service.

At completion of substantive work, an accepted decision, or an observed failure,
the responsible Director checks the current setting before its final handoff.
In an explicit Task, the confirmed manager performs this checkpoint while it
still owns the execution, after verification and before committing its terminal
Task response. Use `work-completed`, `task-completed`, `decision-recorded`, or
`failure-observed` as the capture trigger. No user reminder is needed.

1. Inspect current active notes and the actual work evidence. Capture a useful
   new lesson, decision, verified result, or observed failure with lasting value.
   Skip duplicates, trivial conversation, inspection-only questions, temporary
   progress and unsupported conclusions. Do not invent a note to satisfy a hook.
2. Prepare and review exact record bytes with source hashes and applicability.
   Children return proposals; only the owning Director/confirmed manager can
   approve and publish. Use the existing scoped publication grant and fresh
   native observation. Enabling capture grants no external actions or child
   project authority and bypasses no evidence, privacy or ownership check.
3. Call `memory.py --project-root ROOT capture PAYLOAD --trigger TRIGGER
   --grant-file GRANT --actor ACTOR`. The payload is the same reviewed `publish`
   or `supersede` payload described in [publication examples](publication-examples.md).
   Keep the operation ID on retry; the durable journal prevents duplicate writes.
4. Verify the returned publication receipt. Report an optional capture failure
   separately from the completed work. Required memory deliverables still need
   successful publication. Recovery must not replay terminal Task events.

The initial Task manager reservation must include a bounded `MEMORY/` publication
scope and `control_records/memory/` evidence scope when enabled capture is part
of its completion responsibilities. Use existing assignment `fit.writes` and
native activation gates. Do not add agents or a second canonical Task writer.
Independent solver packets stay frozen; a new note does not enter those packets.

`capture-status` is read-only and returns the current setting and configuration
SHA256. Only on an explicit user preference change, call:

```text
python .agents/skills/memory/scripts/memory.py --project-root ROOT set-capture off --expected-config-sha256 SHA256
```

Use `on` to restore capture. The helper changes only that boolean, rejects stale
configuration and pending recovery, and preserves notes and other settings.
Explicit user-requested publication remains available when automatic capture is
off. Reads never toggle capture or update an index. An enabled semantic backend
needs its normal authorized reindex after configuration or corpus changes;
capture itself writes canonical Markdown and its journal only.

After successful initialization, show the verified capture setting. When on,
say: "Memory automatic capture is on. Would you like to turn it off?" Initialization
is already complete; keep capture on unless the user opts out. Preserve an
existing off preference on reruns. An incompatible preserved installation needs
a scoped upgrade; never substitute an "on" readiness claim for that limitation.
