# Native task-manager feasibility probe

Probe: `PLAN-20260908-6E6F545E-TASK-002`. Recorded: 2026-09-08T06:50:59.158719+00:00.

The bounded native probe passed. A real manager launched three distinct workers at depth two, queued the third until earlier work completed, reused runtime capacity, interrupted a worker at its declared boundary, and reconnected the same native identity. All probe workers are reconciled as completed. No production workflow was implemented by this investigation.

Full evidence: [native-feasibility-receipts.json](./native-feasibility-receipts.json). Disposable fixture: `/var/folders/2k/jj9s1zzs5sxdb_7g557y533c0000gn/T/sys4ai-task-manager-native-xzavoc04`.

| Capability | Result | Evidence / limit |
| --- | --- | --- |
| host_to_manager_launch | passed | Root delegation NEW_TASK to /root/native_probe_manager; E01 native root and distinct manager IDs |
| host_manager_messaging | passed | Manager send_message /root and root replies in the native message stream |
| manager_to_worker_launch | passed | E02; E03; E09 |
| manager_worker_bidirectional_messaging | passed | E05; E06 exact nonce acknowledgement; E12 readiness message |
| explicit_role_loading | passed | Fresh per-assignment catalogs; All worker role_file_sha256 values match live paired files |
| exact_model_and_reasoning_inheritance | passed | Effective developer full-history inheritance guarantee; All spawn calls fork_turns all with model and reasoning_effort omitted; Root configuration inspection receipt; Worker runtime-guarantee receipts Literal effective model/effort telemetry was not exposed. This result relies on the runtime contract and root configuration evidence, not self-reported identity. |
| native_nested_depth_two | passed | E04 root -> distinct manager -> distinct workers No deeper level or maximum native depth was tested. |
| queued_candidate_context_independence | passed | queue.json logical C before initial dispatch; E06/E08 path/hash-only returns; E09 queued C dispatch before any manager candidate read; Worker C context receipt; Distinct private markers and verification text Shared filesystem access is not sandboxed; worker read restrictions and native parent-context evidence are the verified protocol. |
| completion_capacity_release_and_reuse | passed | E04 four simultaneously running agents; E07 native A completed; E08 B final completion; E09 new distinct C accepted after completions; E11 completed A reactivated while C running The runtime exposes no allocator slot identity or explicit close/release API. New-launch and follow-up success establish actual reusable capacity without identifying which completed slot was used. |
| interruption | passed | E12 readiness boundary; E13 previous_status running; E14 native interrupted state |
| same_identity_followup_reconnection | passed | E16 followup to /root/native_probe_manager/solver_a; E17 RECONNECTED same native ID and nonce; E18 native completed state |
| final_worker_reconciliation | passed | E08 completed B and later roster absence; E15/E18 completed C; E17/E18 completed A |
| explicit_manual_agent_close_or_release | not_exercised | No callable operation in direct collaboration tool set or searched nested tool metadata Completion reuse passed; no close/release operation exists in the available tool schema. |
| deeper_native_depth_and_maximum_depth | not_exercised | Only root-manager-worker topology authorized |
| literal_effective_model_effort_telemetry | not_exercised | No such telemetry exposed in native tools |
| production_task_manager_workflow | not_exercised | Disposable feasibility fixture only No production Task-manager role, reviewer/synthesis workflow, Task mutation, source adoption, Template update, Git action, or external action was implemented by this probe. |

## Native identities and final states

| Logical participant | Native ID | Final observed state |
| --- | --- | --- |
| Host Project Director | `/root` | Running its separate implementation task. |
| Probe manager | `/root/native_probe_manager` | Returning this report; root must observe native completion. |
| solver_a (DIRECT SUM) | `/root/native_probe_manager/solver_a` | Completed: E17/E18. |
| solver_b (INCREMENTAL CHECK) | `/root/native_probe_manager/solver_b` | Completed: E08; absent from E11/E14/E18. |
| solver_c (INVERSE CHECK) | `/root/native_probe_manager/solver_c` | Completed: E15/E18. |

The final roster shows solver A and C completed. Solver B returned a completion receipt before C launched and is absent from subsequent live rosters. No agent deletion is claimed. There are no running or interrupted probe workers.

## Configuration, roles, and independence

The effective developer contract guarantees that full-history forks inherit the parent model and reasoning effort and do not accept overrides. Every launch used `fork_turns: all` and omitted both override fields. Root supplied its allowlisted configuration inspection: no agent defaults or custom agent overrides, and no project configuration file. The manager did not reread user configuration. No literal effective model identity or effort value was exposed, so the probe does not self-attest one.

Root selected `project-sub-agent` separately for each arithmetic perspective and the read-only reconnect assignment. Fresh catalogs preceded every assignment and follow-up; all returned one valid role and no invalid roles. Workers explicitly loaded the canonical role pair and returned matching hashes.

| Input | SHA256 |
| --- | --- |
| `sub-agent-roles/project-sub-agent/AGENTS.md` | `f4211b99a8453204053ade52563a6f234d0b43a3fedf88b6bdc362475ab7e876` |
| `sub-agent-roles/project-sub-agent/ROLE.md` | `36ba709cac3009a3c1777b6ba0954f1ed1ac988327700b8dd65e28fb30de1c21` |
| `Verification/task-manager-orchestration/native-problem-packet.json` | `322898ae061ab12cfb8a7db1a0a3fec7985791e528546e707188f8382dc673f8` |
| Common problem, sorted compact JSON | `387769d0c8f92a9b9cad2c5154f1c5604a6d77ba5531471cb0e023903b183f44` |

All three solvers received the same common problem and separate write paths. Before queued C launched, the manager had received only paths, hashes, status, and a messaging nonce from earlier workers. The manager opened candidates only after C was dispatched. All worker receipts report no sibling candidate content in their received context. The three candidate markers and verification texts are distinct; markers occur only in their owning candidates among the inspected probe artifacts. This is observed instruction-based independence on a shared filesystem, not enforced filesystem isolation.

The manager reopened all candidate JSON files and verified exact integer results, input hashes, role hashes, candidate hashes, and verification text. All inspected governing source and packet hashes remained unchanged.

## Scope and verification limit

Highest level reached: runtime behavior observed in the disposable native scenario. Production manager roles, review and synthesis loops, Task state changes, depot sources, Template adoption, registered projects, user configuration, Git and external systems were outside this write scope. Native depth beyond two, literal model telemetry, and an explicit close/release API were not exercised. The available native API has no close/release call; successful new launches and follow-ups directly established capacity reuse.

Manager writes: fresh catalog receipts, queue record, working receipts, validation summary in the fixture, plus the two final verification reports. Workers wrote only their separate candidate and receipt pairs. Exact paths and hashes are retained in the JSON report.

The probe stopping condition is reached. Root retains responsibility for accepting this evidence and deciding the next approved implementation step.
