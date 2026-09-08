# Root intake compatibility fixture results

Finalized: 2026-09-08T03:07:31-06:00.

The disposable installed-layout root stage passed 106 tests in 74.904 seconds:
67 preserved root tests, 35 shared orchestration tests, and 4 root-only tests.
The helper was merged against the original generic source ancestor; root intake,
automatic matching/creation, 30-day inactivity and `close-old-task` remain present.
Its original installed helper was not overwritten.

The four root-only controls passed:

1. An old live match with an unresolved native manager rejects with
   `ORCH_AGE_OWNERS` before old-match exclusion, age closure or successor creation;
   canonical bytes remain unchanged.
2. Explicitly reconciled old schema-2 work age-closes with the distinct status,
   retained response/history and the normal non-completion wording. A matching
   successor links its parent and starts with unset execution/owner.
3. A current matching execution is reused without creation or mutation; status
   remains read-only even under a future clock.
4. An old unassigned schema-2 Task uses a current native intake-host receipt,
   closes successfully and retains the exact empty orchestration object. Its
   successor also has no invented native identity.

Selected unassigned projection recovery additionally passed the shared suite:
a current running bootstrap receipt repairs generated views without changing
canonical bytes or assigning a writer. The same bootstrap proof is rejected for
an already owned Task. Revoked/unresumed native observations cannot restore write
eligibility. All existing root 30-day boundary and history tests remain included.

The first added unassigned-aging fixture attempted to advance an unrelated live
Task by editing only its canonical timestamp; strict integrity correctly rejected
that malformed fixture. The final fixture uses a separate complete disposable
project, preserving the integrity checks. An earlier 103-test stage run had only
a missing new reference-file inventory failure; the final exact stage includes it.
These preparation failures are superseded by the full 106-test passing run.

Stage: `/private/tmp/sys4ai-orchestration-build/root-installed`.
Patch verification copy: `/private/tmp/sys4ai-orchestration-build/root-patch-check`.
The seven-file patch passed `git apply --check`, was actually applied in that
copy, and produced every exact target hash below. Root's separate six-file policy
overlay was present for the suite and is deliberately outside this component patch.

| Installed component path | Before SHA-256 | After SHA-256 |
| --- | --- | --- |
| `.agents/skills/agent-task/scripts/task_state.py` | `abc97dd44db7c32d50bd54e04d8df02dea2a1f49443444170d20f8da4a5acdcb` | `f69c8d0094701d3d70a55f61c1ec0d7ab4ddf203f3110c5bf051e3ea1d5f5c79` |
| `.agents/skills/agent-task/scripts/orchestration_state.py` | absent | `46ae88d4f86ab1c6d47ac185e6a3f543ebb4b1e21aad3fd81c1ab92948a6c7dd` |
| `.agents/skills/agent-task/references/task-system-contract.md` | `a50bf064a2d1064071e6cbd7f0afe833f0cfe69740b5dfb1b0e4e6097706382e` | `ee060791d5b498f3cd4c899ea01de63b937ecd2d0ead8ba8ca18b107ba3151de` |
| `.agents/skills/agent-task/references/orchestration-contract.md` | absent | `1ffa67a116e9b6048cf8787ee16380c262cbd1eba0b51b9b7682baa1ca5a91cc` |
| `.agents/skills/agent-task/tests/test_task_state.py` | `950a52b24aa24eaa661dcefb584b509e42b9cba499dff99a7d2a076e26e8b855` | `58bf1cc08a5ba28f8877b45f9cc77b8c4ce7f4d93f140e0bd2be3771100a7928` |
| `.agents/skills/agent-task/tests/test_orchestration_state.py` | absent | `5c6fa362255ffbc9d75c2f4510ce65d0b2a535bf7548f0bcc6b109c8fc2dc586` |
| `.agents/skills/agent-task/tests/test_root_orchestration_intake.py` | absent | `a28ae005a354c735373aab0964e8d53241ad3e028d22ac273dcd7a453480267c` |

Patch SHA-256: `bf34316ed88542f38714dbfa1c368012c99279a821c9db92a0efcaef5cad9ca2`.

The source-only stage retains generic selection policy. Root-only
`intake_actor` has exactly `native_id` and `receipt`; the native roster must
currently show that actor running. Age closure binds the exact execution and
generation, requires the original bootstrap for an owned Task, and refuses
unconfirmed owners. Unassigned aging records no bootstrap identity. Read-only
status/list/show/continue/validate and unrelated prompts do not invoke this policy.
No live ledger history was upgraded or aged by these fixtures.
