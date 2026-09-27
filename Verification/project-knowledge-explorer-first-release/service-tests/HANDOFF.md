# Service integration handoff

This is the bounded SERVICE_PACKAGE implementation handoff. Current automated verification passed 28 actual host service tests, 11 actual-bundle
instrumented cases and a real isolated Chrome bootstrap flow. Actual OS default-browser dispatch and native clean-tab inspection also passed.
Manager acceptance remains pending. It does not establish
full frontend, renderer, browser, accessibility, human-task, release-performance,
Template adoption, root cutover or whole-project preservation acceptance.

## Execution and package identity

`ontology.py --project-root ROOT explore [--port N] [--session-file PRIVATE_PATH]
[--open]` enters a clean `-I -S -B` interpreter before even argparse/json/pathlib discovery or authoring/profile imports.
The ordinary first invocation is only a launcher. A fixed stdlib bootstrap reads
the service source no-follow, verifies its selected digest and compiles those
exact bytes. It pins the snapshot bootstrap digest before compiling it too.
The resulting `VerifiedPackage` captures the complete ontology helper set,
schema, package/lock/notices/BUILD metadata, manifest and manifested runtime
members. All permitted runtime modules compile from that capture. No project
bytecode cache, ambient project import, authoring dispatcher, optional profile
or generic function/root selector enters the serving closure.

The child worker receives the parent's expected full manifest over a private
bounded pipe before any captured project module is loaded beyond the separately
pinned bootstrap. All members must match before execution. The actual loaded
module digest map and epoch are checked in the ready/result handshakes. The
same bootstrap and checks apply to a later permitted replacement. Interpreter
and stdlib remain trusted runtime components. Package verification is sticky;
restoring an old file after detected drift does not restore sessions.

`prepare_package` is a trusted local integration/test API, not HTTP. Production
enters it through `verified_entry` with the initial compiled bytes and expected
snapshot digest. A direct test import alone is not startup provenance evidence.

## Worker and HTTP ownership

`Service` owns a single select loop, at most eight accepted sockets, one active
read and one queued read. Connections accept one strict HTTP/1.1 request, then
close. Header/body, complete accepted-read and response-write deadlines are
absolute monotonic bounds. Reader calls use the same service-start clock as
session expiry. The supervisor checks its own 64 MiB and the worker's 256 MiB
RSS operational ceilings with a 10 ms select-loop target inside the 50 ms contract ceiling; reported overshoot is
an observation, not a guarantee against transient peaks. Unsupported RSS
observation refuses work. A parent ceiling breach refuses new work until fresh
launch. A worker failure stops and reaps that worker, fails requests already
queued, and permits at most one replacement per 30 seconds on a subsequent
explicit request. There is no background retry.

A client cancel removes queued work. An active canceled read drains under its
original deadline and its result is discarded, allowing other sessions to keep
the healthy worker. Expiry or closing one session similarly discards only its
output. A trusted worker report of package drift is processed before discarded
client output, so cancellation cannot suppress session revocation.

The child constructs Reader from the exact same private package as SnapshotStore
and installs Reader's presentation validator before the first lease. Private
frames are length-bound before decoding. Wire request container limits do not
silently narrow valid response qualifier maps; the private response wrapper has
one additional nesting level. The supervisor validates and compactly serializes
the real closed Reader envelope without changing its meaning. It never sends raw
exception details. Errors retain the fixed null project/snapshot/scope metadata.

## Sessions and private artifacts

Bootstrap, cookie secret, CSRF, cursor secret and session scope are independently
random and memory-only except the explicitly created private bootstrap file and
HttpOnly cookie. A new bootstrap revokes only a previous valid cookie supplied by
that browser; capacity does not evict another reader. Resume retains scope and
absolute expiry. Lowered effective session limits can shorten existing sessions;
no change extends their original deadline. Cookie name binds actual port and the
full per-start instance, with strict same-site and exact API path.

`PrivateFiles.files` inventories exact created regular-file names, inode identity
and bytes for unchanged-only cleanup. `created_directories` lists exactly which
of `.sys4ai`, `.sys4ai/ontology`, and `.sys4ai/ontology/explorer` this instance
created; directories are retained rather than broadly removed. Final release
preservation must account for those exact additions and actual per-instance
bootstrap/service files, never all `.sys4ai` content. Service identity receipts
contain no credentials. Bootstrap URLs are never printed by launch or included
in test output/evidence. Dispose `Service.close()` and reap its owned worker.

## Assets, health and frontend

Static serving binds real schema/lock/notices and checks the whole pinned epoch
before/after reads. Only manifest members and the two entry aliases are served;
nested entry aliases redirect to its canonical path so relative imports retain
meaning. Production baseline CSP stays unchanged. The installed metadata and
notices remain outside HTTP. Launch never builds or installs.

`explorer-health` inspects only this package, selected canonical readability and
an optional exact numeric-loopback origin. Health socket parsing bounds headers,
body and the complete exchange by an absolute two-second deadline, with no
redirect or transfer-encoding acceptance. Public health cannot disclose or prove
project/root identity. A matching selected-root private instance receipt can
establish the local comparison; otherwise wrong-project remains unknown.
Configuration identity mismatch is independently reported. Local validation uses
a bounded disposable reader process, with no listener, runtime file, repair,
optional readiness sweep or service activation.

The minimal `main.ts` synchronously erases the entire bootstrap fragment before
its first fetch/await on initial and same-document hash navigation. A new connection
generation aborts prior requests and ignores late responses even if abort is not
honored; close/expiry callbacks are bound to the same generation and session.
It validates a safe desired route, exchanges or resumes the
session, bounds response bytes before admission, and uses the settled raw client
decoder for actual context correlation. It preserves recorded project text on
expiry/disconnection. Its narrow project-context screen is a service bootstrap,
not the final reader UI. Later frontend changes to main/index/assets require
fresh build and current service/result verification; immutable evidence copies
cannot stand in for the changed live files. Full routes, Back/focus, List/Map,
source drawers and renderer behavior remain later assignments.

## Current evidence and consumer boundary

`criterion-evidence.json` preserves all 14 exact baseline criteria and maps each
to current checks. `current-checks.json` attributes actual execution;
`output-manifest.json` binds live product bytes, `current-context.json` binds
all 33 assigned inputs, and the evidence inventory separately indexes historical
failures and earlier passing candidates. Historical batches remain unchanged.

Source and installed layouts are exercised. Source layout contracts live at
`ONTOLOGY-depo/schema/explorer-v1.json`; installed layout contracts live at
project-root `reference-assets/ONTOLOGY-depo/schema/explorer-v1.json`. Neither
root adoption nor Template propagation was performed by this worker. The current
unchanged Template discovery predicate admits runtime assets and package
metadata while excluding build/dist/node_modules.

The full frontend owner may replace this narrow context screen within its own
authorized scope. Preserve synchronous fragment removal, raw-byte wire admission,
identity/generation guards, isolation and no-runtime-build behavior. Rebuild and
rerun affected service and browser checks on changed live assets. This handoff
does not pre-approve later renderer, List/Map, history/focus, accessibility, offline
release, performance, human walkthrough, Template/root adoption or cutover work.

The final OS check called the verified in-process `command(... explore --open)`
handler and observed the resulting existing Chrome tab with native CUA; it did
not navigate a replacement tab. The public CLI subprocess is covered separately
by the service batch. Only the created test tab was closed; the owned service
received normal SIGTERM, cleaned its exact private files and reaped its worker.

Current observed worker RSS fault peak was 337,051,648 bytes, 68,616,192 bytes
over the 268,435,456-byte ceiling. The supervisor observed a maximum 30.43 ms
sampling gap in that fault and killed/reaped the child in about 66.95 ms. These
are measured operational observations, not a zero-overshoot or broad performance
guarantee. The parent ceiling stayed 67,108,864 bytes; observed exhaustion
refused new API/static work and replacement until fresh launch.
