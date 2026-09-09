# Local module resolution

Resolve one explicit real project root. Installed use reads only these
destination-local packages:

| Resource | Installed path from the selected root |
| --- | --- |
| Thin skill | `.agents/skills/what-did-you-learn/` |
| Module manifest and policy | `reference-assets/LEARNING-depo/` |
| Memory skill and helper | `.agents/skills/memory/` |
| Memory contracts | `reference-assets/MEMORY-depo/` |
| Configuration and canonical lessons | `memory.yaml` and `MEMORY/` |

Run the installed read-only check with the project's Python interpreter:

```text
python .agents/skills/what-did-you-learn/scripts/learning_contract.py --project-root /real/project
```

`resolve(project_root, skill_dir=None)` returns JSON-ready resource paths,
manifest hash, missing/incompatible resources, memory command and trigger
declarations, checkpoint compatibility and governance routing diagnostics.
Default resolution requires the exact installed skill path. It never searches
parent projects, a global skill directory or the depot for missing assets.
Missing, malformed, linked or incompatible resources yield precise read-only
diagnostics; they are not repaired or overwritten.

Reusable-source inspection must explicitly select the exact source skill:

```text
python SKILLS-depo/what-did-you-learn/scripts/learning_contract.py --project-root /real/depot --skill-dir SKILLS-depo/what-did-you-learn
```

Only this layout resolves `LEARNING-depo/`, `MEMORY-depo/` and
`SKILLS-depo/memory/` beneath the same root. Source resolution establishes
source compatibility, never active-project adoption. Tests use the same two
layouts, including the Template's installed layout. Do not mix a source module
with an installed memory dependency or borrow another project's runtime.

## Manifest and support checks

`contract.json` schema 1 declares module/skill version 1.0.0, exact module
resources, required skill resources and the existing memory interfaces. Module
paths are relative to `LEARNING-depo`; skill and memory `required_resources`
are relative to their respective package roots. Memory `contract_resources`
are relative to `MEMORY-depo`. Returned lists expand these to paths relative
to the selected project root. Extra exported module files require a manifest
update. Tests are skill-package files, not exported module lessons.

The resolver reads Python abstract syntax trees, never imports or runs an
installed memory helper to identify support. It checks declared CLI commands,
the exact four capture trigger values, memory schema constants, required
runtime/reference files and the `<!-- sys4ai:learning-review-v1 -->` marker in
the stable memory completion reference. A memory-only package can support its
original workflow without that learning marker; do not call it shared-learning
ready. Customized packages stay intact while their exact limitation is reported.

Governance routing is a direct reference to
`.agents/skills/memory/references/automatic-capture.md` in current `SOUL.md`,
`AGENTS.md` or `ROLE.md`, with all three governing files present. Alternative
custom prose is not silently treated as a verified route. Inspection does not
change governance or refresh its authority binding.

Keep four readiness claims separate:

- Manual review: compatible module and memory interfaces are present. Actual
  use still establishes the current configuration, work boundary and evidence.
- Shared automatic checkpoint: those interfaces, the learning marker and a
  current governance route are present. The actual capture setting is checked
  separately; instructions do not prove that a checkpoint has executed.
- Authorized publication: not assessed by this static resolver. Reinspect
  valid configuration, current owner/grant, sources, versions and native receipt
  through the memory publication contract at the actual operation.
- Optional backend readiness: not assessed by this resolver. Use actual memory
  health output; canonical/exact/lexical use does not require provisioning a
  semantic service. No readiness inspection installs, reindexes or starts it.

The initializer validates configuration and destination authority separately.
The resolver returns static capability booleans plus explicit `not_assessed`
publication/backend fields. A present marker or module version alone is not
an overall readiness claim. Review-only findings can be returned with a named
dependency limitation, but unavailable saving or retrieval must not be claimed.
