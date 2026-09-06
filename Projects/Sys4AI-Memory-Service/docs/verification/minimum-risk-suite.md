# Minimum contractual-risk suite

Status: implemented and directly exercised  
Command: `make validate-memory-minimum-risk`

This gate selects one maintained test node for each contractual risk named by
`P-15`. It is intentionally smaller than the full, security, or integration
suites. Each node appears once, and each has a distinct primary failure mode.

| Risk | Selected acceptance test | Failure detected |
|---|---|---|
| Authority separation | `test_canonical_control_reread_overrules_remembered_permission_copy` | Remembered control data authorizes an action that the current canonical permission denies. |
| Provenance | `test_new_agent_session_recalls_complete_current_project_context` | Reconnected project evidence omits or changes its canonical source ID, path, digest, or locator. |
| Isolation | `test_two_agents_share_scoped_evidence_and_service_serializes_writes` | A foreign project reaches the provider, or concurrent service writes overlap. |
| Data integrity | `test_tampered_active_pointer_is_rejected_without_path_traversal` | A changed generation pointer is trusted or can escape the derived root. |
| Rebuildability | `test_clean_full_rebuild_restores_exact_and_provider_generations` | Clean source-first regeneration changes stable records, relations, source revisions, or exact results. |
| Deletion | `test_public_supersession_and_two_phase_deletion_share_governed_lifecycle` | Preview/digest/receipt controls fail, derived deletion is incorrect, or current history is corrupted. |
| Retrieval correctness | `test_hybrid_composes_channels_and_exact_identifier_stays_first` | Hybrid channel composition loses the deterministic exact result or its source-backed ordering. |

The full release ledger remains the requirement inventory. This command does
not replace broader schema, provider, security, interface, migration,
benchmark, or end-to-end checks when their requirements apply. It provides a
fast minimum gate for the seven cross-cutting risks without copying their test
logic into a second suite.
