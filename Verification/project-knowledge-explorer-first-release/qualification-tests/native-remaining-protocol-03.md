# Native Safari remaining subset — keyboard03

For root execution only after manager release. Build `09b4571b34594b39e9d19be3320f334bf7d608a333e0d06902dfda0a361259b8`, synthetic project `explorer-native-at`. Preserve completed native04/keyboard02, their actual partial outcomes and failed wider-window attempt. This protocol covers the remaining Light keyboard, distinct focus, motion and measured narrow viewport observations. No speech, full TASK022, WCAG or participant-comprehension pass follows from launcher success.

## Admission, readiness and time

Verify the frozen manifest and four admitted tool identities before/after execution. Keep the unchanged driver850-second lifetime and host900-second timeout. Root records per-group completed, failed or unperformed outcomes, actual keys and observation methods; no aggregate substitution. Aim to finish Light/focus by190seconds after ready, motion by310, narrow observations by610, then restore/close by740 and request exact driver stop by780. These are test-session allocations, not performance measurements. If a group consumes its allowance, retain its actual partial evidence, move to restoration and report the remaining actions. Do not extend the product session or driver deadline.

Before launching the private document, record Safari/macOS versions, current Safari running state and owned blank warm-up document identity, then positively observe Safari ready. Native04 cold startup timed out before readiness; the later warm run succeeded. No cold-performance claim. A failed private launch requires exact driver/descendant cleanup and confirmation that its owned document/origin is absent before at most one warm retry. If ownership is uncertain, stop. Never inspect/capture the private bootstrap URL. Begin observation only after `native_ready` confirms clean owned origin, fixture and build. Retain numeric AppleScript ID and distinct CUA UUID.

Record fresh baseline theme/resolved theme, Page Zoom, window geometry/display, Reduce Motion, VoiceOver/caption settings, developer-features preference, whether the owned page already has Inspector or Responsive Design Mode open, and any existing custom viewport dimensions/pixel ratio. Do not assume the prior115%/System/off baseline still applies. Preserve unrelated tabs/windows and all unmodified settings. No clipboard read/change, VoiceOver retry, new automation permission, Simulator, extension or app edit is part of this job.

Use actual keyboard typing, Tab or Safari's documented Option-Tab, reverse traversal, Return/Space, Escape and Command-[ Back. Record the actual "Press Tab to highlight each item" preference and leave it unchanged; use the supported keys for that setting. Root's separate preparation probe found this preference off and developer features off, but the execution must observe fresh values. Observe labels and identities through existing native UI; AX clicks, Inspector state mutation or programmatic focus cannot replace keyboard reachability. Limit any individual traversal to120 steps and record actual counts/difficulty. [Safari keyboard behavior](https://support.apple.com/en-kg/guide/safari/cpsh003/mac).

## A. Light chosen result, List Back and a different focus

1. Select **Light** through the actual theme control and verify the resolved appearance. Keyboard-focus Search, type Orientation, observe both Alignment suggestions, then Escape and Return to submit. Keyboard-activate the first result. Verify the full canonical ID ends in `entry-00000` and the active Definition is exactly **Alignment means scheduling independent fixture inspection windows.** Wait for the current entry's header and Definition; retained previous content is not readiness.
2. Keyboard-open Relationships and select the other Alignment. Verify its distinct ID ends in `entry-00001` and Definition is exactly **Alignment means orientation of a fixture drawing only.** Open View on map, choose List, and record current root, selected ID, Read from identities and retained term/relation counts. This establishes00001 as the current root before the next action.
3. Identify the List row for00000, not merely the first repeated Alignment label. The adjacent term button can be keyboard-selected to reveal its exact ID/definition; then return to that same row's **Focus here** control. Canonical row identity may be read from native structure or the read-only Inspector observation below, but activation must use keys. Activate it and record root before00001, root after00000, selected ID if any, active definition if shown, and new Read from/scope/counts. Require actual distinct identity change; an unchanged root is insufficient. Do not infer focus solely from selection.
4. Command-[ Back and record restored prior root, selection, scope and visible reading content. Record actual behavior even if it differs from the expected useful prior state. Keyboard-open a source trigger from the current readable entry/relation, record its identity, Return then Escape, and observe exact unobscured focus return in Light. This completes the essential second-theme repetition missing from keyboard02. Do not repeat unrelated process/close tests solely to increase counts.

## B. Actual ordinary and reduced-motion transitions

Record the current Reduce Motion setting. In the ordinary setting (temporarily off if necessary), observe an actual Map focus or More connections action and Map/List change, including any motion and the final ID/scope. Repeat comparable actions with Reduce Motion enabled. Use the same declared controls/starting identity in both modes, record their actual transitions, and note whether both are static. Preserve any dynamic loading/focus issue as observed. The setting or a readable AX tree alone is insufficient. The product's preset graph layout is already nonanimated; do not invent a visible ordinary-mode animation requirement.

Restore the exact original Reduce Motion setting immediately afterward and positively verify it. Read-only `matchMedia('(prefers-reduced-motion: reduce)').matches` in the owned page may corroborate media state; it cannot replace the actual visual transition observation. VoiceOver and captions remain unchanged; this is not a screen-reader test.

## C. Measured Safari narrow viewport

Apple documents Develop → Enter Responsive Design Mode (Control-Command-R), editable dimensions, pixel ratio and automatic presentation scaling. The displayed dimensions use screen points; actual CSS width must be measured separately. Web Inspector can accompany the mode. [Apple Responsive Design Mode](https://developer.apple.com/documentation/safari-developer-tools/responsive-design-mode). The prior Move & Resize>Left route is not used.

If Develop is absent, capture its actual preference baseline before temporarily selecting Safari Settings → Advanced → Show features for web developers. [Safari26 Develop tools](https://support.apple.com/en-mk/guide/safari/sfri20948/26.0/mac/26). Record the current responsive preset, custom dimensions/ratio and owned Inspector state before changing them. If those values cannot be captured/restored, report that limit and skip mutations that cannot be restored. Existing unrelated Inspector windows must remain untouched.

On only the clean owned synthetic document, request custom320×800 with pixel ratio1 and Page Zoom100%. Record responsive-mode presentation scale separately from Page Zoom. A shorter height is acceptable to retain100% presentation, with the actual height recorded. Open Inspector for this exact document and select its main-frame Console. Before inspecting DOM, read only `location.origin`; require the exact clean origin from `native_ready`. Never inspect full URL/fragment, cookies, storage, requests, headers, unrelated frames or other documents. If context cannot be established, stop this measurement.

Type these bounded read-only expressions directly through existing UI control; do not use the clipboard:

```javascript
({innerWidth, innerHeight, clientWidth: document.documentElement.clientWidth,
  visualWidth: window.visualViewport?.width, devicePixelRatio,
  scrollWidth: document.documentElement.scrollWidth,
  reducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches})
```

For distinct focus-row identification only, if native structure is insufficient:

```javascript
Array.from(document.querySelectorAll('[data-node-id]')).slice(0,25).map(e =>
  ({id:e.dataset.nodeId, text:e.textContent?.slice(0,160)}))
```

These read existing layout/fixture values; no DOM/CSS mutation, focus call, app-state access or request is permitted. Retain actual numeric output through observed UI text/screenshot without general clipboard access. Require both `innerWidth` and `clientWidth` equal320 before reporting320CSSpx. Otherwise record actual dimensions and leave the exact target unmet. A browser frame size, screenshot width or zoom percentage alone is insufficient. Report this as Safari Responsive Design Mode, not a tested mobile device.

With Inspector hidden or undocked so it does not cover the test view, inspect in Light and Dark: search/filter/status controls, active definition and identity, source drawer and exact Escape focus return, and the first complete relationship sentence plus surrounding List controls. Scroll only as needed and keep the displayed viewport controls/clean context identifiable. Record actual clipping, wrapping, horizontal overflow and its affected content; surrounding text/controls have no diagram exception. Representative native targets should have actual pointer/keyboard hit/focus observation. If CSS geometry is read for a specific observed target, record that selector and its real rectangle separately; no blanket native24px pass from earlier headless evidence. Keep controls reachable without synthetic focus. If time or capability prevents one state, preserve what was observed and explicitly leave the rest unperformed.

## Restoration, receipt and evidence

Restore and positively verify every changed baseline: theme, Reduce Motion, Page Zoom, responsive custom dimensions/ratio/preset, prior mode, owned Inspector state, developer preference and owned window geometry/display. Exit newly entered Responsive Design Mode and close only the newly opened owned Inspector. VoiceOver/captions stay unchanged. If an original custom/preset state cannot be restored, disclose that exact limitation rather than recording successful restoration. No automatic defaults or settings-file edits.

Close only the owned Explorer document/tab; preserve unrelated tabs even if they later share its window. Stop only the exact retained driver through the reviewed wrapper and collect its final fixture/stage/descendant/document-absence receipt. **After** that receipt and all driver AppleEvents, restore Safari's initial app state: if initially nonrunning and no unrelated content appeared, quit it and positively observe absence. Preserve actual extra owned blank-page cleanup. Do not quit Safari first and mistake the driver's later AppleEvents relaunch for restored state.

The root report must bind job/protocol/build/fixture and timestamps; actual keys, IDs, definition/route/scope/focus outcomes for A; both setting states and actual visual transitions for B; actual numeric viewport, settings and each observed narrow state for C; and positive restoration/cleanup. Separate launcher/cleanup pass from group results. Record words as unobserved, Windows AT unexercised and no participant comprehension claim. TASK023, benchmark04/TASK024 and TASK025 remain gated. No report may replace a missing outcome with expected text or declare full TASK022 from this subset alone.
