---
{
  "applicability": [
    "The isolated Learning-Lab intent-routing fixture only; recheck current requirements before reuse."
  ],
  "claim": {
    "level": "accepted_design",
    "summary": "The revised controlled design requires non-empty acceptance criteria, superseding the earlier presence-only rule."
  },
  "confidence": "high",
  "created": "2026-09-09T05:49:15.986007+00:00",
  "id": "MEM-20260909-C3D4E5F6",
  "lifecycle": {
    "reason": "Current controlled design requires non-empty acceptance criteria; preserve the earlier limited decision as superseded history.",
    "superseded_by": null,
    "supersedes": [
      "MEM-20260909-B2C3D4E5"
    ]
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
      "path": "context/lifecycle-v2.md",
      "sha256": "cf941771d1a9921d2c8ef1501b93a9f8993b54dd1c18556b806d8bac2e3eed7b"
    }
  ],
  "state": "active",
  "title": "Validate material field content against current requirements",
  "type": "lesson"
}
---
## Observation

The current controlled lifecycle design rejects a present but empty acceptance-criteria field.

## Evidence

context/lifecycle-v2.md records the revised accepted fixture design and identifies its predecessor.

## Lesson and applicability

Recheck content, not only field presence, when deciding whether this fixture's material intent is complete.

## Limitations

This is a controlled lifecycle revision. The later implementation unit must independently recheck current intent requirements and behavior.

## Improvement disposition

The original field-presence-only note is superseded while its original body and history remain. Any code improvement remains restricted to the separately authorized fixture target.

## Validation and follow-up

The actual two-record supersession must recover the original operation after a controlled interruption. Verify one active successor and one retained superseded predecessor before reporting success.
