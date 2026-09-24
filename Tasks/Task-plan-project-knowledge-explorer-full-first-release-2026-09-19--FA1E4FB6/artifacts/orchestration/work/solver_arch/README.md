# Independent architecture proposal

`candidate.json` is a complete managed-plan create input for the full first release. It contains 49 requirements, 8 ordered phases and 31 planned tasks. All TRD titles, outcomes, acceptance statements and requirement dependencies are preserved verbatim. Every AT-01 through AT-36 appears explicitly in task verification. All task and requirement evidence arrays are empty.

The source is TRD-20260919-B6D51106 revision 2, lifecycle `trd_done`, SHA256 `bc074393b6eb7210154d93ef904b0959db86e0d845f449be56e071b8548c8d4d`. The frozen assignment baseline is `9b3229673777a3696b3ad63d2134748131ee873679b9027b0874b5300359e868`; the supplied empty memory packet is `cde976532caddb28de82c9b1045603d8a6689499bb3ed72a3b2a814347a9cd77`. No independent memory retrieval or sibling proposal inspection occurred.

The implementation choices remain proposed. The candidate favors a dedicated Python reader, thin compact canonical projections, immutable snapshots, signed scoped cursors, TypeScript without a general UI framework, Vite for explicit builds and Cytoscape behind one renderer adapter. No dependency version is asserted current or installed. The plan preserves the separate exact authority gates for installation, root adoption, provenance maintenance and external action.

Three live constraints materially informed the plan:

- Existing `search` defaults to `semantic=True`; its full `explain` shape includes relationships and sources before truncation. The reader needs `semantic=False`, compact records and filters before pagination without changing agent contracts.
- Existing publication is multi-file with a shared lock, durable intent and partial recovery state. The snapshot task covers both active writer races and stable incomplete transactions; before/after file digests alone are insufficient.
- Template distribution excludes `dist` and `build`, while initializer v9 explicitly lists old workbench asset files. The candidate uses a manifest-owned `explorer/assets` package and an explicit current capability/compatibility path, preserving historical receipt meaning.

Direct read-only canonical loading succeeded during inspection: 412 records, 181 relations and 79 current source references, under snapshot `92f101afa25aebd7908344cee561a9ba9984c3921b801b1169ccf7b00023a555`. The checkout HEAD was `744c8b06d5fda905201145ed313a2da8de2e601f`; pre-existing index and untracked work were observed and preserved. Canonical source/reference inventory establishes a Curator process lead but does not prove recorded sequence; full linked-source process classification remains explicit future work.

`check_candidate.py` applies the helper's create normalization, generated-field preparation, source-snapshot and structural validation entirely in memory. It does not call the create command or write canonical state. It also directly compares all 49 requirement definitions and dependency/acceptance arrays to the source and checks all 36 explicit task AT references. `static-check.json` records zero structural errors and 16 honest draft warnings: three future evidence gaps and thirteen proposed decisions. The evidence gaps concern future baseline/browser/test runs, full process-source classification and current dependency/license selection. No product behavior is claimed verified.

The final proposal changed only files in this assigned solver directory. Product files, managed plans, the Task ledger, TRD, root configuration, source collections, Template, registry, historical verification and shared memory were not modified. No packages were installed; no service or browser was launched; no Git mutation or external action occurred. The delegated stopping condition is reached: the complete independent proposal is ready for senior synthesis.

Role reads were completed and verified:

- `SOUL.md`: `3aa4841fa9f2dc177beabaebd341368d797d224cce3bb18b3fd494f34fa473b2`
- `Roles/project-sub-agent/AGENTS.md`: `7d064ae5d5954af65fc1a83b2ce1c69562d5c31f085e70ac92c3ad0bf2e7eec2`
- `Roles/project-sub-agent/ROLE.md`: `4c3ac5415030ab770d9af7b73fc773da43d07b041889c77a8755974284c874e2`

Recheck command:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python Tasks/Task-plan-project-knowledge-explorer-full-first-release-2026-09-19--FA1E4FB6/artifacts/orchestration/work/solver_arch/check_candidate.py
```
