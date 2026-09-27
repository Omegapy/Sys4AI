# Remaining native observations — prepared, not released

This plan follows the actual native04 and native-keyboard02 partial observations on current build `09b4571b34594b39e9d19be3320f334bf7d608a333e0d06902dfda0a361259b8`. It does not change either completed protocol, launch another host job, or advance TASK022. Root operates the host after a separate reviewed frozen successor. No production, system-app, clipboard, watcher or canonical changes are proposed.

The completed keyboard02 evidence already covers chosen-result activation, source Escape and visible exact focus return, List selection/More/Back and process-source navigation. Retain its exact Option-Tab sequences. Focus here acted on the already-current00001; Light repeated only help/source/close; the window-menu attempt moved to a wider display. Neither inference closes the missing observations.

## Small independent keyboard and motion subset

In the clean owned disposable document, record the actual browser, theme, viewport and settings baseline. Repeat the chosen-result and List selection/Back flow in Light using actual keys and recorded IDs, with visible focus and retained route/content observations. In List rooted00001, identify the distinct00000 row by its actual ID before activating its Focus here control; require the new root and shown definition to identify00000, then Back to the recorded prior state. Record any failed or different behavior directly. Do not accept an unchanged root as a changed-focus result.

For motion, record the actual Reduce Motion baseline, observe a representative Map focus/More transition with the ordinary setting, then enable Reduce Motion through the existing host settings owner and repeat the same actions. Observe the actual transition and final content, not merely an available AX tree or a checked setting. A read-only `matchMedia('(prefers-reduced-motion: reduce)').matches` observation may corroborate the media state but cannot replace the visual transition. Restore and positively verify the original setting. If both modes are static, report exactly that observation rather than inventing a contrast.

## Feasible narrow Safari option for review

Apple documents **Develop → Enter Responsive Design Mode** (Control-Command-R), editable viewport dimensions, pixel-ratio controls and an automatically adjusted presentation scale. Its size display is in screen points; it is not itself a measured CSS-width result. The mode can be used with Web Inspector. [Apple Responsive Design Mode](https://developer.apple.com/documentation/safari-developer-tools/responsive-design-mode).

Proposed bounded procedure, not executed: capture the owned document identity and clean origin, original window geometry, Page Zoom, developer-menu preference, and existing responsive-mode custom dimensions/pixel ratio before changing anything. Request a custom320×800 view and ratio1, using Page Zoom100% for the measurement; record the mode's displayed scale separately. Select a shorter height if needed to keep the presentation at100%, recording the actual height. Do not use Move & Resize>Left again or infer CSS width from physical screenshots.

In Web Inspector attached only to that verified clean owned document, the following proposed **read-only** expression provides actual viewport measurements without reading a private URL, cookies, storage or unrelated data:

```javascript
({ innerWidth, clientWidth: document.documentElement.clientWidth,
   visualWidth: window.visualViewport?.width, devicePixelRatio,
   scrollWidth: document.documentElement.scrollWidth })
```

Require actual `innerWidth` and `clientWidth` of320 to call the result320CSSpx. Otherwise retain the measured dimensions and leave that exact target unmet. Capture surrounding search, filters, status, entry text, source drawer and first complete relationship sentence in both themes, including actual keyboard focus near opened controls. Record any horizontal overflow and which content causes it; the diagram exception does not excuse adjacent text or controls. Native representative target geometry may be measured read-only and paired with real hit/focus observations, keeping it distinct from earlier headless measurements and from speech. This is Safari's responsive viewport, not a tested iOS device or assistive-technology result.

If Develop is absent, Apple describes the Advanced preference that shows developer features. The host would need to capture and restore that exact preference as part of the later reviewed job. [Safari26 developer tools](https://support.apple.com/en-mk/guide/safari/sfri20948/26.0/mac/26). If inspection, setting restoration, or controlled measurement is unavailable, stop this subset and report the capability limit; do not substitute assumed pixels. This preparation has not verified that root's current CUA can operate all of these controls.

Restore the prior responsive custom dimensions/pixel ratio, exit the mode, close only the owned Inspector, and restore the actual baseline Page Zoom, theme, window geometry and developer preference. Positively verify each affected state. No new Simulator, browser automation permission, extension or remote-automation setting is needed by this proposal. Preserve any unrelated documents. The driver stop/receipt must precede final Safari restoration; if Safari began nonrunning, a final host Quit and subsequent positive absence observation follow all driver AppleEvents.

## Actual speech remains a separate capability or participant gate

`voiceover-observation-method-decision.md` distinguishes actual VoiceOver words from Safari AX names and explains the current caption-observability limit. The blank `voiceover-utterance-checklist.md` is ready for a real observer to report words, silence, repetitions and help. Approval, process activation, DOM live-region strings and keyboard success supply no utterance. No general clipboard read/change or Desktop audio archive is authorized by this plan. A future confined copied-phrase observer would need its own reviewed preservation/concurrency mechanism; none is currently admitted.

Windows/browser/AT remains explicitly unexercised. TASK023's coordinated full protected-read window, TASK024's frozen benchmark04 and TASK025's actual comprehension participant remain behind the original dependencies. The watcher remains root-held. This document is a reviewable option and a remaining-work map, not an execution descriptor or an acceptance result.
