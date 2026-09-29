# Project app reading contract

The Project app binds one resolved project root to one local reading service.
`project_app_core.ProjectReader(root, package=None).read(operation, params)`
returns the version 1 public response. `package` may be the captured
`VerifiedPackage` supplied by the service or the ontology package directory for
focused direct checks. It does not select a project root from browser input.

## Identity and independent startup

The primary child identity is `project.json` with `project_id` and
`project_name`, matching the initializer's supported record. The depot root
uses only the unique registered `depot-manager` self entry with `path: "."`
in its own `depot/projects.json`. Child projects do not consult a live depot.
Missing, malformed or changed identity gives setup guidance. A symlink root
is rejected. A running reader also checks the root device/inode and identity
before each response.

Core startup imports no ontology or memory owner. Optional configuration must
name the same project and `root: "."`; a mismatch disables only that view.
The transport creates one lazy existing Explorer snapshot/reader shared by
the existing Knowledge API and unified lexical search. The app's `knowledge`
operation reports availability; terms, processes, sources, relationships,
continuations and map/list views keep the existing Explorer protocol.

## Project-owned Home content

`project-app.json` has exactly these fields:

- `schema_version: 1` and `project_id: null | string`.
- `home` containing `purpose`, `scope`, `audience`, and up to six `sections`.
- `documents`, up to 24 explicit `{title, path}` references.
- `start_here`, either null or `{label, path}` selecting a listed document.

Each Home section contains `text`, `sources`, `reviewed_sha256` and
`reviewed_at`. Additional sections may have `title`. Each source is
`{path, sha256}`. `reviewed_sha256` is SHA-256 of the section's exact UTF-8
text, not a JSON digest. A source digest is SHA-256 of its complete bytes.
The review timestamp is project-owned metadata, not an approval service.
The content schema is `assets/project-app/project-app.schema.json`; the
neutral starter contains explicit empty gaps and no domain-specific identity.

Unreviewed output or absent supporting sources displays **Not recorded**.
Changed source bytes retain the reviewed text with **Review needed** and both
recorded and current hashes. A missing or revoked document selection withholds
its derived section text. Reading never rewrites the content. Source identities
are checked again before preview; permission/configuration changes during a
request discard the response.

The core document owner allows only explicitly selected Markdown, plain text
or reStructuredText files under this root. Hidden paths, child projects,
canonical Work/memory records, role trees, reusable collections, runtime or
secret/private paths are excluded. This is an independent core document scope;
it neither requires nor enlarges ontology's `source_allowlist` or memory's
corpus. Knowledge and memory references remain with their respective owners.

## Read operations

| Operation | Parameters | Public result |
| --- | --- | --- |
| `context` | `{}` | Identity, navigation and static capability states |
| `home` | `{}` | Reviewed content, selected documents, bounded current Task summary |
| `work` | `{}` | At most 40 Task, TRD and plan summaries per owner and coverage |
| `task` | `{id}` | One exact Task/TRD/plan ID; public details and explicit links |
| `search` | `{query}` | Typed lexical matches and coverage for each participating owner |
| `source` | `{source_id}` | A current permitted text preview, hash and truncation state |
| `memory` | `{query?}` or `{source_id}` | Search-first Lessons and decisions, or an exact permitted finding |
| `knowledge` | `{}` | Optional Knowledge availability and reading guidance |
| `health` | `{}` | Static capability state and existing scoped setup/Curator notices |
| `help` | `{}` | Installed skill metadata, valid roles and ordinary app instructions |

Every response includes `schema_version`, `operation`, `status`, `project_id`,
`observed_at`, and `issues`. Status is `ready`, `partial`, `unavailable`,
`disabled`, or `error`. Empty results and unavailable owners remain distinct.
`ONTOLOGY-depo/schema/project-app-v1.json` defines the closed Request and
Response envelopes. The transport validates these and caps encoded responses
at 65,536 bytes; direct reads enforce the same response byte cap. Queries have
at most 300 characters. Source previews have at most 24,000 characters.

Source handles are ephemeral keyed identifiers, scoped to the reader instance.
They are not logical references or browser-selectable paths. Copy controls use
the owner, stable record ID or recorded path and available digest. Unknown
historical versions are **Not recorded**. No persistent search index, cache,
knowledge store or broad file catalog is created.

## Trusted owner execution

`assets/project-app/owner-compatibility.json` pins exact reviewed installed
script and asset closure hashes. Matching filenames alone never authorize
execution. Each call verifies bytes, copies the verified closure into an
ephemeral system temporary directory, and invokes only a fixed read route with
the current project root. The app never repairs or adopts an unknown owner.

Allowed owning routes are Task `status/list/show/continue`, TRD and plan
`list/show`, memory `search --mode lexical --limit 15` and `read`, role catalog
`list --format json`, and Curator `status --policy` with the fixed project
policy. `continue` is a read packet, never a browser resume action. Memory's
explicit Task/role validator imports are covered by the same reviewed hashes.

Owner processes have a five-second wall deadline, four-second CPU budget,
two-million-byte output budget and a 512 MiB address-space limit where the
host supports it. They run Python isolated from ambient import paths, with
bytecode writing disabled. An audit hook denies writes, subprocess/network
creation and execution outside the reviewed closure or standard library;
installed helper compilation is checked against the captured hashes. The
original owner closure is rechecked before admitting the result. Temporary
copied code is removed on return; governed project records are not written.

Work projection admits only named human-readable fields. It omits native
thread/agent material, collaboration records and their counts. The latest
Task response contributes only its named **Verification and evidence**
section, with a current owning packet. Explicit safe text artifacts can be
opened only while still listed by that Task's current packet. Unsupported or
private artifact types stay unavailable. Plan sources link by explicit stable
IDs; title similarity creates no relationships. Requirements approval, plan
state, Task completion, assignments, observed activity and release evidence
remain separate statements.

Memory search uses its existing permitted corpus without activating semantic
services. Exact finding reads are admitted only after repeating the original
query and confirming current scope, active lifecycle and bytes. Findings retain
claim level, applicability, supporting sources and supersession metadata.
Other memory document hits support bounded owner excerpts, labeled as such.

Health reports static installation/configuration observations. It never starts
an assessment, service, queue, repair or maintenance loop. Installed roles are
not observations of running agents. Help extracts bounded existing metadata
and recognized input/output/authority headings; missing information directs
the reader to the installed definition.

## Focused verification

`tests/test_project_app_readers.py` checks child identity, source provenance,
revocation, root/source confinement, unknown-owner rejection, public Task
projection and response invalidation when permissions change. The integrated
delivery evidence also exercises real installed owner packets, the shared
transport and ordinary browser journey. These checks make no voice/audio,
dedicated screen-reader, benchmark, broad platform or native-agent-pilot claim.
