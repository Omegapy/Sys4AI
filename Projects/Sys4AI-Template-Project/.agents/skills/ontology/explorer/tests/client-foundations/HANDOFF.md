# Pure client foundations handoff

This delivery implements five pure modules under the accepted v1 contract. It
completes only the CLIENT_FOUNDATIONS slice. It does not complete original
TASK-012, TASK-017 or their service, browser, List, renderer, focus, history,
accessibility and production integration criteria.

## Wire admission

`contracts.ts` exports all 124 named schema types and `isWire(name, value)`.
The generated closed-schema definitions come from the exact frozen schema;
`generate_contracts.py` also records Python's canonical casefold/whitespace
behavior. `contracts-runtime.ts.in` owns the additional runtime checks. Run the
generator only when changing this source implementation, then rerun all checks.
No runtime schema download, validator dependency, evaluation or dynamic code is
used. The schema and approved dependency files remain unchanged.

The fetch owner must bound incoming bytes before buffering, then pass raw bytes
(or strictly decoded text) to `decodeReadResponse(input, expectation)`. Do not
use `Response.json()` or `JSON.parse()` before this function. They lose duplicate
keys and integer-token provenance, and may round a numeric value before the
validator sees it. The returned `Checked<ReadResponse>` has either a validated
value or the fixed local `invalid_response` error. It never echoes raw input.
`isWire` is a shape guard, not network admission or authentication.

`decodeWire('SessionResponse', raw)` supplies the separate closed session shape,
canonical token padding and 1,024-byte checks. `connectIdentity` projects only
public scope/epoch metadata from that already admitted handshake; CSRF, cookie
and bootstrap values belong solely to the future API owner. This module does
not exchange, resume or close sessions.

Use `scopeForRequest(operation, request)` to construct expected normalized scope.
It structurally omits cursor and retains exact Q separately from normalized N.
Python casefold and Python whitespace semantics are used, including sharp S,
Greek final sigma, control whitespace and the distinction between BOM and
whitespace. Invalid request shape/sort/header continuation returns null.

`ResponseExpectation` binds operation, request ID, code epoch, service instance,
session scope, project/root identity, expected snapshot, exact returned scope,
and current effective policy. Initial context alone can use null project and
snapshot. A staged explicit refresh uses the old project/epoch/session and null
expected snapshot for its new context, followed by its exact new snapshot for
all required reads. The decoder checks full source-reference identities using
core canonical_bytes serialization and SHA256, and checks the effective-policy
digest. Server-only authority, live snapshot, source-path and source-byte claims
still require the reader/service's own checks.

Numeric tokens are checked before conversion. Unsafe integer tokens, decimal or
exponent spellings whose normalized decimal value changes through Number,
underflow and negative zero are rejected. Finite ordinary round-trip doubles
remain valid, including 0.1 and 1e-7. Negative zero is rejected because normal
JSON.stringify would erase its sign. The settled backend contract uses the
existing consuming `detail_required` relation marker with `field_limit` and
`detail.section='qualifiers'` for unrepresentable integer or negative-zero
qualifiers. Exact digits/signs remain readable as `canonical_json` TextChunk
text. Do not parse that chunk text as a complete JavaScript object. No new wire
numeric wrapper or schema change is introduced. Actual settled reader-to-client
precision fixture verification remains a separate manager-bound bridge check.

## State and effects

`createReaderState`, `connectIdentity`, `navigate`, `beginRequest`,
`applyResponse`, `failRequest`, `beginRefresh`, `commitRefresh`, `safeHistory`
and `restoreHistory` are pure transitions. They do not fetch or own DOM objects.
The API owner maintains one AbortController per region and executes each
transition's `abort` intentions. A new request returns its complete ticket;
after awaiting raw decode, pass that same ticket to `applyResponse`. It checks
sequence, route generation, exact scope and all authenticated identities again.
Aborting without this check is insufficient. Null-metadata server errors are
applied only to their still-current originating ticket.

Regions are context, search, entry, relationships, neighborhood and source.
Visible content is one bounded response per region; the inactive-cache owner
may later maintain the documented LRU entry/search pages outside history, within
the same limits. This implementation caps retained visible plus staged response
JSON at 256 KiB, retains only one visible source page, and fails a staged read
safely when it cannot fit. It stores no credentials. Cursors are ephemeral and
are never included in history or routes.

For explicit refresh, call `beginRefresh(state, requiredRegions)`, issue the
refresh-context ticket with `{refresh:true}`, stage the exact new context, then
request each declared required region against that context's snapshot. Commit
once with `commitRefresh`. The old visible content remains untouched until all
required reads succeed. Failure discards the staged content and marks the old
screen stale. Commit clears expansion/source/cursor state together. Required
Map/model readiness must be included by the frontend owner before calling this
commit; this pure layer does not instantiate a renderer or invent a graph read.

`navigate` distinguishes select from focus. Select pushes one safe history event
and preserves focus/camera. Focus changes focus and clears expansion/camera.
Camera intentions update replaceable metadata without pushing history. The
frontend must perform actual history.pushState/replaceState/popstate and focus
restoration once per returned intention. History contains at most 50 explicit
safe projections and no responses, bodies, tokens, cursors or knowledge caches.
Restoring metadata for another snapshot marks retained content stale. Browser
Back/Forward and accessible focus behavior remain integration work.

## Routes and preferences

`encodeRoute(route, authenticatedProject)` and `parseRoute(hash, project)` own
only the project-qualified credential-free route grammar. They reject unknown
or duplicate keys, decode once, preserve exact stable IDs, and normalize allowed
filter order. An overlong encoded route falls back to the whole exact stable-ID
destination with an omission notice. The caller must show that notice. Route
parsing is not bootstrap-fragment handling; the API owner must remove bootstrap
credentials before its first await, as the frozen contract requires.

`createPreferences(correlatedContext, storage)` binds only after context admission
and state correlation. It stores exactly theme, rail, relationship_view and
details with closed harmless values. Before identity, it uses nonpersistent
defaults. Its key is exactly
`sys4ai-explorer:v1:<root_scope_id>:<ProjectId>:<Namespace>`. Different root
identity clears in-memory preferences before reading the new key. Reset removes
only that key; storage denial falls back to memory. No source, route, credential
or knowledge content can enter the saved projection.

## Shared relationship model

`admitGraphPage(current, validatedResponse, preRequestCursor, tighterBounds)`
returns an immutable normalized model plus a continuation intention. Both List
and Map must read that same model. It preserves exact nodes, relation IDs,
endpoints, predicates, qualifiers, source references, markers, scope, filters,
status, coverage and diagnostics. It creates no implied edges and imports no
fetch, renderer or Cytoscape module. `orderedRelationships` and `resolveIntent`
provide exact stable order and bounded select/focus/expand/predicate/source
intentions for later consumers.

The shared cumulative ceiling is 100 nodes, 200 logical edge/marker identities
and 2 MiB of measured model JSON, or tighter caller bounds. A full edge and all
its required endpoint nodes are admitted atomically. A marker is retained as a
marker and has no fabricated edge. Only a complete prefix is admitted. If any
suffix is discarded, the result is `retry_after_reset` containing the original
pre-request cursor and counts; it never returns the response's advancing cursor.
The caller must offer focus/filter/reset and re-read from that earlier cursor
after reset. No remainder is silently retained outside the byte cap. Shared IDs
with contradictory data or different project/snapshot/session/filter scope are
rejected instead of overwritten.

## Reproduction and evidence

Run `.venv/bin/python -B
SKILLS-depo/ontology/explorer/tests/client-foundations/run_checks.py` from the
repository. It copies the previously verified dependency closure into a new
private fixture, uses Node 25.9.0/npm 11.12.1/TypeScript 7.0.2, checks the exact
project tsconfig, proves deliberate type errors fail, compiles isolated runtime
modules, executes the pure adversarial suite and independently validates its
success/error examples with installed jsonschema's Draft202012Validator. No
installation, hooks, asset publication or production build occurs.

The evidence directory retains initial failures: a removed TypeScript module
resolution option, the new compiler's required explicit --ignoreConfig for
file-list checks, and a browse test fixture that incorrectly used null rather
than the request's required empty query string. These were test-runner/fixture
corrections; final production compiler checks use the exact unchanged project
configuration. The graph cursor omission and numeric fidelity bugs were real
implementation defects corrected before this delivery. Frozen schema, contract,
package, lock, notices and build configuration hashes are rechecked in delivery.
