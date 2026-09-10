# Ontology first-release implementation

PLAN-20260909-731308FD is implemented and locally verified. The Sys4AI depot now
provides explicit vocabulary lookup, typed graph traversal, capability discovery,
current-source and historical-memory routing, reviewed ontology publication,
derived memory links, frozen Task inputs, and a navigable generated wiki.
The reusable sources, active root installation and registered Template agree.

Start with the [wiki index](../../ONTOLOGY/WIKI/INDEX.md),
[Task definition](../../ONTOLOGY/WIKI/Task-2dd754b49c17.md),
[installed skill](../../.agents/skills/ontology/SKILL.md) or
[command reference](../../.agents/skills/ontology/references/commands.md).

```text
.venv/bin/python .agents/skills/ontology/scripts/ontology.py --project-root . term Task
.venv/bin/python .agents/skills/ontology/scripts/ontology.py --project-root . capability "memory retrieval"
.venv/bin/python .agents/skills/ontology/scripts/check_ontology.py --project-root .
```

The compact local JSON-LD profile and core module are version 1.0.0. The root
contains 176 records, including 111 selected project records, and 51 relationships.
Its wiki has 181 Markdown pages. Twenty-eight executable competency questions
verify meanings, distinctions, capabilities, provenance and governance boundaries.
The core lookup and combined structural/competency check also passed with Python
site packages disabled. No dependency installation or new service was required.

Initializer 10.0.0 uses governance-starter-v8 for new and first-prepared projects.
Actual disposable runs verified distinct identities, local Director bindings,
first preparation, prior-v7 reruns, selected adoption, customized-package
preservation and explicit receipt-owned refresh. Earlier base editions remain
unchanged. A changed reusable fixture source did not update an already initialized
project automatically. [Initializer observations](initializer-observations.json)
retain the actual receipts and preservation evidence.

The [test report](test-results.json) records these final runs:

| Suite | Tests run | Skipped | Result |
| --- | ---: | ---: | --- |
| Ontology source / installed / Template, each | 62 | 0 | Passed |
| Initializer source / installed, each | 100 | 1 | Passed |
| Root repository | 91 | 1 | Passed |
| Template contract | 11 | 0 | Passed |
| Existing memory | 77 | 0 | Passed |
| Existing Agent Task | 111 | 0 | Passed |

Repeated package suites are not unique-test totals. The skips are existing
dual-directory tests requiring a case-sensitive filesystem. Actual directory
entry spelling was inspected: retired `Ontology` remains absent and the new
authorized `ONTOLOGY` entry is present. No case-sensitive-volume test is claimed.

[Fifteen actual installed CLI scenarios](installed-interface-observations.json)
verified terminology, capability, graph/path, deprecated replacement, current
governance, mixed memory and no-match behavior. All 490 observed paths retained
their bytes, mtimes and ctimes. Repeated root graph/wiki builds were byte-identical,
preserved canonical content, and passed generated-link validation. The
[wiki walkthrough](wiki-walkthrough.md) follows the actual Markdown navigation
and sources; it is not a claim of hosted-site or browser rendering validation.

The [reciprocal memory experiment](memory-integration-observations.json) used the
real installed publishers: ontology publication and link generation preserved
memory; subsequent memory supersession preserved ontology. Links changed from
current to stale and became current only after explicit rebuilding. An ordinary
child publication was rejected despite valid proposed ontology content. The real
root memory corpus, schema, backend configuration and capture setting were preserved.

The [native acceptance report](native-task-observations.json) records an actual
confirmed manager, two independent solvers and a distinct senior in one disposable
project. Both initial solvers received the same 13-record packet; a publication
between launches remained excluded. A selected-source edit rejected the old
packet. The manager delivered revised exact inputs through existing Task gates
and continued both original native instances. Their v2 results agreed, the senior
verified and synthesized them, and the manager completed TASK-20260909-D1A13AA3
at revision 40. All 166 protected fixture files were preserved. The host reopened
the terminal Task and response, verified 39 report references, independently ran
Task validation, and observed the manager's native completion. See the
[context comparison](native-context-comparison.json) and
[host handoff check](native-handoff-verification.json).

The [requirement audit](requirement-audit.json) covers all 54 requirements and all
39 implementation tasks, including each acceptance criterion and reverse artifact
mapping. Query tests are consolidated into three focused suites. Policy lives in
the profile, state-path and publication contracts. Durable operations use
`control_records/ontology/intents/` and `receipts/`. These layout choices retain
the planned behavior and are explicit in the audit.

The [distribution audit](distribution-parity.json) verifies the 75 reviewed source
files, complete installed packages, locked core and exact root seed. The real
Template updater applied 57 additions and 16 updates, with no deletions, and its
final check is current. The existing watcher has a fresh successful check. The
[preservation audit](preservation-audit.json) verifies all 66 protected paths,
including source TRDs, other plans, Tasks, roles, learning, memory, licenses,
the existing environment, registry and independent projects.
Final diff inspection also restored the initializer's original executable mode
in source, root and Template; direct invocation passed with unchanged tested
bytes. The [metadata check](executable-mode-verification.json) records this fix.

The accepted [release context](release-candidate.json) is bound to plan revision 4,
SHA256 `bd9669306d759368e7f2d6bd021b15c17e36f18ea681769d08b6616953b0bebf`.
The managed plan remains `ready` and its file is unchanged; this implementation
report does not advance its separately governed lifecycle. The source TRD remains
unchanged. The real root Task ledger still contains 21 terminal Tasks and no
nonterminal Tasks; only the disposable representative Task was created/completed.
No native goal was created. The automatic learning/memory checkpoint was evaluated
without writing the protected root memory corpus; its useful parser-validation
finding was fixed and verified in this implementation.

The highest verification level is local end-to-end verification of the delivered
CLI, initializer, memory and bounded native Task workflows. Native identity and
context boundaries are cooperative protocol checks, not operating-system isolation.
Optional memory-backend provisioning, other hosts, real product rollout, hosted CI,
Git commit/push, external publication and deployment were not performed. The
retired ontology and Memory Service runtime were not restored. No in-scope
implementation item remains deferred. Exact final report and artifact hashes are
recorded in [the final release manifest](final-release-manifest.json).
