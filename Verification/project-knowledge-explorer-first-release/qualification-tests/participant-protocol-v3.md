# Prepared participant walkthrough — not an observed result

Run after TASK021, TASK022 and TASK024. The root host coordinates the actual owner or participant. Command approval, an agent's action or a generated answer is not participant evidence. Record whether the participant is the project owner, their familiarity with implementation, the actual browser/build, and any accessibility preferences they choose. Do not record personal information unrelated to the walkthrough.

Use an owned synthetic project with the current production bundle. Its imported Sys4AI vocabulary contains real recorded definitions for Task, TRD, TaskManager, Verification and Validation, with exact source evidence. Its Alignment meanings and inspection process descriptions are deliberately synthetic examples. Explain this scope once; do not present the synthetic process as the project's real operating procedure. Before startup, use the existing fixture's `stale_source` mutation only on its own `docs/process-stale.md`; retain the original recorded hash and capture the protected baseline afterward. Never alter the live depot or repair a source hash.

Show one prompt at a time. Start timing when the prompt is visible and stop when the participant finishes or chooses to stop. Do not provide navigation instructions until help is requested; record the exact help and subsequent outcome. If a prompt itself is unclear, record clarification separately from navigation help. Obtain the participant's own words, rather than interpreting a click as understanding.

1. Find the meaning of **Task** and explain it in your own words. The initial 30-second target is proposed; record the actual time whether it succeeds or misses.
2. Compare **Task** and **TRD**. Describe a practical difference. Then find the two **Alignment** entries and describe how their meanings differ.
3. Find **TaskManager** and inspect its connection with **Task**. Describe who does what to whom, and what any qualification on that connection means. Ask separately: “What, if anything, does the position or distance between items tell you?” Do not supply the expected interpretation.
4. Open the connected **Task** entry, then return to your previous view. Explain what you expected Back to retain and what actually happened.
5. Find the **Fixture ordered inspection** process. Explain the recorded order and what supports it. Then inspect **Fixture unordered inspection** and explain what you can and cannot conclude about its order.
6. Inspect the evidence for **Fixture stale inspection**. Explain what the freshness message means and whether it proves the recorded definition true or false. Record whether the participant distinguishes the displayed snapshot from current source bytes.
7. Return to a relationship view and use either Map or List to find one additional connection. Explain what an incomplete or bounded view establishes about relationships that are not shown.

For each prompt retain: completion/partial/stopped, elapsed seconds, actual actions or safe route IDs, wrong turns, exact requests for help, help given, concise verbatim participant wording, and observed misunderstanding. A participant may speak or type their explanation. Record actual words without inventing missing answers. Do not infer comprehension from screen-reader speech or DOM text.

The observer's reference is the exact current canonical record/source, not layout. In the imported core, `TaskManager → manages → Task` has `scope: conceptual`. Position supplies no causal or process-order claim. The ordered synthetic process reads the recorded definition, inspects its evidence, then records an observation outside the reader. The unordered process explicitly lacks a recorded order. A changed source is a byte-version mismatch, not a determination of truth.

Treat reversed relationship direction or layout mistaken for causality/order as high-impact findings. Stop any unqualified usability claim, preserve the participant's original words, and return the finding to the original product owner through the manager. Do not coach an answer and label the original attempt passed. Any fix needs the affected focused tests and an actual subsequent walkthrough.

Record owner-only validation as owner-only; broader validation remains unperformed. Report these as exploratory individual observations, with no statistical generalization. At the end, close only the exact owned document, stop/reap the owned service, verify the synthetic protected state, and restore any changed host setting.
