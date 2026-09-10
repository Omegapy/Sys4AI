# Installed wiki walkthrough

The installed root build produced 181 Markdown pages for project `sys4ai-depot`.
The files were reopened and their links followed against the actual filesystem.

1. [Wiki index](../../ONTOLOGY/WIKI/INDEX.md) links to concept/instance,
   relationship, module and capability/skill indexes.
2. [Concepts](../../ONTOLOGY/WIKI/concepts.md) links to the
   [Task page](../../ONTOLOGY/WIKI/Task-2dd754b49c17.md). It states the stable
   core ID, approved lifecycle, asserted classification and exact module version.
   It distinguishes Task state from a TRD, implementation plan, native goal and
   conversation, and separates document approval from activation/completion.
3. Task links to TRD and MemoryRecord through typed directional relationships.
   Its source link resolves to the current installed Task skill and the locked
   core vocabulary source. Both source digests matched during validation.
4. [Capabilities](../../ONTOLOGY/WIKI/capabilities.md) links to
   [MemoryRetrieval](../../ONTOLOGY/WIKI/MemoryRetrieval-b82c14a6929e.md), which
   links to the installed memory skill through `providesCapability` and to
   MemoryRecord through `retrieves`. Backlinks lead to the corresponding
   relation and binding records.

All pages mark themselves as generated and direct edits to canonical records.
This is observed Markdown/file navigation and link verification; it does not
claim an interactive graph viewer or a published website.
