# Independent same-ID input-rebind review

Reviewed on 2026-09-08 at 05:12:48 -06:00. No actionable findings remain in the
bounded repair and adjacent guards assessed here.

The preserved native failure payload reproduces `KeyError: coding_a` with the
old helper. The corrected helper accepts that same payload through pure
in-memory `apply`. It preserves the original native identity, launch receipt,
role-read confirmation, observations, candidates, reviews, synthesis,
acceptance, dependency bindings, canonical writer and generation. It returns
zero artifact writes. No returned state was published.

The repair keeps the old assignment available while reservation checks resolve
accepted analysis dependencies and historical coding candidates. It excludes
only that assignment's own existing ownership from the duplicate-slot and
write-overlap checks. The public event still requires the existing assignment,
same native identity, unchanged loaded role, current generation, exact packet
digests, valid scope and sole writer.

## Direct evidence

The original native Task was read at revision 59. Its canonical SHA-256 before
and after the pure replay was
`adddb3b89693fb25cdf1cebd3db6d1fd1238c35dd413db1dab3c1f39ed1fd242`.
The preserved payload SHA-256 was
`ccdaafadc51c37b579ce2a95f5eadd77a247103f81ad3a7890f59f6d9a7b8a0b`.

| Read file | SHA-256 |
| --- | --- |
| `roles/project-sub-agent/AGENTS.md` | `9acb819779aa05d154804d5022a960c5569a452ccaf6446e6497ee0180a24b2a` |
| `roles/project-sub-agent/ROLE.md` | `fd78736aca9999c20431d910e3e032d89b29128e24e7e2af7c9e2bf6dbaf21fe` |
| Repaired `SKILLS-depo/agent-task/scripts/orchestration_state.py` | `a8b0a6b7e9a2b492b835cac176b6b36aac3be7fd43ef85455b19a0575c0871d4` |
| `SKILLS-depo/agent-task/scripts/task_state.py` | `19275841e4625d9300cfde1852ddcc38d211430f68849caa8f2dad3b0991ccac` |
| `SKILLS-depo/agent-task/tests/test_orchestration_state.py` | `444b5a926c7213b0fa3fa38a119b29c8f59ca6a5898bbdf954fd2cb7b9c55f9a` |
| Preserved old `orchestration_state.py` | `46ae88d4f86ab1c6d47ac185e6a3f543ebb4b1e21aad3fd81c1ab92948a6c7dd` |

Seven adjacent pure-apply negative controls passed without modifying the input
state: foreign writer (`ORCH_WRITER`), stale generation
(`ORCH_STALE_GENERATION`), different native identity and mismatched packet
digests (`ORCH_INPUT_RECEIPT`), changed role bytes (`ORCH_ROLE_CHANGED`),
expanded candidate write scope (`ORCH_CANDIDATE_SCOPE`), and a synthetic
external active owner with the same logical assignment ID
(`ORCH_WRITE_OVERLAP`).

Three focused CLI tests ran on a frozen copy of the repaired source and passed
with zero failures or errors:

- `test_rejected_solver_rebind_retains_provenance_while_checking_analysis_dependency`
- `test_input_rebind_does_not_skip_another_active_write_owner`
- `test_compatible_baseline_rebind_preserves_native_identity`

The source snapshot, executable review script, test log and receipt are under
`/private/var/folders/2k/jj9s1zzs5sxdb_7g557y533c0000gn/T/sys4ai-rebind-independent-3m38s036`.
The durable [review receipt](./independent-review-receipt.json) contains exact
hashes, case outcomes and the before/after native Task hash.

This review performed filesystem reads, pure in-memory replay and disposable
CLI tests. It did not mutate the native fixture, publish returned state, wake
agents, or change source, root or Template packages. It establishes the repair
and named guard behavior; native continuation and project acceptance remain
with the Project Director. The bounded stopping condition was reached.
