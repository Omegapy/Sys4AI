# Role helper capitalization verification

The bounded RC-02/RC-03 source implementation is complete. Root and Template
adoption remain the Director's integration responsibility.

The helper now requires the actual directory entry `Roles`, including on a
case-insensitive filesystem. Discovery, show, creation, validation, reindex and
legacy transition use that root. Read-only operations do not repair casing or
navigation. New legacy previews target `Roles`; old lowercase previews cannot
be replayed as active publication authority.

`case-rename-preview` and confirmed `case-rename-apply` bind the complete original
tree, exact project root and device/inode. The physical move uses two exclusive
renames and a retained `.sys4ai/roles-case-rename.json` receipt. Pending recovery
requires the original inventory and identity at exactly one source, temporary
or destination path. Initial receipt acknowledgement failure and interruptions
before/after both physical hops are covered. Competing trees, aliases, changed
bytes and replaced directory identity are preserved and rejected.

The operation preserves every original tree byte, including custom files,
empty directories, `INDEX.md` and `.transition.json`. Reindex is an explicit
subsequent operation. A completed replay leaves later authorized file edits
intact. Historical lowercase transition paths require the completed rename
proof before they resolve to current `Roles` paths; old receipt hashes remain
historical. The initializer worker independently reported successful integration
of both proof APIs on both filesystem types.

The source suite ran with the project Python 3.12 environment and no new
packages. On normal case-insensitive APFS, 76 tests ran successfully with the
one distinct dual-tree case correctly skipped. On the Director's real
case-sensitive APFS test image, all 76 tests passed without skips. Both runs
exercised native exclusive filesystem rename calls, recovery and old receipt
preservation. AST parsing passed for both changed Python files. Exact commands,
logs, timestamps, instruction-read hashes and source hashes are in
`role-helper-verification.json` and the two `role-helper-tests-*.log` files.

| Changed source file | SHA-256 |
| --- | --- |
| `SKILLS-depo/manage-subagent-roles/SKILL.md` | `6366b1b38cc5ccb1558678a1bebc7f7f2b3b0b408b4616b194cbe08a3d5871d4` |
| `SKILLS-depo/manage-subagent-roles/README.md` | `62de203e2f7412a016776b890bb4f65b93cd176f140d6525a4a7012a702a27f1` |
| `SKILLS-depo/manage-subagent-roles/references/role-schema.md` | `d2c0416585c89621ed25835ce97d2842798e0a54971803f8a9695d677b575186` |
| `SKILLS-depo/manage-subagent-roles/scripts/role_catalog.py` | `3d46f11bc66c781d53edb266f0412127967770b8ef39f3fdc445364849f77945` |
| `SKILLS-depo/manage-subagent-roles/tests/test_role_catalog.py` | `084ddbb22869af8268e600e874e25b95d38451ea3223f6514b53a4a31956f02b` |

Linux's exclusive-rename branch was not executed on this macOS host. An
unsupported host fails explicitly instead of using an overwrite-capable
fallback. These are disposable filesystem and CLI-entry tests, not live
root/Template adoption or native child-role loading. No live role directory,
Task, TRD, managed plan, registry, Git or external-system operation was performed
by this worker. All worker fixtures have been cleaned; the Director owns final
test-image detach and project acceptance.
