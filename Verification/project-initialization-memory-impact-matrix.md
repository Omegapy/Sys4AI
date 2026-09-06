# Project initialization implementation baseline

Observed: 2026-09-04T18:26:52.020911-06:00

Plan: PLAN-20260904-7AEB452E. Implementation Task: TASK-20260904-3D199F0B.

## Authority and ownership

The user authorized implementation and explicitly resolved Q-001: use the current template and Memory Service folders, with Git setup separate. The root Project Director is the single accountable implementation owner. Child projects retain independent project ownership; no parent Git HEAD substitutes for missing child metadata.

| Project | Own Git root observed | Own HEAD | Owner and allowed work |
| --- | --- | --- | --- |
| `.` | True | `31a919bc0785730cdc924dca6d281a3116561e2b` | Root Project Director: root init skill adoption, root canonical memory config/registries, runtime install and derived memory, verification and selected Task/plan tracking. |
| `Projects/Sys4AI-Template-Project` | False | `unavailable; source manifest will bind package provenance` | Root Project Director integration: INIT_MEMORY.md, README, template-specific validation/ignore rules only. |
| `Projects/Sys4AI-Memory-Service` | False | `unavailable; source manifest will bind package provenance` | Bounded delegated implementation with Director acceptance: bootstrap/interfaces, configured provider paths, consumer resources, local wheel tooling/docs and tests. |
| `Projects/Sys4AI-Electronics-Projects` | True | `33fa7f92bdd321cc3df89fdac78ea40eaacfa668` | Protected; no implementation changes. |

## Current sources and protections

- TRD revision 11, schema 2, trd_done; SHA-256 `b32eb2320a46cf30419e5255595986162d37505dc3dbb3ddd80e5a355077c833`.
- All 25 requirements and 29 tasks remain in scope. DEC-018 resolves repository setup without deferring memory or initialization functionality.
- Current root Task/Agent Task policies include automatic intake and close-old-task. Preserve these current packages; no source or child propagation is authorized.
- Baseline snapshot: [project-initialization-memory-baseline.json](project-initialization-memory-baseline.json). It records all 48 protected plan paths as content hashes or bounded metadata for environments/user-wide provider paths.
- Root and Electronics pre-existing changes remain preserved. The root status was inspected with GIT_OPTIONAL_LOCKS=0; template and Memory Service are ignored child trees, so their content must be inspected directly.
- Template and root .sys4ai directories are absent before initialization. Template .venv, .ruff_cache and .DS_Store are excluded from the copied starter and remain untouched.
- Canonical plan/Task records and deterministic projections change only through their helpers. Sources and unrelated completed histories remain protected.

## Planned verification

- Memory Service: existing Python 3.12 environment, pyproject/uv lock, initialization/configuration/provider/interface tests, then make validate-memory.
- Root: unittest repository and adoption tests; new initializer package tests; clean, manual, rerun, conflict, package-immutability and two-project fixture runs.
- Final: compare every preserved path to this snapshot, inspect actual project-local memory paths/receipts and reconcile every task and requirement through context-bound evidence.
- No check result is claimed here beyond the directly inspected repository/source/protection facts.
