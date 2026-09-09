---
{
  "applicability": [
    "The isolated Learning-Lab intent-routing fixture only; recheck current requirements before reuse."
  ],
  "claim": {
    "level": "accepted_design",
    "summary": "The Director accepted a deliberately limited field-presence rule for the isolated lifecycle test."
  },
  "confidence": "high",
  "created": "2026-09-09T05:48:35.814904+00:00",
  "id": "MEM-20260909-B2C3D4E5",
  "lifecycle": {
    "reason": "Current controlled design requires non-empty acceptance criteria; preserve the earlier limited decision as superseded history.",
    "superseded_by": "MEM-20260909-C3D4E5F6",
    "supersedes": []
  },
  "limitations": [
    "Controlled accepted fixture design, not production behavior or a long-term reliability measurement."
  ],
  "modified": "2026-09-09T05:49:15.986007+00:00",
  "origin": {
    "execution_id": null,
    "generation": null,
    "role": null,
    "task_id": null,
    "task_path": null
  },
  "project_id": "wdyl-lab",
  "publication": {
    "actor_id": "/root",
    "actor_kind": "director",
    "approved_at": "2026-09-09T05:49:15.986007+00:00",
    "operation_id": "MEMOP-wdyl-native-supersede-001"
  },
  "schema_version": 1,
  "sources": [
    {
      "kind": "design",
      "locator": "document",
      "path": "context/lifecycle-v1.md",
      "sha256": "c9b3098f9df464d075979de5b1952b021d9ef24ef311f7a6210e68961cf00e74"
    }
  ],
  "state": "superseded",
  "title": "Earlier controlled field-presence rule",
  "type": "lesson"
}
---
## Observation

The controlled earlier lifecycle design accepts field presence alone.

## Evidence

context/lifecycle-v1.md records this deliberately limited fixture decision.

## Lesson and applicability

For this earlier lifecycle design only, a present acceptance_criteria field satisfies presence validation.

## Limitations

This does not establish that an empty field is useful or that final intent requirements are satisfied. It is a controlled supersession input, not a production recommendation.

## Improvement disposition

Separate scoped lifecycle review must revise this note if the accepted design changes. No code change is authorized by the record itself.

## Validation and follow-up

Keep the original body and explicit history when conflicting current design supersedes this earlier decision.
