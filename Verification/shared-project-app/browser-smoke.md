# Project app browser observation

Observed on 2026-09-29, macOS 26.6.2 arm64, Google Chrome 154.0.8037.58. This is a focused observation of the changed local app flow, not a browser/platform or accessibility certification campaign. UI actions used the native Finder and connected browser. No speech or screen-reader check ran.

## Launch and reading

Double-clicking the root `Launch Project.command` in Finder opened Home for `sys4ai-depot`, with the selected root shown. Purpose, scope and audience were ready and bound to reviewed source bytes. Start here opened the README source with digest and freshness. Copy reference acknowledged a logical reference without claiming execution. Browser Back and Forward returned to the corresponding views.

Search for `PLAN-20260929-F690CD02` returned the plan and permitted lexical knowledge matches, with partial owner coverage visible. Plan detail showed revision 3, state `ready`, decisions and bounded history, with an explicit TRD link. Work kept requirements approval distinct from implementation. Task detail for `TASK-20260913-64DDD6CF` showed its objective, recorded state, next step, blockers/completion criteria and explicit references without changing it.

Project knowledge opened within the common app navigation. Terms retained lifecycle/classification information and coverage limits. An Artifact term's source opened the selected section of `ONTOLOGY/modules/sys4ai-core/1.0.0/vocabulary-source.md`, with source SHA and excerpt. Relationships displayed three terms and two directed, labeled relationships; the list remained available when the map was shown. The map rendered the same three nodes and two edges. Processes correctly said none were selected. An existing SPECS source binding was marked stale rather than silently refreshed.

Lessons and decisions found `MEM-20260927-40EAB117` and retained its historical finding, applicability, evidence and lifecycle/body with partial corpus coverage. Health distinguished static availability and recorded notices; it displayed existing Curator pending work without repairing it. Tools and help described launch, stop, source access, setup and blocked Tasks, with installed skills and roles distinguished from running agents.

## Session lifecycle

Close reading session confirmed revocation. Reload required a fresh session while the service remained available. Double-clicking the launcher again reused that owned service and opened Home. Stop app reported accepted shutdown; an independent loopback connection check then found the port closed and the private service receipt absent. `browser-observations/owned-stop.json` records the observation without credentials. The old verification tabs were closed.

## Layout correction and final build

The main journey used build `eae9834d83c52373b6858be89270c06523ea3f995ea800a8857e40de320918fb`. A narrow Home view exposed a long Task source hash overflowing a result row (417 CSS pixels wide, 618 scroll pixels). The existing result-row rule gained `overflow-wrap:anywhere`. The app was stopped before package replacement, rebuilt and delivered through the same reviewed paths.

Final build: `b587accf1f6f44cebac189ce58051bc3e533fd059bc510573ff84c0cddf4853d`. Comparison of the 47 build inputs shows only `src/styles.css` changed between these builds. The earlier functional journey remains evidence for unchanged application logic; it was not repeated wholesale.

The final launcher was double-clicked in Finder and opened the final root app. With viewport override 390 by 844 at the browser's existing 90% zoom, the app measured 417 client pixels and 417 scroll pixels. The saved screenshot was visually inspected: prose and source controls wrapped within the column. Keyboard Tab moved from Home to Work, and Enter opened Work with visible focus and its heading. At 125% browser zoom, Home remained readable, with 647 client pixels and 647 scroll pixels. Original 90% zoom was restored and the temporary viewport override reset. No app console errors were reported. Final Home was saved and left open for the user.

## Saved observations

- `browser-observations/final-home.png`: delivered Home.
- `browser-observations/final-home-narrow.png`: corrected narrow layout.
- `browser-observations/home-zoom125.png`: ordinary enlarged text and visible focus.
- `browser-observations/relationships.png` and `map.png`: integrated Knowledge.
- `browser-observations/home-narrow.png`: retained original overflow evidence.
- `browser-observations/initial-instance.json` and `owned-stop.json`: sanitized lifecycle observations.

The final owned reader is intentionally left running. Closing its tab is not a stop operation. No Task, agent, watcher or independent backend was stopped by the app. Broader browsers, other host platforms, future real-project adoption and the historical Explorer release matrix were not exercised.
