# Exact document correction

The host reviewed the draft and identified one source-terminology error. In the C1/C2 table, the retained values come from curator_session.json events[].sha256. They are event-record hashes, not observation snapshot hashes (context.snapshot / observation.snapshot).

Change only the table header from Snapshot SHA-256 to Event-record SHA-256, preserving both values and all requirement content. Produce new trd-input-v2.json and coverage-checks-v2.json in the existing worker directory; retain the v1 files unchanged. Run only the focused source/header and current-schema payload checks. No new content, system work or canonical writes.

The manager already integrated v1 as draft TRD-20260912-483C93BD revision 1 before this correction arrived. The manager will perform the official content update to revision 2 after accepting the corrected payload. Return v2 paths and hashes and stop.
