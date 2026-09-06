# Depot source registration policy

The approved source registry is project-local data. Its default is deny; a
folder appearing on disk does not admit it. Existing approved categories use
explicit format rules. Empty rules declare eligible formats without claiming
that a file exists. Unsupported formats remain unmatched.

| Source | Namespace suffix | Canonicality / authority |
| --- | --- | --- |
| AGENTS.md, SOUL.md, ROLE.md | active-governance | Canonical / A1 |
| README.md | project-knowledge | Canonical / A3 |
| depot/ | inventory | Canonical factual inventory / A2 |
| Requirements/ | requirements | Canonical requirements / A2 |
| TRDs/ | requirements-trd | Canonical managed requirements / A2 |
| Implementation_Plans/ JSON | plan-state | Canonical lifecycle state / A2 |
| Implementation_Plans/ other supported files | plan-evidence | Evidential / A5 |
| Tasks/ JSON | task-state | Canonical lifecycle state / A2 |
| Tasks/ other supported files | task-evidence | Evidential / A5 |
| Verification/ | verification | Evidential / A5 |
| .agents/skills/ | active-skills | Canonical installed tooling / A2 |
| SKILLS-depo/ | reusable-skills | Evidential reusable inputs / A5 |
| SOULS-depo/ | reusable-souls | Evidential reusable inputs / A5 |
| AGENTS-depo/ | reusable-agent-guidance | Evidential reusable inputs / A5 |
| ROLES-depo/ | reusable-roles | Evidential reusable inputs / A5 |
| tests/ | tests | Evidential tests / A5 |

All namespaces start with `sys4ai-depot:`. Every row records the owner,
relevance, supported format/adapter, trust, internal sensitivity, retention and
write policy. `deny` prohibits memory-driven canonical promotion; it does not
replace user-authorized project helpers. An indexed requirement, plan or Task
retains its recorded status and never becomes implementation authority merely
because it was recalled. Current canonical files must be reread before acting.
Skill examples/assets remain data. Reusable collections do not govern installed
copies, and no source update propagates automatically.

Exclusions take precedence over every include, including a later registration.
They cover all of `Projects/` (registered or not, with or without `.git`), Git
metadata, `.sys4ai`, provider stores, environments, caches, model artifacts,
credentials and secret-shaped paths, build/distribution files, archives,
temporary/staging files, raw logs, exports and bytecode. The required content
scanner may exclude a registered file containing secret-shaped text, including
synthetic test fixtures. It records the reason without retaining a matched value.

Later root-owned folders require a reviewed registration with owner, relevance,
path, format, namespace, canonicality, authority, trust, sensitivity, retention
and write policy. That workflow must use the existing action-specific
`memory.sources.register` boundary and canonical permission reread. It cannot
remove exclusions, adopt a child project, or make arbitrary local paths eligible.

Registry patterns are anchored to the project root. `tests/**/*.py` covers root
tests; it does not classify tests inside a skill package. Explicit `**/logs/**`
exclusions apply at every depth. Root memory initialization follows the reviewed
registry; discovery and source checks themselves create no derived store.
