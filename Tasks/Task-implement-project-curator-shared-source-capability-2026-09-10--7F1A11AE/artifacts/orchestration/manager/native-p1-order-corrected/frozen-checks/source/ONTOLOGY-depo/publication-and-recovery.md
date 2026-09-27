# Ontology publication and recovery

Canonical ontology publication requires a reviewed proposal and a separate current ontology grant. A successful query, valid graph, role title, memory grant or captured suggestion supplies no authority. Current user instructions and governing sources control operational permission.

## Exact reviewed proposal

The proposal has `schema_version: 1`, `operation_id` beginning `ONTOP-`, `operation: publish`, a concrete `reason`, and `changes`. Each change contains one selected canonical `path`, nullable `expected_sha256`, exact UTF-8 JSON `content`, and `sha256` of that content. One operation selects at most fifty files; each content is at most 250000 bytes. Only configured local extension, binding and competency files are mutable. Configuration and imported module updates use the separately authorized initializer/adoption boundary.

`preview(root, proposal)` reads current inputs, verifies expected bytes and validates the complete proposed graph and lifecycle transitions. It returns the exact before/after context, payload digest and `preview_sha256`. Preview writes nothing. Old source references may be stale when the proposal repairs them; the complete proposed graph must resolve current source bytes and locators. This permits exact rebinds after a selected source changes.

`publish(root, proposal, grant, expected_preview_sha256=...)` compares the reviewed preview again after taking the publication lock. It writes only the accepted selected canonical changes, its durable control records and explicit compiled projections. A normal return reports `complete` or `partial`; callers must inspect it rather than assume success. `recover(root, operation_id, grant)` resumes only the exact immutable accepted intent.

## Configuration binding and grant

Neutral configuration has `publication: {enabled: false, binding: null}`. Initialization specializes a destination-local binding with `actor_id`, `scope` containing the selected `ONTOLOGY/modules/project` and/or `ONTOLOGY/bindings` prefixes, and `authority`: exactly `{path, sha256}` references to current SOUL.md, AGENTS.md and ROLE.md. Neither root actor identity nor root governance hashes are copied to another project.

A grant has exactly `schema_version`, `grant_id` beginning `ONTGRANT-`, `project_id`, `actor_id`, `actor_kind` (`director` or `manager`), `operation: publish`, `payload_sha256`, `preview_sha256`, `config_sha256`, `scope`, `native_receipt`, `observed_at`, `expires_at`, `task`, and `reviewed_records`. Scope names the exact changed files. Reviewed records repeat each proposed path, post-content SHA256 and nullable expected SHA256 in proposal order. Canonical encoding is sorted, indented UTF-8 JSON plus one trailing newline.

The native receipt is the actual normalized `collaboration.list_agents` result: `{tool: "collaboration.list_agents", result: {agents: [{agent_name, agent_status}]}}`. It must show the caller running. Native observation and grant expire within five minutes. A Director grant requires the current destination-local actor and all three governing hashes. An unreconciled active, paused or uncertain Task manager with overlapping writes blocks a competing Director.

A manager's `task` value is `{path, sha256, task_id, execution_id, generation, assignment_id}`. The current installed Task helper validates that exact canonical record read-only. Its active manager, native launch, writer, generation, role reads, current role pair and assigned `fit.writes` must agree. An ordinary child or competing generation fails. The Director's `task` is null. No Task record, role index or memory record is written.

These are cooperative local process checks, not cryptographic identity authentication or an operating-system sandbox. A locally forged native receipt cannot be authenticated by a JSON parser. The coordinating owner must save actual tool evidence and bind the actual running actor to each grant.

## Commit, recovery and replay

Under a nonblocking POSIX advisory lock, the helper durably saves one immutable intent containing the exact proposal, reviewed context, original content and publisher attribution. It then checks expected bytes again, writes temporary siblings through opened non-symlink directories, flushes and replaces each selected file, fsyncs the directory and verifies the post-hash. All selected input, configuration, import and helper versions remain bound to the accepted preview. Editors should share this lock; an external editor ignoring it can race a rename, so the helper reports observed conflicts rather than promising an OS-level compare-and-swap.

After canonical commits, explicit compilation publishes deterministic projections. A write, projection or receipt fault yields a durable partial-recovery report naming committed and pending files. Unknown current bytes block replay and are preserved. Repeated delivery of the same operation recognizes matching post-hashes and never commits the same logical change twice. Reusing an operation ID with different content fails.

Recovery requires a fresh current grant for the original payload and preview. It rechecks accepted input versions and ownership, completes only expected pre/post states, and creates the immutable completion receipt. The receipt records actual committed files, prior/current digests, reason, owner and projection result. A historical complete receipt cannot overwrite later human changes. Accepted intent and recovery records are durable work and are never treated as rebuildable indexes.

Suggestions remain draft candidate data until this exact publication path accepts them. `ontology_lifecycle.transition` returns a candidate and never writes files. Deprecated identities retain their reason, previous meaning and optional replacement. Changed approved semantics require renewed exact review with retained history or a draft stage; deletion cannot recycle an ID.

## Version 2 proposals and grants

Version 1 payloads and grants retain their original exact fields and scopes.
A version 2 payload retains the same top-level fields but can also select
already locked `ONTOLOGY/extensions/*.json`, their already selected local
Turtle shapes, and `ontology-advanced.yaml`. The companion change may alter
only existing extension lock hashes. New extension/shape selection, runtime
profiles, authority bindings, guard setup, limits and other configuration
remain separately selected setup operations. Existing extension statement IDs
retain their exact meanings; extension additions use distinct sourced IDs.

Advanced publication needs `publication: {enabled, binding}` in the advanced
companion. Its destination-local binding repeats the current actor and exact
SOUL/AGENTS/ROLE references, with scope exactly `ONTOLOGY/extensions` and
`ontology-advanced.yaml`. It does not broaden the core binding. The existing
current Director/confirmed-manager ownership checks still apply. Advanced
preview and commit run the actual selected standards validation and applicable
consistency checks; unavailable or incompatible backends cannot publish.
The reviewed preview binds the advanced rules/shapes, helper context, exact
certified runtime and returned validation state.

A version 2 grant has all version 1 fields plus `advanced_config_sha256`
(null when no companion exists) and `proposal_review`. Direct advanced
publication may use null `proposal_review`; it still needs the exact validated
preview and current advanced scope. A saved proposal revision instead requires
`proposal_review: {proposal_id, revision, revision_sha256, validation_sha256,
review_sha256}`. `publish_revision` verifies this exact current immutable
candidate, eligible validation, accepted review and target snapshot before
calling the transactional publisher. Review acceptance, saving and a browser
click confer no authority by themselves.

The accepted proposal revision cannot change after its publication intent is
saved. Partial and complete receipts retain its review identity. Recovery uses
the original pre/post bytes, original reviewed companion digest and a fresh
current grant. Unknown edits and changed authority, rules, shapes or backend
certification block replay. Successful recovery does not overwrite later edits.

`preview`, `publish` and `recover` are registered ontology guard adapters.
Enabled guards check exact semantic action context before dispatch, recheck
under the publication lock and recheck unchanged context before each selected
replacement. The owning publisher retains source/version, current authority,
target compare-and-swap, receipt and recovery responsibility. A guard's
conformant semantic result is never a substitute for those checks.

See [the proposal workflow](proposal-workflow.md) for immutable draft storage,
native generation, browser session controls and lossless RDF staging.

## Native Curator grant version 3

Grant v1 core and grant v2 advanced remain unchanged. Grant v3 explicitly selects
`owner_profile: core-v1` or `advanced-v2`, plus `controller_origin: curator` and
a strict ontology-owned broker binding for the current live native call,
protocol, charter and policy. Only the current confirmed version-2 Task manager
can use this envelope. A memory grant supplies no ontology authority.

The advanced profile retains companion config, proposal review/revision, preview,
exact-file, lifecycle and publication checks. The grant is never converted into
a legacy object to compute its digest. Canonical record/config schemas, proposal
versions, journals and original-operation recovery keep their existing owners.
Every v3 publication or recovery check requires a current protected live context;
JSON evidence or an actor string alone cannot produce one. Native and OS proof
remain separate release gates.
