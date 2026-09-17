# Knowledge routing

`knowledge QUERY --intent MODE` uses explicit intent instead of guessing whether
a historical statement is a current rule. The modes are:

| Mode | Evidence read | Returned meaning |
| --- | --- | --- |
| `definition` | Canonical selected ontology and bindings | Definition, aliases, distinctions and lifecycle |
| `relationship` | Selected typed graph | Bounded directional relationships |
| `capability` | Capability/skill entities, relations and bindings | Installed skill source and constraints; no invocation |
| `current` | Exact permitted current governing sources | Actual current excerpts, recorded/current digests and discrepancies |
| `history` | Installed memory search/read or frozen packet interface | Eligible historical records or an explicit limitation |
| `mixed` | Ontology, current permitted sources, memory and existing sidecar | Separately typed semantic, current and historical evidence |

```bash
.venv/bin/python .agents/skills/ontology/scripts/ontology.py --project-root "$PWD" knowledge 'Task approval' --intent current
.venv/bin/python .agents/skills/ontology/scripts/ontology.py --project-root "$PWD" knowledge 'prior Task manager failures' --intent mixed
```

Current-authority routing starts with the selected entity's explicit source
bindings and reads current permitted bytes before combining historical evidence.
A changed recorded source is labeled `recorded_source_version_changed`; the
current excerpt takes precedence for operational rules. The helper compares
versions deterministically, not free-text semantics. An agent must inspect the
actual excerpts when a definition and a current rule disagree and report the
discrepancy; it must not assert that a fresh hash proves semantic agreement.

Mixed results use `source_type` values `ontology`, `current_governance`,
`historical_memory` and `derived_association`. Each retains exact concept,
record, file or sidecar identity and SHA256 evidence. Definitions are not event
evidence, links are not canonical assertions, and past decisions are not current
permission. Missing history, stale evidence or unavailable memory is reported
without inventing a result or provisioning a backend. Ontology still works.

A skill binding reports its installed `SKILL.md` source and freshness. Role
bindings use their actual `Roles/<name>/AGENTS.md` and `ROLE.md` pair rather than
the role index. Capability discovery does not run a skill, assign a role, create
a Task, approve a document, install execution gates or publish anything.

Frozen ontology queries require both global `--packet-file` and
`--packet-sha256`. A mixed/history request in that context additionally requires
`--memory-packet-file` and `--memory-packet-sha256` before memory can be read.
It cannot fall back to new live memory. Current-source excerpts are restricted
to explicit exact documents frozen in the ontology packet.

### Curator coordination

Curator proposes neither, memory, ontology or both from attributable evidence.
This owner retains stable identities, lifecycle/replacement relationships and
authored/inferred provenance. A stale projection with no new knowledge routes to
compile/wiki or the selected existing product owner, not canonical publication.
Canonical/history changes precede recertification and derived maintenance. Failed
required products stay pending; disabled optional backends stay disabled. Recheck
final source and product-input digests after documentation or integration changes.
