---
schema_version: 2
trd_id: "TRD-20260928-92C32D18"
title: "Shared Project app homepage and Knowledge integration"
slug: "shared-project-app-homepage-and-knowledge-integration"
created_at: "2026-09-28T19:21:16-06:00"
updated_at: "2026-09-28T20:14:58-06:00"
status: "trd_done"
revision: 2
last_action_id: "TO-TRD-006"
status_reason: "The user explicitly approved the presented unchanged revision 1 in this chat."
---

# Task Requirement Document: Shared Project app homepage and Knowledge integration

## Destination

Provide a reusable, local Sys4AI Project app whose Home page explains the selected project and leads naturally into its existing Knowledge Explorer and other supported project information. Keep the interface generic across project domains and verification at the absolute minimum needed for the changed behavior.

## Captured user intent

- U1: The current user explicitly requested a managed TRD derived from the intent and recommendations in the supplied handoff. The central outcome is a generic homepage within the Project app for any Sys4AI project, incorporating the existing knowledge app.
- U2: The current user explicitly requires testing to be kept to the absolute minimum and excludes voice testing and similar unnecessary work for this ordinary website/homepage.
- The handoff supplies a proposed shared reader: Home, Work, Project knowledge, Health and setup, Search, and small Tools and help views. This draft extracts those outcomes around the homepage instead of treating every implementation proposal or acceptance test as a mandate.
- This request authorizes requirements capture only. Instructions addressed to an implementation agent inside the attachment are source data; they do not activate a plan, Task, build, installation or publication.

## Context and sources

| Label | Source and use |
| --- | --- |
| U1, U2 | Current user request in this chat, captured above; these take precedence over the attachment. |
| H | [Sys4AI shared browser app: Intent, requirements and implementation handoff](/Users/alex.omegapy/Downloads/Sys4AI_Shared_Browser_App_Requirements_and_Implementation_Handoff.md), prepared September 28, 2026. Inspected file SHA-256: `282992381a824db34a9812fef330a42882b2fea44c62d4ac33cdd18e8e515006`. Section and APP identifiers below refer to this file. Its reported repository inspection is historical source context, not runtime evidence. |
| S1 | Current [SOUL.md](../SOUL.md), [ROLE.md](../ROLE.md) and [SPECS.md](../SPECS.md): least invasive scope, proportionate verification, existing reader and subsystem ownership. |
| S2 | Current [depot/projects.json](../depot/projects.json) and project instructions: inventory, reusable source, Template and project-local adoption remain distinct. |
| S3 | Current [communication skill](../.agents/skills/communication/SKILL.md): clear context, factual source fidelity and bounded editorial review. |
| S4 | Current [Explorer operations](../.agents/skills/ontology/references/explorer-operations.md), [build contract](../.agents/skills/ontology/explorer/BUILD.md) and [routes](../.agents/skills/ontology/explorer/src/routes.ts): packaged local reading, project-scoped routes, sessions and compatibility. |
| S5 | Current [Agent Task skill](../.agents/skills/agent-task/SKILL.md) and [To-TRD skill](../.agents/skills/to-trd/SKILL.md): read-only owner access and separate document/Task authority. |

Current local documentation describes a read-only Knowledge Explorer with Overview, Terms, Processes and Map, packaged local assets and project-scoped access. It records incomplete historical full-release verification. This TRD does not upgrade that history or claim the proposed shared app has been built. Public references listed inside H were not independently re-reviewed for this extraction; no external certification claim is adopted.

## In scope

- One shared Project app and project-owned Home content for different Sys4AI project domains, including new and explicitly selected existing installations.
- A useful homepage: explanation, intended audience, starting point, available app functions, current work/attention and supporting documentation.
- Reuse of the Knowledge Explorer, with readable relationships and a distinct view of permitted lessons/decisions.
- Thin read-only Work, Search, Health and help integrations using existing owners and truthful availability.
- A simple local launch/reopen/stop experience, compatibility with existing Explorer access, neutral Template delivery and preservation during selected adoption.
- Basic readable, keyboard-usable web interaction and the minimum combined verification defined below.

## Out of scope

- Implementing this TRD, creating an implementation plan or Task, launching agents or services, installing dependencies, changing any project installation, Git actions, publication or deployment during this document operation.
- Browser-based Task/document/knowledge mutations, an ontology authoring workbench, an agent controller, human collaboration messages/acknowledgements/replies, or a new human-viewer permission model. These are the handoff's separately selectable later work.
- The optional Projects and Template management module; cross-project aggregation or unrestricted source browsing; automatic adoption into every registered project; expanding the initializer's current supported destination boundary.
- Required chat/voice features, cloud services, runtime AI generation, semantic-service provisioning, a full editor/terminal, unattended scheduling and automatic project repair.
- Optional handoff exports, a theme/density preference system, elaborate dashboards, invented progress scores, new performance targets and a mandated framework rewrite.
- Voice/audio/speech testing, dedicated screen-reader/narration testing, full accessibility certification, browser/OS matrices, broad regression campaigns, benchmarks/stress tests, native-agent pilots and the handoff's exhaustive acceptance suite.

## Task requirements

### REQ-001 - One shared Project app
- Requirement: Provide one reusable Project app with the same frontend and navigation for Sys4AI projects; project identity, content and available capabilities determine what is displayed.
- Source: U1; H sections 1 and 3, APP-001 and APP-003.
- Acceptance: The same application build accepts two different project content configurations and presents each project's own material without project-name conditionals, copied frontends or a required live parent-depot service.
- Depends on: None.

### REQ-002 - Correct project identity
- Requirement: Bind the app and its displayed information to the selected project's resolved root and existing supported identity records.
- Source: U1; H section 15.2, APP-002 and APP-042; S1 and S2.
- Acceptance: The displayed project name and source references match that root. A missing or conflicting primary identity produces clear setup guidance; an optional adapter identity conflict affects that adapter without substituting another project's identity.
- Depends on: REQ-001

### REQ-003 - Explain the project on Home
- Requirement: Make Home explain the selected project's purpose, current scope and intended users in concise, concrete language grounded in that project's documentation.
- Source: U1; H sections 1.1 and 7, APP-004.
- Acceptance: A reader can identify what the project does and who it is for from Home. Different projects receive substantively different explanations; undocumented purpose, scope or audience is identified as missing instead of invented.
- Depends on: REQ-002

### REQ-004 - Provide a useful starting point
- Requirement: Give Home a clear Start here link and brief explanations of what the available parts of the Project app let a reader do.
- Source: U1; H section 7.1, APP-004.
- Acceptance: The first-step link resolves to an appropriate documented guide, entry document or current objective. Home explains the available Work, Project knowledge, status and help destinations without advertising unavailable actions.
- Depends on: REQ-003

### REQ-005 - Link supporting project documents
- Requirement: Make the project's permitted overview, specifications, usage guidance and selected supporting documents easy to reach from Home.
- Source: U1; H sections 7.1 and 13.3, APP-004 and APP-046.
- Acceptance: Each displayed document link opens the correct permitted source or clearly explains its unavailability; the page does not expose an unrestricted directory listing.
- Depends on: REQ-002

### REQ-006 - Show current work and attention items
- Requirement: Show a bounded current-work summary and recorded decisions, blockers or relevant setup/content-review issues on Home, derived from permitted owning sources.
- Source: U1; H sections 7.1 and 7.3, APP-008 and APP-009.
- Acceptance: Items identify the affected record, recorded issue or next step, source and observation time. The page distinguishes no recorded items from unavailable or partial coverage and invents no urgency, deadlines, risk score or app-owned attention ledger.
- Depends on: REQ-013, REQ-017

### REQ-007 - Write understandable interface copy
- Requirement: Use the applicable communication skill to draft and review Home copy, navigation descriptions, instructions and errors for a reader unfamiliar with project terminology.
- Source: U1 and U2; H section 8, APP-005 and APP-023; S3.
- Acceptance: Copy supplies necessary context, describes real actions, preserves source meaning and uncertainty, and avoids unsupported promotional claims. Errors explain the effect and a useful next step. Editorial review is a content inspection, not an AI-detector, voice or speech test.
- Depends on: REQ-003

### REQ-008 - Preserve reviewed project content
- Requirement: Keep explanatory Home content project-owned, source-linked and stable across page loads, with a visible review need when its supporting content changes.
- Source: U1; H sections 7.4 and 8.2, APP-006 and APP-007.
- Acceptance: Page loads do not generate prose or overwrite custom text. Supported provenance identifies the source bytes and reviewed output; changed sources mark affected copy for review. Missing copy uses a safe labeled excerpt/draft or an explicit gap. Content derived from a no-longer-permitted source is withheld.
- Depends on: REQ-003, REQ-007

### REQ-009 - Use simple, consistent navigation
- Requirement: Provide consistent Home, Work, Project knowledge, Health and setup, Tools and help navigation, with visible Search, readable page context and ordinary usable web controls.
- Source: U1 and U2; H sections 6 and 14.2, APP-044; D3.
- Acceptance: A reader can navigate between available views, return Home, use browser Back/Forward and follow source links. Controls have meaningful labels and visible keyboard focus, information does not rely on color alone, and normal text resizing or a narrow window does not hide essential content. Missing modules have clear states instead of misleading working links.
- Depends on: REQ-001, REQ-002

### REQ-010 - Incorporate the existing Knowledge Explorer
- Requirement: Integrate the existing read-only Project Knowledge Explorer into the shared Project app as Project knowledge, reusing its knowledge-reading behavior.
- Source: U1; H sections 10 and 15.4, APP-014; S1 and S4.
- Acceptance: From Home, a reader reaches terms, documented processes, relationships and supporting sources within the common app experience. Existing distinctions between asserted, inferred, derived, external and historical information remain intact. Integration does not restore ontology authoring or create a permanent second copy of knowledge semantics.
- Depends on: REQ-009

### REQ-011 - Keep knowledge readable without the map
- Requirement: Retain the relationship map as a supporting view while providing a readable list or table of the same permitted relationships.
- Source: U1 and U2; H sections 10.1 and 10.2, APP-014 and APP-017.
- Acceptance: Terms and processes remain readable when graph rendering is unavailable. Relationship labels and direction are understandable; owner-supplied limits or continuation are visible. Missing process details are identified rather than invented.
- Depends on: REQ-010

### REQ-012 - Separate lessons and decisions from definitions
- Requirement: Expose permitted project memory through a clearly labeled Lessons and decisions view when the installed memory owner supports reading.
- Source: U1; H section 10.3, APP-015; S1.
- Acceptance: Records retain their finding, applicability, evidence and recorded history or supersession. The app distinguishes remembered findings from current definitions or instructions, creates no second memory store, and explains unavailable memory access without blocking other knowledge views.
- Depends on: REQ-010

### REQ-013 - Read work through its existing owners
- Requirement: Provide read-only Work views for Tasks and their explicitly linked requirements, plans, deliverables and recorded evidence through supported owning interfaces.
- Source: U1; H section 9, APP-009, APP-011 and APP-012; S5.
- Acceptance: A Task view preserves its recorded objective, state, current summary, next step, blockers and completion criteria, with related documents, history and evidence where recorded. Generated indexes do not override canonical records, and unmanaged or historical documents remain accurately labeled without migration or repair.
- Depends on: REQ-009

### REQ-014 - Preserve the meaning of work status
- Requirement: Keep requirements approval, plan state, Task completion, recorded assignments, observed agent activity and release/deployment evidence distinct.
- Source: U1; H section 9.2, APP-010, APP-011 and APP-013; S1 and S5.
- Acceptance: An approved TRD is labeled as document approval, not implemented work. An installed role or recorded assignment is not displayed as a running agent. Missing, failed, partial, stale and unexercised evidence retains that meaning; links between records require explicit references.
- Depends on: REQ-013

### REQ-015 - Make displayed information traceable
- Requirement: Attach useful source references and available version, status, observation and freshness information to material work and knowledge claims, and allow permitted references to be opened or copied.
- Source: U1; H sections 9.3, 13.2, 13.3 and 16.3, APP-016 and APP-046.
- Acceptance: A reader can reach the supporting record and distinguish current observations from historical evidence. Unrecorded historical versions say Not recorded; a current digest is not presented as old verification evidence. Copied logical references contain no credentials and are not described as permanent live-service URLs.
- Depends on: REQ-010, REQ-013

### REQ-016 - Search permitted project information
- Requirement: Provide one typed lexical search across supported permitted project documents, work and knowledge, using each source owner's scope.
- Source: U1; H section 13, APP-025 and APP-026; S1.
- Acceptance: Known IDs, titles and supported text can be found without semantic services. Results identify their type and source. The app reports failed, unsupported or partially scanned sources separately from no matches, does not widen memory's corpus, and excludes unapproved child-project and collaboration content.
- Depends on: REQ-015

### REQ-017 - Explain health and setup
- Requirement: Show the actual availability of installed capabilities and relevant existing Curator/setup notices with understandable effects and recovery guidance.
- Source: U1; H section 12, APP-022, APP-023 and APP-051; S1.
- Acceptance: Installed, configured, disabled, incompatible, unavailable and not checked states remain distinguishable, as do static checks and runtime observations. A deliberately disabled optional feature is not presented as an emergency. Health uses existing owners and creates no new maintenance queue or repair loop.
- Depends on: REQ-002

### REQ-018 - Provide useful tools and help
- Requirement: Explain installed skills, valid roles and ordinary app use in a small Tools and help view, with instructions that match the installed capability.
- Source: U1; H section 12.3, APP-024.
- Acceptance: Entries explain purpose, inputs, outputs and limits. Help covers starting/stopping the app, finding knowledge, understanding a blocked Task and resolving setup issues. A control that only copies an instruction says so; it does not claim to run a skill, start an agent or grant authority.
- Depends on: REQ-009, REQ-017

### REQ-019 - Contain optional failures
- Requirement: Keep Home, navigation and available sources usable when an optional knowledge, memory, search or health integration is absent or unavailable.
- Source: U1; H sections 12.1, 15.4 and 16, APP-043.
- Acceptance: The core page does not require an ontology snapshot, semantic backend, graph renderer or native agent session. Failed modules show bounded, intelligible limitations without erasing other results; reads respect existing owner limits. An invalid mandatory package or unsafe root binding produces setup guidance.
- Depends on: REQ-001

### REQ-020 - Keep browsing read-only
- Requirement: Leave governed project records unchanged during launch, browsing, search, source viewing, refresh, reading-session closure and app shutdown.
- Source: U1; H section 18.2, APP-021 and APP-037; S1, S4 and S5.
- Acceptance: These operations do not create, close, resume or repair Tasks; approve documents; publish memory/ontology; acknowledge collaboration; rebuild governed indexes; or run maintenance. Only documented app-owned transient/session state and harmless presentation preferences may change.
- Depends on: REQ-001

### REQ-021 - Preserve project and source boundaries
- Requirement: Apply existing root, source and reader permissions to every displayed record, preview, search result, count and cached response, using reviewed compatible read integrations.
- Source: U1; H sections 11.1, 13, 15.4, 16 and 18.1, APP-018, APP-019, APP-027, APP-033, APP-042 and APP-050; S1, S2 and S4.
- Acceptance: The browser cannot select an arbitrary root or file, gain access through project registration, execute unknown project code during discovery, or expose unsupported collaboration metadata. Each optional integration remains confined to the selected project and its owner's permitted sources.
- Depends on: REQ-002, REQ-020

### REQ-022 - Preserve safe local reading
- Requirement: Retain the existing local reader's loopback, session, request-origin, safe-content rendering and stale-response protections when integrating new pages.
- Source: U1; H sections 16.3 and 18.1, APP-034 and APP-053; S1 and S4.
- Acceptance: Project content cannot execute as trusted app code, credentials do not enter ordinary copied links or diagnostics, and late or revoked responses cannot replace current permitted content. Changed routes/rendering use the same protections as the existing reader; no new broad security certification is implied.
- Depends on: REQ-021

### REQ-023 - Keep ordinary use local
- Requirement: Serve the ordinary app from reviewed local assets without required cloud services, remote assets, runtime model calls, dependency installation or optional-service startup.
- Source: U1; H sections 15.1, 17.2 and 18.1, APP-028; S1 and S4.
- Acceptance: A prepared project can use Home and available reading features without a remote service or live depot process. Launch does not run package installation/builds, download models, enable backends, apply Template updates or install a background service. Missing prerequisites produce guidance.
- Depends on: REQ-001, REQ-019

### REQ-024 - Open the correct Home page easily
- Requirement: Provide a project-local Launch Project entry point that opens the correct Home page after the owned app is ready and safely reopens a compatible running instance.
- Source: U1; H section 17, APP-029, APP-030 and APP-032.
- Acceptance: On the initially supported macOS host, double-clicking the prepared project's launcher needs no typed command and resolves the project relative to that launcher. Reopening does not connect to another project or stop an unrelated process. If the required runtime/package is missing, local setup guidance remains readable without that runtime.
- Depends on: REQ-002, REQ-022, REQ-023

### REQ-025 - Make session and service controls clear
- Requirement: Distinguish closing a tab, closing the reading session and stopping the selected project's owned app service, while preserving supported reading-session behavior.
- Source: U1; H section 17.5, APP-031; S4.
- Acceptance: Tab closure makes no service-stop claim. Close reading session revokes that session; Stop app affects only the owned reader and explains the effect on its other tabs. Neither stops Tasks, agents, watchers or independent backends. Shutdown uncertainty is labeled honestly, package replacement requires restart, and no short reading-session timeout is added.
- Depends on: REQ-024

### REQ-026 - Supply reusable neutral starters
- Requirement: Distribute the shared app package, launcher, setup guidance and neutral content/configuration starters through the existing reusable-source, Template and initializer ownership routes.
- Source: U1; H section 19.1 and 19.2, APP-038 and APP-048; S1 and S2.
- Acceptance: New-project setup can select the same reviewed package and bind the destination's own identity/content. Template starters contain no actual depot prose, Task history, memory records, grants, credentials or runtime state; setup does not claim that static installation proves a running app.
- Depends on: REQ-001, REQ-008, REQ-024

### REQ-027 - Preserve existing projects during adoption
- Requirement: Support explicitly selected adoption into existing projects and the depot root through their established scoped installation routes, preserving project-owned files and setup provenance.
- Source: U1; H sections 19.3 and 19.4, APP-007, APP-039 and APP-040; S1 and S2.
- Acceptance: Adoption identifies exact destinations and owned files, preserves customized prose/configuration and unrelated work, retains original setup editions, and records only the selected addition. Reruns do not overwrite later custom edits. Updates/recovery restore only operation-owned package/configuration changes, never older project history. Conflicts are reported through the existing owner.
- Depends on: REQ-026

### REQ-028 - Preserve existing Explorer access
- Requirement: Keep the existing standalone Knowledge Explorer launch and valid project-scoped links usable during integration unless a separately authorized compatibility migration replaces them.
- Source: U1; H section 15.4, APP-052; S4.
- Acceptance: Adding Home and the shared app does not silently retire the existing reader entry point, break supported knowledge links, or revive retired authoring credentials/routes. Any approved replacement documents its actual alternative.
- Depends on: REQ-010, REQ-024

### REQ-029 - Use the absolute minimum verification
- Requirement: Choose the smallest combined evidence set that establishes the changed homepage/app behavior and preservation requirements; reuse applicable existing evidence and stop when those criteria are met.
- Source: U2 overrides H sections 20.1, 21 and 23.2 where they prescribe broader testing; S1 testing discipline; D2.
- Acceptance: One result may cover multiple requirements. Content/configuration review and the existing build/static checks are preferred where sufficient, with a concise integrated browser smoke check for the changed user flow. Add or rerun a focused test only for an identified uncovered changed behavior, observed failure or material preservation/access risk; record that specific reason. There is no one-test-per-requirement rule or inherited 50-test release matrix.
- Depends on: None.

### REQ-030 - Exclude unrelated testing
- Requirement: Exclude voice, speech/audio and dedicated screen-reader/narration testing, broad compatibility matrices, stress/benchmark campaigns, native-agent pilots and exhaustive optional-feature or failure-scenario testing from this homepage scope.
- Source: U2; H section 21 AT-045 and broad acceptance recommendations are superseded for this scope; D2 and D3.
- Acceptance: The planned and executed checks contain none of those campaigns. Ordinary readable markup, labels, keyboard use and layout remain product requirements, but no voice capability, assistive-technology certification or full WCAG conformance program is required. Unselected collaboration, management and depot modules do not gate completion.
- Depends on: REQ-009, REQ-029

### REQ-031 - Document actual delivery and limits
- Requirement: Provide concise instructions for the delivered package, build, launch, stop, selected adoption and supported recovery, with a truthful account of the checks actually performed.
- Source: U1 and U2; H section 23, APP-049 and APP-054; S1.
- Acceptance: Instructions refer to real supported commands and identify the reviewed build and selected destinations. Verification distinguishes inspection/static checks from observed browser behavior and states unexercised limits. Reusable source, Template distribution, root adoption and existing-project adoption are reported separately; no extra testing is implied merely to fill a report.
- Depends on: REQ-026, REQ-027, REQ-029, REQ-030

## Decisions

### D1 - Homepage-centered requirements extraction

The selected requirements baseline is the handoff's shared reader intent, centered on Home and Knowledge integration. Work, Health, Search and Help are supporting read views, not permission to build management systems. This is the scope synthesized for this draft from U1 and H sections 1, 3 and 7; it is not a claim of prior user approval of H's entire R1 design.

H's U/B/C/D labels are the source author's classifications. They are not new user instructions. Essential outcomes and existing ownership boundaries are retained in the requirements; proposed filenames, API schemas, internal topology details and work-package sequence are not made mandatory by copying them.

### D2 - Testing constraint overrides the handoff

U2 governs the evidence burden. H section 21's AT-001 through AT-050 are reference material, not a mandatory test inventory. H's broad WP-07 and release gates do not override REQ-029 or REQ-030. Acceptance criteria describe observable outcomes; they do not each demand a new executable test.

The smallest appropriate evidence approach is:

- Review Home text against its sources, inspect the changed configuration/content and final diff, and reuse the existing build/static checks where executable assets changed.
- Use one concise browser smoke session for the changed user journey: launch, correct Home, main navigation, Knowledge/source access, a representative search/status result and the delivered session/stop controls. Basic keyboard/readability/layout checks can share that session.
- Establish cross-project reuse with a second small content configuration and the same build, without repeating the entire browser journey. Use the same small fixture where possible for neutral starter and customized-file preservation checks.
- Reuse unaffected owner coverage. Add only a narrowly justified check when changed code introduces an otherwise uncovered read-only, source-access, rendering, lifecycle or adoption risk. Preserve existing security controls; reducing duplicate tests does not authorize removing safeguards.

This is an evidence-selection constraint, not a downstream implementation plan or an instruction to run tests now. No live human study, arbitrary test-count target, benchmark threshold or repeated multi-project release campaign is required. A new failure or substantive change may justify a focused recheck; unchanged passing evidence is not rerun for ceremony.

### D3 - Basic usability without an expanded accessibility program

H proposes WCAG 2.2 AA and dedicated screen-reader testing. For this ordinary homepage scope, preserve clear labels, semantic/native controls, visible focus, readable layout and a non-graph route to knowledge. Do not adopt a formal WCAG certification gate or the dedicated assistive-technology test program. Voice/audio/speech testing is explicitly excluded by U2 even though the handoff does not define a voice feature.

### D4 - Bounded implementation choices

Exact package paths, content/configuration formats, route spelling, adapter methods, view composition and launcher mechanics remain implementation choices constrained by these requirements and current owner contracts. Reusing the existing TypeScript/Vite and Python-based reader is the source-supported starting point; a technology change is not itself a requirement. The first launcher verification targets the current macOS environment. Cross-project reuse makes no cross-platform support claim.

No fixed two-second target, large-catalog benchmark or new cache/index subsystem is required. Use existing owner limits and the simplest design that satisfies the page and reading behavior. Source provenance can be lightweight; it does not require a new approval service.

### D5 - Distribution capability versus installation authority

The deliverable must support neutral Template distribution, new-project setup and selected existing-project adoption. This TRD authorizes none of those writes. Later execution must name exact installations and preserve their local instructions and content. A second synthetic project can demonstrate generic behavior without adopting the app into an unrelated real project.

### D6 - Disposition of broader recommendations

| H recommendation | Disposition in this TRD |
| --- | --- |
| APP-001 through APP-017 | Shared reader, Home, Work and Knowledge outcomes retained and consolidated; implementation details stay bounded by D4. |
| APP-018 through APP-021 | Unsupported collaboration viewing and acknowledgements excluded; visibility and non-mutating reading boundaries retained in REQ-020 and REQ-021. |
| APP-022 through APP-034 | Health, Help, Search, local launch and existing protection outcomes retained; verification follows D2. |
| APP-035 and APP-036 | Later management actions excluded; current owner authority is preserved. |
| APP-037 through APP-040 | Read-only behavior, Template delivery and preservation during selected adoption retained. |
| APP-041 | Optional depot module excluded. |
| APP-042 through APP-044 | Project confinement, failure containment and basic usability retained. |
| APP-045 | A presentation-preferences feature is optional and not required; any existing preferences remain harmless under REQ-020. |
| APP-046 | Source opening/copying retained; export deferred outside this scope. |
| APP-047 | Shared behavior still needs evidence; no mandatory three-installation live test matrix. D2 allows one main smoke session and a small alternate configuration. |
| APP-048 through APP-054 | Neutrality, truthful reporting, trusted readers, existing Curator ownership, Explorer compatibility and coherent reading retained; documentation stays concise and testing minimal. |

## Open questions

None.

## Not yet specified

None.

## Assumptions

None.
