# Implementation authority and preservation boundary

The current user requested `/goal Implement PLAN-20260908-5F47ADB2` in the
Sys4AI root. Execution uses canonical plan revision 1, SHA256
`6cd29af3938797c9bb15c7d699f416d50b43e26d7a8103b99afd0c01679a58c6`, and TRD
`TRD-20260908-7BA638D7` revision 2, source SHA256
`b4c883e2c68327dc0bf98c3b7ffe7575c8a6f6f9586475a6f240bad5868c5a14`.
The current implementation request supplies the execution authority described
as future work in the planning-time document. Plan and TRD lifecycle state are
preserved; neither named document-management skill was activated for mutation.
The native goal is the user-requested execution tracker. The root Task ledger
had no nonterminal Tasks and remains separate; native integration uses disposable
Task fixtures through the installed helper as required by this plan.

Reusable writes are confined to the new `MEMORY-depo` and memory skill package,
the affected existing Task/role/initializer source guidance, the Template specs,
tests and mapping, and local verification artifacts. The registered Template
is published only through `tools/template_update.py`. Root adoption follows an
exact inspected manifest after the complete source and Template checks.

The request covers the specified isolated `.venv-memory-pilot`, pinned model
provisioning, and a bounded root compatibility pilot with local semantic use
conditional on every mandatory check. Provisioning never enters the root
Python environment or setup/read operations. No MCP registration, cloud service,
Git publication, deployment, existing product adoption or global memory store
is included. A scoped root note may record actual release validation evidence
within this implementation; it must not claim unperformed backend/native work.

`preservation-baseline.json` records existing bytes and modification times.
`execution-baseline.json` records live Git, native settings and watcher state.
The pre-existing To-TRD changes, all historical Task/TRD/plan records, licenses,
role transition history, factual registry and Electronics project are protected.
The watcher was observed loaded and ready, then stopped with `launchctl bootout`
while its existing plist remained intact. Restore that same service after the
complete sources and Template are current; do not install a new service.
