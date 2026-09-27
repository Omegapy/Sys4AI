# Sys4AI root system health

Checked live on September 12, 2026, America/Denver, in `/Volumes/P-SSD/AngryOwl/Sys4AI`, using the root `.venv` and installed helpers.

| System | Result | Evidence and limitation |
| --- | --- | --- |
| Memory | Operational checks pass | Canonical records, evidence handling, projection, index and Basic Memory backend are ready. Actual bounded hybrid retrieval passes with 5 indexed entities and 42 vector chunks. Searching `curator session` retrieves the accepted session decision first, with no fallback limitations. Automatic capture is enabled. |
| Ontology core | Ready | Canonical validation passes; compiled output, wiki and memory links are current. |
| Ontology advanced | Backend probes pass; browser operation unverified | SPARQL, full authored SHACL, finite inference, semantic search and read-only guard validation pass. SHACL completes in 5.7386 seconds. The operational aggregate is `degraded` solely because the enabled on-demand workbench has no observed endpoint; its service state is `not_assessed`. No matching workbench CLI process was found. This is not evidence of a failed browser service. Guarded writes were not exercised. |
| Curator | Installed and enabled for project sessions; catch-up working | Policy and session identity validate. Live startup observes the repository and retains two pending catch-up signals. Four installed session tests pass. All 127 file references in the final adoption manifest match their current bytes. Unattended AI, scheduler and services remain disabled as configured. |

## Items needing attention

1. **Curator is absent from the ontology capability catalog.** The live `capability curator` query returns `no_match`, and the project's canonical ontology modules and binding files contain no Curator/curate entry. Memory does retrieve the Curator decision. The ontology's existing bindings are internally valid, but capability discovery does not yet cover this newly installed system. A scoped ontology addition is the appropriate follow-up.
2. **Curator has pending owner work.** Two catch-up signals remain pending. Startup reports `pending_owner` and `runtime_unavailable` because the collector deliberately does not claim a live owner runtime. It observed 42,406 changed-path metadata records, returned the first 50, and explicitly left source validation pending. Those records are not 42,406 failures. Live collection and fixture queue/consumption behavior were verified; actual completion of these two root maintenance signals was not performed.
3. **One old Task transaction warning remains.** The Task ledger is valid, with zero nonterminal Tasks, but reports a 1,425-byte staged response under cancelled Task `TASK-20260910-7F1A11AE`, revision 238. No top-level transaction file was found in that Task folder. The staged response needs exact owner-led inspection before cleanup; it was preserved.

## Verification scope

The highest evidence reached is actual local diagnostic and retrieval behavior, supported by targeted Curator tests. The browser UI, canonical publication/recovery writes and completed root Curator maintenance were not exercised. The existing installation report was used for comparison; current health results came from fresh commands.

The installed Curator test module requires explicit source and disposable-work paths. The initial direct unittest invocation stopped at import because those variables were absent. The corrected run mapped the required source layout to the actual installed package and passed all four tests in 2.013 seconds.

No fixes, package installations, configuration changes, Task lifecycle writes, Git publication or child-project changes were made. Required session startup added one transport catch-up signal. Diagnostic files are stored alongside this report, outside the project. Final input-hash comparisons found no changes to the assessed ontology or memory inputs during verification.

## Fresh evidence

- [Ontology core health](ontology_core.json)
- [Ontology advanced operational health](ontology_advanced.json)
- [Memory operational health](memory_operational.json)
- [Actual memory search](memory_search.json)
- [Ontology Curator discovery](ontology_curator_discovery.json)
- [Curator policy status](curator_status.json)
- [Curator live startup](curator_session.json)
- [Curator adoption file checks](curator_manifest_check.json)
- [Curator installed tests](curator_tests.stderr)
- [Final verification summary](verification_summary.json)
