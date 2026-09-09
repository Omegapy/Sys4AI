# Memory package

This reusable capability contains the [skill](SKILL.md), standard-library core,
source retrieval/normalization, guarded backend integration, and behavior
tests. Installation occurs through the explicit Sys4AI Template/adoption
workflow. Copying a skill does not grant publication or backend provisioning.

Run focused tests from the owning depot with `PYTHONDONTWRITEBYTECODE=1` and
its `.venv/bin/python`. Canonical contracts and empty starter content are
owned separately by `MEMORY-depo/` and are adopted at
`reference-assets/MEMORY-depo/`.

[Automatic capture](references/automatic-capture.md) is the one shared entry for
completion and the optional `what-did-you-learn` module's explicit review. A
compatible learning module supplies the review and improvement disposition;
this package still owns every retrieval, publication and recovery operation.
Memory-only installations retain their existing workflow. Review-only mode
makes no writes; capture off prevents automatic persistence while preserving
explicitly requested authorized saves. Neither path refreshes indexes. A missing
learning dependency is reported without silently installing or repairing it.
