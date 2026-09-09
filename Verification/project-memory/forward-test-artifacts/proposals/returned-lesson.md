---
{
  "applicability": [
    "Exact integer arithmetic for the three sampled positive integer inputs."
  ],
  "claim": {
    "level": "verified_outcome",
    "summary": "Direct integer sums and n(n+1)/2 agreed for n=1, 10, and 100 in the observed arithmetic check."
  },
  "confidence": "high",
  "created": "2026-09-08T21:01:18.451006+00:00",
  "id": "MEM-20260908-14436ED6",
  "lifecycle": {
    "reason": null,
    "superseded_by": null,
    "supersedes": []
  },
  "limitations": [
    "Three finite cases are not a proof of the formula for every positive integer."
  ],
  "modified": "2026-09-08T21:01:18.451006+00:00",
  "origin": {
    "execution_id": null,
    "generation": null,
    "role": null,
    "task_id": null,
    "task_path": null
  },
  "project_id": "triangular-checks",
  "publication": null,
  "schema_version": 1,
  "sources": [
    {
      "kind": "source",
      "locator": "label:eq:triangular-total",
      "path": "research/triangular.tex",
      "sha256": "7fb8897dc9a1507109a2fe6a1dfa520874124b5cbe8b6c4ab68685e0fb11c5d4"
    },
    {
      "kind": "verification",
      "locator": "json:/outcome",
      "path": "docs/checks/triangular-check.json",
      "sha256": "3385d6f3bd63e6d076229f6ad8aedf1317806e4d6ad8ac7597f1e84f0461a026"
    }
  ],
  "state": "draft",
  "title": "Finite triangular checks support the sampled cases",
  "type": "lesson"
}
---
# Lesson from the triangular sum check

The check compared direct integer sums with n*(n+1)//2 at n=1, 10, and 100 and passed. Retain these as regression examples. Their agreement does not prove the formula for untested values.
