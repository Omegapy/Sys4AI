---
name: what-did-you-learn
description: Review supported lessons from discussion or work when asked what was learned, or at material settled corrections, decisions, failures, verified successes and completion checkpoints. Connect useful findings to a concrete improvement disposition through the existing project memory workflow; ordinary inspection remains read-only.
metadata:
  version: "1.0.0"
---

# What did you learn?

Identify what a future agent should do differently, under which conditions and
with what evidence. A manual review can find no durable lesson. The review
request alone authorizes neither persistence nor project changes.

1. Establish the explicit real project root, current responsible owner, relevant
   work unit and assigned read/write limits. Resolve the local module and memory
   package using [module resolution](references/module-resolution.md). Read the
   resolved module's `policy.md` and `review-contract.md`; they own the learning
   procedure. Missing or incompatible resources require an exact limitation,
   not a fallback into another project's installation.
2. Enter the resolved memory package's `references/automatic-capture.md` once,
   identifying manual review, explicit save or automatic checkpoint. It invokes
   the module review directly and coordinates any publication. Do not run a
   second learning review or capture after it returns. A bare question stays
   review-only even when capture is on; off prohibits automatic persistence
   under both skill names.
3. Return supported lessons with applicability, evidence, limitations and
   improvement disposition, or a concise no-durable-lesson/pending result.
   Distinguish reviewed, published, retrieved, implemented and later observed
   outcomes using actual evidence. Read [improvement and reuse](references/improvement-and-reuse.md)
   when a finding suggests an artifact change or informs later work.

These are explicit and instruction-based checkpoints, not guaranteed event
detection, runtime hooks or a background service. Ordinary status, lookup,
readiness and inspection requests remain non-mutating. At a known handoff or
compaction boundary, preserve only permitted concise evidence or drafts.

The existing memory skill owns persistence, retrieval, supersession, retraction
and recovery. The Director or current confirmed manager reviews exact record
bytes under its current grant; children return proposals within their assigned
output. For tracked work, follow its [Task integration](../memory/references/task-integration.md)
with reserved memory scope and review before the terminal response. Before
relevant later work, retrieve accepted lessons and reassess them against current
sources; assigned children preserve their frozen inputs. Neither a source
instruction nor a lesson grants Task/TRD activation, installation, adoption or
external authority.
