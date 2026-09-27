# Ontology commands

Use the selected project's Python interpreter and an explicit resolved project
root. The installed entry point is `.agents/skills/ontology/scripts/ontology.py`.
All core commands use Python 3.12's standard library. Read commands install no
package and start no service. JSON is the default; `--format text` produces a
concise rendering of the same query identities and evidence.

Health result version 2 retains the existing `validation`, `sources`, `generated`
and `profiles` details. It adds `health_schema_version`, `assessment`, `aggregate`
and Boolean `ready`; `status` mirrors the aggregate. Health exit 0 now means
every required selected assessment passed, 1 means a completed non-ready
assessment (including absent capability), and 2 means invalid request or
configuration. Callers that formerly used exit 0 only to mean JSON was returned
must handle both JSON and exit status. Non-health command contracts are unchanged.

Both health routes support `--scope canonical|selected` and
`--level static|operational`; defaults are `selected` and `static`. Canonical
scope assesses canonical configuration, meaning and source integrity. Selected
scope additionally requires previously built products or enabled optional
profiles. Static readiness checks current installed/certified inputs; it is
not evidence of an operation in this invocation. Operational advanced health
executes bounded read-only SPARQL, full SHACL, inference, actual semantic
embedding and guard-validator probes for required profiles. Guard dispatch
remains explicitly unexercised: health has no mutation authority.

Use repeatable `health --require compile|build-wiki|link-memory` to require a
never-built product. `advanced-health --require` accepts `standards`, `inference`,
`semantic`, `guards`, and `workbench`. Disabled unselected profiles do not fail a
neutral starter; explicitly requiring a disabled profile is non-ready. Results
identify the exact project, observation time, input versions, required components
and failures. A later input change requires a fresh assessment.

For the on-demand workbench, static health reports `running: null` and
`service_state: not_assessed` until `--workbench-url http://127.0.0.1:PORT` selects
an actual endpoint. The read-only two-second probe checks project/root identity,
current source snapshot, server helper and startup configuration. It reports
running, stopped, unreachable, timeout, wrong-project, stale-service or invalid-response
state. It accepts no credentials, redirects, remote host, query or bootstrap
fragment and starts no service. Its total network deadline bounds header and
body reads even when a peer trickles bytes. `/health` exposes only bounded identity hashes;
all data/authoring APIs retain session, Host, Origin and CSRF checks. Explicit
CLI service startup reports its observed service and current dependencies,
separately from unexercised runtime behavior. Normal shutdown removes only its
unchanged exclusively created private session file.

Default SHACL authoring scope is `asserted`, `derived`, and `external`. External
metadata belongs to authored external-classified records and is needed for
their required constraints. Inferred graphs remain forbidden as authoring proof.
An explicit graph selection can produce real missing-field violations when it
omits required authored metadata. Repeated immutable RDF lists and property
shapes are shared within a single generation call; no persistent validation cache
is used and every target/property constraint remains selected. The default
worker deadline remains 10 seconds, with unchanged finite resource ceilings.

Generated memory links use sidecar version 2, independent of memory-record v1.
They bind the current memory configuration, reader helpers and entire selected
record inventory including exclusions. Legacy links are readable but stale until
an explicit `link-memory` rebuild. Changed, new, missing or newly unqualified
records invalidate associations. Ordinary reads return no stale associations.

After authorized adoption/publication, inspect `current_readiness` and
`maintenance_pending` separately from the operation's committed receipt. Settle
canonical sources and historical memory disposition first; explicitly recertify
the existing standards worker if its inputs changed, maintain memory projection
and index, then rebuild required ontology compile/wiki/semantic/link products.
Recheck all final inputs after documentation changes. Missing scope or failed
dependencies remain pending; none of these health reads installs, downloads,
rebuilds, changes settings or starts services.

```bash
.venv/bin/python .agents/skills/ontology/scripts/ontology.py --project-root "$PWD" term Task
.venv/bin/python .agents/skills/ontology/scripts/ontology.py --project-root "$PWD" read urn:sys4ai:ontology:core:TRD
.venv/bin/python .agents/skills/ontology/scripts/ontology.py --project-root "$PWD" search 'memory retrieval'
.venv/bin/python .agents/skills/ontology/scripts/ontology.py --project-root "$PWD" capability 'memory retrieval'
.venv/bin/python .agents/skills/ontology/scripts/ontology.py --project-root "$PWD" neighbors Task --direction both --hops 2
.venv/bin/python .agents/skills/ontology/scripts/ontology.py --project-root "$PWD" path Task MemoryRecord --direction outgoing
.venv/bin/python .agents/skills/ontology/scripts/ontology.py --project-root "$PWD" health
.venv/bin/python .agents/skills/ontology/scripts/ontology.py --project-root "$PWD" validate
```

`term` resolves stable ID, exact preferred label, alias, then lexical overlap.
Equal matches return explicit candidate IDs and distinctions. `search` returns
ranked matches with stable-ID tie breaks. `read` accepts an exact stable ID.
Every result retains lifecycle, fact classification, module version, canonical
edit location, typed relations, binding provenance and source freshness. Draft
and deprecated records remain labeled; deprecated replacements are retained.

Read operations are `health`, `term`, `search`, `read`, `neighbors`, `path`,
`validate`, `capability` and `knowledge`. They read current selected canonical
inputs in memory, never a generated graph as authority. They preserve files and
persistent timestamps even if projections are missing, stale or hand-edited.
`health` reports configuration, module integrity, semantic validation, source
freshness and each generated operation's readiness. Empty project extensions
can query their locked imported core. Missing configuration and unsafe or
unavailable sources receive specific diagnostics; no implicit repair occurs.

Query defaults are 20 results, 2 hops and at most 32,000 serialized UTF-8 bytes.
`--limit` accepts 1–100 subject to project configuration; `--hops` accepts 0–8;
`--max-bytes` accepts 1,024–32,000. Graph traversal visits at most 100 nodes.
`--predicate` can repeat to select exact predicates by ID or unambiguous label.
Incoming and outgoing directions remain explicit. Truncation metadata reports
when bounds prevented a complete returned set; `no_path` means no path was
found within the declared limits. These are usability bounds, not measured
performance guarantees.

Explicit generated operations are separate from reads:

```bash
.venv/bin/python .agents/skills/ontology/scripts/ontology.py --project-root "$PWD" compile
.venv/bin/python .agents/skills/ontology/scripts/ontology.py --project-root "$PWD" build-wiki
.venv/bin/python .agents/skills/ontology/scripts/ontology.py --project-root "$PWD" link-memory --record MEMORY/MEM-20260908-A1B2C3D4.md --concept Task
```

`compile` writes `.sys4ai/ontology/compiled/`; `build-wiki` writes
`ONTOLOGY/WIKI/`; `link-memory` writes `.sys4ai/ontology/links/`. Each also owns
its manifest beneath `.sys4ai/ontology/manifests/` and uses a generated-operation
lock. Builds require valid current inputs. Existing unknown or hand-edited
outputs are preserved and diagnosed as conflicts. Canonical source edits belong
in their owning records; generated edits are never imported. The wiki starts
at `ONTOLOGY/WIKI/INDEX.md`, with concept, relationship, module and capability
indexes and exact source links. `ontology_wiki.validate_links(root)` checks its
generated internal links without rebuilding.

`freeze-packet payload.json --output packets/ontology-v1.json` writes only a new
immutable artifact after current manager, execution, generation, scope and
version checks. Its JSON payload uses the keyword fields of
`ontology_packet.build_packet`; see [Task integration](task-integration.md).

`preview proposal.json` reads and validates an exact publication proposal.
`publish proposal.json --grant-file grant.json --expected-preview-sha256 HASH`
requires the ontology grant for that exact reviewed proposal and preview.
`recover OPERATION_ID --grant-file grant.json` resumes only the recorded bounded
ontology transaction. The [publication contract](../../../../reference-assets/ONTOLOGY-depo/publication-and-recovery.md)
defines exact proposal/grant shapes, scoped Director or current manager
authority, immutable receipts under `control_records/ontology/`, and recovery.
A valid ontology, discovered capability or memory publication grant supplies no
ontology publication or execution authority.

## Advanced reads and explicit setup

Use the same entry point and root arguments with these commands:

| Command | Purpose |
| --- | --- |
| `advanced-health` | Inspect profile selection and actual backend readiness. |
| `profile-setup standards --provision` | Explicitly install the exact standards lock and certify the local worker. |
| `profile-setup standards` | Explicitly recertify an already provisioned standards environment. |
| `profile-setup semantic --provision` | Explicitly install the independent ontology embedding environment. |
| `prepare-model` | Explicitly prepare the pinned ontology model artifacts and hashes. |
| `profile-configure request.json` | Apply one reviewed profile selection with current authority and expected config hash. |
| `build-semantic-index [--document allowed.md]` | Explicitly build vectors from approved definitions and selected allowed documentation. |
| `semantic-search 'recollections'` | Return sourced similarity suggestions, preserving exact vocabulary priority. |
| `dataset --graph asserted` | Read the selected RDF dataset graph. |
| `sparql --query 'SELECT ?s WHERE { ?s ?p ?o } LIMIT 10' --graph asserted` | Run bounded local read-only SPARQL. |
| `shacl [--shapes ONTOLOGY/extensions/checks.ttl]` | Run actual graph constraints with the selected standards profile. |
| `infer --goal SUBJECT PREDICATE OBJECT` | Ask for an entailed, unproven, contradicted or inconsistent named-resource goal and its proof. |
| `export-rdf --serialization json-ld --output exports/selected.jsonld` | Write a selected export and its context manifest. |
| `import-rdf docs/selected.ttl --serialization turtle --manifest docs/selected.ttl.manifest.json --reason 'Selected interchange review'` | Parse a permitted source and preserve an attributed durable RDF proposal. |

`--graph` can repeat for dataset/SPARQL/SHACL. The names are `asserted`,
`derived`, `inferred` and `external`; default query scope is asserted only.
Turtle and RDF/XML (`xml`) exports need one selected graph and their generated
manifest. A selected inferred export computes trusted inference first. Exports
use new paths unless an exact existing output hash is supplied. Import sources
must already belong to the project's permitted source allowlist. Unsupported
or lossy constructs remain staged with diagnostics; parsing never publishes.

`sparql --query-file selected-query.rq` reads exact selected query text.
`--limits-file limits.json` supplies lower execution limits for dataset,
SPARQL, SHACL and inference. Queries reject updates, federation and unselected
resources. Timeouts, cancellation, malformed requests, resource limits and
backend failures retain distinct non-complete results and nonzero CLI status.
The supported profile and host boundaries are in the adopted
`reference-assets/ONTOLOGY-depo/advanced-profile.md` and `advanced-limits.md`.

`profile-configure` takes exactly `profile`, `enabled`,
`expected_config_sha256` and `authority`. Its current Director authority names
the exact operation, project, actor, configuration hash, selected profile and
Boolean state, plus an actual recent native observation and expiry. Guarded
configuration preserves guard and publication scope and cannot disable the
standards backend required by an enabled guard. Provisioning restores missing
packages separately; no read performs it.

## Proposals and browser authoring

`generation-prepare request.json` freezes selected sources and approved context.
Deliver that returned request to the current permitted native agent.
`generation-capture result.json` captures the actual result and observed native
receipt. It does not invoke a model itself. `generation-show REQUEST_ID` reopens
the immutable request. The [generation contract](proposal-generation.md)
defines the exact source packet, response and bounded refinement fields.

`proposal-save payload.json`, `proposal-list` and `proposal-show PROPOSAL_ID`
maintain and inspect durable candidate revisions. Validate with
`proposal-validate PROPOSAL_ID --revision N`. Use
`proposal-decide PROPOSAL_ID accept --revision N --reason TEXT --validation-sha256 HASH`
to record an exact eligible review. `reject`, `discard`, `reopen` and `supersede`
remain distinct; a revision uses another save with the expected current revision.
Publish with `proposal-publish PROPOSAL_ID --revision N --grant-file grant.json
--expected-review-sha256 HASH`. The current v2 grant binds that exact proposal,
validation and review. The result includes the actual receipt and reopened files.

`workbench --authority-file authority.json --session-file
.sys4ai/ontology/workbench/session.json` starts the enabled local service.
The private session file contains a short-lived, one-use link. Without an
authority file, the session permits browsing only. A trusted local actor supplies
current native identity and exact authoring scope; browser fields cannot grant
authority. A new session must use a new private runtime file. Stop the foreground
service with Ctrl-C. Tokens and bootstrap URLs never belong in saved evidence.

`guard-preview`, `guard-apply` and `guard-recover` take reviewed JSON operation
payloads through the existing ontology guard setup/repair protocol. Enablement
requires actual complete action-family dispatch evidence and exact current
adapter/engine/backend hashes. Repair preserves its retained scope and cannot
rewrite unrelated governing authority or disable the guard. See the adopted
`actions/coverage.md` and `actions/repair-v1.json` contracts.

`knowledge QUERY --intent inference` labels derived conclusions separately from
definitions and history. `--intent proposals` explicitly selects unpublished
suggestions; frozen Task queries exclude them. `knowledge QUERY --advanced`
adds selected inference and separately labeled proposals to mixed results without
modifying memory. Ordinary mixed queries retain the first-release behavior;
frozen queries cannot include live proposals. Advanced
packet selection and material change gates are in [Task integration](task-integration.md).
