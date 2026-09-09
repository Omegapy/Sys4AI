# Project memory contracts

This collection owns reusable schemas, policy, empty starters, and non-active
examples. The executable capability is in `SKILLS-depo/memory/`. Learned notes
belong only to the owning project's `MEMORY/` directory.

The Template updater publishes these contracts to
`reference-assets/MEMORY-depo/`. It separately maps
`starter/memory.yaml` to the Template's `memory.yaml` and
`starter/MEMORY/README.md` to `MEMORY/README.md`. The initializer specializes
the stable project ID and name. Registration alone grants no adoption or access.

- [Policy and record/config representation](policy.md)
- [Publication and recovery](publication-and-recovery.md)
- [Record frontmatter schema](schema/record-v1.json)
- [Configuration schema](schema/config-v1.json)
- Empty configuration: `starter/memory.yaml` in this source collection, mapped
  to the owning project's active `memory.yaml` during adoption.
- [Examples](examples/README.md), which are drafts outside canonical memory

The core uses the Python 3.12 standard library. Backend and PDF extraction
availability belong to their selected runtime; neither is needed for direct
Markdown reads, record validation, or lexical retrieval. Do not copy learned
root records or local backend directories into these assets or the Template.
