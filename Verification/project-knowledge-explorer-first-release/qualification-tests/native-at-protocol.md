# Safari and VoiceOver observation protocol

This is preparation for TASK-022, not a result. Run only after TASK-021 passes.
Use the current production build in an independent synthetic project. The host
opens one owned Safari document with the private bootstrap URL through process
memory, observes that the exact owned document URL is clean, then permits UI
inspection. Never retain a bootstrap URL, session value, trace or HAR.

Before the first action, record actual macOS, Safari and VoiceOver versions,
VoiceOver on/off state, caption-panel setting, current browser zoom, theme and
reduced-motion preference. Keep those exact restoration values. Do not close
existing documents or change a global default browser. Windows testing is
unperformed unless a real Windows/browser/AT environment is available.

For every task below, record the actual key sequence, actual VoiceOver spoken or
caption text, focused control, outcome and any failure. A DOM/AX name is not an
announcement observation. Capture only the clean synthetic document and the
VoiceOver caption panel; omit unrelated screen content.

1. Starting from Overview, move by keyboard to “Search project knowledge”.
   Confirm VoiceOver announces its name and combobox state. Type “Orientation”.
   Observe result feedback, move through the two separate Alignment choices
   with arrow keys and hear enough recorded identity distinction to choose one.
   Escape closes the suggestions and preserves the search focus. Submit using
   Enter or the visible Search button and open a chosen result by keyboard.
2. Read the entry name and definition before technical identity details. Reach
   Aliases, Scope, Examples and Non-examples. Open Sources, choose the exact
   source control, hear the source heading/state and read the plain-text excerpt.
   Escape closes the drawer and restores the exact source trigger with visible,
   unobscured focus. Open and close Reader help through keyboard controls.
3. Open Relationships in List. Use selection, Focus here and More connections
   through keyboard; read subject/predicate/object in canonical order. Inspect
   a relation's source. Move Back and confirm the useful previous selection and
   scope are restored. Do not require a canvas, drag, hover or double-click.
   Observe meaningful result/selection announcements and check that layout does
   not produce repeated screen-reader announcements.
4. Open Processes. Observe that each finite selected process resolves its recorded human name, with its exact ID retained. Reach the non-starting ‘Fixture ordered inspection’ by its recorded label using the keyboard, then read its recorded steps and step evidence.
   Read the unordered process and its exact absence-of-recorded-order message.
   No task invokes or executes a process.
5. Repeat the essential search, source drawer, List and menu/focus actions in
   the second theme. Record any contrast, invisible focus or target difficulty.
6. Set and positively observe actual Safari browser zoom at 200 percent; retain
   the original zoom for restoration. Inspect reflow and usable controls around
   the map as well as ordinary entry/source text. Separately use a real narrow
   content window or measured 320 CSS-pixel viewport and report which was tested.
   A text-size override or page-scale factor is not browser zoom.
7. Temporarily enable reduced motion if needed, observe the actual setting and
   graph/focus transitions, then restore it. A graph exception does not cover
   surrounding text or controls. Record manual target-size exceptions explicitly
   if a target is smaller than 24 CSS pixels; do not infer an exception from a
   scanner pass.
8. Close the reading session while on an entry and observe retained text plus
   the session status announcement and reopening guidance.

Restore every recorded setting, including browser zoom, VoiceOver state and
caption configuration; positively verify restoration. Identify the exact owned document/tab in the native browser observation and
close only that document/tab. If its window gained unrelated tabs, preserve them;
window identity alone is insufficient closing authority. Record the exact closure
observation. Stop the exact disposable service, reap its worker and inspect
the fixture preservation comparison. Report an actual unavailable capability or
observed failure as such. Do not turn a scanner result into a WCAG compliance
claim, and do not substitute this host-operated AT walkthrough for TASK-025's
actual participant or owner comprehension evidence.
