# Sys4AI Project Knowledge Explorer
## Frontend replacement recommendations and local-agent implementation handoff

**Date:** 16 September 2026 (America/Denver)  
**Status:** Proposed implementation specification; no repository changes have been made by this review.  
**Target:** `Omegapy/Sys4AI`  
**Interaction reference:** `logseq/logseq`  
**Recommended user-facing name:** **Project Knowledge**  
**Recommended technical component name:** **Ontology Explorer**

> Replace the ontology workbench frontend with a read-only project knowledge explorer. Make definitions easy to find, relationships easy to follow, and processes easy to understand. Keep the ontology's agent-facing capabilities and authority controls behind that interface; do not rebuild them as human-facing management tools.

## How to use this handoff

Read Sections 1–10 for the intended user experience, Sections 11–19 for engineering and migration, and Sections 20–24 for implementation and verification. The source references are clickable and the proposed APIs, commands, and performance targets are explicitly identified.

## Contents

1. [Decision and scope](#1-decision-and-scope)
2. [Examination method and limitations](#2-examination-method-and-limitations)
3. [Findings in Sys4AI](#3-findings-in-sys4ai)
4. [What to take from Logseq](#4-what-to-take-from-logseq)
5. [Requirements and scope boundaries](#5-requirements-and-scope-boundaries)
6. [Information architecture and navigation](#6-information-architecture-and-navigation)
7. [Screen specifications](#7-screen-specifications)
8. [Relationship-map behavior](#8-relationship-map-behavior)
9. [Search and discovery](#9-search-and-discovery)
10. [Content, terminology, and trust](#10-content-terminology-and-trust)
11. [Recommended technical architecture](#11-recommended-technical-architecture)
12. [Read-model and API contracts](#12-read-model-and-api-contracts)
13. [Snapshot consistency and read-only operation](#13-snapshot-consistency-and-read-only-operation)
14. [Frontend modules and state management](#14-frontend-modules-and-state-management)
15. [Security and local access](#15-security-and-local-access)
16. [Accessibility and responsive behavior](#16-accessibility-and-responsive-behavior)
17. [Performance and scale](#17-performance-and-scale)
18. [Repository changes and distribution](#18-repository-changes-and-distribution)
19. [Migration and retirement of the workbench](#19-migration-and-retirement-of-the-workbench)
20. [Implementation sequence](#20-implementation-sequence)
21. [Acceptance tests](#21-acceptance-tests)
22. [Usability validation](#22-usability-validation)
23. [Risks and decisions to preserve](#23-risks-and-decisions-to-preserve)
24. [Local-agent execution brief](#24-local-agent-execution-brief)
25. [Sources](#25-sources)

---

## 1. Decision and scope

### 1.1 The product being built

Build a **reader and relationship explorer**, not an ontology editor with fewer visible buttons.

The human user should be able to answer:

- What does this term mean in this project?
- How is it connected to another term, role, skill, document, or process?
- How does this process work, and what sources describe it?
- Where did this definition or relationship come from?
- Is the information current, superseded, or incomplete?

A graph is important, but it must explain relationships rather than merely display connected circles. A reader must be able to understand the same information without operating the graph.

### 1.2 Recommended decision

Implement a new, small frontend over the existing canonical ontology readers. Use **TypeScript, standard HTML/CSS, and Cytoscape.js** for the interactive map. Use **Vite as a development/build tool**, not as an additional production server. Serve the built assets and a dedicated read-only API from the project's local Python service.

Use Logseq as an interaction reference. Do not fork its complete application, embed its editor, or copy its graph implementation into the Sys4AI codebase. The technical and licensing reasons are discussed below.

These are implementation recommendations, not claims that these components are already installed or that their performance has been measured in Sys4AI.

### 1.3 What “scrap the workbench frontend” means

The replacement must remove the workbench's human-facing authoring model: draft forms, proposal review, publication buttons, query consoles, inference controls, and AI-generation controls.

Keep the underlying agent/CLI workflows that manage ontology changes. An agent may still propose, validate, review, and publish through the existing permitted process. Removing the frontend does not authorize deleting canonical records, proposals, publication receipts, authority checks, or recovery history.

The new browser service must not expose those write operations. Hiding buttons while retaining a general-purpose authoring dispatcher is not the recommended implementation.

### 1.4 Three responsibilities remain separate

| Responsibility | Purpose | What this change does |
| --- | --- | --- |
| Ontology | Defines project meanings, identities, classifications, and relationships. | Preserves its authority and machine-readable records. |
| Memory | Holds historical experience, observations, and prior context. | Leaves its storage, schema, and workflows unchanged. |
| Explorer | Helps a person read and navigate selected ontology information. | Replaces the existing workbench frontend. |

This separation matches the project's existing ontology guidance. [S04]

## 2. Examination method and limitations

### 2.1 Repository snapshots

The recommendations are grounded in these inspected snapshots:

| Repository | Inspected commit | Basis |
| --- | --- | --- |
| Sys4AI | `744c8b06d5fda905201145ed313a2da8de2e601f` | The `main` branch head returned during this examination. |
| Logseq | `08c15e3d9feff9e330430af3a9fab27dd7dbb0a0` | Commit-qualified source returned by repository search and used for graph-source inspection. |

The local agent must compare its checkout with these snapshots before applying the file-level recommendations. A branch can change after an inspection. [S00], [L00]

### 2.2 Material inspected

For Sys4AI, the examination included the workbench HTML and application JavaScript, the Python service and dispatcher, ontology retrieval and graph functions, the wiki generator, the ontology skill and command documentation, project configuration and sample canonical records, repository guidance, licensing, and the template mapping.

For Logseq, the examination included the repository README, graph settings component, graph-rendering bridge, graph-data builder, and license. The inspected source is the current database-oriented development line, not an assumption based on an older Markdown-only version. [L01], [L02], [L03], [L04], [L05]

### 2.3 Evidence boundary

This is a **repository-based architecture and interface review**, not a live-browser usability audit. Neither application was launched in this examination. No production screenshots, timing measurements, screen-reader results, or observed user-task completion rates are claimed.

The screen layouts, interaction rules, performance budgets, and acceptance criteria below are proposed requirements. The local agent must implement and verify them in a running browser. Findings about the existing frontend are based on its source, not inferred screenshots.

## 3. Findings in Sys4AI

### 3.1 The frontend is organized around authoring

`SKILLS-depo/ontology/workbench/index.html` presents Explore, Draft editor, Review, and Advanced sections. It also places five technical filters beside search and exposes draft creation. `app.js` mounts the editor, review, and advanced modules during startup, including in the overall browsing experience. [S01], [S02]

**Recommendation:** Replace the shell and navigation. Merely changing its title or collapsing the advanced panels would retain the wrong product model.

### 3.2 The graph is a limited inspection aid

`drawGraph()` in `app.js` uses a fixed SVG arrangement, takes at most nine node identities, draws plain connecting lines, and displays shortened ID suffixes. The surrounding list carries more relationship information than the drawing. [S02]

**Recommendation:** Replace this renderer with a navigable map that preserves relationship identities, labels, direction, and selection state.

### 3.3 Browser search bypasses richer retrieval behavior

The workbench's `/api/records` implementation performs substring matching over IDs, labels, and aliases. The separate retrieval module already has ranked matching over definitions and scope notes as well. Its `search()` defaults to allowing a semantic fallback. [S03], [S05]

**Recommendation:** Reuse deterministic ranking with `semantic=False`; do not route ordinary explorer search through an embedding-dependent fallback.

### 3.4 The read foundation is reusable

The repository has separate retrieval and bounded graph functions, including `neighbors()` and `path()`. They carry provenance and traversal metadata. The documented core read operations use canonical inputs and do not require generated products. [S05], [S06], [S07]

**Recommendation:** Add a thin presentation adapter, not a second ontology engine.

### 3.5 The wiki is a projection, not the authority

`ontology_wiki.py` generates Markdown pages, relationships, sources, and backlinks from canonical records. `build-wiki` is an explicit generated operation. [S08]

**Recommendation:** Keep the wiki as a useful export/fallback. Do not parse it back into the explorer's authoritative graph or make a wiki rebuild mandatory before browsing.

### 3.6 The existing service contains security worth preserving

The Python workbench uses loopback binding, Host and Origin checks, a one-use bootstrap, session cookies, a CSRF token, restricted source opening, and constrained asset serving. It also imports and dispatches authoring operations. [S03]

**Recommendation:** Preserve the security properties while extracting a read-only service boundary. Do not replace this with an unrestricted directory server or a broadly accessible development server.

### 3.7 Reusable assets and installed copies have different ownership

Root guidance identifies `SKILLS-depo/` as reusable source material. It distinguishes template updates from authorized adoption into the active root or other projects. The template mapping is explicit. [S11], [S12]

**Recommendation:** Implement reusable changes in the source collection, verify template distribution, and separately adopt the change into the active root. Do not edit every matching copy recursively.

### 3.8 Source-backed process content needs an inventory

The inspected project records include skill, capability, artifact, and governance relationships. That sample does not establish that every process has a complete, ordered step description. [S10]

**Recommendation:** Treat process-content coverage as an early implementation check. A frontend cannot safely manufacture missing steps from relationship proximity.

## 4. What to take from Logseq

### 4.1 Adopt its exploration patterns selectively

The inspected Logseq graph code separates settings, interaction/rendering, and graph-data preparation. It includes depth settings, remembered graph preferences, node activation/preview hooks, and incremental display updates. [L02], [L03], [L04]

Translate those ideas into a smaller experience:

| Pattern | Sys4AI adaptation |
| --- | --- |
| Navigate by selecting linked items. | Selecting a term opens a readable definition and its relationships. |
| Move between a graph and an item view. | Keep the same selected identity when switching between Terms and Map. |
| Explore a neighborhood. | Start with direct relationships and expand deliberately. |
| Preview without losing context. | A map selection updates the details panel without moving the whole graph. |
| Remember harmless view preferences. | Retain theme and layout choice; namespace them by project. |
| Separate data from rendering. | Keep canonical ontology semantics out of the renderer and UI components. |

Do not bring over journals, block editing, task checkboxes, plugins, whiteboards, synchronization, database administration, or a general-purpose settings panel.

### 4.2 Do not copy Logseq's edge aggregation

The inspected `graph_view.cljs` builds links with an index keyed by source and target endpoints. That is not the identity model needed for Sys4AI's semantic relations. [L04]

Two Sys4AI records can connect the same nodes while meaning different things. For example, the inspected project has distinct `definedBy` and `governedBy` relations between the installed `agent-task` skill and its source artifact. Those relations must remain distinguishable. [S10]

**Required rule:** Key graph edges by the canonical relationship record ID, not by `(source, target)` alone. Any visual grouping must retain every underlying relation and expose its meaning.

### 4.3 Do not assume the older Logseq architecture

The inspected README describes a database version and identifies it as beta. The graph source uses its own ClojureScript application context and data preparation. [L01], [L02], [L03], [L04]

This is another reason to borrow interaction concepts rather than transplant a supposedly standalone graph widget.

### 4.4 Licensing boundary

Logseq's inspected license is GNU AGPL version 3. Sys4AI's license notice assigns Apache 2.0 to its code and CC BY 4.0 to its documents, while preserving separate third-party terms. Cytoscape.js documents its core under MIT. [L05], [S13], [E01]

**Recommendation:** Write the explorer independently and preserve required dependency notices. Do not copy Logseq code and relabel it Apache 2.0. Any later code reuse requires a specific license review, including the obligations of modified AGPL software; this document does not resolve licensing for a hypothetical combined application.

## 5. Requirements and scope boundaries

### 5.1 Mandatory outcomes

| ID | Requirement | Observable outcome |
| --- | --- | --- |
| UX-01 | Replace the workbench product model. | No draft, review, publish, query-console, or AI-generation controls in the explorer. |
| UX-02 | Find project meanings quickly. | Search finds preferred labels, aliases, IDs, and relevant definition text. |
| UX-03 | Make relationships understandable. | A user can read both endpoints, the relationship label, and its direction. |
| UX-04 | Support visual exploration. | The map supports selection, pan, zoom, focus, and bounded expansion. |
| UX-05 | Explain processes. | Process pages expose only source-supported descriptions and ordering. |
| UX-06 | Preserve context. | Back/Forward and view switching retain the selected identity and route state. |
| UX-07 | Work without the graph. | All substantive graph information and navigation have a text alternative. |
| DATA-01 | Keep canonical authority. | Reader and graph information trace to the selected canonical ontology. |
| DATA-02 | Preserve semantic distinctions. | Multiple relations, qualifiers, lifecycle, and fact classifications are not silently merged. |
| DATA-03 | Keep evidence discoverable. | Definitions and relations link to source references and freshness information. |
| DATA-04 | Keep memory separate. | Initial browsing neither searches nor changes the memory subsystem. |
| SAFE-01 | Enforce read-only access. | Browser requests cannot draft, publish, run a skill, mutate a Task, or change profiles. |
| SAFE-02 | Preserve local confidentiality. | Loopback, session, origin, source-allowlist, and safe-rendering protections remain effective. |
| PORT-01 | Support independent projects. | The same code works with the root, neutral template, and another explicitly selected project. |
| PERF-01 | Bound work and payloads. | Large graphs remain navigable through limits, paging, and visible incompleteness. |

### 5.2 Out of scope for the first release

No ontology editing, drag-to-connect, publication management, inference console, raw SPARQL interface, embedding setup, AI chat, agent execution, Task dashboard, memory browser, multi-project federation, public hosting, collaboration, or automatic project scanning.

Do not add these as hidden “advanced” tabs. A separate agent workflow remains available outside this explorer.

### 5.3 Small features that are in scope

Browser history, a light/dark/system theme choice, a local link or stable-ID copy action, source inspection, readable error states, and keyboard operation directly support exploration. They are not reasons to introduce a settings workbench.

## 6. Information architecture and navigation

Use a single application shell with four destinations:

| Destination | User question | Main content |
| --- | --- | --- |
| **Overview** | Where should I start? | Project purpose, search, and a few source-backed starting points. |
| **Terms** | What does this mean? | Searchable vocabulary and readable entry pages. |
| **Processes** | How does this work? | Process/capability descriptions and supported flow information. |
| **Map** | How are these connected? | Interactive, focused relationship map with a details panel. |

### 6.1 Global shell

Keep the project name and global search visible. Make the navigation collapsible on smaller screens. Place theme and help in a small secondary menu, not a separate administration page.

Do not expose raw storage categories as the main navigation. “Predicate,” “binding,” and “fact kind” are useful technical details, not the first concepts a reader should have to learn.

### 6.2 Desktop layout

Use approximately 224–260 CSS pixels for a collapsible navigation/results rail. Give the remaining width to the current task. Keep reading text near 65–75 characters per line rather than stretching paragraphs across a large monitor.

The Map view uses the remaining area for the graph and a roughly 320–400 pixel details panel. Hide that panel until there is a selection when space is limited. Do not force a permanent four-column layout.

### 6.3 Routes and history

Use stable ontology identities in routes, never labels as identifiers. A small hash router is sufficient and avoids a requirement for arbitrary server-side path fallback.

Illustrative routes:

```text
#/overview
#/terms?q=task
#/entry?id=<percent-encoded-canonical-id>
#/processes
#/map?focus=<percent-encoded-canonical-id>&depth=1
```

Browser Back must restore the prior selected entry, result query, filters, and useful map state. Selecting a node should create one deliberate history event, not a history entry for every camera movement.

A copied local URL works only while the correct local service is available. Keep “Copy stable ID” available for durable reference; do not present an ephemeral loopback URL as a public share link.

### 6.4 Progressive disclosure

Show the definition first. Keep technical identifiers, module versions, raw classification values, source hashes, and diagnostics under **Details** or **Sources**.

Warnings that affect interpretation are exceptions: show “Source changed,” “Deprecated,” “Incomplete results,” or “Inferred” beside the relevant information. Do not hide meaningful uncertainty to make the page look simpler.

## 7. Screen specifications

### 7.1 Overview

The first screen must not be a management dashboard or an unfiltered whole-project graph.

Show the project name, its configured purpose, a prominent search field, and a few starting points linked to real canonical identities. Include an obvious **Explore the map** action.

Starting points can be selected in reviewed presentation configuration or derived deterministically from an explicit project record. Do not invent a hierarchy because some nodes have many connections. With no configured starting points, show browse categories and search instead of fabricated content.

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Project Knowledge · [Project name]        Search project terms…      │
├───────────────┬─────────────────────────────────────────────────────┤
│ Overview      │ What would you like to understand?                   │
│ Terms         │ [Search terms, roles, skills, and processes…]        │
│ Processes     │                                                     │
│ Map           │ [Project purpose from selected configuration]       │
│               │                                                     │
│               │ Start with [real term] · [real process] · [real role]│
│               │ Browse terms                         Explore the map│
└───────────────┴─────────────────────────────────────────────────────┘
```

No build buttons, profile-readiness matrix, proposal counters, or maintenance actions belong here.

### 7.2 Terms and search results

Each result should show a human-readable label, a small category label, a short definition excerpt, and a disambiguating module/project label when necessary.

Display why a non-obvious result matched, such as “Also called …” or “Matches the definition.” Do not expose the internal scoring formula.

Provide **All**, **Terms**, **Roles**, **Skills**, and other categories only where the selected project actually supports them. Category mappings must use verified canonical type IDs or reviewed presentation configuration, not substring guesses from labels.

Keep a single **Filter** control for less common refinements. Show active filters as removable chips. Empty results must offer “Clear filters” and preserve the query.

### 7.3 Entry page

Use this reading order:

1. **Name and definition.** Show the canonical preferred label and definition without machine identifiers preceding them.
2. **Context.** Show aliases, scope distinctions, and examples when recorded.
3. **Relationships.** Group readable outgoing and incoming connections.
4. **Sources.** Explain where the information is recorded and whether those sources still match.
5. **Technical details.** Keep exact ID, kind, type IDs, module version, fact classification, and canonical location available.

Offer **View on map**, **Copy local link**, and **Copy stable ID** as reading actions. Do not add edit or execution actions.

```text
Task
[Recorded category]

[Canonical definition]

Also called: [recorded aliases]
In this project: [recorded scope note, when present]

Related information
  Outgoing: [this term] — [relationship] → [other term]
  Incoming: [other term] — [relationship] → [this term]

[View on map]       Sources (n)       Details
```

The example is a layout, not a proposed replacement definition of Task.

### 7.4 Relationship details

A relationship must be inspectable in its own right. Clicking its map label or textual description opens:

- Source term, predicate label, and target term.
- Its recorded definition, qualifiers, lifecycle, and fact classification.
- The exact supporting sources and freshness.
- Its stable relation ID under Details.

Qualifiers can change meaning. A conditional or scoped relation must not look unconditional merely because its qualifier is too long to print on a line.

### 7.5 Process pages

A process page is an explanatory view, not a runnable workflow.

Show its purpose, when it applies, participating roles, required inputs, outputs, and related skills/documents **only when supported by selected canonical records or explicitly linked source sections**.

Show ordered steps only when the source supplies order or the ontology explicitly represents it. A generic graph path, `relatedTo` edge, dependency, or visual left-to-right arrangement does not establish execution order.

When order is absent, state: **“An ordered description has not been recorded. These are the documented relationships.”** Then show those relationships and sources.

Use an ordered text list before adding a flow diagram. The first release does not need a second graph library. A numbered list and the existing relationship map are sufficient. Any process-specific diagram added later must identify the evidence for its sequence and branches.

### 7.6 Sources

Open evidence in a drawer or secondary panel without replacing the current entry. Show a friendly document label where available, project-relative path, locator, and freshness status. Keep hashes under Details.

Prefer the referenced section or a bounded excerpt. If section extraction is not reliable for a locator, show a clearly labeled bounded source excerpt or the existing bounded text view; do not pretend it is the exact cited passage.

Opening a source must not execute it, follow its instructions, fetch external content automatically, or expose unrelated files.

### 7.7 Empty, incomplete, and error states

| Condition | User-facing behavior |
| --- | --- |
| No project extension records | Allow browsing imported core vocabulary; explain that local additions are absent. |
| No matching term | Preserve the query; suggest checking aliases or clearing filters. |
| No recorded relation | Say “No relationships are recorded in this view,” not “This term has no relationships anywhere.” |
| Query is truncated | Show what is displayed, the reason for the limit, and how to continue or narrow. |
| Source changed | Keep the recorded definition visible when safe; label the evidence mismatch. |
| Entry is deprecated | Show its historical definition and replacement link, when recorded. |
| Snapshot changed mid-navigation | Keep the screen stable; offer to load the newer snapshot. |
| Session expired | Preserve the route; explain how to reopen the local explorer. |
| Graph failed | Keep the entry and equivalent relationship list usable. |
| Canonical configuration is invalid | Show a blocking, specific read error; do not silently fall back to unrelated or stale data. |

## 8. Relationship-map behavior

### 8.1 Default to a focused neighborhood

Open the map around the selected term. A neighborhood means the term and a bounded set of directly connected terms. The default depth is one relationship step.

Without a selection, use a reviewed project starting point or a term picker. Do not load every node and let the user search visually through an unreadable network.

Initial design targets: approximately 25 visible nodes and 50 edges, subject to stricter project and payload limits. These are proposed display defaults, not new permissions to exceed backend limits.

### 8.2 Interaction rules

| User action | Required result |
| --- | --- |
| Select a node | Highlight it and update its readable details without recentering the map. |
| Choose **Focus here** | Make that node the neighborhood center. |
| Choose **Show more connections** | Request another bounded neighborhood/page and add supported nodes and edges. |
| Select an edge | Show the precise relationship and its evidence. |
| Drag empty space | Pan the graph. |
| Use zoom controls | Zoom in/out without changing selected data. |
| Choose **Fit view** | Fit the currently visible graph, not the entire hidden ontology. |
| Choose **Reset view** | Restore the focused neighborhood and its default presentation. |
| Choose **List view** | Read and navigate the same selected relationship data without using the canvas. |
| Press Escape | Close a temporary preview or return focus predictably. |

Do not require double-click, hover, dragging, or a context menu for essential actions. Hover previews may supplement, but never replace, selectable details.

### 8.3 Visual language

Use a restrained 2D map. Prefer readable labels, a clear selected node, and a limited number of category cues. Do not use 3D, continuous motion, glowing effects, or node size as an unexplained importance score.

Edges must show direction when the recorded relationship is directed. Use the predicate's human-readable label. At a crowded zoom level, show labels on selected/adjacent edges and keep every label available in the equivalent list and relationship panel.

Include a compact legend and a short instruction: **“Select a term to read it. Use Focus here to explore its connections.”**

Graph distance and layout position are visual arrangements, not measures of semantic similarity, causality, chronology, or importance.

### 8.4 Preserve semantic identity

Use canonical IDs as the source of node and edge identity. Labels are display text only.

Preserve parallel relations, self-loops, cycles, and qualifiers. If parallel edges are bundled to reduce clutter, display a count and let the user inspect the individual predicates. Do not merge their classifications or evidence.

Relation records become visual edges by default, not extra nodes between every pair of terms. Predicate records remain inspectable through labels. Source files and binding records must not automatically become hundreds of distracting graph nodes.

Default to explicitly recorded semantic relations. Treat type annotations, source associations, document mentions, inferred results, and navigation categories as distinct display layers. Do not silently convert all of them into canonical ontology assertions.

### 8.5 Layout stability

Keep existing node positions when expanding. Place new nodes near their source, run a bounded layout adjustment, then stop. Never continually restart the full layout after selecting a node or opening the details panel.

Honor reduced-motion preferences. Provide an explicit “Arrange” action only if automatic placement is insufficient. Do not expose force constants, physics sliders, or renderer settings to ordinary users.

### 8.6 Honest expansion limits

Distinguish three different constraints:

- **Query limit:** The server returned only a bounded subset.
- **Display limit:** The browser deliberately shows fewer of the records it has received.
- **Filter exclusion:** Matching or related records were excluded by the selected view policy.

Show exact counts only when they are known. If the backend reports only that more results exist, say “More connections are available,” not “37 hidden connections.”

An upper browser display budget of 100 nodes and 200 edges accumulated through multiple bounded requests is a reasonable initial ceiling to test. A single request must still respect the project's current item, traversal, and byte limits. Reaching the display budget should offer focused navigation or a list, not freeze the browser.

### 8.7 Optional relationship-path search

A later enhancement may answer “How are these two terms connected?” using the existing bounded `path()` behavior. This is not required before the basic explorer is usable.

A result means a path exists under the selected predicates, direction, and limits. It does not prove causal influence or process order. A failed bounded search must say “No path found within these limits,” not “These terms are unrelated.” [S06], [S07]

## 9. Search and discovery

### 9.1 Deterministic search first

Reuse the existing ranking precedence: exact identity, preferred label, alias, then lexical matches. Keep the result's canonical identity and match reason. Call the read search path with semantic fallback disabled. [S05]

Add autocomplete behavior around that deterministic core. Start with roughly a 150–200 ms input debounce; cancel or ignore superseded requests. These values are initial tuning choices, not measured requirements of the existing code.

Do not invoke an LLM to explain search results, infer synonyms, or generate definitions during ordinary navigation.

### 9.2 Filtering must precede truncation

Apply visibility rules, category filters, and query ranking before taking the response page. Filtering only after the first bounded result set can make valid matches disappear.

Keep technical filters behind one expandable control. The default reader view should prioritize approved, explicitly recorded information. Deprecated entries remain reachable by exact identity and clearly labeled; drafts must not appear as approved knowledge.

### 9.3 Ambiguity and aliases

When two records share a label or alias, present both with category, module/project, and a brief definition. Never choose one because it happened to be first in a list.

Preserve the actual preferred label after an alias match. Do not create a second page or node for the alias unless the ontology itself records a distinct identity.

### 9.4 Keyboard behavior

Keep an ordinary visible search input and submit action even when autocomplete is available. Support Arrow Up/Down for suggestions, Enter to open the selected result, and Escape to dismiss suggestions without erasing the query. A Command/Ctrl+K shortcut can focus search, but must not be required. Follow the WAI-ARIA combobox pattern where a suggestion list is implemented. [E04]

### 9.5 Discovery without search

Support alphabetical browsing and meaningful category browsing. The user should not need to know a term's name in advance.

In the neutral template, show only categories supported by the imported core or project configuration. In specialized projects, add categories through a reviewed presentation mapping without changing the shared frontend code.

## 10. Content, terminology, and trust

### 10.1 Human labels, exact meaning

Prefer **Terms**, **Relationships**, **Sources**, **Related history**, and **Details** in the interface. Preserve exact technical values in the details panel.

A friendly label must not strengthen an assertion. For example, `relatedTo` can become “related to,” but not “depends on” or “causes.” Inverse sentence labels should come from a reviewed predicate-label mapping; otherwise show the original subject–predicate–object sentence.

### 10.2 Do not synthesize missing explanations

Use recorded definitions, scope notes, examples, and non-examples. Do not paraphrase them at runtime in ways that could change meaning.

A source-grounded explanatory paragraph may be added through the project's existing content-review process. That is a canonical/documentation improvement, not hidden frontend behavior.

### 10.3 Show status only where it helps interpretation

Use a quiet default presentation for approved, current data. Surface anomalies prominently. Explain “Inferred” as a conclusion produced by a selected reasoning process, not a directly recorded assertion. Explain “Source changed” as a mismatch with the recorded evidence version, not proof that the definition is false.

Approval, source freshness, and factual truth are different concepts. Do not use a green badge that implies all three.

### 10.4 Authority is not a graph edge

A relationship to a role, skill, or governing document does not grant permission to execute an action. The existing ontology guidance explicitly separates meaning from current execution authority. [S04], [S07]

The explorer may identify the source of a rule. It must not decide a user's or agent's execution authority from ontology relationships alone.

### 10.5 Memory remains optional and separate

Do not query memory as a side effect of opening a definition. Keep memory out of the initial release.

A future **Related history** expansion may use the established memory-link interface, preserve its freshness rules, and label the content as historical evidence. It must not blend memory text into the canonical definition or turn history into current authority. [S04], [S07]

## 11. Recommended technical architecture

### 11.1 Keep the architecture smaller than the current workbench

Use this separation:

```text
Selected project's canonical ontology + locked imports + source references
                              |
                  Existing Python read functions
                              |
               Read-only explorer presentation adapter
                              |
              Versioned, bounded JSON responses
                              |
         Project Knowledge: search / reader / processes / map

Existing agent/CLI proposal and publication workflows remain separate.
The generated Markdown wiki remains a separate derived output.
Memory is not queried by ordinary explorer navigation.
```

A presentation adapter converts canonical records into small structures that the browser can display. It must not become another ontology database, publish changes, or reinterpret relationships.

### 11.2 Frontend choice

**Recommended:** TypeScript modules, ordinary semantic HTML, CSS custom properties, Cytoscape.js for the map, and Vite for production builds. Cytoscape.js supplies graph rendering, graph interaction, and layout facilities; its suitability here follows from the need to display typed, directed relationships without writing a renderer from scratch. [E01]

The existing frontend is plain JavaScript. A framework migration is not necessary to implement four read-oriented views. Do not introduce React, a global state framework, or a component framework simply because the reference application uses a richer stack. A documented team constraint can justify a different choice, but the required behaviors and boundaries remain the same.

Use a small renderer interface so the rest of the application does not depend on Cytoscape-specific objects. It should accept graph data and selection state, emit user intentions, and expose operations such as fitting the current view and destroying the instance.

| Approach | Decision for this project |
| --- | --- |
| Cytoscape.js behind a small adapter | Recommended balance of existing graph capabilities and a contained integration. |
| Complete Logseq fork or embedded application | Reject: brings an unrelated application model, integration work, and separate licensing obligations. |
| Continue expanding the fixed SVG drawing | Reject as the main approach: makes the project responsible for increasingly complex interaction and layout code. |
| Sigma.js | Consider only if measured scale requirements later justify a different rendering approach; it is not needed merely to imitate Logseq. [E02] |

Start with a bounded, stable two-dimensional layout. Use an available built-in layout before adding layout extensions. Add an extension only when a measured readability problem warrants the extra dependency and license review.

### 11.3 Backend choice

Keep Python as the local runtime. Introduce a dedicated explorer service and reuse the existing canonical readers. Do not add a graph database, a second RDF store, a GraphQL service, a production Node server, or an independently synchronized browser database.

Extract reusable HTTP/session protections from the workbench where practical. Do not make the explorer inherit an authoring dispatcher whose write routes happen to be hidden.

The reader must work with the core ontology when optional standards, inference, and embedding profiles are absent. The existing core/advanced separation supports this direction. [S04], [S07]

### 11.4 Build and runtime boundary

Build the frontend into local static assets. Vite is used to produce that build; it is not the end user's production server. [E05]

Commit or distribute the production bundle through the project's explicit asset pipeline, with its dependency lockfile, build instructions, and third-party notices. The normal launch path should need the selected project's Python interpreter and a browser, not a fresh JavaScript dependency installation.

Never run package installation, download a CDN script, or build the frontend as an implicit side effect of reading a term. If assets are missing, report that the explorer package is incomplete and provide the documented maintenance route.

## 12. Read-model and API contracts

### 12.1 These are proposed contracts

The endpoints in this section do **not** exist in the inspected implementation. They describe the dedicated API to add. Existing agent/CLI response contracts should remain unchanged.

Using authenticated POST requests for read operations is acceptable: read-only means that the operation does not change project knowledge, not that every request must use GET. This also permits retaining the current same-origin JSON and CSRF pattern without putting search text in server request URLs. [S03]

| Proposed endpoint | Responsibility | Important restrictions |
| --- | --- | --- |
| `/api/explorer/v1/context` | Return project identity, snapshot identity, available reader categories, and service capabilities. | No proposal inventory, authority grant, embedding startup, or broad readiness sweep. |
| `/api/explorer/v1/search` | Return ranked, filtered entry summaries with explicit paging information. | Deterministic search; filter before pagination; bounded work and response size. |
| `/api/explorer/v1/entry` | Read one exact canonical identity. | Return the entry and compact metadata, not every related full record. |
| `/api/explorer/v1/relationships` | Read incoming/outgoing relationships for an entry. | Preserve relation IDs, predicates, qualifiers, evidence, and continuation state. |
| `/api/explorer/v1/neighborhood` | Return a bounded graph neighborhood with resolved endpoint labels. | Enforce traversal and payload limits; no graph mutation or uncontrolled recursive expansion. |
| `/api/explorer/v1/source` | Read an authorized source excerpt for a selected record or relationship. | Resolve a registered source reference; validate root, allowlist, locator, size, and evidence version. |

Keep the bootstrap/session endpoint separate. Keep a bounded health endpoint for service identity. Do not add a browser-accessible generic `execute`, `command`, `query`, or Python-function-dispatch endpoint.

A process page can initially use the same entry and relationships APIs. A distinct process endpoint is justified only when there is an actual structured process projection, not merely a differently styled page.

### 12.2 Separate storage shape from reading shape

The compact JSON-LD records already carry stable identity, label, definition, type, classification, and evidence. [S05], [S09], [S10] Map those fields explicitly:

| Canonical field | Reader field or treatment |
| --- | --- |
| `@id` | `id`; keep the exact value as the identity. |
| `label` | `label`; the primary visible name. |
| `definition` | `definition`; preserve the recorded meaning. |
| `@type` | `typeIds`; resolve display labels through known records. |
| `kind` | `recordKind`; retain as technical metadata, not necessarily the navigation category. |
| `aliases` | Searchable alternate names, not extra identities. |
| `scope_note`, examples, non-examples | Optional reading sections when actually present. |
| `lifecycle`, `fact_kind` | Independent status fields; do not collapse into one “verified” flag. |
| `sources`, source status | Source references with recorded version and observed freshness. |
| Relation subject/predicate/object | Exact source identity, predicate identity, and target identity. |
| Module and canonical location | Provenance/details; do not make raw paths the primary labels. |

Navigation categories such as **Roles**, **Skills**, **Documents**, and **Processes** are a presentation mapping over known types. Put that mapping in a small reviewed configuration or adapter table. Do not infer categories from substring matching in names.

### 12.3 Use small result structures

A search card needs an ID, label, category, short definition excerpt, match reason, and relevant warning. It does not need the entire source file, every binding, or the entry's complete relationship neighborhood.

The current `explain()` function attaches relationship and evidence information, and the result envelope can remove results to satisfy its byte bound. Reusing that full shape for every search row would create unnecessary payload pressure. [S05]

Reuse ranking and semantic rules, but build compact reader summaries. Keep detailed relationships and source text behind separate bounded requests. An empty response caused by a byte limit must not be rendered as “No matching term.”

### 12.4 Response envelope

Use one validated envelope for all data responses. For example:

```json
{
  "schemaVersion": 1,
  "projectId": "sys4ai-depot",
  "snapshotId": "<digest of the selected inputs>",
  "state": "partial",
  "data": [],
  "page": {
    "returned": 25,
    "hasMore": true,
    "nextCursor": "<opaque continuation token>"
  },
  "coverage": {
    "complete": false,
    "reasons": ["item_limit"]
  },
  "limits": {
    "maxItems": 25,
    "maxBytes": 32000
  },
  "diagnostics": []
}
```

The example is a contract illustration, not a captured response. Define the meaning of `complete` for each endpoint: it refers to the requested scope and filters, not the entire ontology. Distinguish item limits, byte limits, traversal limits, time limits, and filters in the actual schema.

Use `hasMore: null` when bounded work cannot establish whether more matches exist. Do not fabricate a total. If a total is returned, include its count scope and whether it is exact.

The current traversal envelope's `available_results` can describe discovered results rather than the whole graph. Do not rename it `totalRelationships` without establishing the stronger claim. [S05], [S06]

### 12.5 Cursor and filter semantics

Bind a continuation cursor to the selected project, snapshot, normalized query, filters, direction, sort order, and last returned stable key. Validate it on the server. A signed token or bounded server-side continuation record is preferable to accepting arbitrary client-supplied traversal state.

A changed query or filter starts a new result sequence. A changed snapshot invalidates the cursor. Reject incompatible continuation requests with a specific response; do not silently continue from another version of the ontology.

Implement search pagination in the reader adapter without changing the existing agent command's maximum-result contract. For graph expansion, use separate bounded one-hop requests where appropriate. Never interpret a request for “more” as permission to scan recursively without limits.

### 12.6 Graph contract

Each graph response must identify:

- Nodes by exact canonical ID, with resolved label and presentation category.
- Edges by exact relationship ID, with source, predicate, target, classification, and qualifiers.
- Evidence references and the snapshot that supports the returned assertions.
- The requested scope, filters, and reasons any data was omitted.

A graph edge is not just `{source, target}`. It represents a particular assertion. Preserve distinct assertions even when their endpoints match.

Resolve all returned endpoint labels in the same snapshot. If a reference is broken, report the data problem and keep the underlying ID inspectable; do not invent a label or silently create a valid-looking concept.

### 12.7 Predicate display labels

Prefer the predicate's recorded label. A reviewed presentation mapping may provide a clearer forward or inverse phrase. Keep the canonical predicate ID available in Details.

For incoming relations, either use an explicitly approved inverse phrase or retain the original sentence order. Traversing an edge backward does not reverse the meaning of the assertion.

### 12.8 API failure states

Use distinguishable responses for unavailable identity, ambiguous label, invalid request, expired session, changed snapshot, stale source, resource limit, and unexpected service failure.

Return short user-facing explanations and safe diagnostic codes. Do not expose arbitrary Python exception text, credentials, full local paths outside the selected project, or source contents in generic error messages.

## 13. Snapshot consistency and read-only operation

### 13.1 Use one coherent version at a time

A snapshot identifies the selected ontology inputs and their versions. A definition from one snapshot must not be displayed as though its relationships came from the same snapshot when they did not.

Include `snapshotId` in data requests after context initialization. On a detected change, return a conflict response such as `snapshot_changed`. Preserve the user's route and offer **Refresh knowledge**. Refresh the entry, relationships, and graph together; discard incompatible continuation tokens and old expansions.

The existing context and provenance machinery provides version information to build on. Preserve its meaning rather than substituting a timestamp. [S05], [S07]

### 13.2 Read safely during agent publication

Construct the adapter's in-memory view from a stable set of validated inputs. Use the project's existing transaction/snapshot mechanisms where available. Otherwise, validate the relevant input digests before and after materialization, with a small bounded retry policy.

If the inputs cannot be read consistently, report that the knowledge is being updated. Do not show a partly updated graph or conceal publication conflicts with an empty result.

The local agent must inspect the existing publication implementation before choosing the exact read coordination mechanism. Do not add an independent lock protocol that conflicts with the established publication/recovery process.

### 13.3 Cache views, not authority

An in-memory index is appropriate. Key it by the selected project identity/root, validated input snapshot, relevant helper/adapter version, and presentation mapping version.

Build adjacency indexes for incoming and outgoing relations so selection does not repeatedly scan every relationship. Share one immutable snapshot between concurrent reads. Keep its memory use bounded and release retired snapshots after active readers finish.

Modification times alone are not evidence that source bytes match recorded hashes. A cached page must remain explicitly associated with its snapshot. Revalidate source references when opening evidence, and detect input changes before presenting a newly requested result as current.

Start with correctness. Optimize repeated parsing and indexing only after profiling; do not remove integrity checks to meet a timing target.

### 13.4 Keep startup and browsing separate

Explicitly launching a local service may create narrowly scoped runtime/session state. Ordinary search, navigation, source inspection, and graph expansion must not change canonical records, configuration, generated products, memory, proposals, or receipts.

In particular, those reads must not call `compile`, `build-wiki`, `link-memory`, profile provisioning, embedding preparation, inference execution, or source-hash repair. The existing project commands distinguish these operations. [S04], [S07]

A changed source is a condition to report, not permission to rewrite its provenance hash. A missing optional backend is not permission to install it.

### 13.5 Demonstrate non-mutation

For integration tests, record hashes and relevant timestamps of canonical ontology files, source configuration, memory data/configuration, proposals, and publication receipts. Perform the complete browser read workflow, then compare the protected artifacts.

Whitelist only the documented runtime/session artifacts created by explicit service startup and harmless user view preferences. Do not use an unrestricted whitelist for `.sys4ai/`: it also contains derived state that browsing must not silently rebuild.

## 14. Frontend modules and state management

### 14.1 Suggested source organization

The following tree is proposed, not an existing directory inventory:

```text
SKILLS-depo/ontology/
  explorer/
    src/
      main.ts
      app/                 # shell, routing, typed application state
      api/                 # request client, runtime response validation
      views/               # overview, terms, entry, processes, map
      components/          # search, relationships, source drawer, notices
      graph/               # renderer adapter, layout, display projection
      styles/              # tokens, layout, components, accessibility
    tests/                 # unit/component/browser fixtures and tests
    dist/                  # explicitly built, distributable static assets
    package.json
    <dependency lockfile>
    <Vite configuration>
  scripts/
    ontology_explorer.py       # dedicated read-only local service
    ontology_explorer_read.py  # presentation adapter over canonical readers
    ontology_http.py           # extracted security helpers, if appropriate
    ontology.py                # existing CLI, with an additive explorer command
```

Choose final module names after inspecting current conventions. Do not restructure unrelated skills to match this example. Keep test fixture data outside shipped runtime assets.

### 14.2 Application state

Use one small typed store or equivalent explicit state object. Keep these distinctions:

| State | Meaning |
| --- | --- |
| Selected identity | The entry being inspected. |
| Graph focus identity | The center of the current neighborhood; not automatically changed on selection. |
| Query and filters | The current discovery scope. |
| Expanded identities | Nodes whose neighborhoods the user explicitly requested. |
| Snapshot identity | The version supporting the displayed information. |
| Source selection | The specific evidence reference opened in the drawer. |
| View preferences | Theme, optional panel widths, and similar presentation choices. |

Never store canonical edits in the browser. Keep sensitive source bodies in memory rather than persistent browser storage. Namespace preferences by project, and offer a simple reset rather than a preferences workbench.

### 14.3 Request ordering

Cancel obsolete searches with `AbortController` where practical. Also use request sequence IDs: cancellation alone does not guarantee an earlier response will never arrive.

Before applying a response, verify its project, snapshot, and relevant query/selection identity. A slow response for entry A must not replace entry B after the user has moved on.

### 14.4 Component responsibilities

Search components emit a selected identity. Entry components render known data. Relationship components emit navigation or source-inspection intentions. The graph renderer emits select, focus, and expansion intentions.

Only the application/API layer decides which reads to perform. A renderer must not fetch arbitrary sources, invoke ontology functions, or derive new semantic relationships.

Keep the accessible relationship list and graph synchronized from the same normalized response data. Do not build two independent interpretations of the ontology.

### 14.5 Lifecycle and cleanup

Create the graph instance only when needed. Update selection without rebuilding the whole graph. Add neighborhoods incrementally, preserving existing positions where practical.

Dispose of graph instances, event listeners, timers, and resize observers when leaving the view. Do not keep a layout simulation running behind an entry page.

## 15. Security and local access

### 15.1 Read-only does not mean public

Project definitions and sources can be private. Keep the current loopback-only model and an explicit server-selected project root. A browser request must not choose a filesystem root, scan sibling projects, or access another service's data.

Preserve equivalent Host, Origin, session, CSRF, and source checks when extracting the service. The inspected workbench already implements those protections. [S03]

Do not bind to `0.0.0.0`, enable permissive CORS, or make a development server the normal user-facing launcher.

### 15.2 Separate a reading session from authoring authority

An explorer session permits reading only. It must not require a Director publication grant, accept browser-supplied actor authority, or expose an authoring scope.

Initially preserve the existing security posture for short-lived bootstrap links and configurable sessions. Improve expiry messaging without quietly weakening authentication. An expired session should preserve the desired route and explain how to open a fresh local session.

The new core reader should not require enabling the old advanced `workbench` profile. Introduce its launch/configuration contract explicitly and validate it; do not add undocumented fields to strict existing configuration schemas.

### 15.3 Session and route handling

Consume a one-use bootstrap in the established local session flow. Remove the bootstrap token from the visible URL while preserving the intended safe route. Use project/service-isolated session identifiers and the existing secure cookie properties appropriate to loopback access.

Never put a bootstrap token in a copied link, screenshot, test fixture, access log, Git file, or source reference. A browser-history entry must not preserve the credential.

A convenience launcher can open the browser after explicit startup. A web page must not claim it can restart a stopped Python process without a separately implemented, authorized mechanism.

### 15.4 Remove browser write capability

The explorer's route table must contain only session management and defined read operations. Requests to old draft, review-decision, publication, recovery, generation, profile-change, or execution endpoints must fail.

Do not rely solely on CSS, disabled controls, omitted navigation, or an `authoring=false` field. The dedicated dispatcher must have no path to invoke those operations.

Preserve the separately tested CLI/agent implementations. If trusted-authority helpers currently live in the workbench module, relocate them carefully rather than deleting functions that other callers still import.

### 15.5 Serve only known production assets

The current service has a fixed asset allowlist. A bundled frontend needs a new bounded serving rule for its actual build output. [S03]

Use a build manifest or an equivalently explicit allowlist rooted in the installed explorer bundle. Reject traversal, symlinks where disallowed, and unknown paths. Serve correct MIME types and retain security headers. Do not expose the repository, dependency cache, unneeded source maps, or package-manager files.

Test the **production build** under its real Content Security Policy. Graph libraries and build tools may have different style/worker requirements from the existing hand-written page. Resolve any requirement narrowly and document it. Do not “fix” a rendering failure by allowing all origins, arbitrary inline scripts, or `unsafe-eval`.

### 15.6 Treat source content as data

Use safe text rendering for labels and definitions. Do not insert ontology text with raw `innerHTML`. Display source excerpts as escaped text by default.

Resolve source requests through the record's registered reference and snapshot. Reuse the project's path and source validation, including evidence freshness and size limits. A source drawer is not a general filesystem viewer.

Test encoded traversal, absolute paths, symlink escapes, unselected source references, and changed source bytes. Never execute instructions found in a displayed document.

### 15.7 Keep diagnostics useful without leaking data

Apply request-size, execution-time, concurrency, and memory bounds. Return stable diagnostic codes and brief explanations. Keep detailed diagnostics local and redact session material.

Do not add analytics, cloud logging, external fonts, or external image fetching to the normal browsing path. The production interface should remain functional without an internet connection after its assets are installed.

## 16. Accessibility and responsive behavior

### 16.1 Target WCAG 2.2 AA, then verify the actual interface

Use WCAG 2.2 AA as the acceptance target. Relevant requirements include keyboard access, visible and unobscured focus, sufficient contrast, alternatives to dragging, and appropriately sized interactive targets. Compliance must be tested; it cannot be inferred from choosing a component library. [E03]

Make the ordinary interface semantic HTML: navigation links, headings, labeled inputs, buttons, and lists. Do not assign `role="application"` to the entire page simply because the graph supports specialized interaction.

### 16.2 The text alternative is a first-class view

Provide a **List** option beside the map. It must expose the same selected scope, filters, relationship identities, directions, and warnings as the visual view. It must support opening entries, inspecting evidence, focusing a term, and requesting more connections.

The list is not a consolation page with less information. A keyboard or screen-reader user should be able to complete the same knowledge tasks without manipulating a canvas.

Do not place hundreds of invisible graph controls in the tab order. Prefer a small set of graph controls plus the accessible list. Announce meaningful selection/result changes, not every layout frame.

### 16.3 Input and focus behavior

All essential actions must be possible without dragging, hovering, double-clicking, or memorizing shortcuts. Provide visible Zoom, Fit current view, and Focus here buttons as appropriate.

Escape closes a temporary menu/drawer and restores focus to its trigger. Opening a source drawer moves focus to its heading or first meaningful control. Closing it returns focus to the evidence link. Browser navigation should not leave focus trapped inside a removed component.

Use standard links for navigable entries wherever practical, retaining expected new-tab and copy-link behavior after authentication. Avoid replacing ordinary links with custom clickable text.

### 16.4 Visual baseline

Use the user's system font, a base reading size around 16 CSS pixels, generous line spacing, and a small consistent spacing scale. Use a restrained border/surface system rather than many stacked cards. Keep secondary metadata smaller but still comfortably readable.

Normal text should meet 4.5:1 contrast; large text and relevant non-text controls have their applicable lower contrast requirements. WCAG 2.2 AA includes a 24-by-24 CSS-pixel minimum target criterion with exceptions. Use approximately 44-pixel primary controls as a product comfort target, not as a claim that AA universally requires that size. [E03]

Use category icons, labels, and line styles as well as color. A user should not need to distinguish two hues to understand an edge classification. Check both light and dark themes independently.

Avoid a rainbow of node categories. Start with a small distinguishable set and an unobtrusive legend. Selection must be more prominent than category decoration.

### 16.5 Responsive layout

At narrower widths, collapse navigation into a drawer and make the entry reader the primary surface. Do not squeeze search results, an entry, a graph, and source evidence into parallel columns.

On a phone, present Map as a dedicated view. Selecting a node can open a dismissible details sheet; the List option remains visible. Process steps and source content use ordinary vertical reading.

Test the surrounding interface at a 320 CSS-pixel viewport and with substantial browser zoom. Spatial diagrams can require two-dimensional navigation, but that exception does not excuse non-reflowing menus or unreadable entry text. [E07]

### 16.6 Motion and feedback

Honor reduced-motion preferences. Stop layouts once settled. Do not animate every node on each selection or continuously pulse connections.

Use a quiet loading state that preserves the current context. Avoid flashing the whole page blank while a new neighborhood loads. Use an error beside the failed region rather than replacing unrelated readable content.

### 16.7 Test beyond an automated scanner

Add automated accessibility checks to browser tests, then perform manual keyboard and screen-reader tests. Playwright's documentation explicitly treats automated scanning as only part of accessibility testing. [E06]

At minimum, record the browsers and assistive technologies actually tested. VoiceOver with Safari is relevant to a macOS user. Add a Windows screen-reader/browser combination when available. Report untested combinations rather than declaring universal accessibility.

## 17. Performance and scale

### 17.1 Treat the following as proposed budgets

These values are design targets for an initial benchmark, not measured performance of either repository.

| Interaction | Initial target | Measurement condition |
| --- | --- | --- |
| First readable screen | Within about 2 seconds | Cold local launch, installed assets, representative fixture. |
| Search response applied | p95 within 200 milliseconds | Warm snapshot, excluding the intentional input debounce. |
| Entry opens | p95 within 250 milliseconds | Warm snapshot and bounded entry data. |
| Focused graph becomes usable | Within about 1.5 seconds | Initial neighborhood of roughly 25 nodes/50 edges. |
| Selection feedback | Within 100 milliseconds | Already loaded graph; no full graph recreation. |
| Additional connections | Keep the current view usable while loading | Bounded request, explicit progress, cancellable where practical. |

Benchmark on the actual target machine and record hardware, browser, build, dataset size, payload limits, and whether the run was cold or warm. Use repeated runs and report median and p95, not a single favorable sample.

If source validation dominates latency, profile it separately. Improve reuse of validated immutable inputs before considering a contract change. Never label stale information current merely to satisfy these budgets.

### 17.2 Workload fixtures

Use at least three synthetic, clearly labeled fixture sizes:

| Fixture | Suggested scale | What it tests |
| --- | --- | --- |
| Small | About 50 entries and 100 relationships | Ordinary interactions, empty states, and simple navigation. |
| Representative | About 1,000 entries and 5,000 relationships | Search ranking, paging, snapshot indexes, normal bounded map behavior. |
| Stress | About 5,000 entries and 50,000 relationships | Limits, hub handling, cancellation, and graceful degradation. |

These fixture sizes do not assert that the current loader already meets those targets. Record the limits found. Stress testing is successful when the system remains bounded and honest, not only when it renders everything.

Include long labels, duplicate labels, aliases, many sources, multiple predicates between the same endpoints, cycles, self-loops, highly connected hubs, missing references, and large definitions. Uniform random graphs alone will miss important interaction failures.

### 17.3 Bound graph size at every layer

The browser display budget, API result budget, traversal visit budget, and serialized-byte budget are different limits. Enforce each independently.

The inspected agent retrieval contracts cap traversal at 100 visited nodes and responses at the configured byte limit, with documented maximums. Keep those existing contracts intact. [S05], [S06], [S07]

A browser can combine a few independently bounded reads, but it must also enforce its cumulative visible-node/edge budget. Explain when more information is available through the list or a new focus rather than endlessly accumulating nodes.

Do not fetch the whole project merely to calculate an initial graph layout or a decorative overview statistic.

### 17.4 Load only what the current view needs

Render the shell and reader without waiting for graph code. Lazy-load the graph bundle on first use. Fetch source excerpts only when opened.

Maintain in-memory search and adjacency indexes associated with the current snapshot. Avoid attaching all relationships to every search result and avoid reading a whole source document when a validated section is sufficient.

Measure compressed bundle size and establish a regression baseline. Do not add dependencies casually to solve small styling or formatting problems. Any worker or layout extension must justify its installation, lifecycle, security policy, and accessibility behavior.

### 17.5 Degrade gracefully

If the graph fails, keep the entry and relationship list available. If a layout times out, keep valid returned data and provide a stable fallback arrangement. If an optional richer search feature is unavailable, exact/lexical search still works.

Use **Show fewer connections**, **Focus here**, and narrower filters rather than a crash or an unexplained empty graph. Do not auto-enable external services or remote computation to recover.

## 18. Repository changes and distribution

### 18.1 Source-of-truth change map

The paths below distinguish inspected locations from proposed additions. Recheck them against the implementation checkout.

| Area | Inspected or proposed location | Recommended action |
| --- | --- | --- |
| Old reusable UI | `SKILLS-depo/ontology/workbench/` | Retire active assets after cutover; do not preserve editor/review/advanced bundles in the new build. |
| New reusable UI | `SKILLS-depo/ontology/explorer/` — proposed | Add the reader, map, tests, and distributable production bundle. |
| Existing service | `SKILLS-depo/ontology/scripts/ontology_workbench.py` | Extract reusable security/authority helpers deliberately; retire the old browser-serving role. |
| New service/adapter | `ontology_explorer.py`, `ontology_explorer_read.py` — proposed | Add a read-only dispatcher and presentation adapter. |
| CLI entry | `SKILLS-depo/ontology/scripts/ontology.py` | Add explicit explorer launch; preserve existing agent read/write contracts. |
| Retrieval/graph | `ontology_retrieval.py`, `ontology_graph.py` | Reuse semantics; make only necessary, tested additive changes. |
| Wiki generator | `ontology_wiki.py` | Preserve as an explicit derived-output path. |
| Skill instructions | `SKILLS-depo/ontology/SKILL.md`, `references/commands.md` | Describe the reader launch and remove obsolete human-workbench guidance. |
| Ontology contracts | Relevant `ONTOLOGY-depo/` contracts and starter assets | Update only the contracts/configuration affected by the browser replacement. |
| Distribution | `depot/template-update.json` and actual asset-generation rules | Verify the new assets, build manifest, and notices reach the neutral template. |
| Active root | `.agents/skills/ontology/` | Adopt the reviewed reusable version explicitly; preserve local customizations. |
| Neutral template | `Projects/Sys4AI-Template-Project/` | Verify pipeline output and neutral project behavior. |
| Historical evidence | Existing `Verification/` snapshots and prior initializer editions | Preserve; they are not active copies to bulk-rewrite. |

These ownership boundaries follow the inspected root guidance and template mapping. [S11], [S12]

### 18.2 Find active callers before deleting modules

Search the active source collection, current root installation, template pipeline, tests, launchers, and contract documents for references to the workbench module, asset paths, service identity, command, profile, and session directory.

Classify each match as active runtime, shared helper import, test, current documentation, generated/distributed asset, or historical evidence. Do not perform a repository-wide search-and-replace across all matches.

In particular, inspect imports of trusted-authority and publication-related helpers currently located in `ontology_workbench.py`. Move shared functionality first and verify its callers before deleting the old service module.

### 18.3 Service identity and health compatibility

The inspected service and health probe expect the identity `sys4ai-ontology-workbench` and validate helper/configuration context. [S03], [S07]

Give the new service an explicit identity, such as `sys4ai-ontology-explorer`, and update its health contract and tests. Decide whether to add a dedicated `--explorer-url` probe or retain a narrowly documented compatibility route. Do not pretend a new service is the old authoring service simply to make a health check pass.

Keep these states distinct: installed, configured, running, readable, stale, wrong project, and unavailable. Reader availability must not depend on an unrelated optional inference or embedding profile passing its checks.

### 18.4 Source changes may affect provenance

The current ontology configuration includes skill/document sources with recorded hashes and locked imports. Editing a source document can therefore make its recorded evidence stale. [S09], [S10]

After the code and documentation settle, identify affected provenance, helper certifications, and explicitly generated outputs. Refresh them only through the appropriate authorized workflow. Do not update hashes mechanically just to suppress warnings, and do not let the explorer perform that maintenance itself.

Preserve separate completion records for the frontend change and any authorized ontology/documentation maintenance. A functioning UI does not prove that every optional backend or generated artifact is current.

### 18.5 Template and independent-project verification

The same explorer must read the neutral template without hard-coded Sys4AI-depot labels or IDs. Read the project name, purpose, selected modules, and available categories from the selected project's validated data.

Test against a second fixture project with a different namespace and different meanings for at least one shared label. Verify that routes, caches, preferences, sources, and sessions do not cross project boundaries.

Distribution into the neutral template is not authorization to update all registered product projects. Existing projects retain their own adoption boundary. [S11]

## 19. Migration and retirement of the workbench

### 19.1 Record a baseline

Before implementation, record the checkout commit, relevant file hashes, current launch behavior, existing test commands, and baseline results for canonical retrieval, publication/recovery, and template distribution.

Preserve unrelated local modifications. Do not overwrite user work to obtain a clean diff. Report pre-existing failures separately from regressions introduced by the replacement.

### 19.2 Build the replacement separately, then cut over

A temporary development route is reasonable while the reader is being built. The final product must not leave the old workbench as another prominent navigation destination or a permanent “Advanced” mode.

Make the new frontend the normal human entry point only after its reader, map, source access, security, and project isolation tests pass. Then remove old frontend imports and active static assets.

### 19.3 Decide command compatibility explicitly

A proposed launch command is:

```bash
<project-python> .agents/skills/ontology/scripts/ontology.py --project-root "$PWD" explore --open
```

This is a command to implement, not an existing verified command.

For the old `workbench` command, choose one documented behavior: a deprecation error explaining the new reader command, or a compatibility alias that launches the read-only explorer. An alias must not silently ignore old authoring/grant flags; reject incompatible arguments with a clear explanation.

Update launchers and user documentation. Do not preserve obsolete UI credentials or migrate bootstrap tokens. Let old sessions expire and create fresh reader sessions.

### 19.4 Preserve agent authoring and history

Keep permitted agent/CLI proposal creation, validation, decisions, publication, and exact recovery available through their existing interfaces. Do not delete proposal files, receipts, ontology records, memory records, or historical verification evidence.

Verify those operations independently of the explorer's read-only tests. Removing a browser endpoint is not a reason to weaken the underlying publication rules.

### 19.5 Rollback concerns code, not knowledge

Record a reversible code/asset/configuration migration. A rollback may restore the prior implementation when explicitly chosen; it must not restore old ontology or memory snapshots over newer valid work.

Separate UI deployment state from canonical data. A failed reader rollout must not require reconstructing the project's knowledge or publication history.

## 20. Implementation sequence

Use small reviewable increments with clear completion evidence. Do not begin with a large visual rewrite that leaves data semantics and access controls unspecified.

| Phase | Work | Required output and exit condition |
| --- | --- | --- |
| **0. Verify baseline and content** | Read current project guidance; compare snapshots; locate callers; inventory types, predicates, sources, and process coverage. | Change map, dependency/license decision, data gaps, baseline tests, and confirmed root/template boundaries. |
| **1. Read-only service** | Add the dedicated adapter, envelope, session integration, safe assets, and proposed launch contract. | API tests prove bounded reading, correct identity, source protection, and rejection of browser writes. |
| **2. Reader and discovery** | Build shell, routes, search, term reader, evidence drawer, status handling, and Back/Forward. | A user can find a term, read it, follow a relationship in the list, and inspect its source without graph code. |
| **3. Interactive map** | Add stable labeled/directed relationships, selection/focus separation, expansion, filters, and synchronized list. | Parallel-edge, truncation, keyboard, state-restoration, and graph-failure tests pass. |
| **4. Processes and responsive behavior** | Add source-supported process presentation, content-gap states, mobile layouts, themes, and accessibility fixes. | Supported process content is useful; missing sequence data is not invented; manual browser/keyboard checks are recorded. |
| **5. Retire and distribute** | Remove the active old frontend; update CLI/docs/health contracts; verify template pipeline and active-root adoption. | No old authoring UI ships; agent workflows remain intact; root and neutral-template tests pass. |
| **6. Validate the integrated experience** | Run browser security, accessibility, performance, non-mutation, and user-task checks against the production build. | Requirement-to-test matrix completed, actual evidence attached, and remaining limitations explicitly reported. |

Phase 2 is a vertical slice, not permission to omit the graph from final delivery. Phase 4 includes readable process access; optional automatic flow-diagram generation is not required to satisfy that outcome.

Content gaps that require canonical changes must be recorded and handled through existing approval rules. Implement the honest UI states in this change; do not silently fabricate content to make a demonstration look complete.

## 21. Acceptance tests

### 21.1 Required test matrix

Use real canonical test fixtures and the actual production frontend bundle. The following cases are minimum acceptance coverage, not a claim that such tests already exist.

| Test | Scenario and passing result | Requirements |
| --- | --- | --- |
| AT-01 | Launch the human interface. Only reading/exploration destinations appear; no authoring modules or controls load. | UX-01, SAFE-01 |
| AT-02 | Search a preferred label, alias, exact ID, and words in a definition. Matching is deterministic and relevant. | UX-02 |
| AT-03 | Two entries share a label/alias. Both appear with distinctions; neither is silently selected. | UX-02, DATA-01 |
| AT-04 | Apply category/lifecycle filters to a multi-page result set. Filtering happens before pagination; valid later matches remain reachable. | UX-02, PERF-01 |
| AT-05 | Search returns more matches than one page permits. Continuation is stable, with no duplicate or skipped identities within the same snapshot. | PERF-01 |
| AT-06 | A result is omitted by a byte/time/traversal bound. The UI reports incomplete coverage rather than “nothing exists.” | DATA-01, PERF-01 |
| AT-07 | Read an entry with definition, aliases, scope note, and examples. Present fields faithfully; omit absent sections without inventing content. | DATA-01 |
| AT-08 | Open a deprecated entry by exact ID. Show its status and recorded replacement without silently rewriting history. | DATA-02 |
| AT-09 | A draft or inferred record is available under an explicit permitted filter. Its status remains distinct from approved asserted knowledge. | DATA-02 |
| AT-10 | Select a graph node. Details change, but the camera and graph focus do not unexpectedly move. | UX-04, UX-06 |
| AT-11 | Choose Focus here. The neighborhood changes deliberately, and Back restores the prior useful state. | UX-04, UX-06 |
| AT-12 | Expand a high-degree node. Limits remain enforced and omitted connections are clearly disclosed. | UX-04, PERF-01 |
| AT-13 | Two predicates connect the same endpoints. Both canonical relationship IDs and their meanings remain inspectable. | UX-03, DATA-02 |
| AT-14 | Traverse an incoming relationship. Arrow and sentence retain the canonical subject–predicate–object direction. | UX-03, DATA-02 |
| AT-15 | Render self-loops, cycles, and qualified relationships. No infinite expansion or semantic merging occurs. | DATA-02, PERF-01 |
| AT-16 | Switch between map and list. Selection, filters, returned scope, and warnings agree. | UX-07, DATA-02 |
| AT-17 | Open a supported process. Purpose, roles, inputs/outputs, and ordering appear only where supported by the selected source. | UX-05 |
| AT-18 | A process has no recorded step order. Show the gap; do not infer a sequence from graph layout or unrelated relations. | UX-05, DATA-01 |
| AT-19 | Open a definition's or relationship's source. Show the authorized locator/excerpt and evidence status for the correct identity. | DATA-03 |
| AT-20 | The source bytes change after the entry loads. Do not present the new bytes as the originally recorded evidence without a warning/version distinction. | DATA-03 |
| AT-21 | Canonical inputs change during navigation or publication. Reject mixed-version continuations; refresh the display coherently. | DATA-01 |
| AT-22 | A slow response for entry A arrives after selecting B. B remains the current entry. | UX-06 |
| AT-23 | Session expires or service stops. Preserve readable context and desired route; explain reconnection without making unauthorized startup claims. | UX-06, SAFE-02 |
| AT-24 | Submit direct browser requests to old write or execution endpoints. They fail; no protected artifacts change. | SAFE-01 |
| AT-25 | Use invalid Host/Origin/CSRF/session values or another service's credentials. Requests fail without leaking project data. | SAFE-02 |
| AT-26 | Attempt encoded traversal, absolute-path access, symlink escape, or an unselected source reference. Access is denied. | SAFE-02 |
| AT-27 | Labels/source text contain HTML, script-like text, or malicious links. They display safely and do not execute. | SAFE-02 |
| AT-28 | Load the production bundle under the production CSP with no internet. Reader and graph work without remote assets. | SAFE-02, PORT-01 |
| AT-29 | Complete all major reading tasks by keyboard and via the relationship list. No drag, hover, or canvas-only action is required. | UX-07 |
| AT-30 | Use narrow viewport, browser zoom, reduced motion, and both themes. Text reflows, controls remain operable, and important states remain legible. | UX-07 |
| AT-31 | Browse the root and neutral template, then a separate namespace fixture. No hard-coded project identity, cache leakage, or source crossover occurs. | PORT-01, SAFE-02 |
| AT-32 | Perform all read workflows with missing optional embedding/RDF services. Core reading works; nothing is installed or started implicitly. | DATA-04, SAFE-01 |
| AT-33 | Compare protected file hashes/timestamps before and after the read workflow. Ontology, memory, proposals, receipts, and generated products are unchanged. | DATA-04, SAFE-01 |
| AT-34 | Disable or fail the graph renderer. Definitions, relationship list, and evidence access still work. | UX-07, PERF-01 |
| AT-35 | Run existing agent retrieval, publication/recovery, and template contract tests. No unintended behavioral regression occurs. | DATA-01, PORT-01 |
| AT-36 | Measure the representative and stress fixtures. Publish actual timings, memory/limits, and graceful-degradation results rather than assumed performance. | PERF-01 |

### 21.2 Test layers

**Unit tests:** normalization, deterministic ranking, category mapping, cursor validation, edge identity, predicate direction, graph/list projection, source-reference selection, and state transitions.

**Service integration tests:** selected-root isolation, safe asset routing, session/bootstrap behavior, source freshness, request/response budgets, snapshot conflicts, non-mutation, and inaccessible write operations.

**Browser tests:** search-to-entry navigation, Back/Forward, graph selection/focus, source drawer, keyboard behavior, responsive layout, expired session, CSP, and renderer failure. Use Playwright or the project's established equivalent. Automated accessibility scanning can supplement these flows. [E06]

**Manual tests:** actual readability, focus behavior, screen-reader use, relationship comprehension, and whether a person can find and explain project information without learning ontology-management terminology.

### 21.3 Definition of done

The local agent should not mark the work complete until all mandatory requirements have a corresponding implementation location and test/evidence reference.

Completion requires a working production build, an explicit launch path, safe read-only API, usable search and process reading, an interactive relationship map with text equivalence, verified root/template behavior, updated current documentation, and preserved agent workflows.

Record skipped tests, pre-existing failures, content gaps, and environment limitations separately. Screenshots show visual state; they do not prove API security or read-only behavior. Passing unit tests does not prove that the final UI is understandable.

## 22. Usability validation

### 22.1 Validate knowledge tasks, not feature discovery

Ask a person unfamiliar with the implementation to complete these tasks using only the interface:

| Task | What to observe |
| --- | --- |
| Find the meaning of a named term. | Can the person locate and explain the definition without opening technical metadata? |
| Distinguish two related terms. | Do labels, scope notes, and examples prevent confusion? |
| Explain a displayed relationship. | Can the person correctly identify who relates to whom and what the relationship means? |
| Explore a neighboring concept and return. | Does selection, focus, and Back behavior preserve orientation? |
| Understand a process. | Can the person identify its purpose and supported steps, or recognize that ordering is not recorded? |
| Check the source of a claim. | Can the person open the evidence and understand a freshness warning? |

An initial target is to find a known term and its definition within roughly 30 seconds without instruction. Treat that as a task target, not a universal standard or a measured result.

### 22.2 Use small, honest validation rounds

A small exploratory round with several participants can expose confusing labels and interactions. Record task completion, wrong turns, mistaken relationship interpretations, requests for help, and participant wording. Do not treat a small sample as statistical proof of general usability.

If only the project owner is available, run and document the same task walkthrough. State that broader user validation remains unperformed rather than labeling the UI “validated” without qualification.

### 22.3 Capture useful visual evidence

The implementation handoff should include actual browser screenshots of the overview, search results, a populated entry, a process page, a focused map, a parallel-edge example, a source drawer, an incomplete-result state, and a narrow-screen view.

Capture the running production build, not static mockups alone. Remove private source content and all session material before sharing evidence beyond the authorized local project.

Resolve high-impact comprehension failures before adding polish. A graph that looks attractive but leads people to reverse a dependency or mistake proximity for causality is not acceptable.

## 23. Risks and decisions to preserve

| Risk | Consequence | Required response |
| --- | --- | --- |
| Reintroducing authoring under “Advanced” | Recreates the workbench the user rejected. | Keep authoring and execution out of this interface. |
| Sparse definitions or process metadata | A cleaner page still contains little useful knowledge. | Inventory coverage; improve content through existing review; show honest gaps. |
| Treating all links as equivalent | Incorrect interpretation of typed relationships. | Preserve predicates, directions, canonical relation IDs, and qualifiers. |
| Letting the graph dominate every page | Simple definition lookup becomes unnecessarily difficult. | Reader first for Terms; dedicated Map when spatial exploration helps. |
| Copying Logseq implementation wholesale | Maintenance and licensing burden unrelated to the user's need. | Independent implementation and explicit dependency notices. |
| UI caching hides source changes | The page appears current when evidence has changed. | Snapshot-bound data, source revalidation, and visible refresh states. |
| Source-document edits invalidate recorded hashes | Health/provenance becomes stale after documentation changes. | Separate authorized maintenance; never auto-repair during reads. |
| Raising global retrieval limits for visualization | Agent contracts and resource protections change unnecessarily. | Thin DTOs, paging, bounded expansion, and separate browser display budgets. |
| Updating every project copy automatically | Project-owned customizations or unrelated deployments are overwritten. | Source/template pipeline plus explicit project adoption. |
| Testing only development mode | The shipped bundle fails CSP, asset serving, or offline use. | Test the production build with the actual local service. |
| Marking the work complete after a visual demo | Missing security, accessibility, or semantic regressions remain hidden. | Require the acceptance matrix and integrated evidence. |

Preserve these decisions during implementation: **read-only, project-local, canonical-source-backed, graph plus equivalent text, source-visible, and independent of optional AI services.** Any proposed change to those decisions requires an explicit discussion of user intent, not an assumption that more functionality is better.

## 24. Local-agent execution brief

The following is a ready-to-use implementation brief. It does not itself create a Task, grant publication authority, or authorize changes to unrelated projects.

> Replace the Sys4AI ontology workbench frontend with **Project Knowledge**, a simple read-only ontology reader and relationship explorer. Use this document as the implementation specification, subject to the current project's governing instructions and verified checkout state.
>
> Start by reading the current `SOUL.md`, `ROLE.md`, `AGENTS.md`, and `SPECS.md`, then the relevant ontology skill/contracts and template distribution instructions. Compare the current checkout with the inspected commit recorded in Section 2. Preserve unrelated local changes and report material differences before relying on a file-level recommendation.
>
> Implement four human-facing destinations: Overview, Terms, Processes, and Map. Definitions must be easy to find and read. Relationships must show their actual meaning and direction. The map must support selection, focus, bounded expansion, pan/zoom, and an equivalent accessible list. Preserve context through browser history. Sources and meaningful freshness/status warnings must be easy to inspect.
>
> Do not build an ontology editor. Remove active draft, review, publish, inference, query-console, and AI-generation UI. The browser service must not expose those operations. Preserve the existing agent/CLI proposal, publication, authority, and recovery workflows and their history.
>
> Reuse canonical ontology readers through a small read-only presentation adapter. Use deterministic search without semantic fallback. Keep source evidence, canonical identities, parallel relationships, qualifiers, lifecycle, and fact classifications intact. Do not derive process order from graph layout or invent missing explanations. Do not query or modify memory during normal browsing.
>
> Prefer TypeScript, semantic HTML/CSS, a Cytoscape.js renderer adapter, and an explicitly built static bundle served by the local Python service. Do not fork Logseq, add a production Node server, or introduce another graph database. Keep the existing local security properties and verify the actual production Content Security Policy.
>
> Make reusable changes in the source collection. Verify neutral-template distribution and explicitly adopt the reviewed assets into the active root. Do not recursively overwrite registered product projects, historical verification snapshots, or previous initializer editions. Identify any source-provenance maintenance separately and use the current authorized process.
>
> Follow the implementation sequence and acceptance matrix. Verify a real production build in a browser. Deliver the implementation, launch/build instructions, updated API/compatibility documentation, test results, a requirement-to-evidence map, screenshots, measured performance results, and a reversible code migration. Distinguish pre-existing failures, untested environments, and content gaps from completed work. Do not claim completion based only on generated code or a static screenshot.

### Required completion report

Keep the final implementation report focused on what changed and what was verified. Include the actual commit/build identity, changed-file map, exact commands run, test summaries, browser/accessibility coverage, measured limits, protected-file non-mutation evidence, template/root checks, and remaining limitations.

Do not include bootstrap links, credentials, private source bodies, or unsupported claims that the interface is secure, accessible, or fast. Link to the actual evidence instead.

## 25. Sources

Repository findings refer to the inspected material listed below. Most repository links are pinned to the reviewed commit; the Logseq README is a rolling default-branch reference. External documentation was consulted during this examination. The local agent must recheck versions and any changed contracts before implementation.

### 25.1 Sys4AI primary sources

| Reference | Source | Relevance / inspection scope |
| --- | --- | --- |
| S00 | [Sys4AI inspected commit][S00] | Commit returned by the main-branch metadata read. |
| S01 | [Workbench HTML][S01] | Navigation, technical filters, reader, authoring/review/advanced sections. |
| S02 | [Workbench application JavaScript][S02] | Startup imports, API usage, search/inspection, nine-node SVG graph, session handling. |
| S03 | [Workbench Python service][S03] | Inspected service, session, source, authoring-helper, and dispatcher portions; not an executed security audit. |
| S04 | [Ontology skill][S04] | Core/advanced distinction; read/write, memory, authority, and project boundaries. |
| S05 | [Canonical retrieval implementation][S05] | Ranking, explanation payloads, semantic fallback, limits, and response envelope. |
| S06 | [Graph traversal implementation][S06] | Bounded neighbors/path traversal, canonical direction, edge identity, and truncation. |
| S07 | [Ontology command reference][S07] | Inspected core commands, advanced/read distinctions, limits, health, and generated outputs. |
| S08 | [Wiki generator][S08] | Deterministic derived Markdown, evidence, relationships, backlinks, and explicit build. |
| S09 | [Root ontology configuration][S09] | Selected project, namespaces, modules, sources, publication binding, and retrieval settings. |
| S10 | [Project canonical records][S10] | Inspected sample of skill/capability/artifact/governance relations, including parallel predicates. |
| S11 | [Root agent/project guidance][S11] | Source-collection ownership, template distribution, and project-local adoption boundaries. |
| S12 | [Template update mapping][S12] | Explicit starter overrides and mirrors; implementation must also inspect the current pipeline. |
| S13 | [Sys4AI license-scope notice][S13] | Code/document license assignment and preservation of third-party terms. |

### 25.2 Logseq primary sources

| Reference | Source | Relevance / inspection scope |
| --- | --- | --- |
| L00 | [Logseq source snapshot][L00] | Snapshot used for the commit-qualified graph and license reads. |
| L01 | [Logseq README][L01] | Default-branch README read during examination; rolling reference, including database-version status. |
| L02 | [Logseq graph settings component][L02] | Inspected settings/defaults, saved per-repository preferences, and display-related code. |
| L03 | [Logseq graph-renderer bridge][L03] | Renderer integration, callbacks, incremental updates, and lifecycle handling. |
| L04 | [Logseq graph-data worker][L04] | Inspected graph preparation and endpoint-pair link aggregation. |
| L05 | [Logseq license][L05] | GNU Affero General Public License version 3. |

### 25.3 Official implementation and accessibility references

| Reference | Source | Relevance / inspection scope |
| --- | --- | --- |
| E01 | [Cytoscape.js official documentation][E01] | Graph rendering/interaction/layout capabilities and MIT core license; verify installed dependency version. |
| E02 | [Sigma.js official documentation][E02] | Alternative graph-rendering library reference; not the recommended initial integration. |
| E03 | [W3C WCAG 2.2][E03] | Normative accessibility reference; the document proposes AA as a target, not a verified result. |
| E04 | [WAI-ARIA combobox pattern][E04] | Interaction and semantics reference for search suggestions. |
| E05 | [Vite: Building for Production][E05] | Production static-build reference; not a requirement for a Node production service. |
| E06 | [Playwright: Accessibility testing][E06] | Automated browser accessibility checks and their limits. |
| E07 | [W3C: Understanding Reflow][E07] | Responsive/zoom requirements and the distinction between spatial diagrams and surrounding UI. |

> Architectural choices, interaction defaults, proposed budgets, and the implementation sequence are recommendations derived from the stated user goal and the source review. They are not existing product features or measured results unless explicitly identified as such.

[S00]: https://github.com/Omegapy/Sys4AI/commit/744c8b06d5fda905201145ed313a2da8de2e601f "Sys4AI inspected commit"
[S01]: https://github.com/Omegapy/Sys4AI/blob/744c8b06d5fda905201145ed313a2da8de2e601f/SKILLS-depo/ontology/workbench/index.html "Workbench HTML"
[S02]: https://github.com/Omegapy/Sys4AI/blob/744c8b06d5fda905201145ed313a2da8de2e601f/SKILLS-depo/ontology/workbench/app.js "Workbench application JavaScript"
[S03]: https://github.com/Omegapy/Sys4AI/blob/744c8b06d5fda905201145ed313a2da8de2e601f/SKILLS-depo/ontology/scripts/ontology_workbench.py "Workbench Python service"
[S04]: https://github.com/Omegapy/Sys4AI/blob/744c8b06d5fda905201145ed313a2da8de2e601f/SKILLS-depo/ontology/SKILL.md "Ontology skill"
[S05]: https://github.com/Omegapy/Sys4AI/blob/744c8b06d5fda905201145ed313a2da8de2e601f/SKILLS-depo/ontology/scripts/ontology_retrieval.py "Canonical retrieval implementation"
[S06]: https://github.com/Omegapy/Sys4AI/blob/744c8b06d5fda905201145ed313a2da8de2e601f/SKILLS-depo/ontology/scripts/ontology_graph.py "Graph traversal implementation"
[S07]: https://github.com/Omegapy/Sys4AI/blob/744c8b06d5fda905201145ed313a2da8de2e601f/SKILLS-depo/ontology/references/commands.md "Ontology command reference"
[S08]: https://github.com/Omegapy/Sys4AI/blob/744c8b06d5fda905201145ed313a2da8de2e601f/SKILLS-depo/ontology/scripts/ontology_wiki.py "Wiki generator"
[S09]: https://github.com/Omegapy/Sys4AI/blob/744c8b06d5fda905201145ed313a2da8de2e601f/ontology.yaml "Root ontology configuration"
[S10]: https://github.com/Omegapy/Sys4AI/blob/744c8b06d5fda905201145ed313a2da8de2e601f/ONTOLOGY/modules/project/project.jsonld "Project canonical records"
[S11]: https://github.com/Omegapy/Sys4AI/blob/744c8b06d5fda905201145ed313a2da8de2e601f/AGENTS.md "Root agent/project guidance"
[S12]: https://github.com/Omegapy/Sys4AI/blob/744c8b06d5fda905201145ed313a2da8de2e601f/depot/template-update.json "Template update mapping"
[S13]: https://github.com/Omegapy/Sys4AI/blob/744c8b06d5fda905201145ed313a2da8de2e601f/LICENSE "Sys4AI license-scope notice"
[L00]: https://github.com/logseq/logseq/commit/08c15e3d9feff9e330430af3a9fab27dd7dbb0a0 "Logseq source snapshot"
[L01]: https://github.com/logseq/logseq/blob/master/README.md "Logseq README"
[L02]: https://github.com/logseq/logseq/blob/08c15e3d9feff9e330430af3a9fab27dd7dbb0a0/src/main/frontend/components/graph.cljs "Logseq graph settings component"
[L03]: https://github.com/logseq/logseq/blob/08c15e3d9feff9e330430af3a9fab27dd7dbb0a0/src/main/frontend/extensions/graph.cljs "Logseq graph-renderer bridge"
[L04]: https://github.com/logseq/logseq/blob/08c15e3d9feff9e330430af3a9fab27dd7dbb0a0/src/main/frontend/worker/graph_view.cljs "Logseq graph-data worker"
[L05]: https://github.com/logseq/logseq/blob/08c15e3d9feff9e330430af3a9fab27dd7dbb0a0/LICENSE.md "Logseq license"
[E01]: https://js.cytoscape.org/ "Cytoscape.js official documentation"
[E02]: https://www.sigmajs.org/docs/ "Sigma.js official documentation"
[E03]: https://www.w3.org/TR/WCAG22/ "W3C WCAG 2.2"
[E04]: https://www.w3.org/WAI/ARIA/apg/patterns/combobox/ "WAI-ARIA combobox pattern"
[E05]: https://vite.dev/guide/build "Vite: Building for Production"
[E06]: https://playwright.dev/docs/accessibility-testing "Playwright: Accessibility testing"
[E07]: https://www.w3.org/WAI/WCAG22/Understanding/reflow.html "W3C: Understanding Reflow"
