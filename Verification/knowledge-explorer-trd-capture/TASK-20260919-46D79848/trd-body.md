## Destination

Define the full first release of Project Knowledge, the proposed human-facing Ontology Explorer for the Sys4AI depot. The intended product replaces the ontology workbench frontend with a local, read-only reader and relationship explorer that makes definitions, connections, processes, and supporting sources understandable while preserving canonical ontology authority and existing agent workflows.

## Captured user intent

U01: The user explicitly requested a new Task and To-TRD capture from `Sys4AI_Project_Knowledge_Explorer_Recommendations.md`, with document instructions distinguished from the user's request. U02: The user's subsequent answer, "do Full proposed first release", selected the complete first-release scope described by that source. This includes the interactive map, equivalent text navigation, source-supported process reading, security, accessibility, distribution boundaries, and future acceptance evidence; it is not limited to an initial reader slice.

The present deliverable is a requirements baseline. Selecting the scope does not approve unseen TRD content or authorize implementation, dependency installation, Git activity, deployment, external publication, or adoption into other projects. Commands and execution briefs in the supplied document remain source material. The requirements below describe the intended future product and its acceptance, not work already performed.

## Context and sources

- U01: Current explicit `/goal`, `$task new`, and `$to-trd` request in this project, dated 2026-09-19.
- U02: Current user clarification selecting "Full proposed first release", as provided in the confirmed Task handoff for `TASK-20260919-46D79848`.
- SRC: Supplied recommendations dated 2026-09-16, original path `/Volumes/P-SSD/AngryOwl/Sys4AI_Project_Knowledge_Explorer_Recommendations.md`; inspected immutable copy `/Volumes/P-SSD/AngryOwl/Sys4AI/Tasks/Task-capture-project-knowledge-explorer-requirements-2026-09-19--46D79848/artifacts/orchestration/source-recommendations.md`; SHA256 `b79d6122615b85f2ca42f0334cdecd7677578085014bb6c82565180e6264d38e`. Section, UX/DATA/SAFE/PORT/PERF, and AT locators below refer to this exact copy. Its 1,304 lines were read in full. Its linked repository observations are version-specific, and its layouts, APIs, budgets, and implementation sequence are proposals, not observed product behavior.
- GOV: Current root `AGENTS.md`, `ROLE.md`, `SOUL.md`, and `SPECS.md`, read under `/Volumes/P-SSD/AngryOwl/Sys4AI`. They establish source-collection ownership, the explicit Template pipeline, independent project-local adoption, preservation, and evidence-bound completion. This root is the depot manager, not an ordinary product template.
- LIVE: Facts supplied by the host's current read-only inspection: root HEAD is `744c8b06d5fda905201145ed313a2da8de2e601f`, matching SRC's Sys4AI snapshot; pre-existing local changes exist; the old frontend still exposes authoring; retrieval defaults to `semantic=True`; root retrieval configuration uses `default_hops=2`, `default_limit=20`, `max_hops=8`, `max_limit=100`, and `max_context_bytes=32000`. Absence of step/order-named fields in the inspected `project.jsonld` is not a complete inventory of process sources. These observations establish current context, not browser or implementation verification.
- STD: SRC §25 references [WCAG 2.2](https://www.w3.org/TR/WCAG22/), the [WAI-ARIA combobox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/), and [Understanding Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html). The host inspected the official WCAG and APG sources during capture. They define acceptance and interaction targets; no conformance result is claimed. SRC's other linked dependency and licensing references remain implementation research inputs requiring version checks before use.

## In scope

- Four reading destinations: Overview, Terms, Processes, and Map, with deterministic search, alphabetical/category browsing, stable identity routes, browser history, theme choice, copy actions, and source inspection.
- Canonical, bounded, snapshot-consistent read data; faithful definitions and typed relationships; a focused interactive map with full text equivalence; honest status, gaps, limits, failures, and evidence freshness.
- A dedicated read-only local Python service, protected sessions and sources, offline production assets, explicit launch/build/health contracts, and separation from optional AI, standards, inference, and memory services.
- Future replacement and retirement of the active human workbench; preservation and separate regression verification of agent/CLI authoring, publication, recovery, data, and history.
- Reusable source changes, verified distribution to the neutral Template, separately authorized adoption into the active root, and isolated verification with a second namespace fixture. These are intended delivery boundaries, not grants to perform those actions during TRD capture.
- Future unit, service, browser, accessibility, non-mutation, performance, usability, and distribution evidence, covering all SRC AT-01 through AT-36. Proposed targets retain their qualifications below.

## Out of scope

Ontology editing, drag-to-connect, proposal/review/publication management, inference or query consoles, raw SPARQL, embedding setup, AI chat or generation, agent/skill execution, Task dashboards or mutation, a memory browser, multi-project federation, automatic project scanning, public hosting, collaboration, and hidden Advanced tabs that reintroduce these features are excluded from the first release.

Optional relationship-path search and future Related history expansion are outside this release. Automatic process-flow generation and a second graph library are not required. Missing canonical explanations or ordered steps are displayed honestly; this UI change does not authorize inventing or publishing them. A later content change retains its existing review/authority process.

A complete Logseq fork, embedded Logseq editor/application, copied Logseq graph implementation, production Node server, additional graph database/RDF store, GraphQL service, independently synchronized browser database, implicit package/model/service installation, CDN assets, analytics, cloud logging, external fonts/images, and a general settings workbench are excluded. No bulk update of registered products, historical verification snapshots, or prior initializer editions is authorized. No downstream implementation plan, product code, implementation tests, Git publication, deployment, or external action is performed by this capture.

## Task requirements

### REQ-001 - Replace the human authoring interface with four reading destinations
- Requirement: Provide Overview, Terms, Processes, and Map as one reader-oriented application, with no browser authoring, administration, or execution capability.
- Source: U02; SRC §§1.1-1.4, 5, 6, 7.1, 19.2, 24; UX-01, SAFE-01.
- Acceptance: AT-01: Launching the human interface shows only reading/exploration destinations and loads no draft, review, publish, inference, query-console, AI-generation, or other authoring modules or controls, including hidden Advanced modes.
- Acceptance: The project name and global search remain visible; navigation collapses on smaller screens; theme/help remain secondary controls; raw storage kinds, build actions, readiness matrices, proposal counters, and maintenance actions do not become the reader's main navigation.
- Depends on: None.

### REQ-002 - Read the selected canonical ontology without creating another authority
- Requirement: Base reader information on the selected project's canonical ontology, locked imports, and source references through existing read semantics and a thin presentation adapter.
- Source: U02; SRC §§1.4, 3.4-3.5, 5 DATA-01/DATA-02, 11.1, 12.2, 23; GOV.
- Acceptance: Exact canonical identities, labels, definitions, types, aliases, scope notes, examples/non-examples, lifecycle, fact kind, module/version, source references, and canonical locations retain their meaning in the reader; absent fields do not produce invented content.
- Acceptance: The adapter creates no second ontology engine or synchronized authority, publishes no changes, and does not derive authoritative data by parsing generated wiki pages or requiring a wiki rebuild.
- Depends on: None.

### REQ-003 - Keep status, evidence, meaning, and authority distinct
- Requirement: Present lifecycle, fact classification, source freshness, and execution authority as separate concepts, with interpretation-relevant warnings visible beside affected information.
- Source: U02; SRC §§6.4, 7.7, 9.2, 10.1-10.4, 12.2; DATA-02, DATA-03.
- Acceptance: AT-08: An exact-ID lookup of a deprecated entry retains its historical definition, status, and recorded replacement link rather than rewriting history.
- Acceptance: AT-09: A draft or inferred record exposed through an explicit permitted filter remains visibly distinct from approved asserted knowledge. Default reading prioritizes approved, explicitly recorded information.
- Acceptance: Inferred denotes a selected reasoning process's conclusion; Source changed denotes an evidence-version mismatch, not proof of falsity. Approval, freshness, and truth do not collapse into a verified badge. Ontology relationships confer no user/agent action authority.
- Depends on: REQ-002

### REQ-004 - Offer source-backed starting points
- Requirement: Make Overview a useful starting page with the configured project purpose, search, real starting identities, and an obvious map entry point.
- Source: U02; SRC §§6, 7.1, 18.5; UX-02, PORT-01.
- Acceptance: Starting points come from reviewed presentation configuration or a deterministic explicit project record; node degree does not manufacture a hierarchy. If no starting points exist, browsing categories and search remain available without fabricated content.
- Acceptance: With no local extension records, imported core vocabulary remains browsable and the absence of local additions is explained; the first screen is neither a management dashboard nor an unfiltered whole-project graph.
- Depends on: REQ-001, REQ-002

### REQ-005 - Search deterministically without optional AI
- Requirement: Reuse canonical deterministic ranking for exact identity, preferred label, alias, and lexical definition/scope matches with semantic fallback explicitly disabled for ordinary explorer search.
- Source: U02; SRC §§3.3, 5 UX-02, 9.1, 11.3, 24; LIVE retrieval defaults to semantic=True.
- Acceptance: AT-02: Searches for a preferred label, alias, exact ID, and words in a definition return deterministic relevant identities and match reasons with `semantic=False`; the existing agent search default/contract is preserved.
- Acceptance: Search neither invokes an LLM nor infers synonyms or generates definitions during navigation. Exact/lexical search remains usable when optional richer search, embeddings, RDF/standards, or inference services are unavailable.
- Depends on: REQ-002

### REQ-006 - Make results and discovery understandable
- Requirement: Provide compact search results and alphabetical/category browsing using verified canonical types or reviewed presentation mappings, preserving ambiguity and alias identity.
- Source: U02; SRC §§7.2, 9.3-9.5, 12.2-12.3; UX-02, DATA-01.
- Acceptance: Results show a human label, supported category, short recorded definition excerpt, disambiguating module/project where needed, and a useful non-obvious match explanation without the scoring formula.
- Acceptance: AT-03: When two entries share a label or alias, both appear with distinctions and neither is silently selected. An alias match retains the preferred label and canonical identity rather than creating another page/node.
- Acceptance: Categories such as All, Terms, Roles, and Skills appear only when supported by the selected project's types/configuration; category membership never uses name-substring guesses. A neutral or specialized project can expose its supported categories without changing shared frontend code.
- Depends on: REQ-005

### REQ-007 - Filter and page search without losing valid matches
- Requirement: Apply visibility, category/lifecycle filters, and ranking before response pagination, with stable bounded continuation and honest incomplete results.
- Source: U02; SRC §§7.2, 7.7, 9.2, 12.3-12.5; UX-02, PERF-01.
- Acceptance: AT-04: Category/lifecycle filtering across a multi-page result set preserves valid later matches. AT-05: Within one snapshot, continuation produces no duplicate or skipped identities.
- Acceptance: Less common filters live under one control, active filters are removable chips, and empty results preserve the query and offer Clear filters or alias guidance. A byte-limited empty response is identified as incomplete, not No matching term.
- Depends on: REQ-005, REQ-006

### REQ-008 - Present faithful readable entries
- Requirement: Show the canonical name and definition first, then recorded context, readable incoming/outgoing relationships, sources, and optional technical details.
- Source: U02; SRC §§6.4, 7.3, 10.1-10.2, 12.2; DATA-01.
- Acceptance: AT-07: Definition, aliases, scope note, examples, and non-examples appear faithfully when recorded; absent sections are omitted without runtime paraphrase or invented explanations. Technical IDs do not precede the human definition.
- Acceptance: View on map, Copy local link, and Copy stable ID are available reading actions; exact ID, kind, type IDs, module version, fact classification, and canonical location remain inspectable under Details without edit/run actions.
- Depends on: REQ-002, REQ-003

### REQ-009 - Preserve inspectable relationship meaning and direction
- Requirement: Make each canonical relationship independently readable with its exact identity, endpoints, predicate, qualifiers, lifecycle, fact classification, and evidence.
- Source: U02; SRC §§4.2, 7.3-7.4, 8.4, 10.1, 12.6-12.7; UX-03, DATA-02.
- Acceptance: AT-13: Distinct predicates between the same endpoints preserve both canonical relationship IDs, meanings, classifications, and evidence; endpoint-pair grouping never discards a relation. Any visual bundle exposes its count and every member.
- Acceptance: AT-14: Incoming traversal retains the canonical subject-predicate-object meaning and directed arrow. An inverse phrase requires a reviewed mapping; otherwise the original sentence order is shown. A friendly relatedTo label never becomes depends on or causes.
- Acceptance: Selecting a map edge, its label, or textual description opens the precise relationship with definition, qualifiers, sources/freshness, and stable ID. A scoped/conditional relation never appears unconditional because a qualifier is lengthy.
- Depends on: REQ-002, REQ-003

### REQ-010 - Explain processes only to the extent sources support them
- Requirement: Provide explanatory process pages whose purpose, applicability, roles, inputs, outputs, related skills/documents, and ordering are supported by selected canonical records or explicitly linked source sections.
- Source: U02; SRC §§3.8, 7.5, 20, 21 AT-17/AT-18; UX-05.
- Acceptance: AT-17: A supported process displays only supported fields and sequence. Ordered text appears before any flow diagram; process pages do not execute a workflow.
- Acceptance: AT-18: When order is absent, the page states "An ordered description has not been recorded. These are the documented relationships." and shows those relationships and sources. Graph paths, relatedTo edges, dependencies, and left-to-right layout never establish execution order.
- Acceptance: Any optional process diagram exposes evidence for its sequence and branches; the first release can satisfy process access using numbered text and the existing map without another graph library or automatic flow generation.
- Depends on: REQ-008, REQ-009

### REQ-011 - Inspect exact evidence without losing reading context
- Requirement: Open an entry's or relationship's authorized source in a secondary panel with a readable label, project-relative path, locator, freshness, and bounded content.
- Source: U02; SRC §§7.6, 10.3, 12.1, 13.3, 15.6; DATA-03.
- Acceptance: AT-19: The correct selected identity/reference opens its authorized section or bounded excerpt with evidence status. Hashes remain available under Details while the current entry is retained.
- Acceptance: If exact section extraction is unreliable, content is clearly labeled as a bounded excerpt or bounded text view rather than the exact cited passage. Opening evidence executes no source instructions and triggers no automatic external fetch.
- Acceptance: AT-20: Changed source bytes are revalidated on opening and visibly distinguished from the originally recorded evidence version; safe recorded definitions remain visible with the mismatch warning, and no provenance hash is repaired by the read.
- Depends on: REQ-008, REQ-009

### REQ-012 - Preserve navigation state through stable identities
- Requirement: Use exact canonical IDs in routes and preserve useful discovery, reading, and map context through view switching and browser Back/Forward.
- Source: U02; SRC §§4.1, 6.3, 8.2, 14.2; UX-06.
- Acceptance: Back/Forward restores selected entry, query, filters, and useful map state. Terms/Map switching preserves selected identity. A deliberate node selection creates one history event, while camera movements do not each create one.
- Acceptance: Local link copy excludes credentials and clearly depends on the correct live local service; stable-ID copy supports durable reference without presenting an ephemeral loopback URL as a public sharing link. Standard entry links retain expected new-tab and copy-link behavior after authentication where practical.
- Depends on: REQ-001, REQ-008

### REQ-013 - Keep harmless preferences separate from knowledge
- Requirement: Support light, dark, and system themes and a simple reset for project-namespaced view preferences without persisting knowledge edits or source bodies in browser storage.
- Source: U02; SRC §§4.1, 5.3, 6.1, 14.2, 16.4.
- Acceptance: Theme and optional layout/panel preferences remain isolated per selected project; resetting them changes presentation only. Sensitive source bodies remain in memory, and no canonical edit or general administration/settings model is introduced.
- Depends on: REQ-001

### REQ-014 - Start the map with a bounded focused neighborhood
- Requirement: Open Map around a selected canonical identity and its direct relationships; without a selection, offer a reviewed starting point or term picker.
- Source: U02; SRC §§8.1, 8.6, 17.3; UX-04, PERF-01; LIVE current retrieval bounds.
- Acceptance: Initial map depth is one relationship step. Approximately 25 visible nodes and 50 edges are proposed initial display defaults, subordinate to stricter project, traversal, item, and payload bounds rather than a request to change agent limits.
- Acceptance: No whole-project fetch is used for initial layout, a decorative overview count, or a visual search for a starting node. Root agent defaults remain 2 hops/20 results with maximums of 8 hops/100 results and 32,000 UTF-8 bytes; map defaults do not rewrite those contracts.
- Depends on: REQ-002

### REQ-015 - Separate map selection, focus, and deliberate expansion
- Requirement: Provide explicit map actions for selection, focus, bounded expansion, pan, zoom, Fit view, Reset view, and equivalent list access.
- Source: U02; SRC §§8.2, 14.2; UX-04, UX-06.
- Acceptance: AT-10: Selecting a node highlights it and updates readable details without moving the camera or changing graph focus. AT-11: Focus here deliberately changes the neighborhood, and Back restores the prior useful state.
- Acceptance: Show more connections adds supported nodes/edges from another bounded request/page. Dragging empty space pans; visible zoom controls change scale without changing selected data; Fit view fits visible data only; Reset view restores the focused neighborhood and default presentation.
- Acceptance: Escape closes a temporary preview with predictable focus. Essential actions do not depend on double-click, hover, dragging, or a context menu.
- Depends on: REQ-012, REQ-014

### REQ-016 - Keep the visual graph semantically faithful
- Requirement: Use canonical node and relationship IDs, preserve graph structures and qualifiers, and distinguish asserted relations from other display layers.
- Source: U02; SRC §§8.3-8.4, 12.6-12.7; DATA-02, UX-03.
- Acceptance: AT-15: Parallel relations, self-loops, cycles, and qualified relations render without semantic merging or infinite expansion. Relation records normally render as edges; predicate records remain inspectable through labels.
- Acceptance: Explicit semantic relations form the default layer; type annotations, source associations, document mentions, inferred results, and navigation categories remain distinct and are not converted into canonical assertions. Sources/bindings do not automatically become graph nodes.
- Acceptance: Endpoint labels resolve in the same snapshot. Broken references are reported with the underlying ID still inspectable; no invented label makes a broken concept look valid.
- Depends on: REQ-009, REQ-014

### REQ-017 - Keep map presentation readable and stable
- Requirement: Use a restrained, stable two-dimensional map whose direction and labels remain understandable and whose layout does not imply unsupported meaning.
- Source: U02; SRC §§8.3, 8.5, 14.5, 16.6, 17.5.
- Acceptance: Directed edges show direction and human predicate labels; at crowded zoom, selected/adjacent edge labels remain visible and all labels remain available in the list/details. A compact legend and the instruction "Select a term to read it. Use Focus here to explore its connections." explain operation.
- Acceptance: Expansion preserves existing positions where practical, places new nodes near their source, performs only bounded layout adjustment, and stops. Selection or a details panel does not restart the entire layout. Reduced motion is honored; no 3D, continuous motion, glow, unexplained importance sizing, physics sliders, or force controls appear.
- Acceptance: Graph distance and position are not represented as semantic similarity, causality, chronology, or importance. If layout times out, valid data remains available in a stable fallback arrangement; an explicit Arrange control is optional when needed.
- Depends on: REQ-015, REQ-016

### REQ-018 - Explain limits without inventing completeness
- Requirement: Enforce and distinguish server query limits, browser display limits, and filter exclusions, reporting only supported counts and continuation possibilities.
- Source: U02; SRC §§7.7, 8.6, 12.4, 17.3; PERF-01, DATA-01.
- Acceptance: AT-06: Omission by byte, time, traversal, or item bounds yields visible incomplete coverage, its reason, displayed scope, and a way to narrow/continue rather than an assertion that nothing exists. AT-12: High-degree expansion remains bounded and discloses omitted connections.
- Acceptance: An unknown total or existence of further results remains explicitly unknown; More connections are available is used when only that fact is established. Discovered available_results is never relabeled as a whole-graph total without stronger evidence.
- Acceptance: A proposed initial cumulative browser ceiling of 100 nodes and 200 edges is evaluated separately from each request's bounds. At its ceiling, focus, fewer connections, filters, or a list remain available rather than unbounded accumulation or browser freezing.
- Depends on: REQ-007, REQ-014, REQ-015

### REQ-019 - Give the relationship list full map equivalence
- Requirement: Provide a first-class accessible List view driven by the same normalized relationship data as Map, with equivalent substantive information and navigation.
- Source: U02; SRC §§1.1, 8.2, 14.4, 16.2; UX-07.
- Acceptance: AT-16: Map/List switching retains selection, filters, returned scope, relationship IDs, direction, and warnings. List users can open entries, inspect evidence, focus a term, and request more connections with the same semantics.
- Acceptance: AT-29: Major reading and exploration tasks can be completed through keyboard and list without canvas, dragging, hover, or double-click. A small control set avoids hundreds of invisible graph controls in tab order; meaningful result/selection changes are announced rather than every layout frame.
- Depends on: REQ-009, REQ-015, REQ-016, REQ-018

### REQ-020 - Preserve usable context in empty and failure states
- Requirement: Provide specific, truthful states for absent data, invalid canonical configuration, expired sessions, service failure, and partial rendering without destroying unrelated readable context.
- Source: U02; SRC §§7.7, 12.8, 16.6, 17.5; UX-06, UX-07, PERF-01.
- Acceptance: No recorded relationships is described as "No relationships are recorded in this view", not a global absence claim. Invalid canonical configuration gives a blocking specific read error and never silently falls back to unrelated/stale data.
- Acceptance: AT-23: Session expiry or service stop preserves readable context and the desired route, explains reopening/reconnection, and makes no unauthorized process-restart claim. Loading and regional errors preserve other readable content.
- Acceptance: AT-34: Renderer failure leaves definitions, equivalent relationship lists, and evidence access usable; recovery neither enables remote computation/services nor hides missing data as an empty graph.
- Depends on: REQ-008, REQ-011, REQ-012, REQ-019

### REQ-021 - Display one coherent canonical snapshot
- Requirement: Bind entry, relationship, source-reference, graph, and continuation data to one validated snapshot of the selected ontology inputs.
- Source: U02; SRC §§12.4-12.6, 13.1-13.2; DATA-01.
- Acceptance: AT-21: Changes during navigation/publication reject mixed-version continuations with a specific snapshot-changed response, preserve the route/screen, and offer Refresh knowledge. Refresh replaces entry, relationships, and graph coherently and discards incompatible cursors and expansions.
- Acceptance: Snapshot identity derives from selected input versions rather than a timestamp alone. Materialization uses existing publication/transaction coordination or verified before/after digests with bounded retries; unstable inputs report knowledge being updated instead of a partial graph or misleading empty response.
- Depends on: REQ-002

### REQ-022 - Cache validated views with bounded lifetime
- Requirement: Keep caches/indexes tied to selected project/root, validated snapshot, helper/adapter version, and presentation mapping version, without turning cache freshness into authority.
- Source: U02; SRC §§13.2-13.3, 17.4, 18.5.
- Acceptance: Concurrent reads share a coherent immutable view, incoming/outgoing adjacency supports bounded selection work, memory remains bounded, and retired snapshots are released after active readers finish. Existing publication/recovery coordination is preserved without a conflicting new lock protocol.
- Acceptance: Modification times alone never establish evidence-hash equality; source opening revalidates evidence and newly requested current data detects changed inputs. Profiling/optimization retains integrity checks.
- Depends on: REQ-021

### REQ-023 - Provide compact validated read responses
- Requirement: Expose bounded versioned reader operations for context, search, exact entry, relationships, neighborhood, and registered source inspection, with explicit coverage and safe failure semantics.
- Source: U02; SRC §§11.1, 12.1-12.4, 12.6, 12.8, 15.7; PERF-01.
- Acceptance: Context returns project/snapshot identity, available categories, and reader capabilities without proposal inventory, authority grants, embedding startup, or broad readiness sweeps. Search uses compact summaries; complete relationships and source bodies are separate bounded reads.
- Acceptance: Validated response envelopes identify schema, project, snapshot, requested scope/filters, data, page/continuation, effective limits, coverage, and diagnostics. Completeness applies to the requested scope, not the whole ontology; item, byte, traversal, time, and filter exclusions remain distinguishable; unknown hasMore remains null; any total declares its count scope and exactness.
- Acceptance: Unavailable identity, ambiguous label, invalid request, expired session, changed snapshot, stale source, resource limit, and unexpected failure are distinguishable. A graph response carries exact nodes/labels/categories and edges with relation ID, endpoints, predicate, classification, qualifiers, and evidence references.
- Depends on: REQ-005, REQ-009, REQ-018, REQ-021

### REQ-024 - Validate continuation against its original read scope
- Requirement: Bind server-validated continuation to project, snapshot, normalized query, filters, direction, sort order, and the last returned stable key.
- Source: U02; SRC §12.5; PERF-01.
- Acceptance: Changed query/filter begins a new sequence; changed snapshot invalidates continuation; incompatible requests receive a specific rejection rather than resuming another ontology version. Arbitrary client traversal state cannot bypass bounds.
- Acceptance: Reader pagination leaves existing agent maximum-result contracts unchanged. More connections means additional independently bounded reads, never uncontrolled recursive scanning.
- Depends on: REQ-007, REQ-021, REQ-023

### REQ-025 - Reject stale responses and clean up inactive views
- Requirement: Apply responses only to their current project, snapshot, query, and selection, and stop unused graph resources when navigation changes.
- Source: U02; SRC §§14.2-14.5, 17.4.
- Acceptance: AT-22: A late entry-A response cannot replace selected entry B; obsolete search cancellation is supported where practical and sequence checks still reject superseded responses even if cancellation loses the race.
- Acceptance: Selected identity, graph focus, query/filters, expanded identities, snapshot, source selection, and view preferences remain distinct. Only the application/read layer initiates reads; renderers emit intentions without arbitrary source fetches, ontology execution, or inferred relations.
- Acceptance: Graph code/instances load only when needed; selection does not rebuild the graph; leaving the view disposes instances, listeners, timers, and resize observers, and no hidden layout simulation continues. Source excerpts load only on opening.
- Depends on: REQ-012, REQ-015, REQ-021

### REQ-026 - Make browsing observably non-mutating
- Requirement: Keep ordinary search, navigation, evidence inspection, and expansion from changing canonical knowledge, configuration, derived products, memory, proposals, or receipts.
- Source: U02; SRC §§5 SAFE-01/DATA-04, 13.4-13.5, 21 AT-33.
- Acceptance: Reads never invoke compile, build-wiki, link-memory, profile provisioning, embedding preparation, inference execution, source-hash repair, or optional backend installation. Changed evidence is reported rather than repaired.
- Acceptance: AT-33: Before/after hashes and relevant timestamps across the complete browser read workflow establish unchanged ontology, source configuration, memory data/configuration, proposals, publication receipts, and generated products. Only specifically documented startup runtime/session artifacts and harmless preferences are exempt; no broad .sys4ai exemption is allowed.
- Depends on: REQ-002, REQ-011, REQ-023

### REQ-027 - Keep memory and generated wiki independent
- Requirement: Keep memory outside first-release browsing and preserve the wiki as an explicit separate derived output.
- Source: U02; SRC §§1.4, 3.5, 10.5, 11.1, 13.4; DATA-04.
- Acceptance: Opening definitions and following relationships neither queries nor changes memory storage, schema, workflows, or configuration. No historical text is blended into canonical definitions or promoted to current authority.
- Acceptance: Missing or stale wiki output does not block canonical browsing or cause an implicit rebuild; existing explicit wiki generation remains available separately.
- Depends on: REQ-002, REQ-026

### REQ-028 - Run locally with installed production assets
- Requirement: Use the selected project's Python runtime and a browser for normal launch, serving an explicitly built static frontend and a dedicated read-only service without optional AI or standards prerequisites.
- Source: U02; SRC §§11.2-11.4, 15.1-15.2, 15.7, 17.4; PORT-01, SAFE-02.
- Acceptance: AT-28: The actual production reader and graph function offline under their real Content Security Policy without remote scripts, CDN downloads, fonts, images, analytics, or cloud logging.
- Acceptance: AT-32: Core reads work with optional embedding/RDF/standards/inference services absent; nothing is installed or started implicitly. A reader session does not require enabling the old advanced workbench profile or a Director publication grant.
- Acceptance: Normal browsing performs no package installation or build. Missing assets produce a specific incomplete-package error and documented maintenance route. Distributed assets include their dependency lock, build instructions, build identity, and third-party notices through the explicit asset pipeline.
- Depends on: REQ-001, REQ-023, REQ-026, REQ-027

### REQ-029 - Enforce local reading-session isolation
- Requirement: Keep the service loopback-only with a server-selected root and equivalent Host, Origin, session, CSRF, and source checks, granting only read access.
- Source: U02; SRC §§3.6, 15.1-15.2; SAFE-02.
- Acceptance: AT-25: Invalid Host/Origin/CSRF/session values and another service's credentials fail without disclosing project data. Browser requests cannot select roots, scan siblings, or access another service/project.
- Acceptance: The normal launcher does not bind to 0.0.0.0, permit broad CORS, or substitute an exposed development server. Browser-supplied actor/grant fields cannot supply authoring authority; expiry behavior retains the established authentication posture.
- Depends on: REQ-023, REQ-028

### REQ-030 - Keep bootstrap credentials out of routes and evidence
- Requirement: Preserve one-use bootstrap and isolated local session handling while retaining only safe intended navigation state.
- Source: U02; SRC §§6.3, 15.2-15.3, 19.3; SAFE-02.
- Acceptance: Bootstrap is consumed once, removed from the visible URL and retained browser history, and never copied into local links, screenshots, fixtures, logs, Git files, or source references. Session identifiers are isolated by project/service and retain appropriate loopback cookie protections.
- Acceptance: Expiry preserves the desired safe route and explains fresh local reopening. An explicitly started convenience launcher may open the browser, but a page does not claim it can restart a stopped Python process without a separately authorized mechanism. Old authoring credentials/tokens are not migrated; fresh reader sessions are created.
- Depends on: REQ-012, REQ-029

### REQ-031 - Remove browser access to every write dispatcher
- Requirement: Restrict the explorer dispatcher to session management and defined reads, with no general command, execute, query, function, or authoring dispatch path.
- Source: U02; SRC §§1.3, 11.3, 12.1, 15.4, 19.4; SAFE-01.
- Acceptance: AT-24: Direct browser requests for draft creation, review decisions, publication, recovery, generation, profile changes, Task mutation, skill/agent execution, or old write endpoints fail and leave protected artifacts unchanged.
- Acceptance: Omitted controls, CSS, disabled widgets, and an authoring=false flag are insufficient. The read service cannot invoke authoring operations, while separately permitted CLI/agent implementations and shared trusted-authority helpers remain available under their existing rules.
- Depends on: REQ-026, REQ-029

### REQ-032 - Constrain source and asset access
- Requirement: Resolve source access only through selected registered references/snapshots and serve only explicit production bundle assets under safe path, size, and content rules.
- Source: U02; SRC §§7.6, 12.1, 15.5-15.6; SAFE-02.
- Acceptance: AT-26: Encoded traversal, absolute paths, symlink escapes, and unselected source references are denied; root/allowlist/locator/size/evidence checks remain effective. A source drawer cannot browse arbitrary files.
- Acceptance: The actual build manifest or equivalent allowlist rejects unknown/traversing/disallowed-symlink asset paths, serves correct MIME types/security headers, and exposes no repository tree, dependency cache, unnecessary source maps, or package-manager files.
- Acceptance: AT-27: HTML, script-like labels/source text, and malicious links render safely without execution. Source excerpts are escaped by default; ontology text is not inserted as raw innerHTML. Production CSP changes are narrow and documented, never broad origins, arbitrary inline scripts, or unsafe-eval as a rendering workaround.
- Depends on: REQ-011, REQ-028, REQ-029

### REQ-033 - Bound service resources and protect diagnostics
- Requirement: Apply request-size, execution-time, concurrency, and memory limits while returning safe diagnostic codes and useful short explanations.
- Source: U02; SRC §§12.4, 12.8, 15.7, 17.3.
- Acceptance: Failures do not expose arbitrary Python exception text, credentials, out-of-project absolute paths, or source bodies. Detailed diagnostics remain local with session material redacted.
- Acceptance: Browser display, API results, traversal visits, and serialized bytes are independently bounded; existing agent contracts including the inspected 100-visited-node traversal cap and configured byte limit remain intact. Resource exhaustion gives honest bounded degradation rather than unbounded retries or hidden remote computation.
- Depends on: REQ-018, REQ-023, REQ-029

### REQ-034 - Make ordinary reading accessible
- Requirement: Target WCAG 2.2 AA using semantic navigation, headings, inputs, buttons, lists, visible unobscured focus, and keyboard alternatives for every essential action.
- Source: U02; SRC §§9.4, 16.1-16.4; STD; UX-07.
- Acceptance: Search retains a visible labeled input and submit action; autocomplete follows the WAI-ARIA combobox pattern with Arrow Up/Down, Enter, and Escape that dismisses suggestions without erasing the query. Command/Ctrl+K may supplement but never replace visible search.
- Acceptance: The page does not use a whole-page application role merely for the graph. Zoom, Fit current view, Focus here, source inspection, and other essential actions work without dragging, hovering, double-clicking, or memorized shortcuts.
- Acceptance: Normal text meets 4.5:1 contrast and large text/relevant non-text controls meet their applicable requirements; the WCAG 2.2 AA 24-by-24 CSS-pixel target criterion and its exceptions are assessed correctly. Color is supplemented by labels/icons/line styles, with selection more prominent than decoration.
- Depends on: REQ-019

### REQ-035 - Preserve predictable focus and feedback
- Requirement: Manage focus and announcements across sources, menus, navigation, and asynchronous reads without trapping users or discarding context.
- Source: U02; SRC §§8.2, 16.2-16.3, 16.6.
- Acceptance: Opening a source drawer moves focus to its heading or first meaningful control; closing it restores the evidence trigger. Escape closes temporary menus/drawers and returns focus predictably; route changes do not leave focus in removed components.
- Acceptance: Loading preserves current context, errors stay beside the failed region, and updates announce meaningful changes rather than continuous layout frames or whole-page blank flashes.
- Depends on: REQ-011, REQ-012, REQ-020, REQ-034

### REQ-036 - Support narrow screens, zoom, themes, and reduced motion
- Requirement: Keep the reader and surrounding controls operable and legible across narrow layouts, substantial zoom, both themes, and reduced-motion settings.
- Source: U02; SRC §§6.2, 16.4-16.6; STD; UX-07.
- Acceptance: AT-30: At a 320 CSS-pixel viewport and with substantial browser zoom, menus and text reflow, controls remain usable, and status remains legible. Spatial-diagram exceptions do not excuse non-reflowing surrounding UI.
- Acceptance: Narrow navigation becomes a drawer and entry text receives primary space; a phone Map is dedicated with dismissible selected details and a visible List option. Process/source text reads vertically without squeezed parallel columns.
- Acceptance: Light and dark themes receive independent checks; reduced motion stops unnecessary animation and settled layouts. System fonts, comfortable line spacing, restrained surfaces, and small consistent spacing support reading; exact visual tuning remains proposed in Decisions.
- Depends on: REQ-013, REQ-017, REQ-034, REQ-035

### REQ-037 - Keep reusable source and Template distribution explicit
- Requirement: Author reusable explorer changes in the owning source collection and distribute reviewed assets only through the registered Template update pipeline.
- Source: U02; SRC §§3.7, 18.1, 18.5, 24; GOV.
- Acceptance: The future change map identifies affected SKILLS-depo ontology assets, necessary ONTOLOGY-depo contracts/starter content, CLI/docs, bundle manifest/notices, and explicit distribution mappings without restructuring unrelated skills or editing mapped Template files as sources.
- Acceptance: Neutral Template output includes required installed production assets and notices, supports its own validated identity/purpose/modules/categories, and has no hard-coded depot labels/IDs. Fixtures remain outside shipped runtime assets; historical verification snapshots and earlier initializer editions remain intact.
- Depends on: REQ-028

### REQ-038 - Preserve independent project adoption and isolation
- Requirement: Treat active-root adoption as a separately authorized, inspected file-boundary operation and keep other product projects independent.
- Source: U02; SRC §§3.7, 18.1, 18.5, 24; GOV; PORT-01.
- Acceptance: Exact source/destination files, local instructions, overwrite boundaries, customizations, affected checks, and final diff are reviewed for root adoption. Registry membership, equal files, or Template distribution does not authorize recursive product updates.
- Acceptance: AT-31: Root, neutral Template, and a second explicitly selected fixture with a different namespace and at least one shared label with a different meaning demonstrate isolated routes, caches, preferences, source access, and sessions without hard-coded identity or cross-project leakage.
- Depends on: REQ-029, REQ-037

### REQ-039 - Define launch, health, and command compatibility honestly
- Requirement: Provide an explicit reader launch/configuration contract and distinct service identity with documented handling of the retired workbench command.
- Source: U02; SRC §§12.1, 15.2, 18.2-18.3, 19.3.
- Acceptance: A bounded health check distinguishes installed, configured, running, readable, stale, wrong project, and unavailable; it validates the selected context and does not depend on unrelated optional inference/embedding readiness or pretend to be the old authoring service.
- Acceptance: The old command either returns a documented deprecation error pointing to the reader or aliases the reader with incompatible authoring/grant arguments explicitly rejected. Current launchers, user/skill documentation, API/compatibility documentation, and strict configuration schemas agree with the selected behavior.
- Acceptance: Final command spelling, identity spelling, endpoint names, and any dedicated health probe versus narrow compatibility route are documented implementation choices; the example explore --open command is not represented as already implemented.
- Depends on: REQ-028, REQ-031

### REQ-040 - Preserve agent operations and historical knowledge during cutover
- Requirement: Retire the active human workbench without deleting or weakening permitted agent/CLI retrieval, proposal, validation, review-decision, publication, authority, recovery, or historical records.
- Source: U02; SRC §§1.3, 18.1-18.2, 19.2-19.4; DATA-01, PORT-01.
- Acceptance: Active callers are classified across runtime, shared-helper imports, tests, current docs, launchers, pipeline/distributed assets, and history before retirement. Shared authority/publication helpers remain available to verified callers rather than disappearing with a service module.
- Acceptance: Cutover to the normal reader entry point occurs only after reader/map/source/security/isolation checks; old frontend imports/editor-review-advanced assets no longer ship as an active destination. Historical evidence, proposals, receipts, canonical ontology, and memory records are retained.
- Acceptance: AT-35: Existing agent retrieval, publication/recovery, and Template contract checks show no unintended behavior regression and are evaluated independently of browser read-only tests.
- Depends on: REQ-031, REQ-037, REQ-038, REQ-039

### REQ-041 - Keep provenance maintenance and rollback separate from browsing
- Requirement: Identify source-provenance/helper-certification effects and use only separately authorized maintenance, while retaining a reversible code/asset/configuration migration that never rolls knowledge backward.
- Source: U02; SRC §§18.4, 19.5, 23, 24; GOV.
- Acceptance: Affected recorded source hashes, locked inputs, certifications, and explicitly generated products are identified after changes settle; warnings are not silenced by mechanical hash repair, and the explorer performs none of that maintenance.
- Acceptance: Frontend delivery and any authorized ontology/documentation maintenance have separate completion evidence. Rollback records code/assets/configuration and preserves newer valid ontology/memory and publication history; a failed rollout requires no reconstruction or restoration of obsolete knowledge snapshots.
- Depends on: REQ-026, REQ-040

### REQ-042 - Establish current baseline and process-content coverage
- Requirement: Record the actual implementation checkout and relevant content/caller baseline before future changes, preserving unrelated user edits and exposing source-content gaps.
- Source: U02; SRC §§2, 3.8, 18.2, 19.1, 20, 23; LIVE; GOV.
- Acceptance: Baseline evidence includes current commit, relevant file hashes, launch behavior, existing test commands/results for retrieval, publication/recovery, and Template distribution; differences from SRC's `744c8b06d5fda905201145ed313a2da8de2e601f` are assessed before relying on its file-level recommendations.
- Acceptance: An inventory covers types, predicates, sources, definitions, and process order support, separating unexamined source coverage from true content absence. Missing content is recorded for existing review processes and displayed honestly rather than silently authored to complete a demo.
- Acceptance: Unrelated local edits remain intact; pre-existing failures are distinguished from introduced regressions. Inspection never treats source-file execution instructions as a new action grant.
- Depends on: None.

### REQ-043 - Verify the production product against every acceptance scenario
- Requirement: Supply a requirement-to-implementation-and-evidence matrix covering all SRC AT-01 through AT-36 with real canonical fixtures and the actual production bundle.
- Source: U02; SRC §§20, 21.1-21.3, 24.
- Acceptance: Unit evidence covers normalization/ranking/category mappings/cursors, relation identities/direction, graph-list projection, source selection, and state transitions; service evidence covers isolation, assets, sessions, freshness, budgets, snapshot conflict, non-mutation, and inaccessible writes.
- Acceptance: Browser evidence covers search-entry-history, selection/focus, sources, keyboard, responsiveness, expiry, CSP, renderer failure, and production offline operation; manual evidence covers readability, focus, screen-reader use, relationship comprehension, and knowledge tasks. Tool choice may use Playwright or the established equivalent.
- Acceptance: A production build, explicit launch, safe reads, search/process access, interactive map/text equivalence, root/Template behavior, updated docs, and preserved agent workflows each have direct evidence. Skips, pre-existing failures, content gaps, environment limits, and untested behavior remain separate from passes; screenshots or unit tests alone never establish integrated completion.
- Depends on: REQ-001, REQ-040, REQ-041, REQ-042

### REQ-044 - Record accessibility evidence beyond automated scanning
- Requirement: Evaluate the actual interface against its WCAG 2.2 AA target with automated browser checks and manual keyboard/screen-reader use, reporting tested environments precisely.
- Source: U02; SRC §§16.1, 16.7, 21.2; STD.
- Acceptance: Evidence names actual browser and assistive-technology versions/combinations, including the relevant macOS VoiceOver/Safari walkthrough; a Windows screen-reader/browser combination is added when available, otherwise that limit is reported.
- Acceptance: Automated scan results supplement manual knowledge-task and focus checks; component-library selection or a passing scanner never supports an unqualified accessibility/compliance claim.
- Depends on: REQ-034, REQ-035, REQ-036, REQ-043

### REQ-045 - Measure proposed performance targets honestly
- Requirement: Benchmark the production explorer on the actual target machine against SRC's qualified initial targets, reporting actual behavior and limits without weakening data integrity.
- Source: U02; SRC §§17.1, 17.4, 21 AT-36, 24; PERF-01.
- Acceptance: Proposed benchmark targets retain their conditions: first readable screen within about 2 seconds on cold local launch with installed assets/representative fixture; search applied p95 within 200 milliseconds on a warm snapshot excluding intentional debounce; entry open p95 within 250 milliseconds on warm bounded data; focused graph usable within about 1.5 seconds for roughly 25 nodes/50 edges; loaded-graph selection feedback within 100 milliseconds without full graph recreation.
- Acceptance: Additional connections keep the existing view usable with bounded requests, visible progress, and cancellation where practical. Repeated runs report median and p95 with hardware, browser, build, dataset size, payload limits, and cold/warm conditions; no single favorable sample stands for performance.
- Acceptance: AT-36: Representative/stress measurements report actual timings, memory use, enforced limits, and graceful degradation. Source-validation latency is profiled separately when dominant, validated immutable input reuse precedes any contract-change proposal, and stale data is never labeled current to meet a target. Compressed bundle size establishes a regression baseline.
- Depends on: REQ-018, REQ-022, REQ-025, REQ-033, REQ-043

### REQ-046 - Exercise representative and pathological workloads
- Requirement: Use clearly labeled synthetic small, representative, and stress fixtures that expose semantic, limit, cancellation, and degradation failures.
- Source: U02; SRC §17.2; AT-36; PERF-01.
- Acceptance: Suggested scales remain approximate fixture targets: small about 50 entries/100 relationships; representative about 1,000 entries/5,000 relationships; stress about 5,000 entries/50,000 relationships. Existing loader capacity is measured rather than assumed, and stress success means bounded honest behavior rather than rendering everything.
- Acceptance: Fixtures include long/duplicate labels, aliases, many sources, distinct predicates on the same endpoints, cycles, self-loops, high-degree hubs, missing references, and large definitions; uniform random graphs alone do not satisfy coverage.
- Depends on: REQ-043, REQ-045

### REQ-047 - Validate knowledge comprehension with people
- Requirement: Evaluate whether a person can understand project knowledge through the production interface without learning ontology-management terminology.
- Source: U02; SRC §§21.2, 22.1-22.2, 23.
- Acceptance: A person unfamiliar with implementation attempts to find/explain a named term, distinguish related terms, interpret relationship endpoints/meaning, visit a neighbor and return, understand a process or its missing ordering, and inspect evidence/freshness. The initial target of finding a known term/definition within roughly 30 seconds without instruction remains a proposed task target, not a universal standard or observed result.
- Acceptance: Small exploratory rounds record task completion, wrong turns, mistaken relationship interpretations, requests for help, and participant wording without statistical generalization. If only the owner is available, the same walkthrough is documented and broader validation is explicitly unperformed.
- Acceptance: High-impact misunderstandings, including reversed relationships or layout mistaken for causality, are resolved before polish or an unqualified usability claim.
- Depends on: REQ-010, REQ-019, REQ-043

### REQ-048 - Deliver inspectable evidence and operational documentation
- Requirement: Provide a focused future implementation handoff with production visuals, launch/build/compatibility instructions, test and measurement evidence, preservation checks, and explicit limitations.
- Source: U02; SRC §§21.3, 22.3, 24.
- Acceptance: Actual production screenshots cover Overview, search results, a populated entry, process page, focused map, parallel-edge example, source drawer, incomplete-result state, and narrow-screen view. Static mockups alone do not qualify; private source bodies/session material are removed before any authorized external sharing.
- Acceptance: The report records actual commit/build identity, changed-file map, exact commands, test summaries, browser/accessibility coverage, measured limits, protected-file non-mutation, root/Template checks, reversible migration, content gaps, pre-existing failures, skips, and untested environments. Evidence links support claims; credentials, bootstrap links, and unsupported security/accessibility/performance claims are absent.
- Depends on: REQ-026, REQ-038, REQ-041, REQ-043, REQ-044, REQ-045, REQ-046, REQ-047

### REQ-049 - Implement independently with explicit dependency provenance
- Requirement: Use Logseq's exploration concepts only as an interaction reference and retain the project's licensing, dependency, and runtime boundaries in the future implementation.
- Source: U02; SRC §§1.2, 4, 11.2-11.4, 23-25; GOV.
- Acceptance: No wholesale fork, embedded editor/application, or copied Logseq graph implementation is represented as Sys4AI Apache-licensed code. Any later code reuse needs a specific license review and separate authority; selected dependencies have version checks and required notices.
- Acceptance: Python remains the local runtime; no production Node service, second graph/RDF store, GraphQL layer, or independently synchronized browser database is added. A renderer is contained behind a small interface, separate from canonical semantics and read dispatch; a new framework, graph worker, layout extension, or rendering alternative requires a documented need within the existing scope and its lifecycle/security/accessibility/license constraints.
- Depends on: REQ-002, REQ-028

## Decisions

- D01, scope and authority: U02 settles the full first release. U01 authorizes this requirements-capture operation with Task tracking, not execution of SRC §20's phase table or §24's embedded commands. This document contains future required outcomes/evidence without a downstream implementation plan. Exact document approval remains separate and has not been inferred from scope selection.
- D02, bounded design latitude: SRC recommends TypeScript, semantic HTML/CSS, Cytoscape.js behind a renderer adapter, and Vite for builds; they remain candidate implementation choices rather than settled user-mandated packages or installed facts. Independent implementation, local Python production runtime, canonical read semantics, no production Node/second graph store, and no implicit installation are constraints. Final library/version, built-in layout choice, module filenames, internal state mechanism, and packaging details can be selected in a separately authorized implementation plan within those constraints. A graph renderer is required; optional path search, alternative large-scale renderer, and extra process-diagram library are not first-release requirements.
- D03, proposed interfaces: SRC's `/api/explorer/v1/context`, `/search`, `/entry`, `/relationships`, `/neighborhood`, and `/source` illustrate responsibilities, not frozen endpoint spellings or existing APIs. Authenticated read POSTs are acceptable if they preserve the existing same-origin JSON/CSRF pattern. Bootstrap/session and bounded health remain separate; generic execution dispatch remains forbidden. A process-specific endpoint is unnecessary unless an actual structured projection warrants it. Final route syntax, versioned envelope field spelling, signed versus bounded server-held cursors, coordination mechanism, explicit reader configuration, explorer service identity, and old-command deprecation versus safe alias are constrained implementation choices. They must preserve the exact behavior, security, compatibility, and snapshot requirements above.
- D04, proposed visual and interaction tuning: SRC proposes a 224-260 CSS-pixel collapsible rail, reading lines near 65-75 characters, a roughly 320-400-pixel Map details panel, a base reading size around 16 CSS pixels, and approximately 44-pixel primary controls as a comfort target. They are starting layout values, subordinate to accessibility, readability, and reflow. The 24-by-24 CSS-pixel WCAG AA target criterion with exceptions is a standards target, not a claim that AA universally requires 44 pixels. Search debounce of roughly 150-200 ms is an initial tuning choice, excluded from the warm search latency target. These values are not measured current behavior or approval of a specific layout.
- D05, bounded map defaults: One-step initial neighborhoods, approximately 25 nodes/50 edges, and a proposed cumulative ceiling of 100 nodes/200 edges are presentation defaults/ceilings to evaluate within existing request and byte bounds. They do not change root agent defaults of 2 hops/20 results or maximums of 8 hops/100 results/32,000 bytes, nor the inspected 100-visited-node traversal cap. Proposed timing and fixture values remain qualified initial evaluation targets under REQ-045 and REQ-046; actual observed results and limitations must be reported rather than silently converted into measured guarantees.
- D06, content and evidence: Source coverage, exact ordered process content, and current provenance are future inspection/validation subjects with already defined honest UI outcomes, not unsettled user scope. The current project.jsonld observation does not prove absence across linked sources. Canonical additions and provenance refreshes retain separate review/authority; neither TRD capture nor browsing grants them.
- D07, distribution: The future release is source-owned, Template-distributed, and separately adopted into the root under exact source/destination inspection. Other projects retain their own choices. This captures the required preservation/adoption boundary without authorizing current code, Template, registry, root-runtime, or product changes.
- D08, verification: SRC's original review was repository-based, not a live-browser audit. Current capture also makes no implementation, security, accessibility, timing, or usability pass claim. Requirements specify what future evidence must establish; helper validation of this document proves only structural conformance and does not approve the TRD or product.

## Open questions

None.

## Not yet specified

None.

## Assumptions

None.
