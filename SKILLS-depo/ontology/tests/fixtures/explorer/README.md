# Explorer acceptance fixtures

These source-owned recipes generate synthetic canonical projects in explicitly selected, disposable directories. They do not implement the Explorer or establish a production acceptance pass. `acceptance-matrix.json` is the frozen initial map from all 49 TRD requirements and AT-01 through AT-36 to scenarios, exact plan tasks, and evidence owners. Later production outcomes belong in separate release evidence.

Use the selected project's standard-library Python for builders and canonical checks:

```bash
.venv/bin/python -B SKILLS-depo/ontology/tests/explorer_support.py /private/tmp/explorer-small --scale small
.venv/bin/python -B SKILLS-depo/ontology/tests/fixtures/explorer/verify_fixtures.py
.venv/bin/python -B SKILLS-depo/ontology/tests/fixtures/explorer/build_matrix.py
```

The builder refuses a nonempty destination. It never searches for another project, changes shared agent limits, installs dependencies, invokes optional AI/standards/memory, copies active project knowledge, or starts a service. Generated directories contain the neutral locked core module, synthetic local records/sources, selected configuration, and competency questions. Remove disposable generated roots only through their test owner. The verification runner uses `TemporaryDirectory` and cleans up its own roots.

Python consumers add the ontology package's `tests` directory to their import path:

```python
from pathlib import Path
from explorer_support import make_explorer_project, make_neutral_project, mutate_fixture

fixture = make_explorer_project(Path('/private/tmp/explorer-alpha'))
beta = make_explorer_project(Path('/private/tmp/explorer-beta'), identity='explorer-beta')
neutral = make_neutral_project(Path('/private/tmp/explorer-neutral'))
# For each negative case, start with a fresh generated root.
expected = mutate_fixture(fixture['root'], 'stale_source')
```

`make_explorer_project` returns the selected root, scale, exact canonical IDs, separately scoped counts and a qualified predicted admission field. `scale` is `small`, `representative` or `stress`; optional `entries` and `relationships` override counts. `pathological=False` gives a minimal corpus for near-capacity probing. `make_neutral_project(..., unspecialized=True)` supplies neutral unresolved identity for configuration refusal tests; the canonical loader currently reports `unresolved_identity`, while the later Explorer must map its own documented configuration-needed state. `inspect_fixture` uses `load_project(validate=True)`.

| Recipe | Local entries | Local relations | Extra local bindings | Imported records / relations |
| --- | ---: | ---: | ---: | ---: |
| small | 50 | 100 | 1 | 65 / 9 |
| representative | 1,000 | 5,000 | 1 | 65 / 9 |
| stress | 5,000 | 50,000 | 1 | 65 / 9 |
| minimal reference boundary | 957 or 958 | 0 | 1 | 65 / 9 |

Entries include two predicates and configured process records. Process display identity is explicitly mapped; no unsupported core `Process` type is invented. The reference-boundary recipes have exactly 1,024 and 1,025 owner/binding/source tuples, respectively. This count includes direct references on the binding and references projected from it to its owner. It is distinct from the number of unique paths and from the canonical loader's deduplicated source observations.

The requested scales are workload targets. Each generated canonical document stays below 200,000 bytes and at most 500 records, preserving the unchanged loader's 2,000,000-byte and 10,000-record per-file caps. Massive generated corpora remain disposable; only recipes and bounded receipts are stored here. Representative and stress corpora exceed the Explorer's accepted 1,024-reference-tuple admission cap. The stress corpus also exceeds 32 MiB of canonical bytes and reaches 50,009 relations after imports, above the Explorer's 50,000 aggregate relation cap. These are predictions from counts, not observed service error responses. The later reader must refuse safely; no shared cap should be increased to make this fixture pass.

The small fixture includes:

- Explicit duplicate-label and duplicate-alias distinctions; `Alignment` also has a different definition in the second namespace.
- `FixtureTaskManager` for CamelCase lexical cases, a 5,000-CJK-character label, long Unicode definition, draft/deprecated records with replacement/history, and all four fact classifications.
- Exact parallel relation IDs with different predicates, a self-loop, directed cycle, hub, and a long conditional qualifier.
- 130 references with distinct locators, a separate explicit binding tuple, JSON pointer evidence, a repeated heading that only supports a qualified excerpt, and inert script/link/instruction-like source text.
- Four selected process views. `ordered` has three original numbered lines; `unordered` has no designated order; `partial` has only partial precedence and cannot support numbered steps; `stale` starts current and becomes stale or unavailable only after the explicit mutation. Stored numbering in a presentation mapping is never evidence that the source supports that order.

`mutate_fixture` provides `broken_reference`, `unmodeled_ambiguity`, `duplicate_identity`, `unsupported_property`, `unselected_source`, `invalid_qualifier`, `stale_source`, `missing_source`, and `same_mtime_source`. The first six intentionally fail with named canonical errors. Freshness variants remain loadable with distinct warnings; no provenance is repaired. The validation receipt records the actual codes and before/after fixture hashes and timestamps.

`protocol-cases.json` supplies explicit future cursor, source/asset access, transaction, code-epoch, session/expiry, resource, cancellation, client race, List, offline/CSP, accessibility, preservation, distribution, rollback, performance and human-task protocols. Credentials and signed cursors are created only in ephemeral runtime test memory. A protocol description is not an executed test.

All three corpora have direct successful canonical loader and competency results. The staged stress probe proved canonical loading completed, then exhausted its combined 45-second budget during a second loader/competency invocation. A separate competency-only probe subsequently passed all 16 questions in about 31.0 seconds under the same 45-second bound. Inspect `validation/result.json`, `validation/stress-competency-result.json`, and their exact raw references; the earlier timeout remains preserved. A single canonical loader time or peak RSS is not a production median/p95 or a reader performance pass. The `load_elapsed_seconds` stage includes the pre-read inventory and builder count inspection around the canonical loader; it is not a pure query timer. The staged stress peak was 270,729,216 bytes, above the reader worker operational ceiling; it was observed in this test subprocess, without claiming that a reader enforced its limit. Array-size boundary checks use invalid placeholders only to distinguish `unsupported_kind` at 10,000 from `invalid_graph` at 10,001; normal generated shards are checked independently for actual validity.

Optional presentation/schema verification uses the already installed test-only validator:

```bash
.venv-memory-pilot/bin/python -B SKILLS-depo/ontology/tests/fixtures/explorer/verify_schema.py
```

That invocation uses `jsonschema` only, with strict integer-token and UTF-8 byte checks. It performs no memory operation and adds no production dependency. Its receipt distinguishes structural schema/reference checks from unperformed process extraction and runtime semantic validation.

Fixtures are outside `explorer/assets`. Existing source distribution can install tests as test resources, which is separate from serving HTTP assets. No production asset manifest exists at this checkpoint; actual future bundle, manifest, installed asset closure and HTTP exclusion must be checked by their owning tasks. These receipts do not claim Template/root adoption, browser execution, VoiceOver/Safari, Windows availability, people validation, cutover or final protected-state completion.
