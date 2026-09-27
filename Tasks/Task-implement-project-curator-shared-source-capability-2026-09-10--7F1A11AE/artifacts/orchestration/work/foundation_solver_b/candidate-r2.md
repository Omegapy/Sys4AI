# Foundation candidate B, round 2

Status: complete independent design reassessment, ready for mapped review. This is not an implementation or native proof. Producer: /root/curator_manager/foundation_solver_b. Scope: the complete 21 criteria for TASK-005 through TASK-013. The exact current baseline and evidence bindings are in criteria-r2.json.

## Decision and evidence boundary

Use broker-controlled real native thread/fork, with intrinsic collaboration disabled before every actor's first turn. The recommended confinement unit is one loaded native actor per broker-owned App Server instance, including its own verified standalone code-mode companion. One broker retains authority, canonical-owner dispatch and the complete logical team. Each actor is created by the native App Server session API; no shell-launched model worker, fabricated collaboration receipt or separate user-owned Codex task substitutes for it.

This choice makes actor runtime/helper state and capacity release independently testable. Unloading an actor closes its own authenticated native runtime and verified helper groups, without interrupting another actor. It costs more local runtime processes than one shared instance. It removes dependence on an unproven per-thread helper namespace or an unsubscribe operation being equivalent to unload. Each candidate tool process still requires the enforced filesystem/network profile; separate processes and a common OS user alone are not security boundaries.

The frozen common packet contains 204 unique directly and transitively indexed references. Their bytes matched the supplied digests; JSON was parsed and 111 indexed Python occurrences were AST-parsed without importing or executing them. The 53 prior changed-file snapshots match their current-source counterparts. No runtime/model call, source test, new native actor, source edit or memory retrieval occurred in this reassessment.

The prior frozen checkpoint reports seven criteria passed at deterministic owner/helper level and fourteen blocked. It reports Task 96, memory 100, curate 52 and ontology 183 tests, including one ontology skip. These are retained attributed reports, not reruns by this solver. The v12 manager inspection establishes only the exact fixed native read and authenticated artifact callback. Its original machine-blocked result remains unchanged. No native team, full confinement, owner publication or current final-release pass follows from it.

The approved TRD permits a validated alternative native observation format. Genuine ForkedFromId lineage can satisfy the native relationship obligation if the complete required behavior is proved. It does not become AgentControl parentThreadId, SubAgentSource parentage, collaboration.spawn_agent or collabAgentToolCall. This is a material correction to the round-1 implementation target and requires the existing review, synthesis, acceptance and distinct-implementer cycle.

## Source findings that determine the design

The pinned runtime is /Applications/ChatGPT.app/Contents/Resources/codex, version 0.153.4, with the exact hash in the frozen schema index. Its supplied catalog/effective-setting evidence names gpt-6-astra/xhigh. Retain the original catalog and provider. The upstream rust-v0.153.4 files are supporting source evidence, not binary-equivalence proof.

1. ThreadForkParams permits threadId, exactly one of lastTurnId or beforeTurnId, model, config, cwd, permissions and runtimeWorkspaceRoots. It has no direct effort or allowProviderModelFallback field. Do not invent fields.
2. thread_processor.rs:4692 onward reads persisted source history, applies the cut, and calls load_for_cwd before creating the fork. An ephemeral source and omission of model/effort do not establish viable persistence or inheritance.
3. thread_manager.rs:1354-1401 constructs a real native Session fork with forked_from_thread_id and parent_thread_id absent. StartThreadOptions::new at lines 246-263 defaults allow_provider_model_fallback to false. The fork uses that constructor. This supports a no-fallback hypothesis; actual fork response/metadata and a negative unavailable-model case must still confirm it.
4. session/mod.rs:705-708 restores dynamic tools from persisted history when no new tools are supplied. Live callbacks through a fork remain unproved.
5. role.rs:70-116 applies typed role overrides and only six unrelated feature reductions. It cannot establish disabled intrinsic delegation or per-child sandbox through the proposed default role. Do not retry that route merely because the role is discoverable.
6. thread_unsubscribe_response_inner at thread_processor.rs:1011-1038 removes the connection subscription and reports notLoaded, notSubscribed or unsubscribed. An unsubscribed response is not itself native unload. The pinned schema also exposes thread/closed and notLoaded status; neither an absent response nor idle/interrupted alone frees capacity.
7. Current RuntimeCoordinator.capacity_ready counts every native_id forever and has no proven unload/release transition. Keep its conservative behavior until real release evidence is implemented; do not fix capacity by deleting IDs.
8. Current Broker.dispatch_verified converts every receipt_sequence using adapter.receipt, which constructs a notification observation. That is incompatible with actual assignment.inputs and conflict.deliver receipt shapes and cannot represent an outbound fork response.
9. Current native_observations and owner guards bind one protocol session_id to the live call context. A runtime transport, a broker run, a thread ID and the native Thread.sessionId are distinct. Forks on actor-owned instances must not silently inherit or fabricate a shared native session ID.
10. Current CodexAdapter records an unsolicited thread/started notification directly in its bound thread map. Separate observed-but-unadmitted identities from reserved/accepted actors; any unexpected actor must close admission and trigger reconciliation.

## Preserve the adequate foundation work

Retain the current neutral config/schema, policy validation, document classifier, grants, pure CLI, charter/roles and independent existing publishers. Do not rewrite them merely because the native creation route changes. Preserve all Phase 001 contract bytes, managed plan/TRD, active root installations, products and original round-1 artifacts.

Neutral configuration continues to have null project/repository/root/controller/runtime selections, no branches or entitlements, no autonomous writes, service/hook/schedule or external destination. Null bounds mean unselected and zero means no work. Specialization remains descriptive capability. Validation/status remains read-only with exact malformed/unknown/expired/incompatible diagnostics and no Task, model or installation side effect.

Keep every independent permission class and prior accepted standing entitlement. Missing authority holds; a matching standing entitlement permits a fresh exact operation grant without repetitive human approval. No configuration patch, role label, proposal or broker argument creates authority.

Keep classify_target's stable identity and exact source/section bindings, protected governance floor, explicit overrides above that floor, distinct AGENTS/README/generated-wiki/Task-history routes, generator ownership, alias and rename rejection. Any mixed/unknown target remains held. Candidate edits cannot reclassify the map or alter the current approver. Historical knowledge retains its meaning, source applicability and replacement relationships.

Preserve the finite wire-to-owner dispatcher, transport-derived current caller, private grants, source/import/config closure, lock-time rechecks, exact post-state replay and partial-owner recovery. The new runtime methods enter that same dispatcher; no raw config, model, arbitrary argv, filesystem writer or JSON-RPC proxy becomes a candidate tool.

Preserve Task schema 1, Task schema 2/orchestration 1, current orchestration 2 with observation protocol 1, memory record/config/grant 1 and native grant 2, and ontology record/config/grants 1/2/native 3. The new protocol is explicitly dispatched as described below. Ordinary workers still cannot publish. Only the current confirmed manager with exact Task generation, writer, role reads, source/payload/config and independent memory or ontology grant may invoke the existing owner. Capture off still prevents renamed automatic persistence; separately authorized explicit correction remains possible.

Retain the source CURATOR charter, four specialist role pairs, Director default and generic category rules. Reading another charter never activates it or takes over its work. Fresh role discovery, exact role reads, fit, separately verified skills/tools and stopping conditions remain required. The role's title changes no authority.

## Native creation, settings and frozen input

Add a small actor-runtime pool to curator_runtime.py using the existing CodexAdapter as a per-instance transport. Every adapter has one immutable connection ID and a bound kernel process instance. The pool maps native actor ID and load epoch to its adapter; candidates cannot choose an adapter or connection. Global typed control remains in the one broker.

A runtime_delegate request accepts only an existing reservation ID and accepted operation ID. The broker derives parent, role, scope, profile, settings and history cut from current canonical Task state and private accepted inputs. It rejects an unreserved slot, stale generation, wrong parent/caller, altered input or repeated creation. Task reservation is committed before any App Server fork request is sent. A parent call's acknowledgement is distinct from the later creation/activation receipt.

Creation sequence:

1. Verify source/build/schema/profile and accepted role/input bindings. Reserve one broker admission slot and one exact native creation attempt. Write the private pending operation before sending bytes.
2. Start that actor's pinned App Server instance with the protected runtime cwd/config and all intrinsic collaboration switches off: features.multi_agent=false, features.multi_agent_v2=false and agents.enabled=false. Preserve the selected standalone code_mode_host with disable_in_process_fallback=true and remote_url absent. Disable every other unselected surface and verify current effective configuration.
3. Read current parent settings from its authenticated loaded runtime. Pin model, reasoning effort, provider and relevant trusted configuration in the reservation. In the fork request set model from that observation and config.model_reasoning_effort from the same observation, together with the child's fixed permission profile and trusted cwd. This is explicit precreation propagation of the parent's observed values, not a postlaunch repair or an assumption about omitted fields.
4. Send actual thread/fork against the parent's exact persisted native source ID and frozen cut. The candidate cannot choose path, history, source analytics, config or model. Preserve actual request ID, raw request/response, connection identity and sequence. Require a distinct returned native thread ID.
5. Independently thread/read the returned ID through that actor's connection. Require actual forkedFromId equal to the reserved source ID, and retain actual parentThreadId/source/sessionId exactly, including null. Require no unexpected initial/goal-driven turn. Goals and autonomous continuation remain disabled.
6. Compare fork response and loaded metadata with all precreation settings/profile/root bindings before a role-acknowledgement turn. A mismatch, unavailable field or fallback is a failed creation attempt: close it without modifying it into compliance. The tagged default false fallback is supporting evidence only; test the actual unavailable-model denial in the disposable proof.
7. Deliver exact role/charter reads and frozen input. Accept the child's role acknowledgement only from its actual native dynamic request and matching hashes. Record the launch and activate the designated manager through existing Task owner gates. Later controller and worker canonical writes fail.
8. Release substantive work only after settings, role, input, callback and channel checks pass. No caller-controlled config/permission/model override is accepted on later start, steer or resume.

Use a completed parent initialization turn as the common cut: one exact source_thread_id and lastTurnId, with lastTurnId proved completed and a hash of the actual included history. beforeTurnId is an alternative only when its actual exclusion semantics are verified; never supply both. Both initial solvers use the identical source/cut/history digest and whole-problem packet. No earlier candidate, review, synthesis or private grant bytes may appear in that history.

Read and hash the actual fork histories before admitting work, using the supported history mode and complete paging when required. Exclude source metadata that is legitimately actor-specific only through an explicit comparison schema; do not remove model-visible content to obtain equality. Fix the history mode in the proof packet. Do not use unstable supplied history to manufacture independence. Later manager turns and collected candidate outputs cannot change the frozen cut used for a queued solver.

A lost fork response leaves one pending reservation and occupied admission slot. Reconcile the original request against authentic retained frames and owned native metadata. If exact identity/correlation cannot be established, hold it; do not retry by creating another native actor. Unexpected thread/started or tool-driven delegation belongs in an unadmitted inventory, not automatically in the bound control map.

## Persistence and existing account use

Real stored history is a dependency of this route. The controller and managers that are future fork sources must use verified persistent native histories. Workers may also persist so the same native identity can be unloaded and resumed. This persistence is runtime evidence, not a new Task ledger or project knowledge store.

Prepare a task-owned protected runtime home/state directory and exact per-actor runtime cwd/config directories. Keep canonical project data, candidate workspaces, runtime history, private broker state and helper caches separate. All runtime history/config/import directories are denied to candidate tools. A candidate worktree must not become the runtime cwd from which load_for_cwd discovers approving instructions or config.

Before any charged turn, the designated implementer must establish two precise properties in a host-reviewed non-model preflight:

- The supported runtime can use the selected test-owned persistence/state location while reusing the already selected account through the runtime's normal supported authentication mechanism. Inspect nonsecret account readiness only. Do not copy, read out, symlink or reconstruct credential material, set a new provider, start login or silently fall back to the normal user session store.
- The returned stored thread/history paths and state database location are inside that selected test-owned runtime scope, and ordinary Codex desktop projects/tasks are unaffected. Do not create/open/name a user-visible task to supply a seed. Native threadSource analytics and cwd alone do not establish storage isolation.

The provided schemas do not prove these storage/authentication properties or a particular relocation configuration key. They are named capability gates, not promises. If normal account reuse is unavailable with isolated persistence, return native_auth_reuse_unavailable. If storage isolation is unsupported or ambiguous, return native_storage_unproven. Do not launch model work through an alternative credential or user-visible-task route. The exact supported launch settings must be materialized before the host authorizes the proof packet.

Once proved, every actor instance uses the same selected account and task-owned native store; the broker alone can resolve source IDs there. Restrict source selection to its immutable owned inventory. Shared storage of native histories is safe only because candidates cannot read it or invoke raw native history/list/fork APIs. Reopen exact source lineage/settings/history after resume; persistence does not preserve authorization by itself.

## Versioned native observations and live authority

Retain observation/protocol version 1 unchanged. Add protocol schema_version 2 and observation schema_version 2 for broker-native-fork execution. The backend remains codex-app-server-v2. The effective version is the explicit tuple of Task orchestration version, protocol version and observation version; unsupported combinations fail before mutation.

Protocol v2 binds broker_run_id, exact runtime/schema/source manifest and observation version. It does not call broker_run_id a native Session ID. Each observation contains its actual native thread/session IDs, connection ID, kernel process-instance binding and load_epoch. CallContext v2 binds those same values plus actual server request/turn/call/tool/sequence/digest. The transport creates it; serialized records or model arguments cannot do so.

A fork-launch observation contains:
- the original canonical reservation reference and authenticated delegator call;
- actual outbound thread/fork request/correlation/digest on the child instance;
- actual correlated native response and independent metadata read;
- actual fork source/cut/history digest, new thread/session ID, forkedFromId and unchanged native parentThreadId/source;
- exact settings/profile and runtime process bindings.

The broker authenticates frame ownership against its protected sent/received journal. Structural owner validation checks the typed relationship and current Task binding; hashes by themselves confer no authority. Record outbound frames as well as incoming notifications/responses. Keep raw bytes, parsed canonical digest and direction distinguishable. All evidence is bounded and excludes secrets.

Replace generic receipt_sequence conversion with an event-specific decoder. A reference has protocol version, expected kind and protected operation/sequence locators; the broker loads its body. Never accept a caller-supplied receipt body.

| Canonical operation | Required actual evidence |
| --- | --- |
| manager.reserve bootstrap | current controller call plus native active status, exact controller charter/protocol |
| manager.receipt / assignment.receipt | fork-launch, exact pending reservation and native creation correlation |
| manager.activate / assignment.reads | actual child role acknowledgement and exact role/charter/input hashes |
| assignment.inputs | input-delivery: actual turn/start or turn/steer request/response, same recipient/load epoch, exact packet bytes/digests |
| conflict.deliver | conflict-delivery: exact originating recipient and explanation bytes, actual start/steer delivery; optional acknowledgement reported separately |
| assignment.observe / manager.reconnect | current status with freshness and binding; no historical turn as a current lease |
| assignment.resume | same native identity, current stored lineage and resume response/metadata, new confirmed load epoch |
| stop / reconciliation | actual interrupt request/ack, terminal/native status where available, runtime closure and exact owner post-state |
| owner publication | current authenticated manager request plus independent exact owner grant and current canonical Task/writer/source state |

Task input/conflict receipts must be generated from real delivery frames and match the owner's packet/conflict hashes. Successful delivery is not evidence the actor read or accepted it; role/read acknowledgement remains separate. Reconciliation arrays decode each mapped assignment's proper kind, not a scalar status notification.

Apply this dispatch to every path: event recording, historical validation, lifecycle, input rebind, conflict return, reconnect, pause/replacement and memory/ontology manager authorizers. Existing memory grant-v2 and ontology grant-v3 can retain their outer fields while explicitly dispatching their nested broker protocol and live-call version; only documented version tuples are accepted. Preserve the original protocol-v1 branch exactly. Preserve raw owner grant-file digests and all core/advanced semantic, freshness, journal and scope checks.

Only the current loaded manager with the exact current load epoch may publish. An unload/reconnect does not change Task generation by itself, but grants from the old channel/epoch are invalid. Logical manager replacement still requires the existing reconciled generation transfer. No release event deletes a native identity or rewrites earlier provenance.

## Capacity, stopping and actor-private helper state

Capacity is a broker admission limit on owned loaded native runtimes. It is not the model catalog's native spawn limit, agents.max_threads, the host's four collaboration slots, or a claim about the provider. Count pending creation, loaded actors, unloading actors and uncertain identities as occupied. Record actual loaded/running owned counts separately. Preserve every required logical slot in the queue.

Extend Actor with load_epoch, runtime_binding, capacity_state and immutable lifecycle receipts. Use reserved -> creating -> loaded -> ready -> working -> unload_requested -> released, with explicit creation_uncertain/unload_uncertain states. Keep native_id permanently. A resumed actor keeps native_id and gains a new load_epoch only after real resume/metadata confirmation.

runtime_release is a typed manager control over an authorized actor. If the request originates inside the target's active dynamic callback, acknowledge admission first and schedule shutdown after returning the callback; do not deadlock waiting for its own outstanding request. Close work/publication admission and invalidate future calls for that epoch before interruption.

Request actual turn interruption for any active turn; collect its native acknowledgement and available terminal state. Reconcile candidate outputs and current owner post-state. Close the actor-owned App Server and its owned companion/process groups using the existing kernel-identity machinery. Verify executable hash, UID, actual ancestry and microsecond process-start identity before signalling; verify both groups and the original instances absent afterward. A changed PID identity, detached/unaccounted descendant, missing final observation or failed ownership check is uncertainty, never permission to kill an unrelated process.

The release receipt distinguishes native turn outcome, connection shutdown, verified runtime/helper termination, owner reconciliation and broker admission release. It may report remote provider completion/cancellation unknown; closing a local process does not prove provider billing stopped. Only the exact verified absence of the actor's isolated runtime/helper plus closed broker authority and reconciled owned writes frees its local admission slot. Idle, completed turn, interrupt acknowledgement, unsubscribe or dictionary deletion do not.

An unsubscribe request may be retained as a native control observation. Do not equate unsubscribed/notSubscribed with unload. A correlated thread/closed plus a current notLoaded read is useful native evidence when available, but a missing event cannot be invented. The per-actor runtime design provides a separately explicit runtime-closed release route. Other actors' native runtimes remain observed live and usable throughout a release test.

Resume starts a fresh owned runtime, calls actual thread/resume for the same stored native ID with protected preselected config/profile, and verifies stored lineage and current settings before a new work turn. It never creates another fork and calls it resume. Old epoch callbacks, grants and results fail. All normal current Task/input/review gates still apply.

The helper-state proof must examine actual programmatic state, not model self-report:
- In actor A, execute a fixed inspected program that generates a synthetic random value, stores it under a fixed known key, and returns only its digest.
- In a later A invocation, execute the fixed load-and-hash program and compare the engine-returned digest. This proves positive persistence across actual calls.
- Actor B executes the same-key read through its actual helper and must not obtain A's value. Also try A's actor identifier and artifact handle through every exposed broker/helper route.
- Bind the actual native tool name, complete arguments/program digest, request/response locators and engine output to each result. A model-produced JSON claim or an artifact callback echo cannot substitute for actual execution.
- After A unload/resume, helper state is explicitly reset unless a separately implemented actor-scoped store owns durable state. Canonical artifacts persist through their existing owner and exact allowed handles. Test reset and continued B isolation.
- Require distinct actual helper process instances for separately loaded actors. If the runtime reuses a shared companion or exposes a state channel that defeats isolation, hold the mode. Do not claim that actor-name key prefixes secure an unscoped shared store.

Keep all original adversarial classes: branch/diff/note/config injection; policy/validator/charter/map self-approval; grant/actor/generation forgery and replay; direct canonical/private read/write; raw process/protocol and helper execution; import/environment injection; symlink/hardlink/case/Unicode/rename and parent-directory races; independent network/tool denial. Add intrinsic peer/list/message/control and helper-state probes for each actual actor. Each negative needs a positive in-scope action, exact source/profile/runtime binding, real error/result and final canary inventory. Credentials remain synthetic canaries only.

## Exact implementation delta and tests

Modify the existing source modules rather than creating another execution system:
- curator_runtime_codex.py: pinned fork/unsubscribe method schemas, sent/received frame journal, per-instance identity, fork/read/resume validation, effective precreation settings, and unexpected-actor handling. Keep the v12 exact canonical non-login wrapper matcher and strict companion checks.
- curator_runtime.py: actor runtime pool, explicit creation/load/release epochs, immutable identity history, complete category queues, targeted supervision and partial shutdown results.
- curator_broker.py: finite runtime_delegate/release/resume controls, per-caller adapter lookup, event-specific receipt loading, exact owner/actor/epoch authorization. Resume must actually call resume; it must not fall through to followup.
- native_observations.py and orchestration_state.py: explicit protocol/observation/live-call v2 dispatch, genuine fork lineage, input/conflict/control/reconciliation kinds and current actor epoch. task_state.py changes only if its strict creation/lifecycle/validation entry points need the new version tuple.
- memory_evidence.py, memory_publish.py and ontology_authority.py: route current manager validation through the new explicit version tuple while preserving old formats and all owner semantics.
- references/native-protocol-v2.md plus affected source owner/role/Task documentation: explain actual fork provenance, explicit settings propagation, storage boundaries, epoch release and evidence levels. Phase 001 files remain unchanged.
- run-native-proof.py and targeted tests: implement the staged packet/runner below with truthful bound counters, evidence matching and final-source bindings.

Keep the current policy model_calls field's meaning. A host turn counter cannot satisfy a selected hard provider-call or token limit. Where that bound is unsupported, return the precise unsupported-bound diagnostic and preserve work. The separate VerificationAdmission scope may select supported elapsed-time, turn-admission, runtime-count and byte limits without claiming a provider-call/token cap. Do not silently reinterpret the existing config schema or advertise a production mode whose selected bounds cannot be enforced.

Required deterministic additions are:
1. Fork schema and typed request generation; current-parent settings copied before creation; unavailable-model/fallback/mismatch denial without repair.
2. ForkedFromId accepted only in the new dialect; false AgentControl parentage and mixed/unknown version tuples rejected; old records retain exact validation.
3. Realistic request/response/notification routing fixtures for role reads, assignment.inputs, conflict.deliver, status, interruption, release and resume. Receipt-kind substitution and wrong recipient/history/packet/epoch fail.
4. Pool capacity transitions retain native IDs, queue the full team, deny duplicate uncertain creation, require exact verified release and reject late old-epoch work.
5. Owner grants require current loaded manager/channel/epoch and exact proposal/source/Task scope. Ordinary-worker, forged Director, stale-manager, replay and later-edit cases remain denied.
6. Current policy/classification/role/grant tests continue to cover all retained criteria; rerun affected existing owner suites after the integrated change. Tests remain deterministic fixtures, never native proof.
7. Fixed-probe matcher tests reject altered wrapper/argv/program/output and distinguish genuine helper state results from echoed artifact claims.
8. Stop continues through individual failures and never releases an uncertain slot or claims a hard provider cap.

## Smallest decisive next proof and complete proof

No live action is authorized for this solver. After synthesis and exact acceptance, the designated implementer prepares one new immutable proof packet for host authority assessment. Do not reuse the expired v12 scope or its absent historical runner bytes.

Stage 0 is non-model capability preparation: verify the pinned binary/schema/companion and full effective feature closure; establish isolated native persistence and existing account reuse without credential copying; materialize exact paths, profiles, settings and source hashes. Any missing property returns the named prerequisite failure before a charged turn.

Stage 1 is a small real native fork diagnostic:
- Four native identities: Curator controller, its real native-fork manager, and two independent native-fork solvers. One distinct App Server and companion per loaded actor; broker admission maximum three loaded/creating runtimes. These are selected local limits, not runtime-advertised hard caps.
- Persist the source histories; reserve before each creation. Freeze the manager's completed common-input cut for both solvers. Unload the controller through verified runtime release to allow both solvers while retaining all four historical native IDs.
- At most twelve broker-issued turn/start requests and twenty minutes supervised elapsed time, with thirty-second I/O waits and twenty-second owned-stop grace. Stop at the first applicable limit. Native provider calls/tokens are observed when available but have no claimed hard cap.
- Use only gpt-6-astra/xhigh from current observed parent settings, original advertised catalog/provider, selected normal account reuse and the pinned 0.153.4 runtime. No catalog override, fallback model, login, dependency/service/hook or Git action.
- Use synthetic Task data for reservation, handoff and typed input/conflict delivery. No real project publication. Prove actual fork lineage, manager-only writer, precreation settings, identical excluded-history input, authenticated callbacks, all intrinsic delegation/control routes disabled, actor-private helper state and targeted unload/resume while another actor remains live.
- Deny candidate network and unselected tools. Any later network-negative probe needs its exact synthetic loopback endpoint separately materialized in the packet; no unselected internet destination is needed.
- Exact root/native storage/helper/profile/role/input/canary/expiry/source hashes, tool programs, native actions and stop rules must be filled before execution. A prerequisite failure stops this diagnostic; it does not trigger a new route automatically.

Stage 1 passes only its narrow mechanism. Then run the complete unchanged NP-001 through NP-014 obligations using genuine native forks and honest protocol-v2 receipts: Director-default routing; full generic, complex and extra-complex teams with distinct required identities; manager acceptance and dedicated implementation; complete native input/conflict/control/recovery paths; current inherited settings; actual independent memory and ontology publication; all malicious-content/filesystem/process/helper/tool/network cases; and final source/profile/runtime reinspection. Preserve all queued agents and all independent publication scopes.

Do not create a partial topology and call it complete. A generic worker, two full-problem solvers, mapped extra-complex reviewers, senior and dedicated implementer keep their original rules. Runtime-model use and publication remain separate authority classes. Any source/profile/runtime mutation invalidates affected native results; TASK-047 repeats affected proof against final release bytes.

## Handoff and unresolved proof facts

This proposal selects a concrete fork and actor-runtime mechanism and retains all 21 criteria. The remaining unknowns are actual-runtime prerequisites: isolated persistence with existing account reuse, native fork/dynamic-tool behavior on the pinned binary, effective model/profile equality, helper-state/tool isolation, exact unload/resume behavior and complete publication/confinement. They are not permission to weaken the requirements or continue optional investigation.

Only candidate-r2.md and criteria-r2.json are written in this solver turn. Original artifacts remain unchanged. No source implementation, native execution, new actor, external research or memory publication is part of this result.

Supporting criteria-r2.json SHA256: 3ab5a08430cf9c5ae0d27740df45f14b3946138d369cb4a294b188c56d112819
