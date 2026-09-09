---
{
  "applicability": [
    "The observed Sys4AI root configuration and memory search implementation versions."
  ],
  "claim": {
    "level": "verified_outcome",
    "summary": "Root health, one lexical source lookup and validate preserved the inspected files with semantic retrieval disabled."
  },
  "confidence": "high",
  "created": "2026-09-08T21:28:16.041859+00:00",
  "id": "MEM-20260908-6A59F482",
  "lifecycle": {
    "reason": null,
    "superseded_by": null,
    "supersedes": []
  },
  "limitations": [
    "The root test covered health, one exact-term source query and validate with no learned records initially.",
    "This finding does not claim a backend pilot pass, native Task integration, arbitrary source formats or other project adoption."
  ],
  "modified": "2026-09-08T21:28:50.850240+00:00",
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
    "approved_at": "2026-09-08T21:28:50.850240+00:00",
    "operation_id": "MEMOP-root-lexical-validation-001"
  },
  "schema_version": 1,
  "sources": [
    {
      "kind": "verification",
      "locator": "json:/outcome",
      "path": "Verification/project-memory/root-lexical-observation.json",
      "sha256": "4f84c91e22d1aeb419553181e31b3d04f608de61f469273a4dd841d322329811"
    },
    {
      "kind": "source",
      "locator": "section:def search",
      "path": ".agents/skills/memory/scripts/memory_search.py",
      "sha256": "294877068712251bfde91309e2d444eb47b13f1e8c8ca98e3882684dc4ab7f6b"
    }
  ],
  "state": "active",
  "title": "Root lexical lookup preserves inspected state",
  "type": "finding"
}
---
# Observed result

With the semantic backend disabled, the root memory helper returned README.md for the exact query `project-local`. Public health, lexical search and validate preserved the bytes and modification times of all 175 files in the recorded inspection scope. The evidence includes the actual commands, returned source and before/after hashes.

Use direct Markdown and lexical lookup when semantic retrieval is unavailable. Reinspect current configuration and source versions before applying this recorded result to later work.
