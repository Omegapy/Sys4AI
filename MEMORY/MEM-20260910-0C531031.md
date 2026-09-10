---
{
  "applicability": [
    "The observation at 2026-09-09T02:31:12.103208+00:00 and its exact retained artifact versions."
  ],
  "claim": {
    "level": "historical_context",
    "summary": "The intact 2026-09-09 receipt and retained exact artifacts support the earlier automatic-capture and initializer-v6 observation; this note does not verify the current implementation."
  },
  "confidence": "high",
  "created": "2026-09-10T18:55:58.109061+00:00",
  "id": "MEM-20260910-0C531031",
  "lifecycle": {
    "reason": "The original verified observation is retained with exact historical artifact bytes; its capture and initializer versions differ from the current implementation. The successor records historical context and makes no renewed current verification claim.",
    "superseded_by": null,
    "supersedes": [
      "MEM-20260909-89C402A6"
    ]
  },
  "limitations": [
    "Current capture and initializer code differ from the original observed versions; current verification requires its own observed result.",
    "The original check used disposable fixtures and documented skips. This disposition did not rerun or broaden that historical test result.",
    "Historical memory does not grant current execution, publication, installation or maintenance authority."
  ],
  "modified": "2026-09-10T18:55:58.109061+00:00",
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
    "approved_at": "2026-09-10T18:55:58.109061+00:00",
    "operation_id": "MEMOP-ontology-health-historical-20260910"
  },
  "schema_version": 1,
  "sources": [
    {
      "kind": "verification",
      "locator": "json:/outcome",
      "path": "Verification/automatic-memory-capture/verification.json",
      "sha256": "06bad7195d7fabed2b8d7328a7bbe22c751b9262582ca151403cc436dba479e0"
    },
    {
      "kind": "source",
      "locator": "document",
      "path": "Verification/project-memory/evidence/verification-06bad7195d7fabed2b8d7328a7bbe22c751b9262582ca151403cc436dba479e0.json",
      "sha256": "f01307389f32e8466dce4c32df00839e379a43e9befe37d54e27887a7aeee094"
    },
    {
      "kind": "source",
      "locator": "json:/artifacts",
      "path": "Verification/ontology-health-repairs/memory/retained-artifact-manifest.json",
      "sha256": "a355b85521670d19e5962eaa42e214d6608e236fac019dc0e07ca82066f85e34"
    }
  ],
  "state": "active",
  "title": "Historical automatic-capture v6 verification and current applicability boundary",
  "type": "finding"
}
---
# Historical verification and applicability
The original receipt reports the earlier automatic-capture default and initializer-v6 checks. Its receipt bytes and six referenced test logs retain their original digests. Both changed implementation artifacts were recovered as exact bytes from local Git history; the other observed artifacts were retained from exact matching project bytes.

The predecessor remains readable with its original claim, sources, body and publication history. Current capture and initializer implementations differ from that observation. This successor provides historical context only; current operational readiness and current verification require their own final-version checks.
