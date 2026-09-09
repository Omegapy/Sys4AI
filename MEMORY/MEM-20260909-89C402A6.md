---
{
  "applicability": [
    "Sys4AI automatic-capture implementation and initializer governance-starter-v6."
  ],
  "claim": {
    "level": "verified_outcome",
    "summary": "The capture helper supports on/off preferences, and initializer v6 enables automatic capture for new installations and returns a post-setup opt-out notice."
  },
  "confidence": "high",
  "created": "2026-09-09T02:31:12.143105+00:00",
  "id": "MEM-20260909-89C402A6",
  "lifecycle": {
    "reason": null,
    "superseded_by": null,
    "supersedes": []
  },
  "limitations": [
    "Automatic capture runs in the agent completion workflow; there is no background scheduler.",
    "Existing project opt-outs and older setup receipts are preserved.",
    "Initialization and first-capture integration tests use disposable projects and explicit native receipt fixtures."
  ],
  "modified": "2026-09-09T02:31:12.143105+00:00",
  "origin": {
    "execution_id": null,
    "generation": null,
    "role": null,
    "task_id": null,
    "task_path": null
  },
  "project_id": "sys4ai-depot",
  "publication": {
    "actor_id": "/root",
    "actor_kind": "director",
    "approved_at": "2026-09-09T02:31:12.143105+00:00",
    "operation_id": "MEMOP-auto-capture-default-on-001"
  },
  "schema_version": 1,
  "sources": [
    {
      "kind": "verification",
      "locator": "json:/outcome",
      "path": "Verification/automatic-memory-capture/verification.json",
      "sha256": "06bad7195d7fabed2b8d7328a7bbe22c751b9262582ca151403cc436dba479e0"
    }
  ],
  "state": "active",
  "title": "Automatic capture defaults on for new memory installations",
  "type": "finding"
}
---
# Capture default and initialization
New memory installations start with automatic capture on. At substantive work completion, the owning agent reviews useful durable findings and publishes through the checked capture helper.

Initializer v6 reports the actual setting and offers to turn capture off after successful setup. The explicit off preference survives reruns; current project evidence and publication authority remain required.
