# Current observed keyboard evidence and pending native acceptance

The current production build is `09b4571b34594b39e9d19be3320f334bf7d608a333e0d06902dfda0a361259b8`. Root executed keyboard03 in Chrome 154.0.8037.57. Its exact public report is `qualification-tests/actual-keyboard-03/stdout.json`, with root receipt and attribution beside it.

Four keyboard flows passed using actual typing, Tab, Shift+Tab, Enter and Escape: search to entry, source reading and exact focus return, renderer-independent List selection/More connections/Focus here, and discovery of the non-starting process by its recorded **Fixture ordered inspection** label followed by step-source reading and return. All 14 target centers were inside the viewport and unobscured; the exact canonical process href remained intact. Live-region strings were read from the DOM. They are not observed screen-reader speech.

The initial root wrapper rejected the same reviewed driver for an outdated minimum traversal-count expectation. Its failed receipt is retained under `qualification-tests/actual-keyboard-03-wrapper-failure`; no original raw stdout existed and none was reconstructed. A corrected wrapper reran the unchanged frozen job and produced the passing evidence above.

Actual Safari/VoiceOver acceptance remains unperformed. Root observed the Mac locked, could not automatically unlock it, and asked the user to unlock. Native04 has not launched. No Safari/VoiceOver version, announcement, caption, setting change, restoration or native 200-percent Map/List observation is claimed for this qualification. Earlier actual Chrome zoom evidence belongs to its separately attributed Service V3 scope and does not replace Safari/VoiceOver.

Windows/browser/assistive-technology testing was not exercised. Complete target-size exception review and native reflow/focus review remain pending. The exact native protocol is `qualification-tests/native-at-protocol.md`; it requires actual captions or speech, keyboard outcomes, original-setting capture and positive restoration, and closure of only the owned document.

Automated partial scans and the actual two-theme expiry scan are recorded in `accessibility-results.json`. They do not establish full accessibility or WCAG conformance. The diagram exception does not extend to surrounding text or controls.
