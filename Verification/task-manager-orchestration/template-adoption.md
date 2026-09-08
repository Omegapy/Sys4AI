# Designated Template adoption

The reviewed Template delta was applied through `tools/template_update.py`:
eight additions, thirty updates and two exact legacy role retirements. The
[manifest](template-adoption-manifest.json) binds every source and destination
hash. Actual apply and the following check are in
[apply](template-apply-result.json) and [current check](template-check-result.json).
All 81 managed files are current with no pending recovery or conflicting delta.

Every changed destination was reopened and matched its expected hash. The old
`sub-agent-roles/project-sub-agent/{AGENTS,ROLE}.md` bytes were retained before
retirement in the updater's role-layout-history control directory. A durable
copy of that exact recovery record is
[template-legacy-role-recovery.json](template-legacy-role-recovery.json).

The actual Template passes 87 Agent Task tests, 66 role tests, 14 Task workflow
tests and 8 Template contract tests (175 total). Its role validator reports valid
current generic/manager pairs and index. Task status reports a valid empty
catalog without projection drift. Commands and log hashes are retained in
[template-checks/results.json](template-checks/results.json).

All 42 protected baseline entries pass the post-adoption
[preservation comparison](template-preservation.json). In particular, Template
To-TRD work, historical records, the live registry and unselected product files
retain their original bytes. No active-root skill adoption is included here.

The existing watcher was restored from its unchanged original launchd plist.
[Current readiness](watcher-ready.json) records PID 54987, a fresh successful
check from that same PID, 81 current managed files, and no stale-check flag.
The [restoration receipt](watcher-restoration.json) preserves the original plist
hash and actual bootstrap outcome. This is observed readiness, not merely a
loaded service claim.

Highest level: delivered Template assets, local package behavior and watcher
readiness. Fresh-project native execution remains a later verification gate.

## Superseding native-discovered repair

The later same-ID input-handoff correction, exact destinations, preserved prior
versions and current rerun results are recorded in [the repair report](rebind-repair/report.md).
This earlier adoption snapshot remains attributable to its original hashes and checks.
