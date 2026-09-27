# Requirements coverage

This is source-to-requirement evidence for document capture. It is not implementation evidence or user approval.

Source SHA256: `b79d6122615b85f2ca42f0334cdecd7677578085014bb6c82565180e6264d38e`
Payload SHA256: `74a595375bfa750a082ad080e380fd1fa5debaf74f9e9cdc70b2f1ff3ca63b49`

## Acceptance scenarios

| Source test | Requirement | Preserved source scenario |
| --- | --- | --- |
| AT-01 | REQ-001 | Launch the human interface. Only reading/exploration destinations appear; no authoring modules or controls load. |
| AT-02 | REQ-005 | Search a preferred label, alias, exact ID, and words in a definition. Matching is deterministic and relevant. |
| AT-03 | REQ-006 | Two entries share a label/alias. Both appear with distinctions; neither is silently selected. |
| AT-04 | REQ-007 | Apply category/lifecycle filters to a multi-page result set. Filtering happens before pagination; valid later matches remain reachable. |
| AT-05 | REQ-007 | Search returns more matches than one page permits. Continuation is stable, with no duplicate or skipped identities within the same snapshot. |
| AT-06 | REQ-018 | A result is omitted by a byte/time/traversal bound. The UI reports incomplete coverage rather than “nothing exists.” |
| AT-07 | REQ-008 | Read an entry with definition, aliases, scope note, and examples. Present fields faithfully; omit absent sections without inventing content. |
| AT-08 | REQ-003 | Open a deprecated entry by exact ID. Show its status and recorded replacement without silently rewriting history. |
| AT-09 | REQ-003 | A draft or inferred record is available under an explicit permitted filter. Its status remains distinct from approved asserted knowledge. |
| AT-10 | REQ-015 | Select a graph node. Details change, but the camera and graph focus do not unexpectedly move. |
| AT-11 | REQ-015 | Choose Focus here. The neighborhood changes deliberately, and Back restores the prior useful state. |
| AT-12 | REQ-018 | Expand a high-degree node. Limits remain enforced and omitted connections are clearly disclosed. |
| AT-13 | REQ-009 | Two predicates connect the same endpoints. Both canonical relationship IDs and their meanings remain inspectable. |
| AT-14 | REQ-009 | Traverse an incoming relationship. Arrow and sentence retain the canonical subject–predicate–object direction. |
| AT-15 | REQ-016 | Render self-loops, cycles, and qualified relationships. No infinite expansion or semantic merging occurs. |
| AT-16 | REQ-019 | Switch between map and list. Selection, filters, returned scope, and warnings agree. |
| AT-17 | REQ-010 | Open a supported process. Purpose, roles, inputs/outputs, and ordering appear only where supported by the selected source. |
| AT-18 | REQ-010 | A process has no recorded step order. Show the gap; do not infer a sequence from graph layout or unrelated relations. |
| AT-19 | REQ-011 | Open a definition's or relationship's source. Show the authorized locator/excerpt and evidence status for the correct identity. |
| AT-20 | REQ-011 | The source bytes change after the entry loads. Do not present the new bytes as the originally recorded evidence without a warning/version distinction. |
| AT-21 | REQ-021 | Canonical inputs change during navigation or publication. Reject mixed-version continuations; refresh the display coherently. |
| AT-22 | REQ-025 | A slow response for entry A arrives after selecting B. B remains the current entry. |
| AT-23 | REQ-020 | Session expires or service stops. Preserve readable context and desired route; explain reconnection without making unauthorized startup claims. |
| AT-24 | REQ-031 | Submit direct browser requests to old write or execution endpoints. They fail; no protected artifacts change. |
| AT-25 | REQ-029 | Use invalid Host/Origin/CSRF/session values or another service's credentials. Requests fail without leaking project data. |
| AT-26 | REQ-032 | Attempt encoded traversal, absolute-path access, symlink escape, or an unselected source reference. Access is denied. |
| AT-27 | REQ-032 | Labels/source text contain HTML, script-like text, or malicious links. They display safely and do not execute. |
| AT-28 | REQ-028 | Load the production bundle under the production CSP with no internet. Reader and graph work without remote assets. |
| AT-29 | REQ-019 | Complete all major reading tasks by keyboard and via the relationship list. No drag, hover, or canvas-only action is required. |
| AT-30 | REQ-036 | Use narrow viewport, browser zoom, reduced motion, and both themes. Text reflows, controls remain operable, and important states remain legible. |
| AT-31 | REQ-038 | Browse the root and neutral template, then a separate namespace fixture. No hard-coded project identity, cache leakage, or source crossover occurs. |
| AT-32 | REQ-028 | Perform all read workflows with missing optional embedding/RDF services. Core reading works; nothing is installed or started implicitly. |
| AT-33 | REQ-026 | Compare protected file hashes/timestamps before and after the read workflow. Ontology, memory, proposals, receipts, and generated products are unchanged. |
| AT-34 | REQ-020 | Disable or fail the graph renderer. Definitions, relationship list, and evidence access still work. |
| AT-35 | REQ-040 | Run existing agent retrieval, publication/recovery, and template contract tests. No unintended behavioral regression occurs. |
| AT-36 | REQ-045 | Measure the representative and stress fixtures. Publish actual timings, memory/limits, and graceful-degradation results rather than assumed performance. |

## Source section coverage

| SRC section | Destination |
| --- | --- |
| 1 | REQ-001, REQ-002, REQ-027, REQ-031, REQ-040, REQ-049; scope and authority |
| 2 | Context and sources; REQ-042; D08 |
| 3 | REQ-001, REQ-005, REQ-009, REQ-010, REQ-026, REQ-027, REQ-029, REQ-037, REQ-042 |
| 4 | REQ-006, REQ-009, REQ-012, REQ-013, REQ-015, REQ-025, REQ-049; D02 |
| 5 | All 15 outcome IDs mapped below; In scope and Out of scope |
| 6 | REQ-001, REQ-003, REQ-012, REQ-036; D03-D04 |
| 7 | REQ-004, REQ-006, REQ-008, REQ-009, REQ-010, REQ-011, REQ-020 |
| 8 | REQ-009, REQ-014 through REQ-019; optional path search excluded; D05 |
| 9 | REQ-005, REQ-006, REQ-007, REQ-024, REQ-025, REQ-034; D04 |
| 10 | REQ-003, REQ-008, REQ-009, REQ-011, REQ-027 |
| 11 | REQ-002, REQ-023, REQ-028, REQ-031, REQ-049; D02 |
| 12 | REQ-002, REQ-006, REQ-007, REQ-009, REQ-011, REQ-016, REQ-018, REQ-021, REQ-023, REQ-024, REQ-031, REQ-033; D03 |
| 13 | REQ-011, REQ-021, REQ-022, REQ-026, REQ-027 |
| 14 | REQ-012, REQ-013, REQ-019, REQ-025, REQ-037; D02-D03 |
| 15 | REQ-020, REQ-028 through REQ-033, REQ-039 |
| 16 | REQ-017, REQ-019, REQ-034 through REQ-036, REQ-044; D04 |
| 17 | REQ-014, REQ-018, REQ-020, REQ-022, REQ-025, REQ-033, REQ-045, REQ-046; D04-D05 |
| 18 | REQ-037 through REQ-042, REQ-048 |
| 19 | REQ-030, REQ-039 through REQ-042 |
| 20 | Required outcomes/evidence in REQ-042 through REQ-048; phases are not reproduced as a plan; D01 |
| 21 | AT-01..36 matrix below; REQ-043 |
| 22 | REQ-047, REQ-048 |
| 23 | Preserved through requirements, exclusions, and D01-D08; no reintroduction or blanket propagation |
| 24 | Captured outcome in REQ-001..049; delivery evidence REQ-048; embedded commands/brief carry no execution authority |
| 25 | Context and sources; inherited SRC locators; dependency/version review in REQ-049; official standards targets in REQ-034/036/044 |

## Mandatory source outcomes

| Source outcome | Requirements |
| --- | --- |
| UX-01 | REQ-001, REQ-031, REQ-040 |
| UX-02 | REQ-004, REQ-005, REQ-006, REQ-007, REQ-034 |
| UX-03 | REQ-009, REQ-016, REQ-017 |
| UX-04 | REQ-014, REQ-015, REQ-017, REQ-018 |
| UX-05 | REQ-010, REQ-042 |
| UX-06 | REQ-012, REQ-015, REQ-020, REQ-021, REQ-025 |
| UX-07 | REQ-019, REQ-020, REQ-034, REQ-035, REQ-036, REQ-044 |
| DATA-01 | REQ-002, REQ-007, REQ-008, REQ-021, REQ-022, REQ-023 |
| DATA-02 | REQ-003, REQ-009, REQ-016, REQ-019 |
| DATA-03 | REQ-003, REQ-011, REQ-021, REQ-032 |
| DATA-04 | REQ-026, REQ-027, REQ-028 |
| SAFE-01 | REQ-001, REQ-026, REQ-028, REQ-031 |
| SAFE-02 | REQ-028, REQ-029, REQ-030, REQ-032, REQ-033, REQ-038 |
| PORT-01 | REQ-028, REQ-037, REQ-038, REQ-039, REQ-040 |
| PERF-01 | REQ-007, REQ-014, REQ-018, REQ-022, REQ-023, REQ-024, REQ-025, REQ-033, REQ-045, REQ-046 |

## Qualification and review boundary

All 49 requirements have explicit U02 and SRC section/outcome sources; project ownership constraints also cite GOV and current supplied facts cite LIVE. No normative package choice or new action grant is inferred from source recommendations. Numeric display/latency/fixture/comfort values retain their proposed or approximate status, while existing backend bounds remain intact.

The reverse source map and numeric-preservation inventory are in coverage.json. The content review checked all 25 source sections, all 15 mandatory outcome IDs, and all 36 acceptance cases. Mechanical checks establish parser and identifier coverage only. Manager acceptance and exact-revision user approval remain separate.
