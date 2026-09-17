# Guard capacity repair verification

The user separately authorized a bounded 64 to 128 MiB inventory capacity increase so the governed planning workflow could continue. The supported guard repair completed as `ONTGUARD-capacity-128mib-20260913`; exact pre/post changes, current native Director grant and immutable receipt are retained. No Curator integration implementation was performed.

The only engine behavior change is `MAX_BYTES = 128 * 1024 * 1024`. Complete context and mutation-target inventories, the 10,000-file bound, path and symlink checks, owner and generation checks, lock-time freshness, backend validation and semantic deadline remain intact. Reusable source changes comprise the engine, two focused regression tests and the initializer's exact engine lock. The registered Template received them through its existing update pipeline; final check is current. The active engine was adopted by the exact guard repair, with new immutable verification/bootstrap records and only its companion bootstrap reference changed. Existing bootstraps, other advanced profiles, the root-specific Task helper, registry and product projects are preserved.

## Evidence

- Baseline regression reproduced rejection at 80 and 128 MiB with the old engine; 32/64 MiB and the existing file-count rejection behaved as expected.
- The updated tests verify every returned file digest at 32, 64, 80 and 128 MiB; 128 MiB plus one byte and 10,000 inventory files are rejected. Source guard unit/deadline/profile/recovery run: 20 passes and one setup fixture failure, retained in `unit.stderr`.
- The active initializer is v9, while the reusable initializer and its initial fixture are v11. The original installed dispatch attempt therefore failed its Template allowlist before the intended setup recovery checkpoint. The corrected verification-only runner selects the installed initializer's own existing fixture. It changes no production helper, assertion, guard rule or negative control.
- The corrected actual selected-backend matrix passed all 48 required cases across eight action families. All seven selected dispatch and recovery tests passed with zero skips. Synthetic fixture identities remain explicitly fixture evidence; the actual root repair separately uses the observed live Director identity.
- Fresh root imports reopened the enabled guard, all 4,080 context entries, exact engine/adapters/bootstrap bindings and the 48-case evidence against the installed bytes. Source, active root and neutral Template engine hashes agree. The original Task helper hash remains unchanged.
- Direct 128 MiB snapshot measurement took 0.0594 seconds; process peak RSS was 33,374,208 bytes on this macOS host. These measurements use 1 MiB fixture files and do not predict arbitrary largest-file costs. The existing semantic-deadline tests and actual backend dispatch remain separate evidence.

Highest verification: actual root guard repair and fresh binding behavior observed, supported by targeted tests and actual-backend fixture dispatch. The original integrated Curator implementation remains planned work. The resumed real Task write and managed-plan creation are checked by the subsequent planning workflow.

## Artifacts

- `source-change.patch`: exact source changes relative to pre-repair bytes.
- `repair-preview.json`, `repair-grant.json`, `repair-receipt.json`: supported operation.
- `installed-dispatch-run.json`, `installed-dispatch-evidence.json`, `installed-boundary-evidence.json`: actual test results.
- `final-bindings.json`, `template-post-repair.json`, `capacity-measurements.json`: current verification.
